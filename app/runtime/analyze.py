"""회의록 analyze/inspect API 런타임 라우트."""

import json
from queue import Queue
from threading import Thread
from typing import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.service.analyze_service import (
    AnalyzeInferenceError,
    create_analyze_request_id,
    get_analyze_logic_steps,
    run_analyze_pipeline,
)
from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeSseEventPayload,
)
from app.types.mood import AnalyzeRequest, AnalyzeResponse

router = APIRouter()


def _raise_analyze_llm_failure(exc: AnalyzeInferenceError) -> None:
    """LLM 기반 analyze 실패를 502(Bad Gateway)로 변환한다."""
    raise HTTPException(
        status_code=502,
        detail={
            "error_code": "ANALYZE_LLM_FAILURE",
            "message_ko": "LLM 기반 analyze 추론에 실패했습니다.",
            "message_en": "Analyze inference failed from LLM service.",
            "stage": exc.stage,
        },
    ) from exc


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_meeting(request: AnalyzeRequest) -> AnalyzeResponse:
    """기존 analyze 계약을 유지하면서 공통 파이프라인 결과만 반환한다."""
    try:
        inspect_result = run_analyze_pipeline(request=request)
    except AnalyzeInferenceError as exc:
        _raise_analyze_llm_failure(exc=exc)
    return inspect_result.result


@router.post("/analyze/inspect", response_model=AnalyzeInspectResponse)
def inspect_analyze_meeting(request: AnalyzeRequest) -> AnalyzeInspectResponse:
    """analyze 실행 결과와 내부 추적 정보(steps/logs)를 함께 반환한다."""
    try:
        return run_analyze_pipeline(request=request)
    except AnalyzeInferenceError as exc:
        _raise_analyze_llm_failure(exc=exc)


def _build_sse_frame(payload: AnalyzeSseEventPayload) -> str:
    """SSE 프로토콜 형식(`event/data`)으로 단일 프레임을 직렬화한다."""
    event_name = payload.event
    payload_json = json.dumps(payload.model_dump(exclude_none=True), ensure_ascii=False)
    return f"event: {event_name}\ndata: {payload_json}\n\n"


def _iterate_inspect_stream(request: AnalyzeRequest) -> Iterator[str]:
    """inspect 실행 결과를 SSE 이벤트 시퀀스로 변환해 전송한다."""
    request_id = create_analyze_request_id()
    log_queue: Queue[AnalyzeLogEntry | None] = Queue()
    worker_state: dict[str, AnalyzeInspectResponse | Exception | None] = {
        "inspect_result": None,
        "error": None,
    }

    def _on_log(entry: AnalyzeLogEntry) -> None:
        log_queue.put(entry)

    def _run_pipeline_in_worker() -> None:
        try:
            worker_state["inspect_result"] = run_analyze_pipeline(
                request=request,
                on_log=_on_log,
                request_id=request_id,
            )
        except Exception as exc:
            worker_state["error"] = exc
        finally:
            log_queue.put(None)

    worker = Thread(target=_run_pipeline_in_worker, daemon=True)
    worker.start()

    yield _build_sse_frame(
        AnalyzeSseEventPayload(
            event="start",
            request_id=request_id,
            message_ko="analyze inspect 스트림을 시작했습니다.",
            logic_steps=get_analyze_logic_steps(),
        )
    )

    while True:
        log_entry = log_queue.get()
        if log_entry is None:
            break
        yield _build_sse_frame(
            AnalyzeSseEventPayload(
                event="log",
                request_id=log_entry.request_id,
                step_id=log_entry.step_id,
                message_ko=log_entry.message_ko,
                created_at=log_entry.created_at,
            )
        )

    worker.join()
    if isinstance(worker_state["error"], Exception):
        error = worker_state["error"]
        yield _build_sse_frame(
            AnalyzeSseEventPayload(
                event="error",
                request_id=request_id,
                message_ko=f"analyze inspect 스트림 처리 중 오류가 발생했습니다: {error}",
            )
        )
        return

    inspect_result = worker_state["inspect_result"]
    if not isinstance(inspect_result, AnalyzeInspectResponse):
        yield _build_sse_frame(
            AnalyzeSseEventPayload(
                event="error",
                request_id=request_id,
                message_ko="analyze inspect 스트림 처리 중 결과를 확인하지 못했습니다.",
            )
        )
        return

    yield _build_sse_frame(
        AnalyzeSseEventPayload(
            event="result",
            request_id=inspect_result.request_id,
            result=inspect_result.result,
        )
    )
    yield _build_sse_frame(
        AnalyzeSseEventPayload(
            event="done",
            request_id=inspect_result.request_id,
            message_ko="analyze inspect 스트림이 완료되었습니다.",
        )
    )


@router.post("/analyze/inspect/stream", response_class=StreamingResponse)
def inspect_analyze_meeting_stream(request: AnalyzeRequest) -> StreamingResponse:
    """inspect 결과를 SSE(`text/event-stream`)로 전달한다."""
    return StreamingResponse(
        _iterate_inspect_stream(request=request),
        media_type="text/event-stream",
    )
