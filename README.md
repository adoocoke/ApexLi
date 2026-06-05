# eaagent

**eaagent** 是一个基于 **Grok (xAI)** 的简洁、强大、可扩展的 ReAct Agent 实现。

专为快速构建工具调用型 Agent 而设计，特别适合交易策略、数据分析、自动化任务等场景。

## ✨ 特性

- ✅ 基于 Grok-4.3（当前最强工具调用模型之一）
- ✅ 完整 ReAct 循环（Thought → Action → Observation）
- ✅ 极简 API：一行代码注册工具
- ✅ 完全兼容 OpenAI SDK 格式
- ✅ 支持自定义任意工具（天气、交易数据、计算、网页搜索等）
- ✅ 清晰的执行日志，便于调试
- ✅ 环境变量安全管理（支持 `.env`）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或使用 uv（推荐）：

```bash
uv pip install -r requirements.txt
```

### 3. 配置 xAI API Key

在项目根目录创建 `.env` 文件：

```env
XAI_API_KEY=xai-你的密钥
```

**如何获取 API Key？**

1. 访问 [https://console.x.ai](https://console.x.ai)
2. 使用 X 账号登录
3. 左侧菜单 → **API Keys** → 创建新密钥
4. 复制以 `xai-` 开头的密钥

### 4. 运行示例

```bash
python examples/basic_weather.py
```

### 5. 运行测试

```bash
# 安装开发依赖（包含 pytest）
pip install -e ".[dev]"

# 运行所有测试
pytest

# 只运行 agent 测试
pytest tests/test_agent.py -v
```

## 📦 项目结构

```
eaagent/
├── eaagent/                  # 核心代码
│   ├── __init__.py
│   ├── agent.py
│   └── tools/
├── examples/                 # 使用示例
│   └── basic_weather.py
├── tests/                    # 单元测试
│   ├── __init__.py
│   └── test_agent.py
├── pytest.ini
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

## 🛠️ 自定义工具示例

```python
from eaagent import ReActAgent

def my_calculator(a: float, b: float, op: str) -> float:
    if op == "+": return a + b
    if op == "*": return a * b
    ...

agent = ReActAgent(model="grok-4.3")

agent.add_tool(
    name="calculator",
    description="执行基础数学计算",
    parameters={
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
            "op": {"type": "string", "enum": ["+", "-", "*", "/"]}
        },
        "required": ["a", "b", "op"]
    },
    function=my_calculator
)

agent.run("计算 123 * 45 + 67 的结果")
```

## 🔧 进阶用法

### 修改模型

```python
agent = ReActAgent(model="grok-4.3")           # 推荐（工具调用最强）
# agent = ReActAgent(model="grok-build-0.1")   # 代码生成场景
```

### 关闭详细日志

```python
agent = ReActAgent(verbose=False)
```

### 增加最大步数

```python
agent = ReActAgent(max_steps=20)
```

## 🎯 适用场景

- 交易策略 Agent（期货、技术分析、多时间框架）
- 数据查询 + 分析自动化
- 复杂多步推理任务
- 快速原型验证工具调用能力

## 📌 后续规划（欢迎贡献）

- [ ] 支持 LangGraph / CrewAI 风格多 Agent
- [ ] 内置常用交易工具（K线、技术指标）
- [ ] 支持记忆与 checkpoint
- [ ] CLI 命令行工具
- [ ] 更多真实工具集成（网页搜索、代码执行等）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

---

**Powered by Grok-4.3** | Made with ❤️ by adoocoke

如有问题或建议，欢迎在 Issues 中讨论。refresh contributors
