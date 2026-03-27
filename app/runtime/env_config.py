"""LLM 환경설정 조회 API 런타임 라우트."""

from fastapi import APIRouter, HTTPException

from app.service.llm_config_service import (
    LlmConfigLoadError,
    LlmConfigValidationError,
    get_llm_config,
)
from app.types.llm_config import LlmConfigResponse

router = APIRouter()


@router.get("/api/env/v1", response_model=LlmConfigResponse)
def get_llm_environment_config() -> LlmConfigResponse:
    """현재 `APP_ENV` 기준 LLM 설정을 조회한다."""
    try:
        return get_llm_config()
    except LlmConfigValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "LLM_CONFIG_MISSING_KEY",
                "message_ko": "필수 LLM 설정 키가 누락되었습니다.",
                "message_en": "Required LLM configuration key is missing.",
                "missing_keys": exc.missing_keys,
            },
        ) from exc
    except LlmConfigLoadError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "LLM_CONFIG_LOAD_FAILED",
                "message_ko": "환경설정 파일 로드에 실패했습니다.",
                "message_en": "Failed to load environment configuration.",
                "reason": str(exc),
            },
        ) from exc
