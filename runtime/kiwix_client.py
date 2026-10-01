#!/usr/bin/env python3
"""Stdlib-only Kiwix federation client for THE ARK."""
from __future__ import annotations
from html.parser import HTMLParser
import html, pathlib, re, urllib.parse, urllib.request

class SearchLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.href=None; self.buf=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href and "/content/" in href:
                self.href=href; self.buf=[]
    def handle_data(self,data):
        if self.href:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href:
            self.links.append((self.href," ".join("".join(self.buf).split())))
            self.href=None; self.buf=[]

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0; self.in_title=False; self.title=""
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg"): self.skip+=1
        if tag=="title": self.in_title=True
        if not self.skip and tag in ("p","br","li","h1","h2","h3","h4","tr","div"): self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript","svg") and self.skip:self.skip-=1
        if tag=="title":self.in_title=False
    def handle_data(self,data):
        if self.skip:return
        t=" ".join(html.unescape(data).split())
        if not t:return
        if self.in_title:self.title=(self.title+" "+t).strip()
        self.parts.append(t+" ")
    def text(self):
        value="".join(self.parts)
        value=re.sub(r"[ \t]+"," ",value)
        value=re.sub(r"\n\s*\n+","\n",value)
        return value.strip()

def _get(url:str,limit:int):
    req=urllib.request.Request(url,headers={"User-Agent":"THE-ARK/1.0"})
    with urllib.request.urlopen(req,timeout=10) as r:
        return r.geturl(),r.read(limit).decode("utf-8","replace")

def _content_path(value:str):
    path=urllib.parse.urlparse(value).path
    return path if path.startswith("/content/") else None

def search_kiwix(query:str,zim_dir:pathlib.Path,base_url:str="http://127.0.0.1:8081",limit:int=4)->list[dict]:
    if not query.strip() or not zim_dir.is_dir():return []
    out=[];seen=set()
    for zim in sorted(zim_dir.glob("*.zim")):
        if len(out)>=limit:break
        name=zim.stem
        search=base_url+"/search?"+urllib.parse.urlencode({"content":name,"pattern":query})
        try:final,page=_get(search,384_000)
        except Exception:continue
        final_path=urllib.parse.urlparse(final).path
        if final_path.startswith("/content/"):
            candidates=[(final_path,"")]
        else:
            p=SearchLinks()
            try:p.feed(page)
            except Exception:pass
            candidates=p.links
        for href,label in candidates:
            path=_content_path(href)
            if not path or path in seen:continue
            seen.add(path)
            try:_,article=_get(base_url+path,768_000)
            except Exception:continue
            p=PlainText()
            try:p.feed(article)
            except Exception:continue
            body=p.text()
            if len(body)<80:continue
            title=label or p.title or pathlib.PurePosixPath(path).name.replace("_"," ")
            out.append({"source":"kiwix/"+name,"title":title[:240],"kind":"kiwix-article",
                        "url":"","kiwix_path":path,"excerpt":body[:420],
                        "_body":body[:12000],"score":0.0})
            if len(out)>=limit:break
    return out
