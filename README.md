# eaagent

**eaagent** 是一个基于 **Grok (xAI)** 的简洁、强大、可扩展的 ReAct Agent 框架。

专为快速构建工具调用 + 记忆能力的 Agent 而设计，特别适合**期货交易分析**、数据处理、自动化任务等场景。

## ✨ 核心特性

- ✅ 基于 Grok-4.3（当前工具调用能力最强的模型之一）
- ✅ 完整 ReAct 循环（Thought → Action → Observation → Answer）
- ✅ **Memory 系统**（手动 + 自动提取 + SQLite 持久化）
- ✅ 极简工具注册：一行代码即可添加任意工具
- ✅ 支持 Tushare 期货数据（日线 + 分钟线）
- ✅ 多方式安全管理 API Key（keyring / 环境变量 / GitHub Secrets）
- ✅ 完整测试覆盖 + GitHub Actions CI
- ✅ 清晰的执行日志，便于调试和学习

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
```

### 2. 安装依赖

```bash
pip install -e ".[dev]"
```

### 3. 配置 xAI API Key（推荐方式）

#### 本地开发推荐使用 `keyring`（最安全）

```bash
pip install keyring

# 只需执行一次
python -c "
import keyring
keyring.set_password('eaagent', 'xai_api_key', 'xai-你的密钥')
print('✅ API Key 已安全存入系统密钥管理器')
"
```

#### GitHub CI 配置

在仓库 **Settings → Secrets and variables → Actions** 中添加：

- `XAI_API_KEY`：你的 xai- 密钥
- `TUSHARE_TOKEN`：你的 Tushare Token（用于期货数据测试）

### 4. 运行示例

```bash
python examples/basic_weather.py
```

### 5. 运行测试

```bash
# 运行所有测试
pytest

# 只运行 Agent 测试
pytest tests/test_agent.py -v

# 只运行 Memory 测试
pytest tests/test_memory.py -v
```

## 🧠 Memory 系统（核心亮点）

eaagent 内置了完整的 Memory 能力：

- **手动记忆**：`agent.remember("铁矿石趋势", "目前处于下降通道")`
- **自动记忆提取**：开启 `auto_memory=True` 后，Agent 会自动从对话中提取关键事实
- **SQLite 持久化**：记忆会自动保存到本地数据库，重启后依然存在
- **跨会话可用**：适合需要长期记忆的交易分析场景

## 📦 项目结构

```
eaagent/
├── eaagent/
│   ├── agent.py              # ReAct Agent 核心
│   ├── memory.py             # SQLite 持久化 Memory
│   └── tools/
│       ├── tushare_futures.py   # 日线工具
│       └── tushare_minute.py    # 分钟线工具
├── examples/
├── tests/                    # 完整测试（Agent / Memory / Tushare）
├── .github/workflows/
│   └── test.yml              # CI 配置
├── pyproject.toml
└── README.md
```

## 🛠️ 自定义工具示例

```python
from eaagent import ReActAgent

def get_weather(city: str) -> str:
    return f"{city} 今天天气晴朗，25°C"

agent = ReActAgent(verbose=True)
agent.add_tool(
    name="get_weather",
    description="查询城市天气",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
    },
    function=get_weather
)

agent.run("北京今天天气怎么样？")
```

## 📈 期货数据工具（Tushare）

```python
from eaagent.tools import get_futures_daily, get_futures_minute

# 日线
print(get_futures_daily("RB2405.SHF", "20240301"))

# 分钟线
print(get_futures_minute("RB2405.SHF", "20240305090000", freq="5min"))
```

**需要 Tushare Token？**

访问 [https://tushare.pro](https://tushare.pro) 注册并获取 Token，设置环境变量 `TUSHARE_TOKEN` 即可使用。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**License**: MIT
