# observation.py 单元测试补充计划（详细版）

## 1. 当前测试覆盖情况

`observation.py` 目前**几乎没有单元测试**。这是重构前必须补上的保护网。

## 2. 需要测试的核心函数

| 函数 | 优先级 | 复杂度 | 测试重点 |
|------|--------|--------|----------|
| `structured_observation` | P0 | 高 | 主流程、visual 成功/失败分支、state 变更 |
| `_prepare_daily_data` | P0 | 低 | DataFrame 处理、列过滤、max_rows |
| visual_analyzer 相关逻辑 | P0 | 中 | force_new_image 判断、缓存命中 |

## 3. 推荐测试文件结构

```
tests/nodes/
├── test_observation.py
└── conftest.py（可选，共享 fixtures）
```

## 4. 核心测试场景（必须覆盖）

### 4.1 structured_observation 基础测试

**TC-OBS-001: visual 成功返回 signals**
- Mock visual_analyzer 返回 {"status": "success", "signals": [...]}
- 验证 state["signals"] 被注入
- 验证 obs_data 包含 visual_signals 和 is_cached_image
- 验证 state["observations"] 长度 +1

**TC-OBS-002: visual 失败 fallback 到 LLM**
- Mock visual_analyzer 返回 {"status": "error"}
- Mock call_llm 返回有效 JSON 字符串
- 验证 fallback 分支被执行
- 验证 JSON 解析成功

**TC-OBS-003: force_new_image 逻辑**
- is_first_round = True → force_new = True
- has_new_data_requests = True → force_new = True
- 两者都 False → force_new = False（缓存命中）

**TC-OBS-004: playbook_references 格式标准化**
- 输入为 list[str]（带 "：" 或 ":"）
- 验证自动转换为 list[dict]（rule + match_reason）

**TC-OBS-005: 异常 JSON 解析**
- call_llm 返回非 JSON 字符串
- 验证使用默认 obs_data（phase="解析失败"）

### 4.2 _prepare_daily_data 测试

**TC-OBS-006: 空数据**
- daily_data = []
- 返回 "【无可用历史数据】"

**TC-OBS-007: 正常 DataFrame 处理**
- 验证只保留指定列
- 验证 tail(max_rows)
- 验证 to_csv(index=False)

**TC-OBS-008: 缺失列容错**
- daily_data 缺少部分 keep_cols
- 验证 existing_cols 过滤后仍能正常工作

## 5. Mock 策略

需要 mock 的主要对象：
- `eaagent.a_plus_plus.tools.visual_analyzer`
- `eaagent.a_plus_plus.utils.llm.call_llm`
- `eaagent.playbooks.manager`（可选）

推荐使用 `unittest.mock.patch` + pytest fixtures。

## 6. 测试执行顺序建议

1. 先写 `_prepare_daily_data` 的 3 个测试（简单，快速建立信心）
2. 再写 structured_observation 的 TC-OBS-001 ~ 005
3. 最后补充 edge case（异常 JSON、playbook_references 格式异常等）

## 7. 与重构的配合

- 重构前：所有 Legacy 路径必须有 UT 保护
- 重构中：新路径 `_structured_observation_with_tools` 也要同步写测试
- 重构后：可以用同一套测试验证新旧路径行为一致

## 8. 覆盖率目标

- 首次补测目标：≥ 70% line coverage
- 重构完成后目标：≥ 85% + 关键分支 100% 覆盖

---

**下一步行动**：先创建 tests/nodes/test_observation.py 并实现 TC-OBS-006 ~ 008（最简单），再逐步补全主流程测试。