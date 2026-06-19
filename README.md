# EA Agent

**EA Agent** 是一个基于 **LangGraph** 构建的**期货技术分析智能体**，核心目标是实现**透明、可观测、可迭代**的多轮技术分析流程，而不是黑盒输出。

项目采用 **Martin Fowler Agent Harness** 思想，结合 **Strategy Pattern** 和结构化 LLM 输出，打造可控的分析闭环。

---

## 核心特性

| 特性                    | 说明 |
|-------------------------|------|
| **多轮自动分析**        | 支持最多 5 轮自动迭代分析，遇到问题时自动触发下一轮 |
| **Playbook Strategy**   | 支持 `Full` / `Core` / `IdOnly` 三种 Playbook 注入策略，可通过环境变量切换 |
| **结构化 LLM 输出**     | `structured_observation` 和 `signal_generation` 均输出结构化 JSON，便于后续节点消费 |
| **智能 Sensors**        | `quality_sensor` + `llm_critique` 共同判断是否继续分析，减少无效轮次 |
| **透明可观测**          | 每轮清晰打印策略使用情况、质量检查结果、LLM 返回内容 |
| **Mock / 真实数据**     | 通过 `USE_MOCK_OBSERVATION` 快速切换 Mock 与真实 Tushare 数据 |
| **节点化架构**          | 将分析流程拆分为 `nodes/` 模块，便于维护和扩展 |
| **完整测试覆盖**      | pytest + Makefile 管理测试                                      |

---

## 快速开始

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
pip install -e ".[dev,langgraph,tushare]"
```

### 运行（推荐 Mock 模式）

```bash
python -m eaagent.a_plus_plus.graph
```

### 使用 Core Rules 策略（推荐节省 Token）

```bash
PLAYBOOK_STRATEGY=core python -m eaagent.a_plus_plus.graph
```

### 使用真实 Tushare 数据

```bash
USE_MOCK_OBSERVATION=false python -m eaagent.a_plus_plus.graph
```

> 需要配置环境变量 `TUSHARE_TOKEN`

---

## 项目结构

```
eaagent/
├── eaagent/
│   ├── a_plus_plus/
│   │   ├── graph.py                 # Harness 核心（Graph 组装 + 节点调用）
│   │   ├── types.py                 # TAState 定义
│   │   ├── utils/
│   │   │   ├── llm.py               # call_llm（支持 Mock）
│   │   │   └── console.py           # 颜色输出工具
│   │   ├── nodes/                   # 各分析节点（已拆分）
│   │   │   ├── observation.py       # 结构化市场观察（JSON 输出）
│   │   │   ├── signal.py
│   │   │   ├── quality_sensor.py
│   │   │   └── ...
│   │   ├── strategies/              # Playbook 注入策略
│   │   │   └── playbook_strategies.py
│   │   ├── data_provider.py
│   │   └── playbook_loader.py
│   └── ...
├── tests/
├── todo/
│   └── graph_refactor_plan.md       # 重构进度追踪
└── README.md
```

---

## 主要设计亮点

### 1. Playbook Strategy Pattern
支持三种注入方式：
- `full`：发送完整 Playbook（默认）
- `core`：仅发送精简核心规则（节省 Token）
- `id_only`：后续轮次仅发送 Playbook ID

通过环境变量 `PLAYBOOK_STRATEGY` 控制。

### 2. 结构化 LLM 沟通
- `structured_observation` 输出包含趋势、关键位、量价、形态、结论等结构化信息
- `signal_generation` 输出包含方向、入场、止损、理由的 JSON
- 便于后续 Sensors 和多轮分析复用

### 3. 智能多轮控制
通过 `quality_sensor` + `llm_critique` 共同判断是否继续下一轮，避免无效分析。

---

## 环境变量

| 变量                        | 默认值   | 说明 |
|-----------------------------|----------|------|
| `USE_MOCK_OBSERVATION`      | `true`   | 是否使用 Mock 数据 |
| `PLAYBOOK_STRATEGY`         | `full`   | Playbook 注入策略（`full` / `core`） |
| `TUSHARE_TOKEN`             | -        | Tushare 接口 Token |

---

## 测试

```bash
make test              # 运行所有测试
make test-cov          # 带覆盖率报告
```

---

## 开发建议

- 日常开发推荐使用 `USE_MOCK_OBSERVATION=true`
- 修改节点逻辑后请运行测试
- 重构或新增节点请同步更新 `todo/graph_refactor_plan.md`

---

## License

MIT
