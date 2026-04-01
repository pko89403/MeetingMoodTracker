"""LLM 환경설정 조회 응답 타입 정의."""

from pydantic import BaseModel


class LlmConfigResponse(BaseModel):
    """`GET /api/v1/env`가 반환하는 LLM 환경설정 응답 스키마."""

    LLM_API_KEY: str
    LLM_ENDPOINT: str
    LLM_MODEL_NAME: str
    LLM_DEPLOYMENT_NAME: str
    LLM_API_VERSION: str | None = None
    LLM_MODEL_VERSION: str | None = None
