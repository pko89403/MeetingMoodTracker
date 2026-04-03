"""프로젝트/회의 턴 수집 + 분석 + 저장 API."""

from fastapi import APIRouter, HTTPException

from app.service.turn_ingest_service import (
    TurnIngestInferenceError,
    store_turn_analysis,
)
from app.types.identifiers import normalize_storage_segment
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
        normalized_project_id = normalize_storage_segment(
            project_id,
            field_name="project_id",
        )
        normalized_meeting_id = normalize_storage_segment(
            meeting_id,
            field_name="meeting_id",
        )
        return await store_turn_analysis(
            project_id=normalized_project_id,
            meeting_id=normalized_meeting_id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "INVALID_STORAGE_IDENTIFIER",
                "message_ko": "project_id 또는 meeting_id 형식이 올바르지 않습니다.",
                "message_en": "project_id or meeting_id has an invalid format.",
                "reason": str(exc),
            },
        ) from exc
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
