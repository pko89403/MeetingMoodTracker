"""회의록 analyze/inspect API 런타임 라우트."""

import asyncio
import json
from typing import AsyncIterator

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
async def analyze_meeting(request: AnalyzeRequest) -> AnalyzeResponse:
    """기존 analyze 계약을 유지하면서 공통 파이프라인 결과만 반환한다."""
    try:
        inspect_result = await run_analyze_pipeline(request=request)
    except AnalyzeInferenceError as exc:
        _raise_analyze_llm_failure(exc=exc)
    return inspect_result.result


@router.post("/analyze/inspect", response_model=AnalyzeInspectResponse)
async def inspect_analyze_meeting(request: AnalyzeRequest) -> AnalyzeInspectResponse:
    """analyze 실행 결과와 내부 추적 정보(steps/logs)를 함께 반환한다."""
    try:
        return await run_analyze_pipeline(request=request)
    except AnalyzeInferenceError as exc:
        _raise_analyze_llm_failure(exc=exc)


def _build_sse_frame(payload: AnalyzeSseEventPayload) -> str:
    """SSE 프로토콜 형식(`event/data`)으로 단일 프레임을 직렬화한다."""
    event_name = payload.event
    payload_json = json.dumps(payload.model_dump(exclude_none=True), ensure_ascii=False)
    return f"event: {event_name}\ndata: {payload_json}\n\n"


async def _iterate_inspect_stream(request: AnalyzeRequest) -> AsyncIterator[str]:
    """inspect 실행 결과를 SSE 이벤트 시퀀스로 변환해 전송한다."""
    request_id = create_analyze_request_id()
    log_queue: asyncio.Queue[AnalyzeLogEntry | None] = asyncio.Queue()

    def _on_log(entry: AnalyzeLogEntry) -> None:
        log_queue.put_nowait(entry)

    async def _run_pipeline() -> AnalyzeInspectResponse | Exception:
        try:
            return await run_analyze_pipeline(
                request=request,
                on_log=_on_log,
                request_id=request_id,
            )
        except Exception as exc:
            return exc
        finally:
            log_queue.put_nowait(None)

    # 파이프라인을 비동기 태스크로 실행
    pipeline_task = asyncio.create_task(_run_pipeline())

    yield _build_sse_frame(
        AnalyzeSseEventPayload(
            event="start",
            request_id=request_id,
            message_ko="analyze inspect 스트림을 시작했습니다.",
            logic_steps=get_analyze_logic_steps(),
        )
    )

    while True:
        log_entry = await log_queue.get()
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

    result_or_exc = await pipeline_task

    if isinstance(result_or_exc, Exception):
        yield _build_sse_frame(
            AnalyzeSseEventPayload(
                event="error",
                request_id=request_id,
                message_ko=f"analyze inspect 스트림 처리 중 오류가 발생했습니다: {result_or_exc}",
            )
        )
        return

    inspect_result = result_or_exc
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
async def inspect_analyze_meeting_stream(request: AnalyzeRequest) -> StreamingResponse:
    """inspect 결과를 SSE(`text/event-stream`)로 전달한다."""
    return StreamingResponse(
        _iterate_inspect_stream(request=request),
        media_type="text/event-stream",
    )
