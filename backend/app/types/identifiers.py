"""식별자 정규화 및 저장 경로 안전성 검증 헬퍼."""

UNASSIGNED_AGENT_ID = "__unassigned__"
_PATH_SEPARATORS = ("/", "\\")
_DOT_SEGMENTS = {".", ".."}


def normalize_required_identifier(
    value: str,
    *,
    field_name: str = "identifier",
    enforce_path_segment: bool = False,
) -> str:
    """필수 식별자를 trim하고 필요 시 안전한 path segment 규칙을 강제한다."""
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be blank.")
    if enforce_path_segment:
        if any(separator in normalized for separator in _PATH_SEPARATORS):
            raise ValueError(f"{field_name} must not contain path separators.")
        if normalized in _DOT_SEGMENTS:
            raise ValueError(f"{field_name} must not contain dot segments.")
    return normalized


def normalize_storage_segment(
    value: str,
    *,
    field_name: str,
    allow_reserved_unassigned: bool = False,
) -> str:
    """저장 경로에 들어가는 식별자를 안전한 단일 path segment로 정규화한다."""
    normalized = normalize_required_identifier(
        value,
        field_name=field_name,
        enforce_path_segment=True,
    )
    if normalized == UNASSIGNED_AGENT_ID and not allow_reserved_unassigned:
        raise ValueError(f"{field_name} '{UNASSIGNED_AGENT_ID}' is reserved.")
    return normalized


def normalize_optional_agent_id(
    value: str | None,
    *,
    field_name: str = "agent_id",
    allow_reserved_unassigned: bool = False,
) -> str | None:
    """선택적 agent_id를 trim하고 비어 있으면 None, 아니면 안전한 path segment로 정규화한다."""
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        return None
    return normalize_storage_segment(
        normalized,
        field_name=field_name,
        allow_reserved_unassigned=allow_reserved_unassigned,
    )
