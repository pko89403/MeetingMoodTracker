"""JSON 기반 저장소의 루트 경로를 해석하는 설정 유틸리티."""

import os
from pathlib import Path

DATA_ROOT_ENV_KEY = "MEETING_MOOD_DATA_DIR"


def get_workspace_root() -> Path:
    """저장소 워크스페이스 루트 경로를 반환한다."""
    return Path(__file__).resolve().parents[3]


def get_data_root() -> Path:
    """JSON 저장소가 사용할 data 루트 경로를 반환한다."""
    data_root_raw = os.getenv(DATA_ROOT_ENV_KEY)
    workspace_root = get_workspace_root()
    if data_root_raw is None or data_root_raw.strip() == "":
        return workspace_root / "data"

    configured = Path(data_root_raw)
    if configured.is_absolute():
        return configured
    return workspace_root / configured


def get_projects_data_root() -> Path:
    """프로젝트 계층 저장소가 사용할 `data/projects` 루트를 반환한다."""
    return get_data_root() / "projects"
