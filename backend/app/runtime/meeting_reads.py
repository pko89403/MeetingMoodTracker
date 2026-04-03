"""프로젝트/회의 조회 API."""

from fastapi import APIRouter, HTTPException

from app.service.meeting_read_service import (
    MeetingReadInferenceError,
    MeetingReadNotFoundError,
    get_meeting_agents,
    get_meeting_overview,
    get_meeting_turns,
)
from app.types.identifiers import normalize_storage_segment
from app.types.storage import (
    MeetingAgentsResponse,
    MeetingOverviewResponse,
    MeetingTurnsResponse,
)

router = APIRouter()


def _normalize_meeting_path(project_id: str, meeting_id: str) -> tuple[str, str]:
    """project/meeting path parameter를 공통 규칙으로 정규화한다."""
    normalized_project_id = normalize_storage_segment(
        project_id,
        field_name="project_id",
    )
    normalized_meeting_id = normalize_storage_segment(
        meeting_id,
        field_name="meeting_id",
    )
    return normalized_project_id, normalized_meeting_id


def _raise_invalid_storage_identifier(exc: ValueError) -> None:
    """잘못된 project/meeting 식별자를 422로 변환한다."""
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "INVALID_STORAGE_IDENTIFIER",
            "message_ko": "project_id 또는 meeting_id 형식이 올바르지 않습니다.",
            "message_en": "project_id or meeting_id has an invalid format.",
            "reason": str(exc),
        },
    ) from exc


def _raise_meeting_not_found(project_id: str, meeting_id: str) -> None:
    """존재하지 않는 project/meeting 경로를 404로 변환한다."""
    raise HTTPException(
        status_code=404,
        detail={
            "error_code": "MEETING_NOT_FOUND",
            "message_ko": "요청한 project_id/meeting_id 경로의 회의를 찾을 수 없습니다.",
            "message_en": "Meeting not found for the given project_id/meeting_id path.",
            "project_id": project_id,
            "meeting_id": meeting_id,
        },
    )


def _raise_meeting_read_failure(exc: MeetingReadInferenceError) -> None:
    """overview aggregate 계산 실패를 502로 변환한다."""
    raise HTTPException(
        status_code=502,
        detail={
            "error_code": "MEETING_READ_LLM_FAILURE",
            "message_ko": "회의 overview aggregate 계산에 실패했습니다.",
            "message_en": "Meeting overview aggregate inference failed.",
            "stage": exc.stage,
        },
    ) from exc


@router.get(
    "/api/v1/projects/{project_id}/meetings/{meeting_id}",
    response_model=MeetingOverviewResponse,
)
async def read_meeting_overview(
    project_id: str,
    meeting_id: str,
) -> MeetingOverviewResponse:
    """회의 overview 화면용 aggregate 응답을 반환한다."""
    try:
        normalized_project_id, normalized_meeting_id = _normalize_meeting_path(
            project_id=project_id,
            meeting_id=meeting_id,
        )
        return await get_meeting_overview(
            project_id=normalized_project_id,
            meeting_id=normalized_meeting_id,
        )
    except ValueError as exc:
        _raise_invalid_storage_identifier(exc=exc)
    except MeetingReadNotFoundError:
        _raise_meeting_not_found(project_id=project_id, meeting_id=meeting_id)
    except MeetingReadInferenceError as exc:
        _raise_meeting_read_failure(exc=exc)


@router.get(
    "/api/v1/projects/{project_id}/meetings/{meeting_id}/turns",
    response_model=MeetingTurnsResponse,
)
async def read_meeting_turns(
    project_id: str,
    meeting_id: str,
) -> MeetingTurnsResponse:
    """회의 timeline/detail 패널용 정렬된 턴 목록을 반환한다."""
    try:
        normalized_project_id, normalized_meeting_id = _normalize_meeting_path(
            project_id=project_id,
            meeting_id=meeting_id,
        )
        return get_meeting_turns(
            project_id=normalized_project_id,
            meeting_id=normalized_meeting_id,
        )
    except ValueError as exc:
        _raise_invalid_storage_identifier(exc=exc)
    except MeetingReadNotFoundError:
        _raise_meeting_not_found(project_id=project_id, meeting_id=meeting_id)


@router.get(
    "/api/v1/projects/{project_id}/meetings/{meeting_id}/agents",
    response_model=MeetingAgentsResponse,
)
async def read_meeting_agents(
    project_id: str,
    meeting_id: str,
) -> MeetingAgentsResponse:
    """회의 agent별 aggregate 응답을 반환한다."""
    try:
        normalized_project_id, normalized_meeting_id = _normalize_meeting_path(
            project_id=project_id,
            meeting_id=meeting_id,
        )
        return get_meeting_agents(
            project_id=normalized_project_id,
            meeting_id=normalized_meeting_id,
        )
    except ValueError as exc:
        _raise_invalid_storage_identifier(exc=exc)
    except MeetingReadNotFoundError:
        _raise_meeting_not_found(project_id=project_id, meeting_id=meeting_id)
