"""Build a small public site from reports generated from real GitHub snapshots."""

from __future__ import annotations

from html import escape
from pathlib import Path
import shutil

from .core import ROOT


def build_site(output: Path | None = None) -> Path:
    """Copy generated reports into a static site; fail when no real report exists."""
    output = output or ROOT / "site"
    daily_dir = ROOT / "reports/daily"
    daily_reports = sorted(daily_dir.glob("*.md"))
    if not daily_reports:
        raise FileNotFoundError("No generated reports found; run python3 -m radar first.")

    output.mkdir(parents=True, exist_ok=True)
    reports_dir = output / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    for report in sorted((ROOT / "reports").glob("**/*.md")):
        relative = report.relative_to(ROOT / "reports")
        destination = reports_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(report, destination)

    latest = daily_reports[-1]
    report_link = f"reports/daily/{escape(latest.name)}"
    index = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="基于真实公开 GitHub 仓库快照生成的 AI 开源趋势报告。">
<title>GitHub AI Trend Radar · 最新趋势报告</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b1020;color:#edf3ff;font:16px/1.7 system-ui,-apple-system,sans-serif}}main{{max-width:900px;margin:10vh auto;padding:32px}}.eyebrow{{color:#62e5d2;text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:700}}h1{{font-size:clamp(2rem,6vw,4rem);line-height:1.1;letter-spacing:-.04em;margin:14px 0}}p{{color:#a9b7cc;max-width:650px}}.card{{margin-top:32px;padding:24px;border:1px solid #25324b;border-radius:18px;background:#111a2d}}a{{color:#62e5d2}}.button{{display:inline-block;margin-top:8px;padding:12px 18px;background:#62e5d2;color:#07121e;text-decoration:none;border-radius:10px;font-weight:750}}.note{{font-size:13px;color:#8796ae}}footer{{margin-top:38px;font-size:13px;color:#8796ae}}@media(max-width:600px){{main{{padding:22px}}}}
</style></head><body><main><div class="eyebrow">Open source AI · GitHub signals</div>
<h1>看见 AI 开源项目如何成长</h1>
<p>从公开 GitHub 仓库快照观察项目增长、技术方向与生态变化。没有历史基线时明确标注“数据不可得”，不推测缺失数据。</p>
<section class="card"><h2>最新日报 · {escape(latest.stem)}</h2>
<p>报告由自动化任务从 GitHub 公开数据生成。首次快照只建立基线，真实增长需要后续观察。</p>
<a class="button" href="{report_link}">阅读最新趋势报告 →</a>
<p class="note">数据来自公开仓库元数据；分类和趋势分是启发式研究辅助，不代表质量或投资结论。</p></section>
<footer><a href="https://github.com/ttbabala/github-ai-radar">GitHub 项目</a> · <a href="https://github.com/ttbabala/github-ai-radar/blob/main/docs/使用手册.md">使用手册</a></footer>
</main></body></html>"""
    (output / "index.html").write_text(index, encoding="utf-8")
    shutil.copyfile(latest, output / "latest.md")
    return output


if __name__ == "__main__":
    print(build_site())
