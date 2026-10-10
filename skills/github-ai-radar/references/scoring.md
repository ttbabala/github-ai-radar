# Trend Score

Weights are in `config/radar.yaml` and default to 30% 7-day growth, 20% 30-day growth, 15% acceleration, 15% technical importance, 10% community activity and 10% ecosystem impact. The weights must sum to 1.

Each component is normalized to 0–100 with `clamp(50 + 20 * sign(x) * ln(1 + abs(x)), 0, 100)`. Growth and acceleration are raw observed star deltas. Technical importance, community activity and ecosystem impact are explicitly heuristic proxies derived from taxonomy, last push date, open issue count and square-root star count; they are not independent verified measurements. If any required input is unavailable, Trend Score is null and must not be ranked as a measured score. Insufficient 7/30 day history remains null.

Lifecycle heuristics and thresholds are configuration-driven. Viral requires a large observed 7-day increase plus insufficient longer history; Emerging indicates positive acceleration; Infrastructure prioritizes foundational domains; Strategic is a directional label; Cooling signals negative acceleration. Labels are descriptive screening signals, not forecasts.
