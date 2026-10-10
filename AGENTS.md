# Project rules

- This project collects public GitHub AI repository data and produces repeatable trend reports.
- Never fabricate GitHub data or present missing values as zero; use null in stored data and “数据不可得” in reports.
- Install with `python3 -m pip install -e '.[test]'`; run with `python3 -m radar` and `python3 -m radar --report`.
- Keep source under `radar/`, configuration under `config/`, snapshots under `data/`, reports under `reports/`, and deterministic tests under `tests/`.
- Keep network access behind the GitHub client and make analysis/report generation usable with fixture data.
- Follow Python typing and standard-library conventions; keep scoring weights configurable.
- Tests must use fixtures/mocks and must not call GitHub. Run `python3 -m pytest` when validating changes.
