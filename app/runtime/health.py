"""프로세스 liveness 확인용 healthz API 라우트."""

from fastapi import APIRouter

from app.types.health import HealthzResponse

router = APIRouter()


@router.get("/healthz", response_model=HealthzResponse)
def healthz() -> HealthzResponse:
    """애플리케이션 프로세스 응답성을 확인하는 healthz 엔드포인트."""
    return HealthzResponse()
