from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from .core import ROOT, classify, deduplicate, historical_metrics, lifecycle, load_config, repo_snapshot, score
from .github import GitHubClient
from .report import render_report


def _paths():
    return ROOT / "data/snapshots", ROOT / "data/history/repositories.jsonl"


def load_history(path):
    if not path.exists(): return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            try: rows.append(json.loads(line))
            except json.JSONDecodeError: continue
    return rows


def discover(client, cfg):
    found = []
    for query in cfg["discovery"]["search_queries"]:
        try: found.extend(client.search(query, cfg["discovery"]["max_results_per_query"]))
        except Exception as e: print(f"Search failed ({query}): {e}", file=sys.stderr)
    try: found.extend(client.trending())
    except Exception as e: print(f"Trending fetch failed: {e}", file=sys.stderr)
    return deduplicate(found)[:cfg["discovery"]["max_candidates"]]


def run(args):
    cfg = load_config()
    snaps, histpath = _paths()
    history = load_history(histpath)
    now = datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    if args.report:
        files = sorted(snaps.glob("*.json"))
        if not files: print("No snapshots found. Run python3 -m radar first.", file=sys.stderr); return 1
        data = json.loads(files[-1].read_text(encoding="utf-8"))
        items = data.get("repositories", [])
        output_report(items, data.get("snapshot_time", stamp), args)
        return 0
    if not os.getenv("GITHUB_TOKEN"):
        print("GITHUB_TOKEN is not set. Requests will use the unauthenticated GitHub API rate limit; set export GITHUB_TOKEN=\"...\" for higher limits.", file=sys.stderr)
    client = GitHubClient()
    candidates = discover(client, cfg)
    if not candidates:
        print("No repositories were collected. Check network access and GitHub API limits.", file=sys.stderr); return 2
    repos = []
    for raw in candidates:
        full = raw.get("full_name")
        if not full: continue
        # Refresh metadata individually as explicitly requested; failed refresh is not replaced by invented data.
        try: raw = client.repo(full)
        except Exception as e: print(f"Metadata unavailable for {full}: {e}", file=sys.stderr)
        r = repo_snapshot(raw, stamp)
        r["readme"] = client.readme(full)
        r["latest_release"] = client.latest_release(full)
        metrics = historical_metrics(full, r.get("stars"), history, now)
        r.update(metrics)
        r["domains"], r["layers"] = classify(r, cfg)
        # Transparent rule-based proxies based on observable repository metadata, not claimed as measured quality.
        r["technical_importance"] = 70 if any(x in r["domains"] for x in ("AI Infrastructure", "Agent Runtime", "MCP", "AI Safety")) else 55 if r["domains"] else 40
        pushed = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")) if r.get("pushed_at") else None
        r["community_activity"] = min(100, 40 + (30 if pushed and (now - pushed).days <= 30 else 0) + min(30, (r.get("open_issues") or 0) // 10))
        r["ecosystem_impact"] = min(100, int((r.get("stars") or 0) ** 0.5 * 2))
        r["trend_score"] = score(r, cfg)
        r["lifecycle"] = lifecycle(r, cfg)
        repos.append(r)
    # Persist the API-derived snapshot and append immutable observation history.
    snaps.mkdir(parents=True, exist_ok=True); histpath.parent.mkdir(parents=True, exist_ok=True)
    day = now.date().isoformat()
    existing = snaps / f"{day}.json"
    old = json.loads(existing.read_text(encoding="utf-8")) if existing.exists() else {"repositories": []}
    merged = {r["repo"]: r for r in old.get("repositories", []) if r.get("repo")}
    merged.update({r["repo"]: r for r in repos})
    payload = {"snapshot_time": stamp, "repositories": list(merged.values())}
    existing.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with histpath.open("a", encoding="utf-8") as f:
        for r in repos: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    output_report(repos, stamp, args)
    print(f"Saved {len(repos)} repository observations to {existing} and {histpath}")
    return 0


def output_report(repos, stamp, args):
    date = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    day = date.date().isoformat()
    text = render_report(repos, stamp, period=args.days or (30 if args.monthly else 7), focus=args.domain)
    daily = ROOT / f"reports/daily/{day}.md"; daily.parent.mkdir(parents=True, exist_ok=True); daily.write_text(text, encoding="utf-8")
    weekly = ROOT / f"reports/weekly/{date.isocalendar().year}-W{date.isocalendar().week:02d}.md"; weekly.parent.mkdir(parents=True, exist_ok=True); weekly.write_text(text, encoding="utf-8")
    monthly = ROOT / f"reports/monthly/{date:%Y-%m}.md"; monthly.parent.mkdir(parents=True, exist_ok=True); monthly.write_text(text, encoding="utf-8")
    print(f"Reports: {daily}, {weekly}, {monthly}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Research GitHub AI project trends from real repository data")
    p.add_argument("--days", type=int, choices=(7, 30), default=7)
    p.add_argument("--domain")
    p.add_argument("--report", action="store_true", help="render a report from the latest saved snapshot without fetching")
    return run(p.parse_args(argv))
