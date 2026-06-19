# Testing Strategy

## 测试方式

- 使用 `pytest` 进行测试
- 重点测试单元测试和集成测试
- 使用 Mock 模式避免依赖外部服务

## 命令

```bash
make test          # 运行全部测试
make test-cov      # 带覆盖率报告
```

## 测试原则

- 新增 Node 必须写单元测试
- 重要逻辑建议先写测试再实现
- 使用 `USE_MOCK_LLM=true` 进行快速测试