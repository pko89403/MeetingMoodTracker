from pathlib import Path

from harness.runner import agent_runner


def test_runner_execution_order_full(monkeypatch, tmp_path: Path) -> None:
    sequence: list[str] = []

    monkeypatch.setattr(
        agent_runner,
        "_run_architecture",
        lambda _base_dir: sequence.append("architecture") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_fastapi_contract",
        lambda _base_dir: sequence.append("fastapi-contract") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_linter",
        lambda _base_dir: sequence.append("linter") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_pytest",
        lambda _base_dir: sequence.append("pytest") or 0,
    )

    exit_code = agent_runner.run(mode="full", base_dir=tmp_path)
    assert exit_code == 0
    assert sequence == ["architecture", "fastapi-contract", "linter", "pytest"]


def test_runner_execution_order_precommit(monkeypatch, tmp_path: Path) -> None:
    sequence: list[str] = []

    monkeypatch.setattr(
        agent_runner,
        "_run_architecture",
        lambda _base_dir: sequence.append("architecture") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_fastapi_contract",
        lambda _base_dir: sequence.append("fastapi-contract") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_linter",
        lambda _base_dir: sequence.append("linter") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_pytest",
        lambda _base_dir: sequence.append("pytest") or 0,
    )

    exit_code = agent_runner.run(mode="precommit", base_dir=tmp_path)
    assert exit_code == 0
    assert sequence == ["architecture", "fastapi-contract", "linter"]


def test_runner_stops_on_first_failure(monkeypatch, tmp_path: Path) -> None:
    sequence: list[str] = []

    monkeypatch.setattr(
        agent_runner,
        "_run_architecture",
        lambda _base_dir: sequence.append("architecture") or ["arch-error"],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_fastapi_contract",
        lambda _base_dir: sequence.append("fastapi-contract") or [],
    )
    monkeypatch.setattr(
        agent_runner,
        "_run_linter",
        lambda _base_dir: sequence.append("linter") or [],
    )

    exit_code = agent_runner.run(mode="full", base_dir=tmp_path)
    assert exit_code == 1
    assert sequence == ["architecture"]
