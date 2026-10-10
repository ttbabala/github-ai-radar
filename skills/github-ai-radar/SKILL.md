# GitHub AI Trend Radar

## When to use
Use this workflow when asked to run GitHub-AI-Radar, compare recent GitHub AI activity, focus on a domain, or inspect rising/cooling projects. Run `python -m radar` from the project root; use `--domain agent` or `--domain small-model` to focus the report.

## Data acquisition
Use GitHub REST Search API for the configured AI/LLM, Agent, MCP/RAG, multimodal/coding, memory/infrastructure and local/small-model queries. Supplement candidates with GitHub Trending page discovery and refresh candidate repository metadata plus README through REST endpoints. Deduplicate by canonical `owner/name`. Read `GITHUB_TOKEN` only from the environment. Without it, state that the unauthenticated rate limit applies.

## Data integrity
Never invent counts, dates, authors, features or trends. A missing value stays null and is rendered as “数据不可得”. Growth is calculated only from persisted observations at or before the exact lookback boundary. Preserve timestamp and source records. Initial runs cannot claim 7/30 day growth.

## Trend analysis
Compare current 7-day growth with the previous 7-day interval for acceleration. Interpret positive acceleration as accelerating and negative as cooling. Lifecycle labels are heuristic; avoid causal claims from star counts alone. Aggregate domain counts and observed growth, and distinguish observation from inference. Score weights are loaded from `config/radar.yaml`; methodology is documented in `references/scoring.md`.

## Report generation
Generate dated daily, ISO-weekly, and monthly Markdown reports. Include summary, top 7/30 day rankings, deep dives, domain clusters, rising/cooling/strategic directions, an evolution map with evidence limits, recommended research candidates, and a strategic conclusion. Use “数据不可得” for unavailable metrics. Use the required report structure in `references/report-template.md`.

## Taxonomy
Classify projects into one or more domains and one or more technology layers using `references/trend-taxonomy.md` and the editable configuration. Keyword matches are provisional labels, not human-verified technical review.
