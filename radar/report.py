from collections import defaultdict
from datetime import datetime


def _fmt(v): return "数据不可得" if v is None else f"{v:,}" if isinstance(v, int) else str(v)
def _growth_fmt(v): return "数据不可得" if v is None else f"{v:+,}" if isinstance(v, int) else str(v)


def render_report(items, snapshot_time, period=7, focus=None):
    items = [r for r in items if not focus or focus.lower() in " ".join(r.get("domains", [])).lower() or focus.lower() in (r.get("description") or "").lower()]
    ranked = sorted(items, key=lambda x: (x.get("trend_score") is not None, x.get("trend_score") or -1), reverse=True)
    selected = sorted(items, key=lambda x: x.get(f"growth_{period}d") if x.get(f"growth_{period}d") is not None else -10**18, reverse=True)
    lines = ["# GitHub AI Trend Radar", "", f"快照时间：{snapshot_time}。本报告只将观测到的 GitHub 数据用于增长计算；无历史快照时明确标示数据不可得。", "", "## 1. Executive Summary", ""]
    rising = defaultdict(lambda: [0, 0])
    for r in items:
        for d in r.get("domains", []):
            rising[d][0] += 1
            if r.get("growth_7d") is not None: rising[d][1] += r["growth_7d"]
    if not items: lines.append("- 本次没有成功收集到候选项目。")
    else:
        lines += [f"- 纳入分析 {len(items)} 个去重项目；趋势分可计算项目 {sum(r.get('trend_score') is not None for r in items)} 个。",
                  f"- 具备真实 7 天历史基线的项目：{sum(r.get('growth_7d') is not None for r in items)} 个；30 天基线：{sum(r.get('growth_30d') is not None for r in items)} 个。"]
        for domain, (count, total) in sorted(rising.items(), key=lambda x: x[1][1], reverse=True)[:5]:
            observed = any(r.get("growth_7d") is not None and domain in r.get("domains", []) for r in items)
            lines.append(f"- {domain}：{count} 个项目；7 天增长合计：{_growth_fmt(total) if observed else '数据不可得'} stars。")
    lines += ["", "## 2. Top 7 Days", "", _table(selected, "7d"), "", "## 3. Top 30 Days", "", _table(sorted(items, key=lambda x: x.get("growth_30d") if x.get("growth_30d") is not None else -10**18, reverse=True), "30d"), "", "## 4. Project Deep Dive", ""]
    for r in ranked[:5]:
        lines += [f"### [{r.get('repo')} ]({r.get('html_url')})", "", f"- 项目描述：{r.get('description') or '数据不可得'}", f"- 技术领域：{', '.join(r.get('domains') or []) or '数据不可得'}；层级：{', '.join(r.get('layers') or []) or '数据不可得'}", f"- 生命周期：{r.get('lifecycle') or '数据不可得'}；7 天增长：{_fmt(r.get('growth_7d'))}；30 天增长：{_fmt(r.get('growth_30d'))}；加速度：{_fmt(r.get('acceleration'))}", f"- 最近 Release：{(r.get('latest_release') or {}).get('tag_name') or '数据不可得'}（{(r.get('latest_release') or {}).get('published_at') or '数据不可得'}）", f"- 解决的问题 / 技术与商业价值 / 持续性：{_excerpt(r)}", f"- 推荐度：{'建议进一步研究' if r.get('trend_score') is not None and r['trend_score'] >= 65 else '观察；信息不足时不作结论'}", ""]
    lines += ["## 5. Trend Clusters", "", "| Domain | 项目数 | 已知 7d 增长合计 |", "|---|---:|---:|"]
    for d, (n, total) in sorted(rising.items(), key=lambda x: x[1][1], reverse=True): lines.append(f"| {d} | {n} | {_fmt(total) if any(r.get('growth_7d') is not None and d in r.get('domains',[]) for r in items) else '数据不可得'} |")
    cooling = [r for r in items if r.get("lifecycle") == "Cooling"]
    emerging = [r for r in items if r.get("lifecycle") in ("Emerging", "Viral")]
    strategic = [r for r in items if r.get("lifecycle") in ("Strategic", "Infrastructure")]
    lines += ["", "## 6. Rising Trends", "", _names(emerging), "", "## 7. Cooling Trends", "", _names(cooling), "", "## 8. Strategic Trends", "", _names(strategic), "", "## 9. AI Evolution Map", "", "历史数据不足以可靠推断方向迁移。当前候选集所覆盖的方向：" + (", ".join(sorted(rising)) or "数据不可得") + "。未来走向需结合连续快照观察。", "", "## 10. Recommended Projects", ""]
    for r in ranked[:10]:
        lines += [f"- **[{r.get('repo')}]({r.get('html_url')})**：值得研究什么：{r.get('description') or '读取 README 后再判断'}。部署：需结合安全审查与 README；二次开发 / 商业化：仅凭公开元数据无法判断。", ""]
    lines += ["## 11. Strategic Conclusion", "", "当前报告的历史基线有限，不能据此断言长期赢家。建议团队优先跟踪：Agent / Runtime / MCP 基础设施、小模型与本地推理、多模态能力；用后续 7/30 天真实快照验证投入方向。", "", "## Data Notes", "", "增长只在可用的历史快照跨过目标时间点时计算；星标量之外的信息来自 GitHub 仓库元数据与 README。趋势分为启发式排序，不代表客观技术质量。", ""]
    return "\n".join(lines)


def _table(items, period):
    key = "growth_" + period
    out = ["| Rank | Repository | Stars | Growth | Acceleration | Domain | Layer | Score |", "|---:|---|---:|---:|---:|---|---|---:|"]
    for i, r in enumerate(items[:20], 1):
        rank = str(i) if r.get(key) is not None else "—"
        out.append(f"| {rank} | [{r.get('repo')}]({r.get('html_url')}) | {_fmt(r.get('stars'))} | {_growth_fmt(r.get(key))} | {_growth_fmt(r.get('acceleration'))} | {', '.join(r.get('domains', [])) or '数据不可得'} | {', '.join(r.get('layers', [])) or '数据不可得'} | {_fmt(r.get('trend_score'))} |")
    if not items: out.append("| — | 数据不可得 | — | — | — | — | — | — |")
    return "\n".join(out)


def _excerpt(r):
    text = (r.get("readme") or "").strip().replace("\n", " ")
    return (text[:500] + "…") if text else "README 不可得；仅有仓库描述，无法可靠推断功能。"


def _names(rows):
    return ", ".join(f"[{r.get('repo')}]({r.get('html_url')})" for r in rows) if rows else "数据不可得"
