"""Build a readable public site from reports generated from real GitHub snapshots."""

from __future__ import annotations

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import shutil
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

import markdown

from .core import ROOT


SITE_URL = "https://ttbabala.github.io/github-ai-radar/"
REPO_URL = "https://github.com/ttbabala/github-ai-radar"
ALLOWED_TAGS = {
    "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4",
    "hr", "li", "ol", "p", "pre", "strong", "table", "tbody", "td", "th",
    "thead", "tr", "ul",
}


class _ReportHTML(HTMLParser):
    """Keep Markdown output readable while stripping unsafe link targets and tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.open_tags: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in ALLOWED_TAGS:
            self.open_tags.append(None)
            return
        if tag == "a":
            href = next((value for key, value in attrs if key == "href"), None)
            parsed = urlsplit(href or "")
            if parsed.scheme not in {"https", "http"} or not parsed.netloc:
                self.parts.append("<span>")
                self.open_tags.append("span")
                return
            self.parts.append(
                f'<a href="{escape(href or "", quote=True)}" '
                'target="_blank" rel="noopener noreferrer">'
            )
        else:
            self.parts.append(f"<{tag}>")
        self.open_tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.open_tags:
            return
        opened = self.open_tags.pop()
        if opened:
            self.parts.append(f"</{opened}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data))

    def render(self, content: str) -> str:
        self.feed(content)
        self.close()
        while self.open_tags:
            opened = self.open_tags.pop()
            if opened:
                self.parts.append(f"</{opened}>")
        return "".join(self.parts)


def _render_markdown(source: str) -> str:
    # Escape raw HTML before parsing because README excerpts are repository data.
    escaped_source = escape(source, quote=False)
    rendered = markdown.markdown(escaped_source, extensions=["tables"], output_format="html5")
    return _ReportHTML().render(rendered)


def _report_page(title: str, source: str, report_url: str) -> str:
    body = _render_markdown(source)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="基于真实公开 GitHub 仓库快照生成的 AI 开源项目趋势报告。">
<meta property="og:type" content="article"><meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="真实历史快照、中文项目解读；数据不足时明确标示。">
<meta property="og:url" content="{escape(report_url, quote=True)}"><meta name="twitter:card" content="summary">
<link rel="canonical" href="{escape(report_url, quote=True)}">
<title>{escape(title)}</title>
<style>
:root{{--bg:#0b1020;--panel:#111a2d;--line:#293650;--text:#edf3ff;--muted:#a9b7cc;--cyan:#62e5d2;--blue:#8eb4ff}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 10% 0,#1c3150 0,transparent 38%),var(--bg);color:var(--text);font:16px/1.75 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header,main,footer{{width:min(980px,calc(100% - 36px));margin:auto}}header{{padding:42px 0 26px;border-bottom:1px solid var(--line)}}.brand{{color:var(--cyan);font-size:12px;font-weight:750;letter-spacing:.14em;text-transform:uppercase}}header h1{{font-size:clamp(26px,5vw,42px);line-height:1.2;margin:10px 0}}header p,footer{{color:var(--muted)}}nav{{display:flex;gap:16px;flex-wrap:wrap;margin-top:18px}}a{{color:var(--cyan)}}nav a{{text-decoration:none;font-weight:650}}main{{padding:28px 0 70px}}.report{{background:linear-gradient(155deg,#111a2d,#0f1729);border:1px solid var(--line);border-radius:18px;padding:clamp(18px,4vw,38px);box-shadow:0 20px 55px #0003}}.report h1,.report h2,.report h3{{line-height:1.3;letter-spacing:-.02em;margin-top:1.6em}}.report h1{{margin-top:0;font-size:30px}}.report h2{{font-size:23px;border-bottom:1px solid var(--line);padding-bottom:8px}}.report h3{{font-size:18px}}.report p,.report li{{color:#d0dced}}.report blockquote{{margin:20px 0;padding:5px 18px;border-left:3px solid var(--cyan);background:#16243a;color:var(--muted)}}.report table{{width:100%;border-collapse:collapse;display:block;overflow-x:auto;white-space:nowrap;font-size:14px}}.report th,.report td{{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left}}.report th{{color:var(--cyan);background:#16243a}}.report code{{background:#1a2941;border-radius:5px;padding:2px 5px}}.report pre{{overflow:auto;background:#08101e;border:1px solid var(--line);border-radius:10px;padding:14px}}.report hr{{border:0;border-top:1px solid var(--line);margin:28px 0}}.note{{margin-top:22px;color:var(--muted);font-size:13px}}footer{{padding:0 0 38px;font-size:13px}}@media(max-width:600px){{header{{padding-top:28px}}.report{{padding:18px}}}}
</style></head><body>
<header><div class="brand">GitHub AI Trend Radar</div><h1>{escape(title)}</h1>
<p>面向跟踪 AI 开源生态的开发者与技术负责人：用公开历史快照观察项目变化。历史不足时明确说明，不推测增长。</p>
<nav><a href="{SITE_URL}">最新报告</a><a href="{SITE_URL}reports/">历史报告</a><a href="{REPO_URL}">查看仓库 / Star</a><a href="{REPO_URL}/issues/new">反馈问题</a><a href="{REPO_URL}/blob/main/docs/使用手册.md">使用手册</a></nav></header>
<main><article class="report">{body}</article><p class="note">本报告来自 GitHub 公开仓库元数据。分类和趋势分是启发式研究辅助，不代表代码质量、商业价值或投资结论。</p></main>
<footer>数据源：公开 GitHub 仓库页面与 API · <a href="{REPO_URL}">项目源码</a></footer></body></html>"""


def build_site(output: Path | None = None) -> Path:
    """Render generated daily reports as shareable HTML pages and build an index."""
    output = output or ROOT / "site"
    reports_root = ROOT / "reports"
    daily_reports = sorted((reports_root / "daily").glob("*.md"))
    if not daily_reports:
        raise FileNotFoundError("No generated reports found; run python3 -m radar first.")

    output.mkdir(parents=True, exist_ok=True)
    reports_dir = output / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    for source in sorted(reports_root.glob("**/*.md")):
        relative = source.relative_to(reports_root)
        destination = reports_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        html_destination = destination.with_suffix(".html")
        report_url = f"{SITE_URL}reports/{relative.with_suffix('.html').as_posix()}"
        html_destination.write_text(
            _report_page(f"GitHub AI Trend Radar · {source.stem}", source.read_text(encoding="utf-8"), report_url),
            encoding="utf-8",
        )

    latest = daily_reports[-1]
    latest_html = f"reports/daily/{latest.stem}.html"
    latest_title = f"AI 开源项目趋势报告 · {latest.stem}"
    index_report_url = f"{SITE_URL}{latest_html}"
    index = _report_page(latest_title, latest.read_text(encoding="utf-8"), index_report_url)
    (output / "index.html").write_text(index, encoding="utf-8")
    shutil.copyfile(latest, output / "latest.md")

    archive_items = "\n".join(
        f'<li><a href="daily/{escape(path.stem)}.html">日报 · {escape(path.stem)}</a></li>'
        for path in reversed(daily_reports)
    )
    archive = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>报告归档 · GitHub AI Trend Radar</title><body style="max-width:760px;margin:48px auto;padding:0 20px;font:16px/1.7 system-ui;background:#0b1020;color:#edf3ff">
<h1>趋势报告归档</h1><p><a href="../">返回最新报告</a></p><ul>{archive_items}</ul></body></html>"""
    (reports_dir / "index.html").write_text(archive, encoding="utf-8")
    report_urls = [
        f"{SITE_URL}reports/{path.relative_to(reports_root).with_suffix('.html').as_posix()}"
        for path in sorted(reports_root.glob("**/*.md"))
    ]
    sitemap_urls = "\n".join(
        f"  <url><loc>{xml_escape(url)}</loc></url>" for url in [SITE_URL, f"{SITE_URL}reports/", *report_urls]
    )
    (output / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap_urls}\n</urlset>\n',
        encoding="utf-8",
    )
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(build_site())
