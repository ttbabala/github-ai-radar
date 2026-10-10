# GitHub AI Trend Radar

**看见 AI 开源项目如何成长。** GitHub AI Trend Radar 是一个开源研究工具：它从公开 GitHub 仓库发现 AI 项目，保存可复查的数据快照，并用中文报告和本地交互式驾驶舱呈现项目增长与技术方向。

> 项目正在早期积累阶段。它展示可观察到的公开仓库数据，不声称覆盖 GitHub 上全部 AI 项目，也不会把缺失的历史数据伪装成增长。

中文用户请从[中文使用手册](docs/使用手册.md)开始。English readers: this project is an experimental, reproducible research tool for exploring public GitHub AI repositories. Contributions and documentation improvements are welcome.

## 你可以用它做什么

- **发现项目：** 根据可配置的搜索主题整理 AI 仓库候选，并读取公开仓库元数据。
- **观察成长：** 保存每天的 Star 等公开指标快照；历史基线足够时才计算 7 天、30 天变化和加速度。
- **理解方向：** 按技术领域和层级整理项目，并生成中文 Markdown 趋势报告。
- **浏览驾驶舱：** 在本机查看项目、历史曲线、分类和中文解读。
- **复现分析：** 报告生成可以使用已保存的数据，不需要访问 GitHub。

## 驾驶舱预览

运行 `python3 -m radar.dashboard` 后，在浏览器打开 <http://127.0.0.1:8765>。仪表盘从本机 `data/` 和 `reports/` 读取数据；没有历史记录时会明确显示“数据不可得”。

## 快速开始

需要 Python 3.9 或更新版本。

```bash
git clone https://github.com/ttbabala/github-ai-radar.git
cd github-ai-radar
python3 -m pip install -e '.[test]'
python3 -m radar
python3 -m radar.dashboard
```

在另一个终端重新生成最新快照对应的报告（不访问网络）：

```bash
python3 -m radar --report
```

GitHub Token 是可选项，只用于提高公开 API 的请求额度。请使用只读、最小权限的 Token，并通过环境变量提供；不要把真实 Token 写进文件、提交或 issue。没有 Token 时仍会尝试使用 GitHub 的未认证公开 API 额度。

```bash
read -s "GITHUB_TOKEN?输入 GitHub Token："
export GITHUB_TOKEN
python3 -m radar
unset GITHUB_TOKEN
```

## 常用命令

| 命令 | 用途 |
|---|---|
| `python3 -m radar` | 从 GitHub 更新公开数据并生成日报、周报、月报 |
| `python3 -m radar --report` | 使用最近保存的快照重新生成报告，不请求 GitHub |
| `python3 -m radar --domain agent` | 更新数据并只在报告中关注匹配方向 |
| `python3 -m radar.dashboard` | 启动本地交互式数据驾驶舱 |
| `python3 -m pytest` | 运行不访问 GitHub 的自动化测试 |

首次运行只建立基线。需要持续定期采集，才可能获得真实的 7 天和 30 天变化。更完整的安装、操作和常见问题见[使用手册](docs/使用手册.md)。

## 数据与隐私

- 只采集 GitHub 上公开可访问的仓库信息；本工具不会创建、修改或推送 GitHub 仓库。
- `GITHUB_TOKEN` 只在当前进程中读取，不写入项目配置或生成的报告。
- 本机采集的快照、历史记录和报告均在 `.gitignore` 中排除，不会被正常 Git 提交带入仓库。
- GitHub API 及 Trending 页面的公开数据受其服务条款、速率限制和可用性约束。
- 报告可能包含公开仓库的 README 摘录和项目元数据。分享报告前请自行检查内容。

## 方法与局限

- 搜索和 GitHub Trending 仅用于发现候选，不是完整清单；Trending 页面不是官方稳定 API。
- 项目分类基于关键词和少量人工核对信息，可能误判。请回到原始仓库核实。
- Star 变化仅基于实际保存的历史观察。缺少目标时间点之前的基线时，数值保持缺失。
- 趋势分数中的部分维度是可配置的启发式代理指标，不代表代码质量、技术影响力或商业价值的客观测量。
- Star 数不能单独证明项目质量、用户留存、商业前景或技术优势。

## 项目结构

```text
config/       搜索范围、分类词表、权重和阈值
dashboard/    本地交互式驾驶舱页面
docs/         中文使用手册
radar/        采集、分析、报告和本地服务
skills/       可复用的 Agent 研究规范与分类参考
tests/        使用固定数据的离线测试
data/         本机快照与历史记录（Git 忽略）
reports/      本机生成的 Markdown 报告（Git 忽略）
```

## 参与贡献

欢迎提交问题报告、文档改进和代码贡献。开始前请阅读[贡献指南](CONTRIBUTING.md)和[安全政策](SECURITY.md)。分类或指标建议请尽量附上可复现的例子；测试不得调用 GitHub。

## 许可

本项目按 [MIT License](LICENSE) 开源。
