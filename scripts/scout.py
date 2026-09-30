#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "https://api.github.com"
UA = "ENDWORLD-SCOUT/0.1"


def api(path: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception as exc:
        return {"_error": str(exc)}


def snapshot(repo_name: str) -> dict:
    meta = api(f"/repos/{repo_name}")
    release = api(f"/repos/{repo_name}/releases/latest")
    default_branch = meta.get("default_branch", "main")
    commit = api(f"/repos/{repo_name}/commits/{default_branch}")
    return {
        "repo": repo_name,
        "url": meta.get("html_url"),
        "description": meta.get("description"),
        "stars": meta.get("stargazers_count"),
        "archived": meta.get("archived"),
        "pushed_at": meta.get("pushed_at"),
        "license": (meta.get("license") or {}).get("spdx_id"),
        "default_branch": default_branch,
        "head_sha": commit.get("sha"),
        "latest_release": {
            "tag": release.get("tag_name"),
            "published_at": release.get("published_at"),
            "url": release.get("html_url"),
        } if release.get("tag_name") else None,
        "errors": [
            x["_error"] for x in (meta, release, commit)
            if isinstance(x, dict) and x.get("_error")
        ],
    }


def search(query: str, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    result = api(f"/search/repositories?q={q}&sort=updated&order=desc&per_page={limit}")
    rows = []
    for item in result.get("items", []):
        rows.append({
            "repo": item.get("full_name"),
            "url": item.get("html_url"),
            "description": item.get("description"),
            "stars": item.get("stargazers_count"),
            "forks": item.get("forks_count"),
            "language": item.get("language"),
            "archived": item.get("archived"),
            "pushed_at": item.get("pushed_at"),
            "license": (item.get("license") or {}).get("spdx_id"),
        })
    return rows


def main():
    caps = yaml.safe_load((ROOT / "manifests" / "capabilities.yml").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((ROOT / "manifests" / "scout.yml").read_text(encoding="utf-8"))

    known_repos = {c["repo"].lower() for c in caps["capabilities"]}
    known = []
    for c in caps["capabilities"]:
        row = snapshot(c["repo"])
        row.update(id=c["id"], family=c["family"], priority=c["priority"])
        known.append(row)

    candidates = {}
    limit = int(cfg["policy"].get("max_candidates_per_query", 10))
    for q in cfg["queries"]:
        for item in search(q["query"], limit):
            name = (item.get("repo") or "").lower()
            if not name or name in known_repos:
                continue
            if cfg["policy"].get("reject_archived", True) and item.get("archived"):
                continue
            item["family"] = q["family"]
            item["discovered_by"] = q["query"]
            candidates.setdefault(name, item)

    now = dt.datetime.now(dt.timezone.utc)
    report = {
        "schema": 1,
        "generated_at": now.isoformat(),
        "mode": "DISCOVERY_ONLY",
        "notice": "Nothing in this report is trusted, executed or automatically promoted.",
        "known_capabilities": known,
        "candidate_capabilities": list(candidates.values()),
    }

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    (out / "scout-latest.json").write_text(payload, encoding="utf-8")
    (out / f"scout-{now.date().isoformat()}.json").write_text(payload, encoding="utf-8")
    print(f"Known: {len(known)}; candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
