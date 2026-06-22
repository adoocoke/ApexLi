# Remaining Work - EA Agent Project

> 最后更新：2026-06-22

本文档总结当前 EA Agent 项目还剩下的主要工作，并与之前的 `graph_refactor_plan.md` 和 `martin_fowler_harness_review.md` 相关联。

---

## 1. 高优先级（建议尽快完成）

| 任务 | 说明 | 优先级 | 工作量 |
|----------|----------|----------|----------|
| 清理根目录旧测试文件 | 把 `tests/` 根目录剩余的旧 `test_*.py` 文件彻底清空或删除 | 高 | 小 |
| 验证 CI + 覆盖率 | 确保 GitHub Actions 能正常运行新结构测试，并收集覆盖率 | 高 | 中 |
| 更新 README.md | 在 README 中引用 `docs/AGENTS.md` 和新的测试结构 | 高 | 小 |

## 2. 中优先级（核心功能增强）

| 任务 | 说明 | 优先级 | 工作量 |
|----------|----------|----------|----------|
| 完善多轮分析循环 | 强化 Quality Sensor、LLM Critique、自适应轮次判断 | 高 | 中~大 |
| Playbook 更好集成 | 让 Agent 更严格遵循 Playbook 规则 | 高 | 中 |
| Strategy Pattern 完善 | Full / Core / ID-Only 三种策略的完整实现与切换 | 中 | 中 |
| 持久化 + HITL | 状态持久化 + 人类审核节点 | 中 | 中 |

## 3. 中低优先级（文档与工程化）

| 任务 | 说明 | 优先级 | 工作量 |
|----------|----------|----------|----------|
| 文档体系完善 | 创建 ADR 模板、`docs/specs/` 结构、更新 Wiki | 中 | 中 |
| Notion 知识库 | 把 Agent 开发经验整理到 Notion | 中 | 大 |
| Dev Experience | 添加 `Makefile`、`pyproject.toml` 脚本支持（`make test`、`make lint` 等） | 中 | 小 |

## 4. 长期 / 扩展方向

- 真实 Tushare 数据 + 多时间框分析能力强化
- 多 Agent 协作（Sub-agents / Worktree）
- 更完善的交易信号生成与风险控制模块
- 生产环境部署与监控

---

## 相关文档

- `todo/graph_refactor_plan.md`
- `todo/martin_fowler_harness_review.md`
- `docs/AGENTS.md`

---

**最后更新**：2026-06-22