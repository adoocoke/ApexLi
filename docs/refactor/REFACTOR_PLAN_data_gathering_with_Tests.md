# data_gathering 节点重构计划（含单元测试补充）

## 1. 总体目标

在进行 `data_gathering` 节点重构前，**优先补充单元测试**，建立测试保护网，再采用**绞杀者模式**逐步迁移到原生 Tool Calling 方式。

核心原则：
- 先有测试保护，再做重构
- 新旧逻辑并存，通过开关控制
- 逐步替换，最终清理旧代码

## 2. 当前问题

- `data_gathering.py` 目前**几乎没有单元测试**覆盖
- 直接重构风险较高（尤其是重命名或大幅修改逻辑）
- 需要为后续双路径改造提供安全保障

## 3. 阶段规划

### 阶段 0：补充单元测试（必须先做）

在任何重构代码前，先为 `data_gathering.py` 中的所有函数补充单元测试。

#### 3.1 需要测试的函数

| 函数名                    | 优先级 | 复杂度 | 说明 |
|---------------------------|--------|--------|------|
| `extract_ts_code`         | P0     | 低     | 字符串解析工具函数 |
| `get_related_for_symbol`  | P0     | 低     | 相关品种映射逻辑 |
| `data_gathering`          | P0     | 中高   | 核心业务逻辑（重点） |

#### 3.2 单元测试补充计划

**测试文件位置**：`tests/nodes/test_data_gathering.py`

**核心测试场景**：

**A. `extract_ts_code` 测试**
- 正常提取 `ts_code`
- 处理重复代码情况（如 `"RB2610 RB2610.SHF"`）
- 异常输入处理（空字符串、非字符串等）

**B. `get_related_for_symbol` 测试**
- 常见品种映射（RB、SA、I 等）
- 未知品种返回默认值
- 输入带后缀的情况

**C. `data_gathering` 主函数测试（重点）**
- `data_requests` 为空
- `data_type` 包含 `longer_history` / `12个月`
- `data_type = "相关品种日线"`
- `data_type = "holding"`
- `data_type = "news"`
- `data_type = "技术指标"`
- 多种请求同时存在
- 异常 `data_requests` 格式容错

**测试技术要点**：
- 使用 `pytest`
- 大量使用 `unittest.mock.patch` mock 外部数据函数
- 使用 fixture 构建基础 `state`
- 每个测试验证 `extra_data`、`news`、`market_data` 等状态变更

**执行顺序建议**：
1. 先写 `extract_ts_code` 和 `get_related_for_symbol` 的测试
2. 再写 `data_gathering` 的核心分支测试
3. 所有测试通过后再开始代码重构

### 阶段 1：工具函数 `@tool` 化

在测试保护下，将相关函数改成 LangChain `@tool` 形式：
- `get_futures_holding`
- `get_futures_basic`
- `get_related_futures_dynamic`
- `get_futures_news`

### 阶段 2：实现双路径（绞杀者模式核心）

保持 `data_gathering` 函数名不变，内部实现双路径：

```python
def data_gathering(state: TAState) -> TAState:
    use_native = os.getenv("USE_NATIVE_TOOL_CALLING", "false").lower() == "true"
    if use_native:
        return _data_gathering_with_tools(state)
    else:
        return _data_gathering_legacy(state)
```

- `_data_gathering_legacy`：保留原有全部逻辑
- `_data_gathering_with_tools`：新路径（使用 `bind_tools`）

### 阶段 3：灰度与验证

- 通过环境变量控制新旧路径
- 新路径逐步补全测试
- 验证功能一致性

### 阶段 4：清理旧代码（最终阶段）

新路径稳定后，逐步删除 `_data_gathering_legacy` 及相关旧逻辑。

## 4. 风险控制

- **测试先行**：所有重构前必须有 UT 覆盖
- **函数名不变**：`data_gathering` 对外接口保持不变
- **开关控制**：可随时回滚到旧逻辑
- **Mock 机制**：新旧路径都要支持 Mock 数据

## 5. 预期成果

- `data_gathering.py` 获得较完整的单元测试覆盖
- 重构过程安全可控
- 为后续 `observation` 和 `signal_generation` 的重构积累经验和模板

## 6. 下一步行动

1. 创建 `tests/nodes/test_data_gathering.py`
2. 编写 `extract_ts_code` + `get_related_for_symbol` 的测试
3. 编写 `data_gathering` 核心场景的测试
4. 跑通所有测试
5. 开始 `@tool` 化和双路径实现

---

**备注**：本计划将“补充单元测试”作为重构的**前置必做步骤**，而非可选。