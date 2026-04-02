"""LLM 연동용 환경설정 로드/검증 서비스."""

import os
from pathlib import Path
from typing import Mapping

from app.config.llm_env import get_project_root, load_env_file_values
from app.types.llm_config import LlmConfigResponse

REQUIRED_LLM_KEYS: tuple[str, ...] = (
    "LLM_API_KEY",
    "LLM_ENDPOINT",
    "LLM_MODEL_NAME",
    "LLM_DEPLOYMENT_NAME",
)


class LlmConfigLoadError(Exception):
    """환경 파일 자체를 읽지 못했을 때 발생하는 예외."""

    pass


class LlmConfigValidationError(Exception):
    """필수 LLM 키가 누락되었을 때 발생하는 예외."""

    def __init__(self, missing_keys: list[str]) -> None:
        """누락 키 목록을 보관하고 사람이 읽기 쉬운 메시지를 구성한다."""
        self.missing_keys = missing_keys
        missing_text = ", ".join(missing_keys)
        super().__init__(f"Missing required LLM keys: {missing_text}")


def _extract_required_values(values: Mapping[str, str | None]) -> dict[str, str]:
    """필수 키 집합을 추출하고, 누락 시 검증 예외를 발생시킨다."""
    resolved: dict[str, str] = {}
    missing_keys: list[str] = []

    for key in REQUIRED_LLM_KEYS:
        value = values.get(key)
        if value is None or value.strip() == "":
            missing_keys.append(key)
            continue
        resolved[key] = value

    if missing_keys:
        raise LlmConfigValidationError(missing_keys=missing_keys)

    return resolved


def get_llm_config(
    app_env_raw: str | None = None, project_root: Path | None = None
) -> LlmConfigResponse:
    """`APP_ENV` 기준 env 파일에서 LLM 설정을 로드해 모델로 반환한다."""
    env_value = app_env_raw if app_env_raw is not None else os.getenv("APP_ENV")
    base_dir = project_root if project_root is not None else get_project_root()

    try:
        loaded_values = load_env_file_values(
            project_root=base_dir,
            app_env_raw=env_value,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise LlmConfigLoadError(str(exc)) from exc

    required_values = _extract_required_values(values=loaded_values)

    api_version = loaded_values.get("LLM_API_VERSION")
    if api_version is not None and api_version.strip() != "":
        required_values["LLM_API_VERSION"] = api_version

    model_version = loaded_values.get("LLM_MODEL_VERSION")
    if model_version is not None and model_version.strip() != "":
        required_values["LLM_MODEL_VERSION"] = model_version

    return LlmConfigResponse(**required_values)
