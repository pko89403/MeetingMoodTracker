"""프로젝트/회의 턴 수집 + 분석 + 저장 API."""

from fastapi import APIRouter, HTTPException

from app.service.turn_ingest_service import (
    TurnIngestInferenceError,
    store_turn_analysis,
)
from app.types.storage import TurnAnalysisRecord, TurnIngestRequest

router = APIRouter()


@router.post(
    "/api/v1/projects/{project_id}/meetings/{meeting_id}/turns",
    response_model=TurnAnalysisRecord,
)
async def ingest_meeting_turn(
    project_id: str,
    meeting_id: str,
    request: TurnIngestRequest,
) -> TurnAnalysisRecord:
    """프로젝트/회의 경로 아래 발화 턴 하나를 분석하고 저장한다."""
    try:
        return await store_turn_analysis(
            project_id=project_id,
            meeting_id=meeting_id,
            request=request,
        )
    except TurnIngestInferenceError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": "TURN_ANALYSIS_LLM_FAILURE",
                "message_ko": "LLM 기반 턴 분석 저장에 실패했습니다.",
                "message_en": "Turn analysis persistence failed from LLM service.",
                "stage": exc.stage,
            },
        ) from exc
