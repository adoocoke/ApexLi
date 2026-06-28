# ApexLi Prompt Fortress 升级计划
## 目标
让Agent永远严格遵守Playbook + 期货领域规则，输出可审计、可追溯。

## 今天（2026-06-27）完成 Phase 1
- [ ] 在所有Playbook最前面增加“Agent铁律”段
- [ ] 创建 eaagent/prompts/fortress.py（统一管理强制模板）
- [ ] 重写 structured_observation 节点，强制回答3个问题 + 规则编号
- [ ] 更新 web/app_graph.py 支持显示当前使用的Playbook风格
- [ ] commit + push + 测试 zen / dow / abu 切换效果

## 后续阶段
Phase 2：多风格智能融合 + Prompt版本管理
Phase 3：Prompt A/B测试框架 + 性能指标记录
