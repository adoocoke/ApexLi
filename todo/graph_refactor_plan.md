# Graph 重构计划（Node 拆分）

## 目标
将 `eaagent/a_plus_plus/graph.py` 中臃肿的节点函数拆分到 `nodes/` 目录下，使代码结构更清晰、职责更单一，便于后续维护和扩展。

## 当前状态（2026-06-19 更新）
- [x] 提取 `call_llm` 到 `utils/llm.py`
- [x] 提取 Console 颜色工具到 `utils/console.py`
- [x] 新增 `types.py`（独立存放 `TAState`，解决循环导入）
- [x] 拆分 `persist` 节点到 `nodes/persist.py`
- [ ] 继续拆分其他节点（暂停中）

## 拆分节奏（一个节点一个 Commit + Push）

| 顺序 | 节点文件                  | 对应函数                          | 状态      | 备注 |
|------|---------------------------|-----------------------------------|-----------|------|
| 1    | `nodes/persist.py`        | `persist`                         | ✅ Done   | 已完成并推送 |
| 2    | `nodes/data_ingestion.py` | `data_ingestion`                  | TODO      | - |
| 3    | `nodes/quality_sensor.py` | `quality_sensor`                  | TODO      | - |
| 4    | `nodes/signal.py`         | `signal_generation`               | TODO      | - |
| 5    | `nodes/observation.py`    | `structured_observation`          | TODO      | - |
| 6    | `nodes/critique.py`       | `llm_critique` + `should_continue_after_critique` | TODO | - |
| 7    | `nodes/initialize.py`     | `initialize_state`                | TODO      | 最复杂，最后做 |
| 8    | `nodes/final_output.py`   | `final_output`                    | TODO      | - |

## 每个节点的拆分要求
1. 将函数移动到对应文件
2. 在 `nodes/__init__.py` 中导出
3. 在 `graph.py` 中 import 使用
4. 添加/更新对应测试（如有必要）
5. Commit + Push

## 拆分原则
- 每个节点函数独立成文件
- 保持原有逻辑不变
- 每完成一个节点就测试 + commit + push
- 拆分过程中保持 `graph.py` 可运行

## 后续优化（拆分完成后）
- [ ] 优化 Console 输出（颜色 + Sensors 突出显示）
- [ ] 进一步清理 `graph.py`（只保留 Graph 组装逻辑）
- [ ] 考虑是否需要 `nodes/base.py` 统一定义节点接口

## 备注
- 2026-06-19：已完成工具模块提取 + persist 节点拆分，暂时暂停继续拆分
