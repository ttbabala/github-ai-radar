from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import re
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path | None = None) -> dict:
    with (path or ROOT / "config/radar.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def growth(current: int | None, before: int | None) -> int | None:
    return current - before if current is not None and before is not None else None


def historical_metrics(repo: str, stars: int | None, history: list[dict], now: datetime):
    rows = [r for r in history if r.get("repo") == repo and r.get("stars") is not None and parse_time(r.get("snapshot_time"))]
    rows.sort(key=lambda x: parse_time(x["snapshot_time"]))
    def at(days):
        target = now - timedelta(days=days)
        eligible = [r for r in rows if parse_time(r["snapshot_time"]) <= target]
        return eligible[-1]["stars"] if eligible else None
    s7, s30 = at(7), at(30)
    g7, g30 = growth(stars, s7), growth(stars, s30)
    prev7 = at(14)
    previous7 = growth(s7, prev7) if s7 is not None and prev7 is not None else None
    return {"growth_7d": g7, "growth_30d": g30, "previous_7d_growth": previous7,
            "acceleration": g7 - previous7 if g7 is not None and previous7 is not None else None,
            "insufficient_history": g7 is None or g30 is None}


def classify(repo: dict, cfg: dict):
    text = " ".join(str(repo.get(k) or "") for k in ("name", "description", "readme", "topics")).lower()
    domains, layers = cfg["classification"]["domains"], cfg["classification"]["layers"]
    assigned = [name for name, terms in domains.items() if any(term.lower() in text for term in terms)]
    assigned_layers = [name for name, terms in layers.items() if any(term.lower() in text for term in terms)]
    return assigned or ["AI Infrastructure"], assigned_layers or ["L6 Application Layer"]


def score(repo: dict, cfg: dict) -> float | None:
    weights = cfg["scoring"]["weights"]
    vals = {"growth_7d": repo.get("growth_7d"), "growth_30d": repo.get("growth_30d"),
            "acceleration": repo.get("acceleration"), "technical_importance": repo.get("technical_importance"),
            "community_activity": repo.get("community_activity"), "ecosystem_impact": repo.get("ecosystem_impact")}
    if any(v is None for v in vals.values()):
        return None
    # Log scaling prevents absolute star counts from overwhelming the score; component values are normalized 0..100.
    import math
    def norm(v):
        return max(0.0, min(100.0, 50.0 + 20.0 * math.copysign(math.log1p(abs(v)), v)))
    return round(sum(weights[k] * norm(v) for k, v in vals.items()), 2)


def lifecycle(repo: dict, cfg: dict):
    t = cfg["scoring"]["lifecycle_thresholds"]
    g7, accel = repo.get("growth_7d"), repo.get("acceleration")
    domains = repo.get("domains", [])
    if accel is not None and accel < t["cooling_acceleration"]:
        return "Cooling"
    if g7 is not None and g7 >= t["viral_daily_growth"] * 7 and repo.get("insufficient_history"):
        return "Viral"
    if accel is not None and accel >= t["emerging_min_acceleration"]:
        return "Emerging"
    if any(d in domains for d in ["AI Infrastructure", "Agent Runtime", "MCP", "AI Safety"]):
        return "Infrastructure"
    if any(d in domains for d in ["Frontier Model", "Open Model", "Multi-Agent", "Agent"]):
        return "Strategic"
    return "Emerging" if g7 and g7 > 0 else "Cooling" if g7 is not None else "Strategic"


def deduplicate(items):
    out = {}
    for item in items:
        full = (item.get("full_name") or item.get("repo") or "").lower()
        if full:
            out[full] = item
    return list(out.values())


def repo_snapshot(raw: dict, snapshot_time: str, readme=None):
    owner = (raw.get("owner") or {}).get("login") if isinstance(raw.get("owner"), dict) else raw.get("owner")
    return {"repo": raw.get("full_name") or raw.get("repo"), "owner": owner,
            "stars": raw.get("stargazers_count", raw.get("stars")), "forks": raw.get("forks_count", raw.get("forks")),
            "open_issues": raw.get("open_issues_count", raw.get("open_issues")), "created_at": raw.get("created_at"),
            "updated_at": raw.get("updated_at"), "pushed_at": raw.get("pushed_at"),
            "description": raw.get("description"), "topics": raw.get("topics") or [], "language": raw.get("language"),
            "license": (raw.get("license") or {}).get("spdx_id") if isinstance(raw.get("license"), dict) else raw.get("license"),
            "html_url": raw.get("html_url") or ("https://github.com/" + str(raw.get("full_name"))),
            "latest_release": raw.get("latest_release"), "readme": readme, "snapshot_time": snapshot_time}


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value)
