#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, re, shutil, sqlite3, subprocess, tarfile, tempfile, zipfile
from html.parser import HTMLParser

TEXT_EXT={".md",".txt",".rst",".py",".js",".ts",".tsx",".jsx",".java",".rs",".go",".c",".h",".cpp",".hpp",".sh",".yml",".yaml",".json",".toml",".ini",".cfg",".html",".css",".sql",".xml"}
MAX_FILE=512*1024

MAX_DOC_TEXT=2*1024*1024
IMAGE_EXT={".png",".jpg",".jpeg",".tif",".tiff",".webp"}

class MarkupText(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","svg","noscript"):self.skip+=1
        if not self.skip and tag in ("p","br","div","li","h1","h2","h3","h4","tr"):self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in ("script","style","svg","noscript") and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
    def text(self):
        x=" ".join("".join(self.parts).split())
        return x[:MAX_DOC_TEXT]

def command_text(args,timeout=120):
    try:
        p=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
        if p.returncode==0:return p.stdout[:MAX_DOC_TEXT]
    except Exception:pass
    return ""

def pdf_text(path):
    body=command_text(["pdftotext","-layout",str(path),"-"],180) if shutil.which("pdftotext") else ""
    if len(body.strip())>=120:return body
    if not (shutil.which("pdftoppm") and shutil.which("tesseract")):return body
    chunks=[]
    with tempfile.TemporaryDirectory(prefix="ark-ocr-") as td:
        prefix=str(pathlib.Path(td)/"page")
        try:subprocess.run(["pdftoppm","-f","1","-l","12","-jpeg","-r","160",str(path),prefix],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=180)
        except Exception:return body
        for img in sorted(pathlib.Path(td).glob("page-*.jpg")):
            text=command_text(["tesseract",str(img),"stdout","-l","spa+eng"],90)
            if text:chunks.append(text)
    return ("\n".join(chunks) or body)[:MAX_DOC_TEXT]

def image_ocr(path):
    if not shutil.which("tesseract"):return ""
    return command_text(["tesseract",str(path),"stdout","-l","spa+eng"],120)

def epub_text(path):
    parts=[]
    try:
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.is_dir():continue
                if pathlib.PurePosixPath(info.filename).suffix.lower() not in (".xhtml",".html",".htm"):continue
                if sum(len(x) for x in parts)>=MAX_DOC_TEXT:break
                p=MarkupText()
                try:p.feed(z.read(info).decode("utf-8","replace"))
                except Exception:continue
                t=p.text()
                if t:parts.append(t)
    except (zipfile.BadZipFile,OSError):pass
    return "\n".join(parts)[:MAX_DOC_TEXT]

def docx_text(path):
    try:
        with zipfile.ZipFile(path) as z:
            raw=z.read("word/document.xml").decode("utf-8","replace")
    except Exception:return ""
    raw=re.sub(r"</w:p>", "\n", raw)
    raw=re.sub(r"<[^>]+>", " ", raw)
    return " ".join(raw.split())[:MAX_DOC_TEXT]

def rich_document(db,p,rel,budget):
    ext=p.suffix.lower();body=""
    try:n=p.stat().st_size
    except OSError:return 0
    if not budget.take(min(n,MAX_DOC_TEXT)):return 0
    if ext==".pdf":body=pdf_text(p);kind="pdf"
    elif ext==".epub":body=epub_text(p);kind="epub"
    elif ext==".docx":body=docx_text(p);kind="docx"
    elif ext in IMAGE_EXT:body=image_ocr(p);kind="ocr-image"
    else:return 0
    return insert(db,rel,p.name,body,kind,"/vault/"+rel)

def decode(data):
    if not data or b"\x00" in data[:4096]:return None
    try:return data.decode("utf-8")
    except UnicodeDecodeError:return data.decode("utf-8",errors="replace")

class Budget:
    def __init__(self,n):self.max=n;self.used=0
    def take(self,n):
        if self.used+n>self.max:return False
        self.used+=n;return True

def insert(db,source,title,body,kind,url=""):
    if not body or not body.strip():return 0
    db.execute("INSERT INTO ark_fts(source,title,body,kind,url) VALUES(?,?,?,?,?)",(source,title,body.strip(),kind,url));return 1

def plain(db,p,source,url,budget):
    try:
        n=p.stat().st_size
        if n>MAX_FILE or not budget.take(n):return 0
        return insert(db,source,p.name,decode(p.read_bytes()),"file",url)
    except OSError:return 0

def tar_archive(db,p,rel,budget,max_members):
    count=0
    try:
        with tarfile.open(p,"r:*") as tf:
            for m in tf:
                if count>=max_members or budget.used>=budget.max:break
                if not m.isfile() or pathlib.PurePosixPath(m.name).suffix.lower() not in TEXT_EXT or m.size>MAX_FILE:continue
                if not budget.take(m.size):break
                f=tf.extractfile(m)
                if not f:continue
                body=decode(f.read(MAX_FILE+1))
                if body:count+=insert(db,rel+"::"+m.name,m.name,body,"source-archive","/vault/"+rel)
    except (tarfile.TarError,OSError):pass
    return count

def zip_archive(db,p,rel,budget,max_members):
    count=0
    try:
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                if count>=max_members or budget.used>=budget.max:break
                if info.is_dir() or pathlib.PurePosixPath(info.filename).suffix.lower() not in TEXT_EXT or info.file_size>MAX_FILE:continue
                if not budget.take(info.file_size):break
                body=decode(z.read(info))
                if body:count+=insert(db,rel+"::"+info.filename,info.filename,body,"source-archive","/vault/"+rel)
    except (zipfile.BadZipFile,OSError):pass
    return count

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--vault",required=True);ap.add_argument("--repo",default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--output");ap.add_argument("--max-text-mb",type=int,default=256);ap.add_argument("--max-members-per-archive",type=int,default=2500)
    a=ap.parse_args();vault=pathlib.Path(a.vault).resolve();repo=pathlib.Path(a.repo).resolve()
    out=pathlib.Path(a.output).resolve() if a.output else vault/"state/search/ark-search.sqlite"
    out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix(".tmp");tmp.unlink(missing_ok=True)
    db=sqlite3.connect(tmp);db.execute("PRAGMA journal_mode=OFF");db.execute("PRAGMA synchronous=OFF")
    db.execute("CREATE VIRTUAL TABLE ark_fts USING fts5(source UNINDEXED,title,body,kind UNINDEXED,url UNINDEXED,tokenize='unicode61 remove_diacritics 2')")
    db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT)")
    budget=Budget(a.max_text_mb*1024*1024);count=0
    for rootname in ("docs","profiles","manifests","scripts","runtime"):
        root=repo/rootname
        if not root.exists():continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in TEXT_EXT:count+=plain(db,p,"repo/"+str(p.relative_to(repo)),"",budget)
    lockdir=vault/"lock"
    for lock in sorted(lockdir.glob("*.lock.json")) if lockdir.exists() else []:
        try:
            data=json.loads(lock.read_text(encoding="utf-8"))
            for rec in list(data.get("artifacts",[]))+list(data.get("containers",[])):
                count+=insert(db,"lock/"+lock.name,str(rec.get("id") or "artifact"),json.dumps(rec,ensure_ascii=False,sort_keys=True),"inventory","/api/lock")
        except Exception:pass
    for p in sorted(vault.rglob("*")):
        if not p.is_file():continue
        rel=str(p.relative_to(vault))
        if rel.startswith("state/"):continue
        low=p.name.lower()
        if p.suffix.lower()==".zim":
            count+=insert(db,rel,p.stem,"Offline Kiwix collection. Use local Kiwix for collection full-text.","kiwix-collection","")
        elif p.suffix.lower() in TEXT_EXT:
            count+=plain(db,p,rel,"/vault/"+rel,budget)
        elif p.suffix.lower() in ({".pdf",".epub",".docx"} | IMAGE_EXT):
            count+=rich_document(db,p,rel,budget)
        elif rel.startswith("source/") and low.endswith((".tar.gz",".tgz",".tar")):
            count+=tar_archive(db,p,rel,budget,a.max_members_per_archive)
        elif rel.startswith("source/") and low.endswith(".zip"):
            count+=zip_archive(db,p,rel,budget,a.max_members_per_archive)
    db.execute("INSERT INTO meta VALUES('documents',?)",(str(count),));db.execute("INSERT INTO meta VALUES('indexed_text_bytes',?)",(str(budget.used),))
    db.execute("INSERT INTO meta VALUES('universal_formats',?)",("text,code,pdf,epub,docx,ocr-image,kiwix-federated",))
    db.commit();db.close();tmp.replace(out)
    print(json.dumps({"index":str(out),"documents":count,"indexed_text_bytes":budget.used},indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
