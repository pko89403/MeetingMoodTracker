import json

from fastapi.testclient import TestClient

import app.runtime.analyze as analyze_runtime
from app.main import app
from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeLogicStep,
)
from app.types.mood import AnalyzeResponse

client = TestClient(app)


def _payload() -> dict[str, str]:
    return {
        "meeting_id": "m_12345",
        "text": "오늘 회의에서는 새로운 서버 아키텍처에 대해 논의했습니다.",
    }


def _parse_sse_response_body(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for chunk in body.split("\n\n"):
        chunk = chunk.strip()
        if chunk == "":
            continue
        event_name = ""
        data_lines: list[str] = []
        for line in chunk.splitlines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        if event_name == "":
            continue
        payload = json.loads("\n".join(data_lines)) if data_lines else {}
        events.append((event_name, payload))
    return events


def test_analyze_and_inspect_return_identical_result_for_same_input() -> None:
    analyze_response = client.post("/api/v1/analyze", json=_payload())
    inspect_response = client.post("/api/v1/analyze/inspect", json=_payload())

    assert analyze_response.status_code == 200
    assert inspect_response.status_code == 200
    inspect_data = inspect_response.json()
    assert analyze_response.json() == inspect_data["result"]
    assert inspect_data["request_id"].startswith("anl_")
    assert len(inspect_data["logic_steps"]) == 4
    assert len(inspect_data["logs"]) == 4


def test_analyze_and_inspect_share_single_service_method(monkeypatch) -> None:
    call_count = {"count": 0}

    def _fake_run_analyze_pipeline(request) -> AnalyzeInspectResponse:
        call_count["count"] += 1
        assert request.meeting_id == "m_12345"
        return AnalyzeInspectResponse(
            request_id="anl_test_001",
            result=AnalyzeResponse(topic="Architecture", mood="Positive", confidence=0.95),
            logic_steps=[
                AnalyzeLogicStep(
                    step_id="receive_request",
                    title_ko="입력 수신",
                    description_ko="요청 수신 단계",
                )
            ],
            logs=[
                AnalyzeLogEntry(
                    request_id="anl_test_001",
                    step_id="receive_request",
                    message_ko="요청 수신",
                    created_at="2026-03-30T00:00:00+00:00",
                )
            ],
        )

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _fake_run_analyze_pipeline)

    analyze_response = client.post("/api/v1/analyze", json=_payload())
    inspect_response = client.post("/api/v1/analyze/inspect", json=_payload())

    assert analyze_response.status_code == 200
    assert inspect_response.status_code == 200
    assert call_count["count"] == 2
    assert analyze_response.json() == {
        "topic": "Architecture",
        "mood": "Positive",
        "confidence": 0.95,
    }
    assert inspect_response.json()["result"] == analyze_response.json()


def test_analyze_inspect_stream_emits_expected_event_order(monkeypatch) -> None:
    def _fake_run_analyze_pipeline(
        request,
        on_log=None,
        request_id=None,
    ) -> AnalyzeInspectResponse:
        assert request.meeting_id == "m_12345"
        resolved_request_id = request_id or "anl_test_stream_001"
        logs = [
            AnalyzeLogEntry(
                request_id=resolved_request_id,
                step_id="receive_request",
                message_ko="요청 수신",
                created_at="2026-03-30T00:00:00+00:00",
            ),
            AnalyzeLogEntry(
                request_id=resolved_request_id,
                step_id="compose_response",
                message_ko="응답 조합",
                created_at="2026-03-30T00:00:01+00:00",
            ),
        ]
        if on_log is not None:
            for entry in logs:
                on_log(entry)
        return AnalyzeInspectResponse(
            request_id=resolved_request_id,
            result=AnalyzeResponse(topic="Architecture", mood="Positive", confidence=0.95),
            logic_steps=[
                AnalyzeLogicStep(
                    step_id="receive_request",
                    title_ko="입력 수신",
                    description_ko="요청 수신 단계",
                )
            ],
            logs=logs,
        )

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _fake_run_analyze_pipeline)

    response = client.post("/api/v1/analyze/inspect/stream", json=_payload())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse_response_body(response.text)
    assert [event_name for event_name, _ in events] == [
        "start",
        "log",
        "log",
        "result",
        "done",
    ]
    assert events[3][1]["result"] == {
        "topic": "Architecture",
        "mood": "Positive",
        "confidence": 0.95,
    }


def test_analyze_inspect_stream_returns_error_event_on_failure(monkeypatch) -> None:
    def _raise_error(request, on_log=None, request_id=None) -> AnalyzeInspectResponse:
        _ = request
        _ = on_log
        _ = request_id
        raise RuntimeError("forced failure")

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _raise_error)

    response = client.post("/api/v1/analyze/inspect/stream", json=_payload())

    assert response.status_code == 200
    events = _parse_sse_response_body(response.text)
    assert [event_name for event_name, _ in events] == ["start", "error"]
    assert events[0][1]["request_id"].startswith("anl_")
    assert events[1][1]["request_id"] == events[0][1]["request_id"]
    assert "오류" in events[1][1]["message_ko"]
