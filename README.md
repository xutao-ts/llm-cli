# llm-cli

LLM 命令行问答工具：通过模型 API 完成对话、结构化输出与流式返回，作为大模型架构师学习路线阶段 0 的第一个可运行工程。

## 功能规划

- [x] 项目骨架与工程规范（配置外置、日志、单测入口）
- [ ] 模型调用封装（OpenAI 兼容协议）
- [ ] 命令行交互（参数、配置、日志）
- [ ] 流式输出
- [ ] JSON 结构化输出与校验
- [ ] 多模型对比

## 目录结构

```
llm-cli/
├── src/llm_cli/        # 源码包
│   ├── __init__.py
│   ├── config.py      # 配置加载（环境变量 + 外置配置）
│   ├── logger.py      # 日志初始化
│   ├── client.py      # 模型调用封装（预留）
│   └── cli.py          # 命令行入口
├── config/            # 外置配置示例（不含密钥）
├── tests/             # pytest 单测
├── docs/              # 笔记与设计说明
├── .gitignore
├── pyproject.toml     # 项目元数据、依赖、工具配置
└── README.md
```

## 环境准备

要求 Python 3.12。首次搭建：

```bash
# 1. 创建虚拟环境（在项目根目录执行）
python3.12 -m venv .venv
source .venv/bin/activate

# 2. 安装开发依赖
pip install -e ".[dev]"

# 3. 配置环境变量（复制示例并填写，密钥不入库）
cp config/config.example.toml config/config.toml
export LLM_API_KEY="你的 API Key"
```

## 常用命令

```bash
# 运行 CLI
python -m llm_cli "你好"

# 跑测试
pytest

# 代码检查（lint / 格式化）
ruff check src tests
ruff format src tests
```

## 配置说明

- 敏感信息（API Key）只通过环境变量或本地 `config/config.toml` 提供，该文件已被 `.gitignore` 忽略。
- 默认配置见 `config/config.example.toml`，提交示例而不是真实配置。

## 开发约定

- 提交信息格式：`feat: 新功能` / `fix: 修复` / `docs: 文档` / `chore: 杂项`。
- 新增公共函数补类型注解；关键分支补单测。
- 配置与代码分离，不在源码里硬编码地址、密钥、模型名。
