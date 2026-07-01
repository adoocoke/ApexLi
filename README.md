# EA Agent

**EA Agent** 是一个基于 **LangGraph** 构建的**期货技术分析智能体**，采用 **Martin Fowler Agent Harness** 架构（Guides/Sensors/Actor/Steering/Memory），专注于为期货交易者提供**结构化、多轮自动优化**的技术分析。

**核心理念**：每一步分析都**可审计** — 数据来源、精确引用的 Playbook 规则、质量传感器结果、LLM Critique 以及多轮演进过程在控制台和报告中完全可见。没有黑盒。

---

## 核心特性

| 特性                  | 说明                                                                 |
|-----------------------|----------------------------------------------------------------------|
| **多轮自动分析**      | 默认最多进行 3 轮分析，遇到问题时自动继续优化                        |
| **透明日志**          | 每轮都会清晰打印数据来源、参考的 Playbook 规则、质量检查结果         |
| **Playbook 驱动**     | 自动加载 `trading_playbook_v3.md`，并在分析时展示匹配的规则          |
| **Mock / 真实数据切换** | 通过环境变量 `USE_MOCK_OBSERVATION` 控制是否使用真实 Tushare 数据   |
| **质量检查 (Sensors)** | 自动检测数据不足、置信度低等问题，并触发下一轮分析                   |
| **持久化支持**        | 支持通过 `thread_id` 继续追问同一个品种                              |
| **完整测试覆盖**      | 使用 pytest + Makefile 管理测试                                      |

---

## 快速开始

### 安装

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
pip install -e ".[dev,langgraph,tushare]"
```

### 基础运行（Mock 模式，默认推荐）

```bash
python -m eaagent.a_plus_plus.graph
```

### 使用真实 Tushare 数据

```bash
USE_MOCK_OBSERVATION=false python -m eaagent.a_plus_plus.graph
```

> 需要提前配置环境变量 `TUSHARE_TOKEN`

---

## 项目结构

```
eaagent/
├── eaagent/
│   ├── a_plus_plus/              # 核心增强模块（当前主力）
│   │   ├── graph.py              # 多轮分析 + 透明日志 + Harness 核心
│   │   ├── prompt_builder.py     # Playbook 加载
│   │   └── tools.py
│   ├── tools/                    # Tushare 等工具
│   └── agent.py
├── tests/                        # 完整测试
├── Makefile                      # 便捷测试命令
└── README.md
```

---

## 运行效果示例

```text
======================================================================
[初始化] 开始分析 RB2605
  - 数据来源: MOCK
  - Playbook: ✅ 成功加载（共 12 条关键规则）
  - 最大分析轮次: 3
======================================================================

[第 1 轮] 数据获取阶段
  → 使用 Mock 数据

[第 1 轮] 结构化市场观察
  → 参考 Playbook 规则: ['量仓变化优先', '多时间框架一致性']

[第 1 轮] 生成交易信号
  → 参考 Playbook 规则: ['严格止损纪律']

[第 1 轮] 质量检查 (Sensors)
  → 发现问题，进入第 2 轮...

[第 2 轮] 数据获取阶段
...

======================================================================
【RB2605 技术分析报告】（共 2 轮）
======================================================================
数据来源: MOCK
Playbook 使用: 是
实际分析轮次: 2
最终综合置信度: 81%
最终交易信号:
  • 多头 | 入场 4125 | 止损 4080
✅ 分析完成，未发现明显问题
======================================================================
```

---

## 主要模块说明

### `eaagent/a_plus_plus/graph.py`（核心）

当前项目的**核心引擎**，实现了以下能力：

- 多轮自动分析循环（问题驱动）
- 清晰的每轮日志输出
- Playbook 规则匹配展示
- Tushare / Mock 数据源切换
- Sensors 质量检查机制

### Playbook 集成

项目会自动尝试加载 `trading_playbook_v3.md`，并在分析过程中展示**参考了哪些规则**。

支持的加载路径（按优先级）：
- `artifacts/trading_playbook_v3.md`
- `artifacts/playbooks/trading_playbook_v3.md`
- 项目根目录 `trading_playbook_v3.md`

---

## 测试

```bash
# 运行全量测试
make test

# 运行带覆盖率的测试
make test-cov
```

---

## 环境变量

| 变量                        | 默认值   | 说明                                      |
|-----------------------------|----------|-------------------------------------------|
| `USE_MOCK_OBSERVATION`      | `true`   | 是否使用 Mock 数据，设为 `false` 时尝试调用真实 Tushare |
| `TUSHARE_TOKEN`             | -        | Tushare 接口 Token                        |

---

## 开发建议

- 日常开发推荐开启 Mock 模式 (`USE_MOCK_OBSERVATION=true`)。
- 修改 `graph.py` 或 nodes 后必须运行 `make test` (AGENTS.md Test-First)。
- 新功能 (Web 双菜单主力合约 K线 + **中文品种名**) 已集成 — 菜单显示“螺纹钢 RB2610.SHF”、“铁矿石 I2609.DCE”等关注品种 (过滤/搜索/动态K线/相关图支持)。
- 参考 `docs/AGENTS.md` (Orient-Clarify-Slice-Check-TDD-Verify-Reflect 循环)、`docs/wiki/Development-Guide.md` 和 `todo/remaining_work.md`。
- 高优先剩余任务：完善 Strategy 完全切换、清理旧测试文件、CI 覆盖率。

---

## License

MIT

---

**最近进展 (EA-001~EA-005 + Web + Tools + Report)**

- **EA-001~EA-005**：完成质量提升计划（结构化`playbook_references` + "引用XX规则："强reason + quality_sensor软单观测 + LLM Critique早停优化 + 多轮路径总结/关键规则一览/最终决策依据）。
- **Web UI**：中文主力合约菜单（螺纹钢 RB2610.SHF、铁矿石 I2609.DCE、纯碱 SA2609.ZCE、焦煤 JM、焦炭 J、玻璃 FG 等关注品种及其相关），支持交易所过滤、搜索、Strategy切换、动态K线 + 相关品种独立Tabs、可拖拽50%宽度报告控制台（富文本Blog风格，高度680px匹配K线）。
- **LLM Tools**（5个，已注册）：`get_futures_holding`（持仓排名）、`get_futures_basic`（合约信息）、`get_related_futures_dynamic`（相关品种）、`generate_kline_chart`（K线）、**`get_futures_news`**（实时网络搜索5条重要新闻/宏观政策，fallback mock）。Prompt明确使用理由（news用于基本面驱动、holding用于仓位博弈、basic用于合约规格）。
- **报告优化**：Extra Data（详细Holding broker/vol）+ **📰 重要新闻区块**（5条 + LLM理解/弃用说明：“已纳入决策”或“暂未深度分析/弃用”） + 多轮总结/规则引用/决策依据。强制多轮（<4轮始终继续）。
- **其他**：动态RELATED_MAP（RB→I/JM等）、CZCE/SA数据修复、Test-First（pytest全通过）、AGENTS.md严格遵循（Orient-Clarify-Slice-Check-TDD-Verify-Reflect，每步commit/push）。

**整体质量**：从早期42-72%提升至85%+，Web体验、透明度、可解释性大幅改善。LLM可自主调用工具，报告完整展示工具调用结果 + 分析逻辑。

*Built for transparency. Maintained with ❤️ by the ApexLi team.*
