# Structured LLM Communication

## 目标
让系统与 LLM 的所有交互都输出结构化 JSON，而非自由文本，提升可解析性和一致性。

## 当前实现

### 1. structured_observation
输出包含以下结构：
- `trend`（中期/短期趋势）
- `key_levels`（强压力位 / 强支撑位）
- `volume_analysis`
- `pattern`
- `conclusion`
- `risk_note`
- `playbook_references`

### 2. signal_generation
输出包含：
- `direction`
- `entry_zone`
- `stop_loss`
- `target`
- `reason`（必须引用 Playbook）

### 3. llm_critique
输出包含：
- `should_continue`
- `reason`

## 好处

- 下游节点（Sensors、Critique）可以可靠消费数据
- 便于多轮分析中的增量判断
- 提升最终报告的可读性和可追渲性