#!/usr/bin/env python3
"""Persistent offline scheduler/event queue for THE ARK Agent."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_VAULT = pathlib.Path(os.getenv("ENDWORLD_VAULT", "/srv/endworld"))

ALLOWED_ROLES = {"field","research","steward","mesh"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id TEXT PRIMARY KEY,
  goal TEXT NOT NULL,
  profile TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'field',
  created_at INTEGER NOT NULL,
  next_run INTEGER NOT NULL,
  every_seconds INTEGER,
  enabled INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'queued',
  last_run INTEGER,
  last_rc INTEGER,
  last_task_id TEXT,
  run_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS jobs_due ON jobs(enabled,next_run);
"""

def db_path(vault: pathlib.Path) -> pathlib.Path:
    p = vault / "state/agent/scheduler.sqlite"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def connect(vault: pathlib.Path) -> sqlite3.Connection:
    db = sqlite3.connect(db_path(vault))
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db

def parse_when(value: str | None) -> int:
    if not value:
        return int(time.time())
    if value.isdigit():
        return int(value)
    try:
        return int(dt.datetime.fromisoformat(value.replace("Z","+00:00")).timestamp())
    except Exception as exc:
        raise SystemExit("invalid --at; use unix seconds or ISO-8601") from exc

def add(vault, goal, profile, role, at, every):
    if role not in ALLOWED_ROLES:
        raise SystemExit("role must be one of: "+", ".join(sorted(ALLOWED_ROLES)))
    if every is not None and every < 60:
        raise SystemExit("--every-seconds must be >= 60")
    jid = "job-" + uuid.uuid4().hex[:12]
    now = int(time.time())
    with connect(vault) as db:
        db.execute("""INSERT INTO jobs(id,goal,profile,role,created_at,next_run,every_seconds)
                      VALUES(?,?,?,?,?,?,?)""",
                   (jid,goal,profile,role,now,parse_when(at),every))
    print(json.dumps({"id":jid,"next_run":parse_when(at),"every_seconds":every},indent=2))
    return 0

def rows(vault):
    with connect(vault) as db:
        data=[dict(x) for x in db.execute("SELECT * FROM jobs ORDER BY next_run,id")]
    print(json.dumps(data,indent=2))
    return 0

def set_enabled(vault, jid, enabled):
    with connect(vault) as db:
        cur=db.execute("UPDATE jobs SET enabled=? WHERE id=?",(1 if enabled else 0,jid))
        if cur.rowcount != 1:
            raise SystemExit("job not found")
    print(jid)
    return 0

def run_one(vault, row):
    jid=row["id"]; stamp=int(time.time())
    task_id=f"sched-{jid}-{stamp}"
    goal=f"[ROLE {row['role']}] {row['goal']}"
    cmd=[sys.executable,str(ROOT/"scripts/agent_runner.py"),
         "--vault",str(vault),"--profile",row["profile"],
         "--task-id",task_id,"--json",goal]
    p=subprocess.run(cmd,text=True,capture_output=True,timeout=300)
    interval=row["every_seconds"]
    next_run=stamp+int(interval) if interval else stamp
    enabled=1 if interval else 0
    status="queued" if interval else ("completed" if p.returncode==0 else "failed")
    with connect(vault) as db:
        db.execute("""UPDATE jobs SET next_run=?,enabled=?,status=?,last_run=?,last_rc=?,
                      last_task_id=?,run_count=run_count+1 WHERE id=?""",
                   (next_run,enabled,status,stamp,p.returncode,task_id,jid))
    event_dir=vault/"state/agent/scheduler-events"
    event_dir.mkdir(parents=True,exist_ok=True)
    event={"ts":stamp,"job_id":jid,"task_id":task_id,"returncode":p.returncode,
           "stdout":p.stdout[-8000:],"stderr":p.stderr[-4000:]}
    (event_dir/f"{stamp}-{jid}.json").write_text(json.dumps(event,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return event

def run_due(vault, limit):
    now=int(time.time())
    with connect(vault) as db:
        due=[dict(x) for x in db.execute(
            "SELECT * FROM jobs WHERE enabled=1 AND next_run<=? ORDER BY next_run,id LIMIT ?",
            (now,max(1,min(limit,20))))]
    results=[]
    for row in due:
        try: results.append(run_one(vault,row))
        except subprocess.TimeoutExpired:
            with connect(vault) as db:
                db.execute("UPDATE jobs SET status='failed',last_run=?,last_rc=124 WHERE id=?",(int(time.time()),row["id"]))
            results.append({"job_id":row["id"],"returncode":124,"error":"agent timeout"})
    print(json.dumps({"due":len(due),"results":results},indent=2,ensure_ascii=False))
    return 0 if all(x.get("returncode")==0 for x in results) else 2

def main():
    ap=argparse.ArgumentParser(prog="ark-agent-scheduler")
    ap.add_argument("--vault",default=str(DEFAULT_VAULT))
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("add");a.add_argument("goal");a.add_argument("--profile",default=os.getenv("ENDWORLD_PROFILE","nano"))
    a.add_argument("--role",default="field");a.add_argument("--at");a.add_argument("--every-seconds",type=int)
    sub.add_parser("list")
    r=sub.add_parser("run-due");r.add_argument("--limit",type=int,default=2)
    e=sub.add_parser("enable");e.add_argument("id")
    d=sub.add_parser("disable");d.add_argument("id")
    x=ap.parse_args();vault=pathlib.Path(x.vault).resolve()
    if x.cmd=="add":return add(vault,x.goal,x.profile,x.role,x.at,x.every_seconds)
    if x.cmd=="list":return rows(vault)
    if x.cmd=="run-due":return run_due(vault,x.limit)
    return set_enabled(vault,x.id,x.cmd=="enable")

if __name__=="__main__":
    raise SystemExit(main())
