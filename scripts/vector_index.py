#!/usr/bin/env python3
"""Embed the universal SQLite index locally and upsert it into local Qdrant."""
from __future__ import annotations
import argparse, json, pathlib, sqlite3, urllib.error, urllib.request, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"runtime"
sys.path.insert(0,str(RUNTIME))
from vector_client import embedding, QDRANT, COLLECTION

def request(path,payload=None,method="GET",timeout=30):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(QDRANT+path,data=data,headers={"Content-Type":"application/json"},method=method)
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--vault",default="/srv/endworld")
    ap.add_argument("--collection",default=COLLECTION);ap.add_argument("--max-docs",type=int,default=50000)
    ap.add_argument("--keep-existing",action="store_true");a=ap.parse_args()
    dbp=pathlib.Path(a.vault)/"state/search/ark-search.sqlite"
    if not dbp.is_file():raise SystemExit("lexical index missing; run endworld index first")
    db=sqlite3.connect(f"file:{dbp}?mode=ro",uri=True)
    rows=db.execute("SELECT rowid,source,title,body,kind,url FROM ark_fts ORDER BY rowid LIMIT ?",(a.max_docs,)).fetchall()
    if not rows:raise SystemExit("lexical index empty")
    first_text=(rows[0][2]+" "+rows[0][3])[:6000]
    v=embedding(first_text,"search_document")
    if not v:raise SystemExit("embedding service unavailable")
    if not a.keep_existing:
        try:request(f"/collections/{a.collection}",method="DELETE")
        except urllib.error.HTTPError as e:
            if e.code!=404:raise
    try:
        request(f"/collections/{a.collection}",{"vectors":{"size":len(v),"distance":"Cosine"}},method="PUT")
    except urllib.error.HTTPError as e:
        if e.code not in (400,409):raise
    done=0;batch=[]
    for row in rows:
        rid,source,title,body,kind,url=row
        text=(str(title or "")+"\n"+str(body or ""))[:6000]
        try:vec=embedding(text,"search_document")
        except Exception:continue
        if not vec:continue
        batch.append({"id":int(rid),"vector":vec,"payload":{"source":source,"title":title,"kind":kind,"url":url,
                     "excerpt":str(body or "")[:700],"body":str(body or "")[:4000]}})
        if len(batch)>=16:
            request(f"/collections/{a.collection}/points?wait=true",{"points":batch},method="PUT",timeout=60);done+=len(batch);batch=[]
    if batch:request(f"/collections/{a.collection}/points?wait=true",{"points":batch},method="PUT",timeout=60);done+=len(batch)
    db.close()
    print(json.dumps({"collection":a.collection,"vectors":done,"dimensions":len(v)},indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
