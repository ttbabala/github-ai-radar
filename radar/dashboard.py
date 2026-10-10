"""Local, dependency-free web dashboard for saved Radar data."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .cli import _paths, load_history
from .core import ROOT


ASSET = ROOT / "dashboard" / "index.html"

DOMAIN_ZH = {
    "Frontier Model": "前沿大模型", "Open Model": "开放权重模型", "Small Model": "小模型", "MoE": "混合专家模型",
    "Fine-tuning": "模型微调", "Multimodal": "多模态", "Vision": "视觉理解", "Speech": "语音", "Video": "视频生成/理解",
    "Robotics": "机器人", "AI Coding": "AI 编程", "Agent": "AI 智能体", "Agent Skills": "智能体技能",
    "Agent Memory": "智能体记忆", "Agent Runtime": "智能体运行环境", "Agent Sandbox": "智能体沙箱",
    "Agent Security": "智能体安全", "Context Engineering": "上下文工程", "RAG": "检索增强生成（RAG）",
    "Knowledge System": "知识系统", "MCP": "模型上下文协议（MCP）", "Multi-Agent": "多智能体协作",
    "Agent Organization": "智能体团队组织", "Computer Use": "计算机操作智能体", "AI Search": "AI 搜索",
    "AI Research": "AI 科研", "Local AI": "本地 AI", "Edge AI": "边缘 AI", "Enterprise AI": "企业 AI",
    "AI Infrastructure": "AI 基础设施", "AI Evaluation": "AI 评测", "AI Governance": "AI 治理", "AI Safety": "AI 安全",
}
DOMAIN_INFO = {
    "Frontier Model": "能力边界领先的大型基础模型及其训练、推理生态。", "Open Model": "可以获取模型权重并自行部署或研究的模型。",
    "Small Model": "参数规模较小、成本和延迟较低，适合本地或端侧运行的模型。", "MoE": "混合专家架构：根据输入选择部分专家网络参与计算。",
    "Fine-tuning": "通过额外训练让已有模型适配特定任务或数据。", "Multimodal": "同时处理文本、图像、音频或视频等多种信息。",
    "Vision": "图像与视频理解、识别、生成相关能力。", "Speech": "语音识别、语音合成与音频交互。", "Video": "视频生成、编辑、理解或处理。",
    "Robotics": "将 AI 能力用于机器人感知、决策和控制。", "AI Coding": "使用 AI 理解、编写、修改或测试软件代码。",
    "Agent": "能调用工具并分步骤完成任务的 AI 智能体。", "Agent Skills": "供智能体复用的任务步骤、工具说明或技能模块。",
    "Agent Memory": "帮助智能体跨步骤或跨会话保存、检索信息。", "Agent Runtime": "运行智能体、管理工具调用和执行过程的软件环境。",
    "Agent Sandbox": "隔离智能体执行环境，限制文件、网络或命令权限。", "Agent Security": "保护智能体及工具调用免受攻击和越权影响。",
    "Context Engineering": "组织提示、历史、检索内容和工具结果，让模型获得合适上下文。",
    "RAG": "先检索外部资料，再把相关内容交给模型生成回答。", "Knowledge System": "组织、检索和维护结构化或非结构化知识。",
    "MCP": "用于让 AI 应用以统一方式连接外部工具和数据源的协议。", "Multi-Agent": "多个智能体分工、协作或互相校验。",
    "Agent Organization": "管理智能体角色、团队结构、任务分配和协作关系。", "Computer Use": "让智能体通过屏幕、鼠标、键盘或浏览器操作软件。",
    "AI Search": "使用模型或语义检索发现和整理信息。", "AI Research": "用 AI 辅助文献、实验、分析或科学发现。",
    "Local AI": "在个人设备或自管服务器上运行 AI。", "Edge AI": "在手机、嵌入式设备等靠近数据源的位置运行 AI。",
    "Enterprise AI": "面向组织内部流程、权限、数据和业务系统的 AI。", "AI Infrastructure": "支撑模型训练、推理、部署、数据和计算的底层组件。",
    "AI Evaluation": "测量模型或智能体质量、可靠性与安全性的工具和基准。", "AI Governance": "管理 AI 的权限、审计、合规和风险。", "AI Safety": "降低 AI 造成的有害输出、失控行为和安全风险。",
}
LAYER_ZH = {
    "L1 Model Layer": "L1 模型层", "L2 Capability Layer": "L2 能力层", "L3 Agent Layer": "L3 智能体层",
    "L4 Runtime Layer": "L4 运行时层", "L5 Orchestration Layer": "L5 编排层", "L6 Application Layer": "L6 应用层",
    "L7 Enterprise / AI Operating System Layer": "L7 企业平台 / AI 操作系统层",
}
LAYER_INFO = {
    "L1 Model Layer": "模型权重、架构、训练与推理本身。", "L2 Capability Layer": "视觉、语音、检索等模型能力组件。",
    "L3 Agent Layer": "智能体如何理解目标、使用工具和执行任务。", "L4 Runtime Layer": "模型或智能体实际运行所需的进程、隔离和资源管理。",
    "L5 Orchestration Layer": "把多个步骤、工具或智能体组织成可执行流程。", "L6 Application Layer": "面向具体用户任务的产品和应用。",
    "L7 Enterprise / AI Operating System Layer": "为组织统一管理 AI 应用、权限、数据和运行资源的平台层。",
}
LIFECYCLE_ZH = {"Viral": "快速爆发", "Emerging": "正在升温", "Infrastructure": "基础设施", "Strategic": "战略方向", "Cooling": "热度降温"}

# Curated Chinese briefs grounded in the repository descriptions and README excerpts
# collected in the current snapshot. Unknown repositories get a cautious Chinese fallback.
PROJECT_GUIDES = {
    "mvschwarz/openrig": {"status":"AI 项目", "short":"把 Claude Code、Codex、Pi 等编码智能体组织成可持续协作的团队。", "what":"OpenRig 把分散的编码智能体整理成一个有角色、有共享上下文、能够持续协作的团队。", "problem":"多个编码智能体通常各自在终端里运行，团队任务、上下文和责任边界容易分散。", "how":"README 说明可以用 YAML 定义团队，再通过一条命令启动；可让负责人智能体协调不同专长的成员。", "value":"适合研究多智能体编程团队、任务分工、共享上下文和团队运行方式。", "caveat":"这里的介绍来自当前仓库简介和 README 摘要；实际能力、模型兼容性和安全边界应以项目文档为准。"},
    "boykopovar/anyps5": {"status":"非 AI 项目（搜索误入）", "short":"这是 PS5 程序跨平台移植工具，当前资料没有显示它使用 AI。", "what":"AnyPS5 的 README 介绍的是把 PS5 可执行程序移植到 Linux 和 Windows。", "problem":"游戏程序依赖特定平台的可执行格式和系统库，跨平台运行需要转换程序格式并适配系统接口。", "how":"项目提到 relinker（重新链接器）和系统库实现；README 明确写了无需模拟器或独立运行时进程。", "value":"可作为系统软件与兼容层项目了解，不属于本雷达应重点分析的 AI 技术趋势。", "caveat":"它被关键词搜索误收录；其仓库简介和 README 均未显示 AI 功能。"},
    "heygen-com/hyperframes": {"status":"AI 相关工具（需核对）", "short":"把 HTML 渲染成视频，并面向智能体工作流使用。", "what":"项目简介是“编写 HTML、渲染视频、为智能体打造”。因此它位于视频生成/渲染工具与智能体工作流的交叉处。", "problem":"让程序化生成的网页内容能够转成视频，并纳入自动化内容生产流程。", "how":"目前快照中的简介支持 HTML 到视频渲染这一点；更细的渲染架构、智能体接口和能力边界需阅读完整文档确认。", "value":"值得观察程序化视频制作与 AI 智能体自动化结合的工具链。", "caveat":"当前中文解读依据仓库简介；不能仅凭“built for agents”推断它自身包含模型或自主决策能力。"},
    "cursor/plugins": {"status":"AI 开发工具生态", "short":"Cursor 官方插件及扩展集合，覆盖开发工具、工作流和学习辅助。", "what":"这是 Cursor 编辑器的插件规范与官方插件集合；仓库内每个插件可以独立安装和维护。", "problem":"让开发者在编辑器中接入常用框架、SaaS 服务、团队流程和可复用开发辅助功能。", "how":"README 列出多种插件，例如持续学习、团队开发流程、代码审查和本地自动化等。", "value":"可研究 AI 编程产品如何通过插件生态扩展能力，以及技能、工作流如何分发。", "caveat":"仓库是插件集合，不应把其中每个插件都视为 AI 模型或智能体。具体插件功能需逐项查看。"},
    "nvidia/openshell": {"status":"AI 项目", "short":"为自主 AI 智能体提供更安全、私密的运行环境。", "what":"OpenShell 是面向自主智能体的运行时与隔离环境，重点是安全和隐私。", "problem":"智能体需要执行命令、访问文件或连接工具；缺少隔离时可能造成越权或数据暴露。", "how":"README 强调隔离机制、运行时能力和扩展接口；具体权限模型应以 NVIDIA 官方文档为准。", "value":"属于智能体基础设施方向，值得研究工具权限、执行隔离和安全控制如何落地。", "caveat":"本摘要不构成安全审计；部署前应核对威胁模型、默认权限和网络访问策略。"},
    "panniantong/agent-reach": {"status":"AI 项目", "short":"通过一个命令行工具，让 AI 智能体读取和搜索多个互联网平台。", "what":"Agent-Reach 为智能体接入互联网内容，仓库介绍的来源包括 Twitter/X、Reddit、YouTube、GitHub、Bilibili 和小红书。", "problem":"智能体通常缺少对不同网站的统一读取和搜索入口，各平台接入方式也会变化。", "how":"README 中文说明它会帮助安装、配置并检查连接方式；可作为 CLI 或相关智能体工具使用。", "value":"值得研究智能体如何接入多来源信息、工具连接如何维护，以及平台变化时如何降级。", "caveat":"“零 API 费用”等表述来自项目宣传；实际可用性、平台规则和费用应以项目文档及各平台条款为准。"},
    "thedotmack/claude-mem": {"status":"AI 项目", "short":"记录智能体会话，把信息压缩后带入后续会话，帮助跨会话保留上下文。", "what":"Claude-Mem 是跨会话记忆工具。项目简介称它会捕获会话活动、用 AI 压缩，并在后续会话中注入相关上下文。", "problem":"新会话往往丢失之前的任务背景、决定和操作记录，用户需要反复补充上下文。", "how":"按项目简介，它从会话中整理信息并在后续会话检索、注入；简介列出 Claude Code、OpenClaw、Codex、Gemini、Copilot 等支持对象。", "value":"适合研究智能体长期记忆、上下文压缩、信息筛选和跨会话恢复。", "caveat":"会话记录可能包含敏感内容；部署前应确认存储位置、保留期限、脱敏与删除机制。"},
    "pablostanley/yoinks": {"status":"非 AI 项目（搜索误入）", "short":"从命令行下载多个网站的视频或音频，当前资料没有显示它使用 AI。", "what":"yoinks 是命令行媒体下载工具。README 提到 YouTube、X/Twitter、Instagram、TikTok 等网站。", "problem":"用户希望从终端下载视频、选择分辨率或提取音频，而不经过广告下载页面。", "how":"项目简介提到粘贴链接后选择视频分辨率或 MP3 音频。", "value":"属于开发者工具，不是 AI 项目趋势样本。", "caveat":"当前仓库简介与 README 没有显示 AI 功能；它被候选发现过程误收录。下载行为应遵守来源网站规则和版权要求。"},
    "duartesantos8/opengym": {"status":"非 AI 项目（搜索误入）", "short":"自托管健身与体重记录应用，当前资料没有显示它使用 AI。", "what":"openGym 是可自行部署的健身和体重追踪应用。", "problem":"用户希望自己管理训练计划、运动记录和身体数据，而不是把数据交给第三方服务。", "how":"README 提到计划训练、记录组数与体重、跨设备同步，以及 passkey 登录。", "value":"属于个人健康应用，不是 AI 项目趋势样本。", "caveat":"当前仓库简介与 README 没有显示 AI 功能；它被候选发现过程误收录。"},
    "tile-ai/tilelang": {"status":"AI 相关基础设施（方向相邻）", "short":"用于编写高性能 GPU、CPU 和加速器计算内核的领域专用语言。", "what":"TileLang 是面向高性能计算内核开发的领域专用语言，支持 GPU、CPU 和加速器场景。", "problem":"手写和优化底层并行计算内核复杂，开发者需要更高层的表达方式兼顾性能。", "how":"仓库简介将其定位为简化高性能内核开发的语言；具体支持硬件、编译流程和性能需查阅项目文档与基准。", "value":"它可能支撑模型训练和推理性能优化，属于 AI 计算基础设施的相邻方向。", "caveat":"仓库简介描述的是通用高性能内核语言，不能据此断言它只服务 AI。需要结合实际案例和基准评估。"},
    "hunxbyts/ghosttrack": {"status":"非 AI 项目（搜索误入）", "short":"README 描述的是 IP 与手机号信息查询工具，当前资料没有显示它使用 AI。", "what":"GhostTrack 自述为 OSINT（开源情报）和信息收集工具，涉及 IP 与手机号查询。", "problem":"项目尝试从公开或外部信息源汇总网络地址和号码相关信息。", "how":"README 描述了 IP Tracker、Phone Tracker 等菜单功能。", "value":"不属于 AI 技术趋势样本，建议从 AI 领域分析中排除。", "caveat":"当前仓库简介与 README 没有显示 AI 功能；使用此类信息查询工具还需遵守当地法律和隐私规则。"},
}
PROJECT_TAXONOMY = {
    "mvschwarz/openrig": (["AI Coding", "Agent", "Agent Runtime", "Multi-Agent", "Agent Organization"], ["L3 Agent Layer", "L5 Orchestration Layer"]),
    "boykopovar/anyps5": ([], []),
    "heygen-com/hyperframes": (["Video", "Agent"], ["L6 Application Layer"]),
    "cursor/plugins": (["AI Coding", "Agent Skills"], ["L6 Application Layer"]),
    "nvidia/openshell": (["Agent", "Agent Runtime", "Agent Sandbox", "AI Infrastructure"], ["L4 Runtime Layer"]),
    "panniantong/agent-reach": (["Agent", "MCP"], ["L3 Agent Layer", "L6 Application Layer"]),
    "thedotmack/claude-mem": (["Agent Memory", "Context Engineering"], ["L3 Agent Layer", "L4 Runtime Layer"]),
    "pablostanley/yoinks": ([], []),
    "duartesantos8/opengym": ([], []),
    "tile-ai/tilelang": (["AI Infrastructure"], ["L2 Capability Layer", "L4 Runtime Layer"]),
    "hunxbyts/ghosttrack": ([], []),
}


def dashboard_data():
    snapshots_dir, history_path = _paths()
    snapshots = []
    if snapshots_dir.exists():
        for path in sorted(snapshots_dir.glob("*.json")):
            try:
                snapshots.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    current = {}
    for snapshot in snapshots:
        for repo in snapshot.get("repositories", []):
            if repo.get("repo"):
                current[repo["repo"].lower()] = repo
    history = load_history(history_path)
    observations = {}
    for row in history:
        name = row.get("repo")
        if not name:
            continue
        observations.setdefault(name.lower(), []).append({
            "snapshot_time": row.get("snapshot_time"),
            "stars": row.get("stars"),
            "growth_7d": row.get("growth_7d"),
            "growth_30d": row.get("growth_30d"),
            "acceleration": row.get("acceleration"),
            "trend_score": row.get("trend_score"),
        })
    slim_repos = []
    for repo in current.values():
        slim = {k: repo.get(k) for k in (
            "repo", "owner", "stars", "forks", "open_issues", "created_at", "updated_at", "pushed_at",
            "description", "topics", "language", "license", "html_url", "latest_release", "domains", "layers",
            "growth_7d", "growth_30d", "previous_7d_growth", "acceleration", "insufficient_history",
            "trend_score", "lifecycle", "community_activity", "technical_importance", "ecosystem_impact")}
        guide = PROJECT_GUIDES.get((repo.get("repo") or "").lower())
        slim["guide_zh"] = guide or {
            "status": "待补充中文解读",
            "short": "已发现该仓库，但系统尚未整理经过核对的中文项目介绍。",
            "what": "当前仅能确认仓库名称、GitHub 简介和自动分类；暂不据此推断项目功能。",
            "problem": "数据不可得。需要阅读 README 和项目文档后再总结。",
            "how": "数据不可得。请查看项目原文说明及代码。",
            "value": "可先根据领域标签把它作为候选观察对象；自动标签不代表人工确认。",
            "caveat": "尚无经过核对的中文项目摘要。请打开 GitHub 仓库查看完整 README。",
        }
        taxonomy = PROJECT_TAXONOMY.get((repo.get("repo") or "").lower())
        domains, layers = taxonomy if taxonomy is not None else (repo.get("domains") or [], repo.get("layers") or [])
        slim["domains_zh"] = [{"name": d, "label": DOMAIN_ZH.get(d, d), "info": DOMAIN_INFO.get(d, "此分类由仓库关键词自动匹配，可能有误。")}
                               for d in domains]
        slim["layers_zh"] = [{"name": d, "label": LAYER_ZH.get(d, d), "info": LAYER_INFO.get(d, "此层级由仓库关键词自动匹配，可能有误。")}
                             for d in layers]
        slim["is_ai_project"] = not (guide and guide.get("status", "").startswith("非 AI"))
        slim["lifecycle_zh"] = "不适用（候选误收）" if not slim["is_ai_project"] else LIFECYCLE_ZH.get(repo.get("lifecycle"), "数据不可得")
        slim_repos.append(slim)
    return {
        "snapshot_time": max((s.get("snapshot_time", "") for s in snapshots), default=None),
        "snapshot_count": len(snapshots),
        "history_count": len(history),
        "repositories": sorted(slim_repos, key=lambda r: r.get("stars") or 0, reverse=True),
        "observations": observations,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/data":
            body = json.dumps(dashboard_data(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/", "/index.html"):
            try:
                body = ASSET.read_bytes()
            except OSError:
                self.send_error(500, "Dashboard asset not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, fmt, *args):
        print("[dashboard] " + fmt % args)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve the local GitHub AI Radar dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: local machine only)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"GitHub AI Radar dashboard: http://{args.host}:{args.port}")
    print("Keep this terminal open while using the dashboard. Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
