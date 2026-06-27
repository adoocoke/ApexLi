# ApexLi 下周冲刺计划（1周极致版） - 2026.06.28 ~ 07.04

**目标**：快速落地三个大方向，1周内做出可演示的强版本

**优先级**：多Playbook → 多品种组 → Harness加强

---

## 📅 Day 1（周一）- 多Playbook 框架（最优先）

- [ ] 重构 `playbook_loader.py` → `PlaybookManager`
- [ ] 新建 `eaagent/playbooks/` 目录，创建 v3、zen、dow、abu 四个 playbook 文件
- [ ] 实现 Playbook 注册 + 动态加载
- [ ] 修改 `initialize_state` 支持切换
- [ ] Web 界面增加 Playbook 下拉选择框
- [ ] 测试切换后 Prompt 是否正常加载不同风格

**里程碑**：能在界面切换不同 Playbook 并看到明显不同分析风格

---

## 📅 Day 2（周二）- 多品种 + 关联组分析

- [ ] 新增关联品种映射配置（RB → I/J/JM 等）
- [ ] 扩展 `data_gathering` 支持组查询
- [ ] State 增加 `analysis_groups` 和 `related_symbols`
- [ ] 右侧 K线图改为 Tab（当前合约 + 铁矿 + 焦炭 + 焦煤）
- [ ] 输出“产业链共振评分”

**里程碑**：输入一个合约后，右侧能同时显示多个关联品种 K线

---

## 📅 Day 3（周三）- Harness 加强 + 界面升级

- [ ] 把 Harness 独立为 `HarnessEngine` 类
- [ ] 增加三种模式（严格 / 平衡 / 激进）
- [ ] Web 界面增加 Harness 模式切换
- [ ] 左侧 Console 优化为更漂亮的实时滚动
- [ ] 整体界面做深色专业升级

**里程碑**：界面明显更专业，可切换三种 Harness 模式

---

## 📅 Day 4-5（周四-周五）- 整合测试

- [ ] 三方向完全打通
- [ ] 增加“一键全模式”按钮（同时切换 Playbook + 品种组 + Harness）
- [ ] 全面测试 + Bug 修复

---

## 📅 Day 6-7（周六-周日）- 收尾

- [ ] 更新 README + 添加功能截图
- [ ] 准备 Demo 视频/截图
- [ ] 最终 Commit & Push + 写总结

---

**本周目标（必须达成）**
- 支持 4 种 Playbook 切换
- 多品种组 + 多 K线展示
- Harness 可配置模式
- 界面大幅升级

**执行原则**：每天晚上 23:00 前 Commit 一次，遇到卡点立刻找我。

当前状态：已提交稳定基础版本 ✓
开始日期：2026.06.28（周一）

