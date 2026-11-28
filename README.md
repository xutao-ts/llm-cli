# llm-cli

LLM 命令行问答工具：通过 OpenAI 兼容协议调用模型，完成对话、结果解析与用量统计，作为大模型架构师学习路线阶段 0 的第一个可运行工程。

## 当前版本能力（v0.1.0）

- [x] 项目骨架与工程规范（`src` 布局、配置外置、统一日志、单测入口）
- [x] 模型调用封装：OpenAI 兼容协议 `/chat/completions`，同步非流式
- [x] 流式输出：SSE 逐段打印（`--stream`），支持 `--raw` 查看原始 chunk
- [x] 多轮对话：交互模式内维护上下文，支持 `/clear`、`/exit`
- [x] 响应结构化解析：回复正文、模型名、结束原因、token 用量（含推理 token）
- [x] 命令行入口：问题参数、模型覆盖、DEBUG 日志、原始 JSON 输出
- [x] pytest 单测与 ruff 检查 / 格式化配置

## 待规划

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

Windows 用户请看下文的 [Windows 使用说明](#windows-使用说明powershell)。

## 常用命令

```bash
# 普通问答（格式化输出回复与用量）
python -m llm_cli "你好"

# 流式输出（边生成边打印，结束后补打用量摘要）
python -m llm_cli "你好" --stream

# 指定模型
python -m llm_cli "介绍一下 RAG" --model deepseek-chat

# 输出模型返回的原始 JSON（调试用）
python -m llm_cli "你好" --raw

# 流式模式下的原始 chunk（每行一个 JSON）
python -m llm_cli "你好" --stream --raw

# 关闭 / 开启思考（透传 thinking 参数；不填则用服务端默认）
python -m llm_cli "你好" --stream --thinking disabled
python -m llm_cli "你好" --stream --thinking enabled

# 打印模型的思考过程
python -m llm_cli "你好" --stream --show-reasoning

# 开启 DEBUG 日志
python -m llm_cli "你好" --debug

# 跑测试
pytest

# 代码检查与格式化
ruff check src tests
ruff format src tests
```

## 多轮对话（交互模式）

不传问题文本即进入交互模式，上下文在同一进程内累积，每轮都会把历史消息一起发给模型：

```bash
python -m llm_cli
# 或带流式
python -m llm_cli --stream
```

```
进入交互模式：直接输入问题，/clear 清空上下文，/exit 退出。
你> 我叫小明，请记住我的名字
...
你> 我叫什么名字？
小明
```

内置命令：

| 命令              | 作用                                |
| --------------- | --------------------------------- |
| `/clear`        | 清空对话上下文，重新开始                      |
| `/exit`、`/quit` | 退出交互模式（`Ctrl+C` / `Ctrl+Z` 同样可退出） |

`--stream`、`--thinking`、`--show-reasoning`、`--raw` 在交互模式下同样生效；单轮请求失败不会写入上下文，可重试或继续提问。上下文仅保存在内存中，退出后清空。

## Windows 使用说明（PowerShell）

以下命令均在项目根目录执行（PowerShell 5.1 及以上）。

### 1. 环境准备

```powershell
# 允许当前窗口执行激活脚本（仅本会话生效，不修改系统策略）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# 退出虚拟环境
deactivate
# 安装开发依赖；网络慢时加国内镜像
python -m pip install -e ".[dev]"
# python -m pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制环境变量示例并填写密钥
Copy-Item .env.example .env
```

不想激活虚拟环境时，直接用 `.\.venv\Scripts\python.exe -m llm_cli "你好"` 调用。安装 `-e` 之后也可以直接用入口命令 `llm-cli "你好"`。

### 2. 环境变量

- 推荐把配置写在项目根目录的 `.env`（工具只读取**当前工作目录**的 `.env`），该文件已被 `.gitignore` 忽略。
- 已存在的系统 / 用户环境变量**优先于** `.env`。如果改了 `.env` 不生效，先检查是否有同名旧变量：

```powershell
Get-ChildItem Env: | Where-Object Name -like "LLM_*"

# 清理当前窗口的旧值（永久删除需用 SetEnvironmentVariable，机器级需要管理员）
Remove-Item Env:LLM_API_KEY -ErrorAction SilentlyContinue
```

- 只在当前窗口临时覆盖：

```powershell
$env:LLM_API_KEY  = "ark-xxxx"
$env:LLM_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
$env:LLM_MODEL    = "deepseek-v4-1-flash-economy-261017"
```

### 3. 常用命令

```powershell
python -m llm_cli                          # 交互模式（多轮对话）
python -m llm_cli "你好"                  # 普通问答
python -m llm_cli "你好" --stream         # 流式输出
python -m llm_cli "你好" --raw            # 原始 JSON
python -m llm_cli "你好" --stream --raw   # 流式原始 chunk
python -m llm_cli "你好" --stream --thinking disabled      # 关闭思考
python -m llm_cli "你好" --stream --show-reasoning         # 打印思考过程
python -m llm_cli "你好" --model deepseek-chat --debug

# 脚本中判断执行结果：0 成功，1 配置缺失或模型请求失败
if ($LASTEXITCODE -ne 0) { Write-Error "调用失败" }
```

### 4. 中文输出乱码

Windows 终端默认编码可能不是 UTF-8，出现乱码时先执行：

```powershell
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
```

### 5. 运行测试

```powershell
# 未通过 pip install -e 安装时，指定源码目录
$env:PYTHONPATH = "src"
python -m pytest

# 只跑 CLI / 客户端用例
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_client.py -q
```

`pytest` 用例通过 monkeypatch 模拟模型响应，无需真实 API Key 和网络；需要联调整条链路时，可先用本地假服务（OpenAI 兼容的 SSE 接口）替代真实模型地址。

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

关于思考（推理）：

- 默认不显示思考过程，用量摘要里的“其中推理 N”是模型实际消耗的推理 token。
- `--show-reasoning` 打印 `reasoning_content`（流式时以 `[思考] ...` 前缀逐段输出）。
- `--thinking auto|enabled|disabled` 透传 `thinking` 参数控制思考开关；不填则完全使用服务端默认（例如当前 Ark 上的 DeepSeek 模型默认开启）。

## 配置说明

- 配置项见 `.env.example`：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_TIMEOUT`、`LLM_LOG_LEVEL`。
- 敏感信息（API Key）只通过环境变量或本地 `.env` 提供，`.env` 已被 `.gitignore` 忽略，不提交仓库。
- `config/config.example.toml` 是非敏感配置的结构示例；真实配置不入库。
- 支持 OpenAI 兼容协议的服务（DeepSeek、火山方舟、阿里云百炼、本地 vLLM/Ollama 等）替换 `LLM_BASE_URL` 与 `LLM_MODEL` 即可。

## 开发约定

- 提交信息格式：`feat: 新功能` / `fix: 修复` / `docs: 文档` / `chore: 杂项`。
- 新增公共函数补类型注解；关键分支补 pytest 用例。
- 配置与代码分离，不在源码里硬编码地址、密钥、模型名。
