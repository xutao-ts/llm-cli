# 开发笔记

## 阶段 0 工程规范约定

- Python 3.12，源码放 `src/llm_cli`，测试放 `tests`。
- 配置外置：环境变量优先，本地 `config/config.toml` 不入库；示例见 `config/config.example.toml`。
- 日志统一走 `logger.setup_logger`，不在业务代码里直接 `print`。
- 公共函数补类型注解；关键分支补 pytest 用例。
- 提交信息：`feat / fix / docs / chore / refactor`。

## 待办（对应周排期）

- [x] 接入第一家模型 API，跑通一次问答（W01）
- [x] 补 asyncio 并发调用示例（W02，见 `examples/async_batch.py`）
- [x] Transformer 基础概念笔记（W02，见 `docs/notes_transformer.md`）
- [x] 失败案例环节归因记录（W02，见 `docs/notes_failures.md`）
- [ ] 异常处理与单测覆盖（W03）
- [ ] 流式输出与 JSON 结构化输出（W03）
