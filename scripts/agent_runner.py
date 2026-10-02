#!/usr/bin/env python3
"""THE ARK offline agent: bounded local planning + allowlisted tools."""
from __future__ import annotations

import argparse, datetime as dt, hashlib, json, os, pathlib, re, shutil
import socket, sqlite3, sys, time, urllib.request
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from kiwix_client import search_kiwix
from vector_client import vector_search

DEFAULT_VAULT = pathlib.Path(os.getenv("ENDWORLD_VAULT", "/srv/endworld"))
LLAMA_URL = os.getenv("ENDWORLD_AGENT_LLM_URL", "http://127.0.0.1:8082/v1/chat/completions")
MAX_TEXT = 12000

ROLE_GUIDANCE = {
    "field": "Prioritize immediate offline operability, concise steps, local evidence and resource constraints.",
    "research": "Prioritize source-grounded synthesis, citations, uncertainty and cross-checking local evidence.",
    "engineer": "Prioritize reproducible technical diagnosis, architecture and safe non-destructive implementation steps.",
    "coordinator": "Reconcile specialist findings, resolve conflicts, track evidence and produce one bounded execution plan.",
}

class AgentError(RuntimeError): pass
class PolicyDenied(AgentError): pass

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def internet_online():
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=.35):
            return True
    except OSError:
        return False

def safe_name(value):
    return (re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")[:80] or "field-note")

@dataclass
class State:
    task_id: str
    goal: str
    profile: str
    task_dir: pathlib.Path
    evidence: dict = field(default_factory=dict)
    step: int = 0
    role: str = "field"

    @property
    def workspace(self):
        return self.task_dir.parents[1] / "workspace"

    def event(self, kind, **data):
        row = {"ts": now(), "step": self.step, "kind": kind, **data}
        self.task_dir.mkdir(parents=True, exist_ok=True)
        with (self.task_dir / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self.persist()

    def persist(self, status="running", answer=None):
        payload = {
            "schema": 1, "task_id": self.task_id, "goal": self.goal,
            "profile": self.profile, "role": self.role, "status": status, "step": self.step,
            "updated_at": now(), "workspace": str(self.workspace),
            "evidence": [{k:v for k,v in x.items() if k != "_body"} for x in self.evidence.values()],
        }
        if answer is not None: payload["answer"] = answer
        self.task_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.task_dir / "task.json.tmp"
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, self.task_dir / "task.json")

class Tools:
    def __init__(self, vault, profile, state):
        self.vault = vault.resolve(); self.profile = profile; self.state = state
        self.allowed = {
            "ark.search": self.search, "ark.read_source": self.read_source,
            "ark.status": self.status, "ark.maps": self.maps,
            "ark.write_note": self.write_note, "ark.mesh_status": self.mesh_status,
            "ark.playbook": self.playbook,
        }

    def call(self, name, args):
        if name not in self.allowed:
            raise PolicyDenied("tool not allowlisted: " + name)
        if not isinstance(args, dict): raise AgentError("tool args must be an object")
        return self.allowed[name](args)

    def _fts(self, query, limit):
        dbp = self.vault / "state/search/ark-search.sqlite"
        if not dbp.is_file(): return []
        toks = re.findall(r"[\w.+#/-]+", query, flags=re.UNICODE)[:12]
        if not toks: return []
        match = " AND ".join('"' + t.replace('"',"") + '"' for t in toks)
        try:
            db = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True)
            rows = db.execute("""SELECT source,title,kind,url,substr(body,1,12000),bm25(ark_fts)
              FROM ark_fts WHERE ark_fts MATCH ? ORDER BY bm25(ark_fts) LIMIT ?""",
              (match, max(1,min(limit,12)))).fetchall()
            db.close()
        except sqlite3.Error:
            return []
        return [{"source":r[0],"title":r[1],"kind":r[2],"url":r[3],
                 "_body":r[4],"score":r[5],"excerpt":(r[4] or "")[:420]} for r in rows]

    def search(self, args):
        q = str(args.get("query") or "").strip()
        if not q: raise AgentError("query required")
        limit = max(1,min(int(args.get("limit",6)),10))
        hits = self._fts(q, max(1,limit//2))
        hits += vector_search(q,max(1,limit//3))
        if len(hits) < limit:
            hits += search_kiwix(q, self.vault/"knowledge/zim", limit=limit-len(hits))
        out=[]
        for hit in hits[:limit]:
            eid=f"E{len(self.state.evidence)+1}"
            rec={"id":eid,**hit}; self.state.evidence[eid]=rec
            out.append({k:v for k,v in rec.items() if k!="_body"})
        return {"query":q,"results":out}

    def read_source(self,args):
        eid=str(args.get("id") or "").upper(); rec=self.state.evidence.get(eid)
        if not rec: raise AgentError("source id must come from ark.search")
        return {"id":eid,"title":rec.get("title"),"source":rec.get("source"),
                "kind":rec.get("kind"),"text":str(rec.get("_body") or "")[:MAX_TEXT]}

    def status(self,args):
        services={}
        for name,url in {"portal":"http://127.0.0.1/health","knowledge":"http://127.0.0.1:8081/",
                         "ai":"http://127.0.0.1:8082/health","voice":"http://127.0.0.1:8083/"}.items():
            try:
                with urllib.request.urlopen(url,timeout=1.2) as r: services[name]=200<=r.status<500
            except Exception: services[name]=False
        maps=list((self.vault/"maps/tiles").glob("*.pmtiles")) if (self.vault/"maps/tiles").is_dir() else []
        return {"profile":self.profile,"internet":internet_online(),"services":services,
                "maps":len(maps),"frozen_vault":str(self.vault),"workspace":str(self.state.workspace)}

    def maps(self,args):
        root=self.vault/"maps/tiles"; rows=[]
        if root.is_dir():
            for p in sorted(root.glob("*.pmtiles")):
                rows.append({"id":p.stem,"bytes":p.stat().st_size,"path":str(p.relative_to(self.vault))})
        return {"maps":rows}

    def write_note(self,args):
        name=safe_name(str(args.get("name") or "field-note")); text=str(args.get("text") or "")
        if not text.strip(): raise AgentError("note text required")
        if len(text.encode())>65536: raise AgentError("note exceeds 64 KiB")
        self.state.workspace.mkdir(parents=True,exist_ok=True)
        dest=(self.state.workspace/(name+".md")).resolve()
        try: dest.relative_to(self.state.workspace.resolve())
        except ValueError: raise PolicyDenied("workspace escape rejected")
        dest.write_text(text.rstrip()+"\n",encoding="utf-8")
        return {"written":True,"path":str(dest),"bytes":dest.stat().st_size}

    def mesh_status(self,args):
        return {"ark_mesh_script":(ROOT/"scripts/ark_mesh.py").is_file(),
                "reticulum_cli":shutil.which("rnstatus") is not None,
                "comms_plan":(self.vault/"state/field/comms-plan.md").is_file(),
                "mesh_state":(self.vault/"state/mesh").is_dir()}

    def playbook(self,args):
        name=str(args.get("name") or "")
        if name=="integrity-summary":
            p=self.vault/"lock"/(self.profile+".lock.json")
            if not p.is_file(): return {"ok":False,"reason":"lock missing"}
            d=json.loads(p.read_text(encoding="utf-8"))
            return {"ok":not d.get("failures"),"profile":d.get("profile"),
                    "artifacts":len(d.get("artifacts",[])),"containers":len(d.get("containers",[])),
                    "payload_bytes":d.get("payload_bytes")}
        if name=="field-readiness":
            maps=list((self.vault/"maps/tiles").glob("*.pmtiles")) if (self.vault/"maps/tiles").is_dir() else []
            return {"internet":internet_online(),"comms_plan":(self.vault/"state/field/comms-plan.md").is_file(),
                    "maps":len(maps)}
        raise PolicyDenied("playbook not allowlisted: "+name)

class Agent:
    def __init__(self,vault,profile,goal,task_id,max_steps=8,timeout_s=240,role="field"):
        if role not in ROLE_GUIDANCE: raise AgentError("unknown role: "+str(role))
        self.state=State(task_id,goal,profile,vault/"state/agent/tasks"/task_id,role=role)
        self.tools=Tools(vault,profile,self.state); self.max_steps=max(1,min(max_steps,16))
        self.deadline=time.monotonic()+max(30,timeout_s)

    def system(self):
        role_line = ROLE_GUIDANCE[self.state.role]
        return """You are THE ARK offline field agent.
Current specialist role: %s
Role guidance: %s
Return exactly one JSON object and no markdown.
Tool action: {"action":"tool","tool":"ark.search","args":{"query":"..."}}
Final action: {"action":"final","answer":"..."}
Allowed tools: ark.search(query,limit), ark.read_source(id), ark.status(),
ark.maps(), ark.write_note(name,text), ark.mesh_status(),
ark.playbook(name) where name is integrity-summary or field-readiness.
Only cite source ids returned by tools, such as [E1].
There is no arbitrary shell, package installation, disk flashing, trust-root
change or silent WAN fallback. Frozen vault data is read-only. If a request
needs a forbidden action, say so rather than inventing a capability.""" % (self.state.role, role_line)

    def model(self,messages):
        payload={"model":"local","messages":messages,"temperature":.1,
                 "max_tokens":int(os.getenv("ENDWORLD_AGENT_MAX_TOKENS","512")),"stream":False}
        req=urllib.request.Request(LLAMA_URL,data=json.dumps(payload).encode(),
                                   headers={"Content-Type":"application/json"},method="POST")
        timeout=min(90,max(5,int(self.deadline-time.monotonic())))
        with urllib.request.urlopen(req,timeout=timeout) as r: data=json.load(r)
        raw=str(data.get("choices",[{}])[0].get("message",{}).get("content","")).strip()
        fence=chr(96)*3
        if raw.startswith(fence):
            raw=re.sub(r"^"+re.escape(fence)+r"(?:json)?\s*|\s*"+re.escape(fence)+r"$","",raw,flags=re.S)
        try: action=json.loads(raw)
        except json.JSONDecodeError as e: raise AgentError("model returned invalid JSON: "+raw[:240]) from e
        if not isinstance(action,dict) or action.get("action") not in {"tool","final"}:
            raise AgentError("invalid agent action")
        return action

    def run(self):
        self.state.workspace.mkdir(parents=True,exist_ok=True)
        self.state.event("task_started",goal=self.state.goal,role=self.state.role)
        messages=[{"role":"system","content":self.system()},{"role":"user","content":self.state.goal}]
        try:
            for step in range(1,self.max_steps+1):
                if time.monotonic()>=self.deadline: raise AgentError("task time limit reached")
                self.state.step=step; action=self.model(messages)
                self.state.event("model_action",action=action)
                if action["action"]=="final":
                    answer=str(action.get("answer") or "").strip()
                    if not answer: raise AgentError("empty final answer")
                    self.state.event("task_completed",answer=answer); self.state.persist("completed",answer)
                    return {"ok":True,"task_id":self.state.task_id,"answer":answer,
                            "workspace":str(self.state.workspace),"steps":step}
                tool=str(action.get("tool") or ""); args=action.get("args") or {}
                try:
                    result=self.tools.call(tool,args)
                    self.state.event("tool_result",tool=tool,args=args,result=result)
                except PolicyDenied as e:
                    result={"error":"POLICY_DENIED","detail":str(e)}
                    self.state.event("policy_denied",tool=tool,args=args,error=str(e))
                except Exception as e:
                    result={"error":"TOOL_ERROR","detail":str(e)}
                    self.state.event("tool_error",tool=tool,args=args,error=str(e))
                messages += [{"role":"assistant","content":json.dumps(action,ensure_ascii=False)},
                             {"role":"user","content":"TOOL RESULT:\n"+json.dumps(result,ensure_ascii=False)[:MAX_TEXT]}]
            raise AgentError("step limit reached")
        except Exception as e:
            self.state.event("task_failed",error=str(e)); self.state.persist("failed",str(e)); raise

def make_task_id(goal):
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+hashlib.sha256(goal.encode()).hexdigest()[:10]

def policy_selftest(vault,profile):
    tid="policy-selftest-"+hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]
    state=State(tid,"policy selftest",profile,vault/"state/agent/tasks"/tid)
    tools=Tools(vault,profile,state); denied=[]
    for tool,args in [("os.shell",{"command":"id"}),("ark.playbook",{"name":"flash-disk"}),
                      ("ark.write_note",{"name":"../escape","text":""})]:
        try: tools.call(tool,args)
        except (PolicyDenied,AgentError): denied.append(tool)
    return {"ok":len(denied)==3,"denied":denied}

def main():
    ap=argparse.ArgumentParser(prog="endworld-agent"); ap.add_argument("goal",nargs="?")
    ap.add_argument("--vault",default=str(DEFAULT_VAULT)); ap.add_argument("--profile",default=os.getenv("ENDWORLD_PROFILE","nano"))
    ap.add_argument("--task-id"); ap.add_argument("--max-steps",type=int,default=8); ap.add_argument("--timeout",type=int,default=240)
    ap.add_argument("--role",choices=sorted(ROLE_GUIDANCE),default="field")
    ap.add_argument("--json",action="store_true"); ap.add_argument("--policy-selftest",action="store_true")
    a=ap.parse_args(); vault=pathlib.Path(a.vault).resolve()
    if a.policy_selftest:
        r=policy_selftest(vault,a.profile); print(json.dumps(r)); return 0 if r["ok"] else 2
    if not a.goal: ap.error("goal is required")
    tid=a.task_id or make_task_id(a.goal)
    try: r=Agent(vault,a.profile,a.goal,tid,a.max_steps,a.timeout,a.role).run()
    except Exception as e:
        r={"ok":False,"task_id":tid,"error":str(e)}; print(json.dumps(r) if a.json else "ERROR: "+str(e)); return 2
    print(json.dumps(r,ensure_ascii=False) if a.json else r["answer"]); return 0

if __name__=="__main__": raise SystemExit(main())
