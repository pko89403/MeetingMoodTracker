"""Analyze 파이프라인 공통 실행 로직."""

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Callable
from uuid import uuid4

from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeLogicStep,
)
from app.types.mood import AnalyzeRequest, AnalyzeResponse

MAX_ANALYZE_LOG_BUFFER_SIZE = 200
_analyze_log_buffer: deque[AnalyzeLogEntry] = deque(maxlen=MAX_ANALYZE_LOG_BUFFER_SIZE)
_analyze_log_lock = Lock()

_ANALYZE_LOGIC_STEPS: tuple[AnalyzeLogicStep, ...] = (
    AnalyzeLogicStep(
        step_id="receive_request",
        title_ko="입력 수신",
        description_ko="요청 본문(meeting_id, text)을 수신하고 기본 메타를 확인합니다.",
    ),
    AnalyzeLogicStep(
        step_id="extract_topic",
        title_ko="의제 추론",
        description_ko="회의 텍스트에서 핵심 의제를 추론합니다.",
    ),
    AnalyzeLogicStep(
        step_id="analyze_mood",
        title_ko="분위기 추론",
        description_ko="문장 톤을 바탕으로 분위기와 신뢰도를 산출합니다.",
    ),
    AnalyzeLogicStep(
        step_id="compose_response",
        title_ko="응답 조합",
        description_ko="분석 결과를 API 응답 스키마로 직렬화합니다.",
    ),
)


def _now_iso_utc() -> str:
    """UTC 기준 ISO8601 타임스탬프 문자열을 생성한다."""
    return datetime.now(tz=timezone.utc).isoformat()


def _new_request_id() -> str:
    """analyze 요청 식별자를 생성한다."""
    return f"anl_{uuid4().hex[:12]}"


def create_analyze_request_id() -> str:
    """외부 호출자용 analyze 요청 식별자를 생성한다."""
    return _new_request_id()


def get_analyze_logic_steps() -> list[AnalyzeLogicStep]:
    """UI 표시용 analyze 로직 단계 목록을 복제해 반환한다."""
    return [step.model_copy(deep=True) for step in _ANALYZE_LOGIC_STEPS]


def _append_log(entry: AnalyzeLogEntry) -> None:
    """전역 링버퍼에 로그를 저장한다."""
    with _analyze_log_lock:
        _analyze_log_buffer.append(entry)


def list_recent_analyze_logs(
    limit: int = 50,
    request_id: str | None = None,
) -> list[AnalyzeLogEntry]:
    """메모리 링버퍼에 저장된 최근 로그를 반환한다."""
    normalized_limit = max(1, min(limit, MAX_ANALYZE_LOG_BUFFER_SIZE))
    with _analyze_log_lock:
        snapshot = list(_analyze_log_buffer)

    if request_id is not None and request_id.strip() != "":
        snapshot = [entry for entry in snapshot if entry.request_id == request_id]
    return snapshot[-normalized_limit:]


def _record_log(
    request_id: str,
    step_id: str,
    message_ko: str,
    collected_logs: list[AnalyzeLogEntry],
    on_log: Callable[[AnalyzeLogEntry], None] | None,
) -> None:
    """파이프라인 로그를 생성/버퍼링/콜백 전파한다."""
    entry = AnalyzeLogEntry(
        request_id=request_id,
        step_id=step_id,
        message_ko=message_ko,
        created_at=_now_iso_utc(),
    )
    _append_log(entry=entry)
    collected_logs.append(entry)
    if on_log is not None:
        on_log(entry)


def _infer_topic(text: str) -> str:
    """의제 추론 결과를 생성한다.

    현재는 기존 회귀 호환을 위해 고정값(`Architecture`)을 반환한다.
    """
    _ = text
    return "Architecture"


def _infer_mood(text: str) -> str:
    """분위기 추론 결과를 생성한다.

    현재는 기존 회귀 호환을 위해 고정값(`Positive`)을 반환한다.
    """
    _ = text
    return "Positive"


def _infer_confidence(text: str) -> float:
    """분위기 추론 신뢰도를 계산한다.

    현재는 기존 회귀 호환을 위해 고정값(`0.95`)을 반환한다.
    """
    _ = text
    return 0.95


def run_analyze_pipeline(
    request: AnalyzeRequest,
    on_log: Callable[[AnalyzeLogEntry], None] | None = None,
    request_id: str | None = None,
) -> AnalyzeInspectResponse:
    """`/analyze`, `/inspect`, `/inspect/stream`가 공통으로 호출하는 단일 메서드."""
    resolved_request_id = request_id or create_analyze_request_id()
    collected_logs: list[AnalyzeLogEntry] = []

    _record_log(
        request_id=resolved_request_id,
        step_id="receive_request",
        message_ko=(
            f"요청 수신 완료: meeting_id={request.meeting_id}, "
            f"text_length={len(request.text)}"
        ),
        collected_logs=collected_logs,
        on_log=on_log,
    )

    topic = _infer_topic(text=request.text)
    _record_log(
        request_id=resolved_request_id,
        step_id="extract_topic",
        message_ko=f"의제 추론 완료: topic={topic}",
        collected_logs=collected_logs,
        on_log=on_log,
    )

    mood = _infer_mood(text=request.text)
    confidence = _infer_confidence(text=request.text)
    _record_log(
        request_id=resolved_request_id,
        step_id="analyze_mood",
        message_ko=f"분위기 추론 완료: mood={mood}, confidence={confidence}",
        collected_logs=collected_logs,
        on_log=on_log,
    )

    result = AnalyzeResponse(topic=topic, mood=mood, confidence=confidence)
    _record_log(
        request_id=resolved_request_id,
        step_id="compose_response",
        message_ko="응답 스키마 조합 완료",
        collected_logs=collected_logs,
        on_log=on_log,
    )

    return AnalyzeInspectResponse(
        request_id=resolved_request_id,
        result=result,
        logic_steps=get_analyze_logic_steps(),
        logs=collected_logs,
    )
