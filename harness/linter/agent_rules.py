import ast
from pathlib import Path
from typing import List


class AgentWorkflowLinter:
    """
    에이전트가 코드를 작성할 때, 사람의 리뷰 없이도 기계적으로
    코드 품질(타입 힌트, 라우터 반환 타입 등)을 검증하는 커스텀 린터입니다.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def validate_file(self, file_path: Path) -> List[str]:
        violations = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                # 함수/메서드 수준 검사 (타입 힌트 누락 검증)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 매직 메서드 제외
                    if not node.name.startswith("__"):
                        if node.returns is None:
                            violations.append(
                                f"[Agent Linter Error] {file_path.relative_to(self.base_dir)}:{node.lineno}\n"
                                f"  -> 함수 '{node.name}'에 반환 타입 힌트(Return Type Hint)가 없습니다.\n"
                                f"  [How to fix (Next Action)]: 'def {node.name}(...) -> SomeType:' 형태로 반환 타입을 명시하세요."
                            )

        except Exception:
            # 기본 문법 에러는 여기서 잡지 않습니다.
            pass

        return violations

    def run(self) -> List[str]:
        all_violations = []
        # 대상은 app 소스코드 (추후 도메인에 따라 확장)
        app_dir = self.base_dir / "app"
        if not app_dir.exists():
            return []

        for python_file in app_dir.rglob("*.py"):
            all_violations.extend(self.validate_file(python_file))

        return all_violations
