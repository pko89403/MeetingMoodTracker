import os
from pathlib import Path
from typing import Mapping

from app.config.llm_env import get_project_root, load_env_file_values
from app.types.llm_config import LlmConfigResponse

REQUIRED_LLM_KEYS: tuple[str, str, str] = (
    "LLM_API_KEY",
    "LLM_ENDPOINT",
    "LLM_MODEL",
)


class LlmConfigLoadError(Exception):
    pass


class LlmConfigValidationError(Exception):
    def __init__(self, missing_keys: list[str]) -> None:
        self.missing_keys = missing_keys
        missing_text = ", ".join(missing_keys)
        super().__init__(f"Missing required LLM keys: {missing_text}")


def _extract_required_values(values: Mapping[str, str | None]) -> dict[str, str]:
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
    return LlmConfigResponse(**required_values)
