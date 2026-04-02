import ast
from pathlib import Path
from typing import Dict, List, Set

ROUTE_DECORATOR_NAMES = {"get", "post", "put", "patch", "delete"}
ALLOWED_IO_MODULE_PREFIX = "app.types"
ALLOWED_SSE_ROUTE_PATHS = {
    "/analyze/inspect/stream",
    "/api/v1/analyze/inspect/stream",
}
ALLOWED_STREAMING_RESPONSE_TYPES = {
    "StreamingResponse",
    "fastapi.responses.StreamingResponse",
    "starlette.responses.StreamingResponse",
}
SSE_MEDIA_TYPE = "text/event-stream"


class FastAPIContractValidator:
    """
    FastAPI 런타임 라우트가 프로젝트 I/O 헌법을 준수하는지 검사합니다.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.runtime_dir = self.base_dir / "app" / "runtime"

    def _resolve_relative_module(
        self, module_name: str, file_path: Path, level: int
    ) -> str:
        if level == 0:
            return module_name

        relative = file_path.relative_to(self.base_dir).with_suffix("")
        parts = list(relative.parts[:-1])
        if level > len(parts):
            return module_name

        parent_parts = parts[: len(parts) - level + 1]
        if not module_name:
            return ".".join(parent_parts)
        return ".".join(parent_parts + module_name.split("."))

    def _build_import_map(self, tree: ast.AST, file_path: Path) -> Dict[str, str]:
        imports: Dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    alias_name = alias.asname or alias.name.split(".")[0]
                    imports[alias_name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                resolved_module = self._resolve_relative_module(
                    module_name=module,
                    file_path=file_path,
                    level=node.level,
                )
                for alias in node.names:
                    alias_name = alias.asname or alias.name
                    if resolved_module:
                        imports[alias_name] = f"{resolved_module}.{alias.name}"
                    else:
                        imports[alias_name] = alias.name
        return imports

    def _collect_name_paths(self, node: ast.AST) -> Set[str]:
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, ast.Attribute):
            base_paths = self._collect_name_paths(node.value)
            if not base_paths:
                return {node.attr}
            return {f"{path}.{node.attr}" for path in base_paths}
        if isinstance(node, ast.Subscript):
            return self._collect_name_paths(node.value) | self._collect_name_paths(
                node.slice
            )
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            names: Set[str] = set()
            for elem in node.elts:
                names |= self._collect_name_paths(elem)
            return names
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return self._collect_name_paths(node.left) | self._collect_name_paths(
                node.right
            )
        if isinstance(node, ast.Call):
            return self._collect_name_paths(node.func)
        if isinstance(node, ast.Constant):
            return set()
        return set()

    def _resolve_import_paths(
        self, names: Set[str], import_map: Dict[str, str]
    ) -> Set[str]:
        resolved: Set[str] = set()
        for dotted in names:
            root, *rest = dotted.split(".")
            if root in import_map:
                base = import_map[root]
                resolved.add(".".join([base] + rest) if rest else base)
            else:
                resolved.add(dotted)
        return resolved

    def _extract_route_path(self, decorator: ast.Call) -> str:
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            route_path = decorator.args[0].value
            if isinstance(route_path, str):
                return route_path
        return "<unknown>"

    def _is_allowed_sse_route(self, route_path: str) -> bool:
        return route_path in ALLOWED_SSE_ROUTE_PATHS

    def _has_streaming_response_class(
        self,
        decorator: ast.Call,
        import_map: Dict[str, str],
    ) -> bool:
        for keyword in decorator.keywords:
            if keyword.arg != "response_class":
                continue
            names = self._collect_name_paths(keyword.value)
            resolved = self._resolve_import_paths(names, import_map)
            if any(
                response_type in ALLOWED_STREAMING_RESPONSE_TYPES
                for response_type in resolved
            ):
                return True
        return False

    def _has_sse_media_type(
        self,
        fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
        import_map: Dict[str, str],
    ) -> bool:
        for node in ast.walk(fn_node):
            if not isinstance(node, ast.Call):
                continue

            call_names = self._collect_name_paths(node.func)
            resolved_call_names = self._resolve_import_paths(call_names, import_map)
            is_streaming_response_call = any(
                call_name in ALLOWED_STREAMING_RESPONSE_TYPES
                for call_name in resolved_call_names
            )
            if not is_streaming_response_call:
                continue

            for keyword in node.keywords:
                if (
                    keyword.arg == "media_type"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == SSE_MEDIA_TYPE
                ):
                    return True

        return False

    def _validate_route_function(
        self,
        fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
        import_map: Dict[str, str],
    ) -> List[str]:
        violations: List[str] = []
        route_decorators = [
            dec
            for dec in fn_node.decorator_list
            if isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and dec.func.attr in ROUTE_DECORATOR_NAMES
        ]

        if not route_decorators:
            return violations

        route_path = self._extract_route_path(route_decorators[0])
        relative_file = file_path.relative_to(self.base_dir)
        is_allowed_sse_route = self._is_allowed_sse_route(route_path=route_path)

        if fn_node.returns is None:
            violations.append(
                f"[FastAPI Contract Error] {relative_file}:{fn_node.lineno}\n"
                f"  -> '{route_path}' 라우트 핸들러 '{fn_node.name}'에 반환 타입 힌트가 없습니다.\n"
                f"  [How to fix (Next Action)]: 라우트 핸들러에 Pydantic 응답 모델 기반 반환 타입을 명시하세요."
            )

        if is_allowed_sse_route:
            primary_decorator = route_decorators[0]
            if not self._has_streaming_response_class(
                decorator=primary_decorator,
                import_map=import_map,
            ):
                violations.append(
                    f"[FastAPI Contract Error] {relative_file}:{primary_decorator.lineno}\n"
                    f"  -> '{route_path}' SSE 라우트는 response_class=StreamingResponse가 필요합니다.\n"
                    f"  [How to fix (Next Action)]: @router.<method>(..., response_class=StreamingResponse) 형태로 선언하세요."
                )
            if not self._has_sse_media_type(fn_node=fn_node, import_map=import_map):
                violations.append(
                    f"[FastAPI Contract Error] {relative_file}:{fn_node.lineno}\n"
                    f"  -> '{route_path}' SSE 라우트에서 media_type='text/event-stream'을 확인하지 못했습니다.\n"
                    f"  [How to fix (Next Action)]: StreamingResponse(..., media_type='text/event-stream')를 반환하세요."
                )
        else:
            has_response_model = False
            for dec in route_decorators:
                for kw in dec.keywords:
                    if kw.arg == "response_model":
                        has_response_model = True
                        names = self._collect_name_paths(kw.value)
                        resolved = self._resolve_import_paths(names, import_map)
                        app_paths = {
                            name for name in resolved if name.startswith("app.")
                        }
                        if not any(
                            name.startswith(ALLOWED_IO_MODULE_PREFIX)
                            for name in app_paths
                        ):
                            violations.append(
                                f"[FastAPI Contract Error] {relative_file}:{dec.lineno}\n"
                                f"  -> '{route_path}' 라우트의 response_model은 app/types 기반 모델이어야 합니다.\n"
                                f"  [How to fix (Next Action)]: app.types.* 경로의 Pydantic 모델을 response_model로 지정하세요."
                            )
                        forbidden = [
                            name
                            for name in app_paths
                            if not name.startswith(ALLOWED_IO_MODULE_PREFIX)
                        ]
                        if forbidden:
                            violations.append(
                                f"[FastAPI Contract Error] {relative_file}:{dec.lineno}\n"
                                f"  -> '{route_path}' 라우트의 response_model에서 app/types 외 경로를 사용했습니다: {forbidden[0]}\n"
                                f"  [How to fix (Next Action)]: API 입출력 모델은 app.types.*로 통일하세요."
                            )
                        break
                if has_response_model:
                    break

            if not has_response_model:
                violations.append(
                    f"[FastAPI Contract Error] {relative_file}:{fn_node.lineno}\n"
                    f"  -> '{route_path}' 라우트 데코레이터에 response_model이 없습니다.\n"
                    f"  [How to fix (Next Action)]: @router.<method>(..., response_model=YourResponseModel) 형태로 지정하세요."
                )

        for node in ast.walk(fn_node):
            if isinstance(node, ast.Return) and isinstance(
                node.value, ast.Dict | ast.List
            ):
                violations.append(
                    f"[FastAPI Contract Error] {relative_file}:{node.lineno}\n"
                    f"  -> '{route_path}' 라우트에서 dict/list 리터럴을 직접 반환하고 있습니다.\n"
                    f"  [How to fix (Next Action)]: app.types.*의 Pydantic 모델 인스턴스를 생성해 반환하세요."
                )
                break

        # 라우트 시그니처에서 app.* 타입은 반드시 app.types.* 경로여야 함.
        all_args = (
            list(fn_node.args.posonlyargs)
            + list(fn_node.args.args)
            + list(fn_node.args.kwonlyargs)
        )
        if fn_node.args.vararg:
            all_args.append(fn_node.args.vararg)
        if fn_node.args.kwarg:
            all_args.append(fn_node.args.kwarg)

        for arg in all_args:
            if arg.arg in {"self", "cls"} or arg.annotation is None:
                continue
            names = self._collect_name_paths(arg.annotation)
            resolved = self._resolve_import_paths(names, import_map)
            forbidden = [
                name
                for name in resolved
                if name.startswith("app.")
                and not name.startswith(ALLOWED_IO_MODULE_PREFIX)
            ]
            if forbidden:
                violations.append(
                    f"[FastAPI Contract Error] {relative_file}:{arg.lineno}\n"
                    f"  -> '{route_path}' 라우트 파라미터 '{arg.arg}'에서 app/types 외 타입을 사용했습니다: {forbidden[0]}\n"
                    f"  [How to fix (Next Action)]: 라우트 입출력 타입은 app.types.*만 사용하세요."
                )
                break

        return violations

    def validate(self) -> List[str]:
        violations: List[str] = []
        if not self.runtime_dir.exists():
            return violations

        for python_file in self.runtime_dir.rglob("*.py"):
            try:
                with open(python_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(python_file))
            except Exception as exc:
                relative = python_file.relative_to(self.base_dir)
                violations.append(
                    f"[FastAPI Contract Error] {relative}:1\n"
                    f"  -> 파일 파싱에 실패하여 FastAPI 계약 검증을 수행할 수 없습니다: {exc}\n"
                    f"  [How to fix (Next Action)]: 파이썬 문법 오류를 수정한 뒤 다시 검증을 실행하세요."
                )
                continue

            import_map = self._build_import_map(tree, python_file)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    violations.extend(
                        self._validate_route_function(
                            fn_node=node, file_path=python_file, import_map=import_map
                        )
                    )

        return violations
