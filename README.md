# EA Agent

**EA Agent** 是一个基于 ReAct 架构的智能期货交易代理框架，结合结构化市场观察、Playbook 知识注入和自我反思能力，旨在帮助交易者构建可解释、可迭代的交易决策系统。

## 核心特性

- **结构化市场观察**：自动提取量仓变化、ATR、均线、关键价格位置等关键信息
- **Playbook 驱动**：将个人交易经验蒸馏为结构化规则，通过 Prompt 注入 Agent
- **自我反思机制**：Agent 能够基于 Playbook 对自身输出进行规则检查与反思
- **Mock 模式支持**：开发阶段可快速切换模拟数据，避免受数据源限制
- **LangGraph 工作流**：支持状态管理、工具调用和人类反馈闭环
- **模块化扩展**：通过 `a_plus_plus` 子包轻松扩展能力

## 项目结构

```
eaagent/
├── eaagent/
│   ├── a_plus_plus/          # A++ 扩展模块（核心新增）
│   │   ├── tools.py          # 结构化 Observation + Mock 支持
│   │   ├── graph.py          # LangGraph 工作流（Reasoning + Tools + Reflection）
│   │   ├── prompt_builder.py # Playbook 加载与 Prompt 构建
│   │   └── ...
│   ├── agent.py              # 基础 ReActAgent
│   └── tools/                # 原始工具集
├── tests/
├── pyproject.toml
└── README.md
```

## 快速开始

### 安装

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
pip install -e ".[dev,tushare,langgraph]"
```

### 启用 Mock 模式（推荐开发时使用）

```bash
export USE_MOCK_OBSERVATION=true
python -c "
from eaagent.a_plus_plus.graph import build_graph, create_initial_state

app = build_graph()
state = create_initial_state()
state['current_symbol'] = 'RB2605'
state['messages'] = [{'role': 'user', 'content': '请分析当前螺纹钢走势'}]

config = {'configurable': {'thread_id': 'demo-001'}}
result = app.invoke(state, config)
print(result['messages'][-1])
"
```

### 使用真实 Playbook（CI 默认）

项目使用单独的私有仓库管理 `trading_playbook_v3.md`，CI 会自动通过 Token 拉取并加载。

本地开发如需使用真实 Playbook，请将文件放置于以下任一路径：

- `artifacts/playbooks/trading_playbook_v3.md`
- `artifacts/trading_playbook_v3.md`
- 项目根目录 `trading_playbook_v3.md`

## 核心模块说明

### `eaagent.a_plus_plus`

- **tools.py**：提供结构化市场观察，支持真实数据与 Mock 模式
- **graph.py**：定义 ReAct + Reflection 工作流
- **prompt_builder.py**：负责加载 Playbook 并构建系统 Prompt

### Reflection 机制

Agent 在输出后会进行自我反思，检查是否符合 Playbook 中的核心原则，例如：
- 是否基于足够 Observation 进行判断
- 是否关注量仓变化
- 是否体现了“信息不足时主动放弃”的原则

## 开发建议

- 日常开发推荐开启 Mock 模式（`USE_MOCK_OBSERVATION=true`）
- CI 默认使用真实 Playbook 进行验证
- 新增规则或 Few-shot 示例建议更新 `trading_playbook_v3.md`

## License

MIT
