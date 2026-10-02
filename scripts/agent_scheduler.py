#!/usr/bin/env python3
"""Persistent offline scheduler/event queue for THE ARK Agent."""
from __future__ import annotations
import argparse, datetime as dt, json, os, pathlib, sqlite3, sys, time, uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:sys.path.insert(0,str(ROOT/"scripts"))
from agent_runner import Agent, ROLE_GUIDANCE

def now_ts(): return int(time.time())
def iso(ts=None): return dt.datetime.fromtimestamp(ts or time.time(),dt.timezone.utc).isoformat()

def connect(path:pathlib.Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=10)
    db.execute("pragma journal_mode=WAL")
    db.execute("pragma busy_timeout=10000")
    db.executescript("""
    create table if not exists jobs(
      id text primary key,
      kind text not null check(kind in ('schedule','event')),
      event_name text,
      goal text not null,
      profile text not null,
      role text not null,
      interval_seconds integer,
      next_run integer,
      enabled integer not null default 1,
      max_steps integer not null default 8,
      timeout_seconds integer not null default 240,
      last_task_id text,
      last_status text,
      last_error text,
      created_at text not null,
      updated_at text not null
    );
    create table if not exists events(
      id integer primary key autoincrement,
      name text not null,
      payload text not null,
      created_at text not null
    );
    create table if not exists event_runs(
      event_id integer not null,
      job_id text not null,
      task_id text,
      status text not null,
      created_at text not null,
      primary key(event_id,job_id)
    );
    """)
    return db

def add_schedule(db,goal,profile,role,every_minutes,max_steps,timeout_seconds,job_id=None):
    if every_minutes<1:raise SystemExit("interval must be at least 1 minute")
    if role not in ROLE_GUIDANCE:raise SystemExit("unknown role")
    jid=job_id or "job-"+uuid.uuid4().hex[:12];t=now_ts()
    db.execute("""insert into jobs(id,kind,goal,profile,role,interval_seconds,next_run,max_steps,timeout_seconds,created_at,updated_at)
                  values(?,?,?,?,?,?,?,?,?,?,?)""",
               (jid,"schedule",goal,profile,role,every_minutes*60,t,max_steps,timeout_seconds,iso(),iso()))
    db.commit();return jid

def add_event_job(db,name,goal,profile,role,max_steps,timeout_seconds,job_id=None):
    if not name or len(name)>128:raise SystemExit("event name required")
    if role not in ROLE_GUIDANCE:raise SystemExit("unknown role")
    jid=job_id or "event-"+uuid.uuid4().hex[:12]
    db.execute("""insert into jobs(id,kind,event_name,goal,profile,role,max_steps,timeout_seconds,created_at,updated_at)
                  values(?,?,?,?,?,?,?,?,?,?)""",
               (jid,"event",name,goal,profile,role,max_steps,timeout_seconds,iso(),iso()))
    db.commit();return jid

def emit(db,name,payload):
    if len(payload.encode())>16384:raise SystemExit("event payload exceeds 16 KiB")
    db.execute("insert into events(name,payload,created_at) values(?,?,?)",(name,payload,iso()))
    eid=db.execute("select last_insert_rowid()").fetchone()[0];db.commit();return eid

def run_agent(vault,job,goal_suffix="",task_id=None):
    jid,_,_,goal,profile,role,_,_,_,max_steps,timeout_seconds,*_=job
    full_goal=goal+(("\n\nEVENT:\n"+goal_suffix) if goal_suffix else "")
    tid=task_id or ("sched-"+jid+"-"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    try:
        result=Agent(vault,profile,full_goal,tid,int(max_steps),int(timeout_seconds),role).run()
        return tid,"completed",result,None
    except Exception as exc:
        return tid,"failed",None,str(exc)

def due_jobs(db):
    t=now_ts()
    return db.execute("""select id,kind,event_name,goal,profile,role,interval_seconds,next_run,enabled,max_steps,timeout_seconds,last_task_id,last_status,last_error,created_at,updated_at
                         from jobs where enabled=1 and kind='schedule' and next_run<=? order by next_run,id""",(t,)).fetchall()

def event_work(db):
    return db.execute("""select e.id,e.name,e.payload,j.id,j.kind,j.event_name,j.goal,j.profile,j.role,j.interval_seconds,j.next_run,j.enabled,j.max_steps,j.timeout_seconds,j.last_task_id,j.last_status,j.last_error,j.created_at,j.updated_at
      from events e join jobs j on j.kind='event' and j.enabled=1 and j.event_name=e.name
      left join event_runs r on r.event_id=e.id and r.job_id=j.id
      where r.event_id is null order by e.id,j.id""").fetchall()

def tick(db,vault):
    results=[]
    for job in due_jobs(db):
        jid=job[0];interval=int(job[6] or 60)
        db.execute("update jobs set next_run=?,updated_at=? where id=?",(now_ts()+interval,iso(),jid));db.commit()
        tid,status,result,error=run_agent(vault,job)
        db.execute("update jobs set last_task_id=?,last_status=?,last_error=?,updated_at=? where id=?",(tid,status,error,iso(),jid));db.commit()
        results.append({"job":jid,"task":tid,"status":status,"error":error})
    for row in event_work(db):
        eid,name,payload=row[:3];job=row[3:]
        jid=job[0]
        suffix=json.dumps({"name":name,"payload":json.loads(payload)},ensure_ascii=False)
        tid,status,result,error=run_agent(vault,job,suffix)
        db.execute("insert into event_runs(event_id,job_id,task_id,status,created_at) values(?,?,?,?,?)",(eid,jid,tid,status,iso()))
        db.execute("update jobs set last_task_id=?,last_status=?,last_error=?,updated_at=? where id=?",(tid,status,error,iso(),jid));db.commit()
        results.append({"event":eid,"job":jid,"task":tid,"status":status,"error":error})
    return results

def recover(vault,limit=8):
    root=vault/"state/agent/tasks";rows=[]
    if not root.is_dir():return rows
    for p in sorted(root.glob("*/task.json"),key=lambda x:x.stat().st_mtime)[:limit*4]:
        try:d=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        if d.get("status")!="running":continue
        tid=str(d.get("task_id") or p.parent.name);goal=str(d.get("goal") or "").strip()
        if not goal:continue
        role=str(d.get("role") or "field");profile=str(d.get("profile") or "nano")
        try:
            result=Agent(vault,profile,goal,tid,8,240,role).run()
            rows.append({"task":tid,"status":"completed","resumed":True})
        except Exception as exc:
            rows.append({"task":tid,"status":"failed","resumed":True,"error":str(exc)})
        if len(rows)>=limit:break
    return rows

def list_state(db):
    jobs=[dict(zip(["id","kind","event_name","goal","profile","role","interval_seconds","next_run","enabled","max_steps","timeout_seconds","last_task_id","last_status","last_error","created_at","updated_at"],r))
          for r in db.execute("select id,kind,event_name,goal,profile,role,interval_seconds,next_run,enabled,max_steps,timeout_seconds,last_task_id,last_status,last_error,created_at,updated_at from jobs order by id")]
    events=[dict(zip(["id","name","payload","created_at"],r)) for r in db.execute("select id,name,payload,created_at from events order by id desc limit 50")]
    for e in events:
        try:e["payload"]=json.loads(e["payload"])
        except Exception:pass
    return {"jobs":jobs,"events":events}

def main():
    ap=argparse.ArgumentParser(prog="ark-agent-scheduler")
    ap.add_argument("--vault",default=os.getenv("ENDWORLD_VAULT","/srv/endworld"))
    ap.add_argument("--db")
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("add");a.add_argument("--goal",required=True);a.add_argument("--profile",default="nano");a.add_argument("--role",choices=sorted(ROLE_GUIDANCE),default="field");a.add_argument("--every-minutes",type=int,required=True);a.add_argument("--job-id");a.add_argument("--max-steps",type=int,default=8);a.add_argument("--timeout",type=int,default=240)
    oe=sub.add_parser("on-event");oe.add_argument("--event",required=True);oe.add_argument("--goal",required=True);oe.add_argument("--profile",default="nano");oe.add_argument("--role",choices=sorted(ROLE_GUIDANCE),default="field");oe.add_argument("--job-id");oe.add_argument("--max-steps",type=int,default=8);oe.add_argument("--timeout",type=int,default=240)
    em=sub.add_parser("emit");em.add_argument("event");em.add_argument("--payload",default="{}")
    sub.add_parser("list");sub.add_parser("tick")
    rc=sub.add_parser("recover");rc.add_argument("--limit",type=int,default=8)
    ds=sub.add_parser("disable");ds.add_argument("job_id")
    en=sub.add_parser("enable");en.add_argument("job_id")
    x=ap.parse_args();vault=pathlib.Path(x.vault).resolve();dbp=pathlib.Path(x.db).resolve() if x.db else vault/"state/agent/scheduler.sqlite";db=connect(dbp)
    if x.cmd=="add":out={"job_id":add_schedule(db,x.goal,x.profile,x.role,x.every_minutes,x.max_steps,x.timeout,x.job_id)}
    elif x.cmd=="on-event":out={"job_id":add_event_job(db,x.event,x.goal,x.profile,x.role,x.max_steps,x.timeout,x.job_id)}
    elif x.cmd=="emit":
        try:payload=json.dumps(json.loads(x.payload),ensure_ascii=False)
        except json.JSONDecodeError:raise SystemExit("payload must be JSON")
        out={"event_id":emit(db,x.event,payload)}
    elif x.cmd=="list":out=list_state(db)
    elif x.cmd=="tick":out={"scheduled":tick(db,vault),"recovered":recover(vault)}
    elif x.cmd=="recover":out={"recovered":recover(vault,x.limit)}
    elif x.cmd=="disable":db.execute("update jobs set enabled=0,updated_at=? where id=?",(iso(),x.job_id));db.commit();out={"job_id":x.job_id,"enabled":False}
    else:db.execute("update jobs set enabled=1,updated_at=? where id=?",(iso(),x.job_id));db.commit();out={"job_id":x.job_id,"enabled":True}
    print(json.dumps(out,indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
