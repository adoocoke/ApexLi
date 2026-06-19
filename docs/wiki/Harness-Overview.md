# Harness 架构概览

EA Agent 采用 **Martin Fowler Agent Harness** 思想进行设计，核心目标是构建一个**可控、可观测、可迭代**的分析系统。

## 核心组件

| 组件          | 职责                             | 当前实现位置                  |
|-------------------|--------------------------------------|---------------------------------------------|
| **Guides**        | 初始化任务、注入领域知识 | `initialize_state` + Playbook Strategy      |
| **Sensors**       | 质量检查 + 自我审查     | `quality_sensor` + `llm_critique`           |
| **Actor**         | 执行具体分析动作         | `structured_observation` + `signal_generation` |
| **Steering**      | 控制分析流程（是否继续） | `should_continue_after_critique`            |
| **Memory**        | 保存状态与历史             | LangGraph MemorySaver + State               |

## 设计原则

- **结构化沟通**：所有与 LLM 的交互优先使用结构化 JSON
- **策略可切换**：Playbook 注入支持多种策略（Full / Core / IdOnly）
- **薄垂直切片**：每个节点职责单一，便于独立演进
- **可观测优先**：日志和输出设计以人为中心

## 当前架构演进

- 已完成：Strategy Pattern、结构化 Observation & Signal、节点初步拆分
- 进行中 / 计划中：进一步节点拆分、可观测性增强、Wiki 知识沉淀