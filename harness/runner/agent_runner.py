import sys
from pathlib import Path

import pytest

# 부모 디렉터리들을 PATH에 추가하여 로컬에서 바로 실행할 수 있도록 지원
sys.path.append(str(Path(__file__).parent.parent.parent))

from harness.linter.agent_rules import AgentWorkflowLinter
from harness.validators.arch_checker import ArchitectureValidator


def print_single_error(error_msg: str):
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
    sys.exit(1)


def main():
    base_dir = Path(__file__).parent.parent.parent

    # 1. 헌법(아키텍처) 검증
    print(">> [1/3] 프로젝트 헌법(Architecture) 검증 중...")
    arch_validator = ArchitectureValidator(base_dir=str(base_dir))
    arch_violations = arch_validator.validate()

    if arch_violations:
        error_msg = (
            "아키텍처 의존성 방향 오류 (프로젝트 헌법 위반!):\n\n"
            + "\n".join(f"- {v}" for v in arch_violations)
            + "\n\n[How to fix (Next Action)]: 스위스 치즈 모델을 방지하기 위해, 하위 레이어에서 상위 레이어를 임포트한 코드를 즉시 삭제하십시오."
        )
        print_single_error(error_msg)

    # 2. 에이전트 린터 검증
    print(">> [2/3] 에이전트 맞춤형 기계적 린터 검증 중...")
    linter = AgentWorkflowLinter(base_dir=str(base_dir))
    lint_violations = linter.run()

    if lint_violations:
        # 단일 문제 집중: 가장 첫 번째 오류 딱 하나만 반환합니다.
        error_msg = "타입 힌트 누락 등 린트 규칙 위반:\n\n" + lint_violations[0]
        print_single_error(error_msg)

    # 3. 비즈니스 로직 테스트 (pytest)
    print(">> [3/3] 비즈니스 스펙 (pytest) 검증 중...")
    # TDD 기반 루프이므로 `--maxfail=1` 플래그를 강제합니다. (최초 단일 실패에서 실행 중단)
    # `--tb=short`로 간결한 에러 화면만 출력.
    exit_code = pytest.main(
        ["-v", "--maxfail=1", "--tb=short", str(base_dir / "tests")]
    )

    if exit_code != 0:
        print("\n\n" + "=" * 60)
        print("🛑 [스펙 실패 발생! - 단일 에러 화면]")
        print(
            "위의 pytest 단위 테스트 결과에서 실패한 '단 한 개의 테스트'를 통과시키는 코드만 작성하세요."
        )
        print("다른 코드 리팩터링이나 불필요한 구현은 절대 금지됩니다.")
        print("=" * 60 + "\n")
        sys.exit(exit_code)

    print(
        "\n✨ 모든 프로젝트 헌법(Architecture), 린트(Linter), 스펙(Pytest)이 통과되었습니다. ✨"
    )
    print(
        "에이전트의 현재 작업은 종료되었으며, 다음 퀘스트(새로운 테스트 스펙 작성)를 기다립니다!\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
