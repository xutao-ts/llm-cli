"""支持 `python -m llm_cli` 方式启动。"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
