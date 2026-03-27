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
    try:
        return get_llm_config()
    except LlmConfigValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Required LLM configuration key is missing.",
                "missing_keys": exc.missing_keys,
            },
        ) from exc
    except LlmConfigLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
