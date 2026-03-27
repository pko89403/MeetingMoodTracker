from pathlib import Path


def test_pre_commit_hook_uses_runner_single_entrypoint() -> None:
    hook_path = Path(__file__).parent.parent.parent / "scripts" / "pre_commit_hook.sh"
    content = hook_path.read_text(encoding="utf-8")

    assert "agent_runner.py --mode precommit" in content
    assert "uv run pytest tests/architecture/test_imports.py -q" not in content
    assert "uv run ruff check app/ tests/" not in content
