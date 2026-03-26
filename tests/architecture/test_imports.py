from pathlib import Path

from harness.validators.arch_checker import ArchitectureValidator


def test_project_constitution_architecture():
    """
    [Project Constitution - Structural Test]
    단일 실패와 힌트를 강제하는 SDD 루프의 첫 보호막(Guardrail)입니다.
    """
    # 루트 디렉터리 (tests/architecture 에서 부모를 타고 최상단으로 이동)
    root_dir = Path(__file__).parent.parent.parent

    validator = ArchitectureValidator(base_dir=str(root_dir))
    violations = validator.validate()

    if violations:
        error_msg = "\n======================\n[Project Constitution Error] 의존성 방향 규칙이 위반되었습니다!\n\n"
        error_msg += "발생한 위반 내역:\n\n"
        error_msg += "\n\n".join(f"- {v}" for v in violations)
        error_msg += "\n\n[How to fix (Next Action)]: 스위스 치즈 모델을 피하기 위해 하위 레이어에서 상위 레이어의 임포트 코드를 즉시 삭제하십시오.\n======================"

        assert False, error_msg
