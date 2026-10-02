#!/usr/bin/env python3
"""Local embedding + Qdrant client used by portal and agent."""
from __future__ import annotations
import json, urllib.request

EMBED_URL="http://127.0.0.1:8084/v1/embeddings"
QDRANT="http://127.0.0.1:6333"
COLLECTION="ark_knowledge"

def _json(url,payload,method="POST",timeout=8):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method=method)
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def embedding(text,prefix="search_query"):
    data=_json(EMBED_URL,{"model":"local","input":[f"{prefix}: {text}"]},timeout=30)
    rows=data.get("data") or []
    if not rows:return None
    v=rows[0].get("embedding")
    return v if isinstance(v,list) and v else None

def vector_search(query,limit=5):
    try:v=embedding(query,"search_query")
    except Exception:return []
    if not v:return []
    try:data=_json(f"{QDRANT}/collections/{COLLECTION}/points/query",{"query":v,"limit":max(1,min(limit,10)),"with_payload":True},timeout=8)
    except Exception:return []
    result=data.get("result") or {}
    points=result.get("points") if isinstance(result,dict) else result
    out=[]
    for p in points or []:
        payload=p.get("payload") or {}
        out.append({"source":payload.get("source","vector"),"title":payload.get("title",""),
                    "kind":payload.get("kind","vector"),"url":payload.get("url",""),
                    "excerpt":payload.get("excerpt",""),"score":p.get("score"),"vector":True,
                    "_body":payload.get("body","")})
    return out
