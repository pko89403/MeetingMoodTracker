import argparse
import subprocess
import sys
from pathlib import Path

import pytest

# 부모 디렉터리들을 PATH에 추가하여 로컬에서 바로 실행할 수 있도록 지원
sys.path.append(str(Path(__file__).parent.parent.parent))

from harness.linter.agent_rules import AgentWorkflowLinter
from harness.validators.arch_checker import ArchitectureValidator
from harness.validators.fastapi_contract_checker import FastAPIContractValidator


def print_single_error(error_msg: str) -> None:
    """
    에이전트에게 전체 파일이 아니라 '단일 문제'만 노출하여 집중을 유도하는 출력 래퍼
    """
    print("\n" + "=" * 60)
    print("🛑 [에이전트 퀘스트 발생! - 단일 에러 컨텍스트]")
    print("=" * 60)
    print(error_msg)
    print(
        "\n[현재 워크플로 룰]: 이 메시지에 적힌 단 하나의 'Next Action'만 수행하세요."
    )
    print("다른 파일을 미리 수정하거나 추측하지 마십시오.")
    print("=" * 60 + "\n")


def _run_architecture(base_dir: Path) -> list[str]:
    arch_validator = ArchitectureValidator(base_dir=str(base_dir))
    return arch_validator.validate()


def _run_fastapi_contract(base_dir: Path) -> list[str]:
    validator = FastAPIContractValidator(base_dir=str(base_dir))
    return validator.validate()


def _run_ruff_check(base_dir: Path) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "app/", "tests/"],
        cwd=str(base_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return []

    merged = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
    first_line = next((line for line in merged.splitlines() if line.strip()), merged)
    return [
        "[Agent Linter Error] Ruff 정적 분석에 실패했습니다.\n"
        f"  -> {first_line}\n"
        "  [How to fix (Next Action)]: Ruff 오류를 우선 해결한 뒤 하네스를 다시 실행하세요."
    ]


def _run_linter(base_dir: Path) -> list[str]:
    linter = AgentWorkflowLinter(base_dir=str(base_dir))
    lint_violations = linter.run()
    if lint_violations:
        return lint_violations
    return _run_ruff_check(base_dir)


def _run_pytest(base_dir: Path) -> int:
    # TDD 기반 루프이므로 `--maxfail=1` 플래그를 강제합니다. (최초 단일 실패에서 실행 중단)
    # `--tb=short`로 간결한 에러 화면만 출력.
    return pytest.main(["-v", "--maxfail=1", "--tb=short", str(base_dir / "tests")])


def run(mode: str, base_dir: Path | None = None) -> int:
    resolved_base = base_dir or Path(__file__).parent.parent.parent

    print(">> [1/4] 프로젝트 헌법(Architecture) 검증 중...")
    arch_violations = _run_architecture(resolved_base)
    if arch_violations:
        error_msg = (
            "아키텍처 의존성 방향 오류 (프로젝트 헌법 위반!):\n\n"
            + "\n".join(f"- {v}" for v in arch_violations)
            + "\n\n[How to fix (Next Action)]: 스위스 치즈 모델을 방지하기 위해, 하위 레이어에서 상위 레이어를 임포트한 코드를 즉시 삭제하십시오."
        )
        print_single_error(error_msg)
        return 1

    print(">> [2/4] FastAPI 계약(FastAPI Contract) 검증 중...")
    fastapi_violations = _run_fastapi_contract(resolved_base)
    if fastapi_violations:
        print_single_error("FastAPI 계약 규칙 위반:\n\n" + fastapi_violations[0])
        return 1

    print(">> [3/4] 에이전트 맞춤형 린터(Custom + Ruff) 검증 중...")
    lint_violations = _run_linter(resolved_base)
    if lint_violations:
        print_single_error("타입 힌트/정적 분석 규칙 위반:\n\n" + lint_violations[0])
        return 1

    if mode == "precommit":
        print("\n✅ pre-commit 하네스 검증(Architecture + FastAPI + Linter)을 통과했습니다.\n")
        return 0

    print(">> [4/4] 비즈니스 스펙(Pytest) 검증 중...")
    exit_code = _run_pytest(resolved_base)
    if exit_code != 0:
        print("\n\n" + "=" * 60)
        print("🛑 [스펙 실패 발생! - 단일 에러 화면]")
        print(
            "위의 pytest 단위 테스트 결과에서 실패한 '단 한 개의 테스트'를 통과시키는 코드만 작성하세요."
        )
        print("다른 코드 리팩터링이나 불필요한 구현은 절대 금지됩니다.")
        print("=" * 60 + "\n")
        return exit_code

    print(
        "\n✨ 모든 프로젝트 헌법(Architecture), FastAPI 계약, 린트(Linter), 스펙(Pytest)이 통과되었습니다. ✨"
    )
    print(
        "에이전트의 현재 작업은 종료되었으며, 다음 퀘스트(새로운 테스트 스펙 작성)를 기다립니다!\n"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="MeetingMoodTracker agent harness runner")
    parser.add_argument(
        "--mode",
        choices=["precommit", "full"],
        default="full",
        help="precommit: 빠른 로컬 게이트, full: precommit + pytest",
    )
    args = parser.parse_args()
    sys.exit(run(mode=args.mode))


if __name__ == "__main__":
    main()
