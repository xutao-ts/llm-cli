"""CLI 入口单测。"""

from __future__ import annotations

from llm_cli.cli import main


def test_cli_with_question(capsys, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    exit_code = main(["你好"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "你好" in captured.err + captured.out


def test_cli_without_question(capsys):
    exit_code = main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "交互模式" in captured.err + captured.out
