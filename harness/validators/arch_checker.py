import ast
from pathlib import Path
from typing import List, Tuple


class ArchitectureValidator:
    """
    프로젝트 헌법(Project Constitution)을 기계적으로 집행(Enforce)하는 클래스입니다.
    지정된 디렉터리의 파이썬 소스 코드 AST(Abstract Syntax Tree)를 파싱하여,
    허용되지 않은 상위/외부 레이어의 임포트 시도를 적발합니다.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

        # 헌법 (Project Constitution Rules)
        # 단방향 의존성 헌법: Types <- Config <- Repo <- Service <- Runtime <- UI
        self.forbidden_imports = {
            "app/types": [
                "app.config",
                "app.repo",
                "app.service",
                "app.runtime",
                "app.ui",
            ],
            "app/config": ["app.repo", "app.service", "app.runtime", "app.ui"],
            "app/repo": ["app.service", "app.runtime", "app.ui"],
            "app/service": ["app.runtime", "app.ui"],
            "app/runtime": ["app.ui"],
            "app/ui": [],
        }

    def _get_imports_from_file(self, file_path: Path) -> List[Tuple[int, str]]:
        imports = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append((node.lineno, node.module))
        except Exception:
            # Syntax 에러 등은 일반 린터/구문 테스트가 잡도록 위임하고 여기선 무시합니다.
            pass
        return imports

    def validate(self) -> List[str]:
        violations = []

        for rule_path, forbidden_list in self.forbidden_imports.items():
            dir_to_check = self.base_dir / rule_path

            # 폴더가 아직 생성되지 않았다면 스킵
            if not dir_to_check.exists() or not dir_to_check.is_dir():
                continue

            for python_file in dir_to_check.rglob("*.py"):
                file_imports = self._get_imports_from_file(python_file)
                for line_no, imported_module in file_imports:
                    for forbidden in forbidden_list:
                        # 모듈의 시작이 금지된 문자열과 일치할 경우 (예: app.runtime.analyze)
                        if imported_module.startswith(forbidden):
                            err = (
                                f"[헌법 위반] {python_file.relative_to(self.base_dir)}:{line_no}\n"
                                f"  -> '{rule_path}' 계층은 '{forbidden}' 계층을 임포트할 수 없습니다."
                            )
                            violations.append(err)

        return violations
