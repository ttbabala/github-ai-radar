from datetime import datetime, timedelta, timezone

from radar.core import classify, deduplicate, growth, historical_metrics, load_config, score
from radar.report import render_report


def test_growth_and_missing():
    assert growth(120, 100) == 20
    assert growth(None, 100) is None


def test_star_growth_exact_delta():
    assert growth(1000, 875) == 125


def test_7d_and_30d_growth():
    now = datetime(2025, 2, 1, tzinfo=timezone.utc)
    hist = [{"repo": "a/b", "stars": 100, "snapshot_time": (now-timedelta(days=31)).isoformat()},
            {"repo": "a/b", "stars": 150, "snapshot_time": (now-timedelta(days=8)).isoformat()}]
    m = historical_metrics("a/b", 170, hist, now)
    assert m["growth_7d"] == 20
    assert m["growth_30d"] == 70


def test_7_day_growth_is_null_without_baseline():
    now = datetime(2025, 2, 1, tzinfo=timezone.utc)
    m = historical_metrics("a/b", 12, [], now)
    assert m["growth_7d"] is None


def test_30_day_growth_is_null_without_baseline():
    now = datetime(2025, 2, 1, tzinfo=timezone.utc)
    hist = [{"repo": "a/b", "stars": 10, "snapshot_time": (now-timedelta(days=8)).isoformat()}]
    assert historical_metrics("a/b", 12, hist, now)["growth_30d"] is None


def test_acceleration_and_insufficient_history():
    now = datetime(2025, 2, 1, tzinfo=timezone.utc)
    hist = []
    for d, s in [(31, 100), (14, 120), (7, 140)]:
        hist.append({"repo": "a/b", "stars": s, "snapshot_time": (now-timedelta(days=d)).isoformat()})
    m = historical_metrics("a/b", 175, hist, now)
    assert m["growth_7d"] == 35
    assert m["previous_7d_growth"] == 20
    assert m["acceleration"] == 15
    assert m["insufficient_history"] is False


def test_acceleration_requires_two_observed_intervals():
    now = datetime(2025, 2, 1, tzinfo=timezone.utc)
    hist = [{"repo": "a/b", "stars": 100, "snapshot_time": (now-timedelta(days=8)).isoformat()}]
    assert historical_metrics("a/b", 120, hist, now)["acceleration"] is None


def test_score_uses_configured_weights_and_nulls():
    cfg = load_config()
    row = {"growth_7d": 20, "growth_30d": 50, "acceleration": 10, "technical_importance": 50,
           "community_activity": 50, "ecosystem_impact": 50}
    assert score(row, cfg) is not None
    row["growth_7d"] = None
    assert score(row, cfg) is None


def test_classification_and_dedup():
    cfg = load_config()
    domains, layers = classify({"name":"agent-memory", "description":"Agent memory runtime", "topics":[]}, cfg)
    assert "Agent" in domains and "Agent Memory" in domains
    assert layers
    assert len(deduplicate([{"full_name":"x/y"}, {"full_name":"X/Y"}])) == 1


def test_report_handles_null_data():
    text = render_report([{"repo":"a/b", "stars":10, "growth_7d":None, "growth_30d":None,
                           "acceleration":None, "domains":[], "layers":[], "insufficient_history":True}], "2025-01-01T00:00:00+00:00")
    assert "数据不可得" in text
    assert "Top 30 Days" in text and "Recommended Projects" in text
