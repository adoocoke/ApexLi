# Development Roadmap

## Release 规划

| Release | 名称               | 重点内容                              | 状态     |
|---------|------------------------|--------------------------------------------------|---------------|
| **MVP** | 基础可用版     | 结构化 Observation + Signal + 基础多轮控制 | 已完成   |
| **R1**  | Playbook 策略版     | CoreRulesStrategy + 策略切换 + 日志改进 + EA-001~EA-005 质量提升 | 已完成   |
| **R2**  | 可观测性增强版 | Console 颜色 + Sensors 突出显示 + Web 双菜单主力合约 K线 | 进行中   |
| **R3**  | 工程化完善版   | 节点进一步拆分 + 类型系统完善 + Strategy 完全切换 | 计划中   |

## 当前重点

- Web 双菜单主力合约 + **中文品种显示** (螺纹钢 RB、铁矿石 I、纯碱 SA 等关注品种，已实现，测试通过)
- 完善 Playbook Strategy 完全切换 (Core/IdOnly 动态)
- 清理旧测试文件 + CI 覆盖率
- 更新 Wiki 和 ADR 文档