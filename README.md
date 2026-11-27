# llm-cli

LLM 命令行问答工具：通过 OpenAI 兼容协议调用模型，完成对话、结果解析与用量统计，作为大模型架构师学习路线阶段 0 的第一个可运行工程。

## 当前版本能力（v0.1.0）

- [x] 项目骨架与工程规范（`src` 布局、配置外置、统一日志、单测入口）
- [x] 模型调用封装：OpenAI 兼容协议 `/chat/completions`，同步非流式
- [x] 响应结构化解析：回复正文、模型名、结束原因、token 用量（含推理 token）
- [x] 命令行入口：问题参数、模型覆盖、DEBUG 日志、原始 JSON 输出
- [x] pytest 单测与 ruff 检查 / 格式化配置

## 待规划

- [ ] 流式输出（逐 token 打印）
- [ ] JSON 结构化输出与字段校验
- [ ] 多轮对话历史维护
- [ ] 多模型输出对比

## 目录结构

```
llm-cli/
├── src/llm_cli/          # 源码包
│   ├── __init__.py
│   ├── __main__.py       # 支持 python -m llm_cli 启动
│   ├── config.py        # 配置加载（环境变量 + .env）
│   ├── logger.py        # 统一日志初始化
│   ├── client.py        # 模型调用封装与响应解析
│   └── cli.py            # 命令行入口与结果渲染
├── config/
│   └── config.example.toml  # 配置示例（不含密钥）
├── tests/               # pytest 单测
├── docs/                # 笔记与设计说明
├── .env.example        # 环境变量示例（复制为 .env）
├── .gitignore
├── pyproject.toml       # 项目元数据、依赖、pytest/ruff 配置
├── LICENSE
└── README.md
```

## 环境准备

要求 Python 3.12。首次搭建：

```bash
# 1. 创建并激活虚拟环境（在项目根目录执行）
python3.12 -m venv .venv
source .venv/bin/activate

# 2. 安装开发依赖
pip install -e ".[dev]"

# 3. 配置环境变量（复制示例并填写，密钥不入库）
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL 等
```

## 常用命令

```bash
# 普通问答（格式化输出回复与用量）
python -m llm_cli "你好"

# 指定模型
python -m llm_cli "介绍一下 RAG" --model deepseek-chat

# 输出模型返回的原始 JSON（调试用）
python -m llm_cli "你好" --raw

# 开启 DEBUG 日志
python -m llm_cli "你好" --debug

# 跑测试
pytest

# 代码检查与格式化
ruff check src tests
ruff format src tests
```

## 输出说明

默认渲染为易读文本：

```
============================================================
回复：你好！很高兴见到你 😊 有什么我可以帮忙的吗？
------------------------------------------------------------
模型：deepseek-v4-1-flash-economy-261017
结束原因：stop
Token 用量：输入 31 / 输出 60 / 合计 91（其中推理 23）
============================================================
```

加 `--raw` 可查看未经解析的原始响应 JSON。

## 配置说明

- 配置项见 `.env.example`：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_TIMEOUT`、`LLM_LOG_LEVEL`。
- 敏感信息（API Key）只通过环境变量或本地 `.env` 提供，`.env` 已被 `.gitignore` 忽略，不提交仓库。
- `config/config.example.toml` 是非敏感配置的结构示例；真实配置不入库。
- 支持 OpenAI 兼容协议的服务（DeepSeek、火山方舟、阿里云百炼、本地 vLLM/Ollama 等）替换 `LLM_BASE_URL` 与 `LLM_MODEL` 即可。

## 开发约定

- 提交信息格式：`feat: 新功能` / `fix: 修复` / `docs: 文档` / `chore: 杂项`。
- 新增公共函数补类型注解；关键分支补 pytest 用例。
- 配置与代码分离，不在源码里硬编码地址、密钥、模型名。
