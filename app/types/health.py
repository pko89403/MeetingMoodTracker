"""서비스 상태 점검(healthz) 응답 타입 정의."""

from typing import Literal

from pydantic import BaseModel


class HealthzResponse(BaseModel):
    """프로세스 liveness 확인용 healthz 응답 스키마."""

    status: Literal["ok"] = "ok"
