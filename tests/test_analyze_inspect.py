import json

from fastapi.testclient import TestClient

import app.runtime.analyze as analyze_runtime
from app.main import app
from app.service.analyze_service import AnalyzeInferenceError
from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeLogicStep,
)
from app.types.mood import (
    AnalyzeCorrelation,
    AnalyzeEmotion,
    AnalyzeEmotionDistribution,
    AnalyzeResponse,
    AnalyzeSentiment,
    AnalyzeSentimentDistribution,
    AnalyzeTopic,
    AnalyzeTopicCandidate,
)

client = TestClient(app)


def _payload() -> dict[str, str]:
    return {
        "meeting_id": "m_12345",
        "text": "오늘 회의에서는 새로운 서버 아키텍처에 대해 논의했습니다.",
    }


def _sample_result() -> AnalyzeResponse:
    return AnalyzeResponse(
        topic=AnalyzeTopic(
            primary="Architecture",
            candidates=[
                AnalyzeTopicCandidate(label="Architecture", confidence=80),
                AnalyzeTopicCandidate(label="Roadmap", confidence=61),
            ],
        ),
        sentiment=AnalyzeSentiment(
            distribution=AnalyzeSentimentDistribution(
                positive=60,
                negative=10,
                neutral=30,
            ),
            polarity="positive",
            confidence=60,
        ),
        emotion=AnalyzeEmotion(
            distribution=AnalyzeEmotionDistribution(
                anger=8,
                joy=32,
                sadness=6,
                neutral=12,
                anxiety=22,
                frustration=9,
                excitement=7,
                confusion=4,
            ),
            primary="joy",
            confidence=32,
        ),
        correlation=AnalyzeCorrelation(
            topic_sentiment=70,
            topic_emotion=56,
            sentiment_emotion=67,
            summary="토픽과 감성/감정의 상관도가 중간 이상입니다.",
        ),
    )


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


def test_analyze_and_inspect_return_identical_result_for_same_input(monkeypatch) -> None:
    def _fake_run_analyze_pipeline(request) -> AnalyzeInspectResponse:
        assert request.meeting_id == "m_12345"
        return AnalyzeInspectResponse(
            request_id="anl_test_002",
            result=_sample_result(),
            logic_steps=[
                AnalyzeLogicStep(
                    step_id="receive_request",
                    title_ko="입력 수신",
                    description_ko="요청 수신 단계",
                ),
                AnalyzeLogicStep(
                    step_id="extract_topic",
                    title_ko="Topic 세분화",
                    description_ko="Topic 세분화 단계",
                ),
                AnalyzeLogicStep(
                    step_id="analyze_sentiment",
                    title_ko="Sentiment 세분화",
                    description_ko="Sentiment 세분화 단계",
                ),
                AnalyzeLogicStep(
                    step_id="analyze_emotion",
                    title_ko="Emotion 세분화",
                    description_ko="Emotion 세분화 단계",
                ),
                AnalyzeLogicStep(
                    step_id="compose_response",
                    title_ko="Correlation 재조합",
                    description_ko="Correlation 재조합 단계",
                ),
            ],
            logs=[
                AnalyzeLogEntry(
                    request_id="anl_test_002",
                    step_id="receive_request",
                    message_ko="요청 수신",
                    created_at="2026-03-30T00:00:00+00:00",
                ),
                AnalyzeLogEntry(
                    request_id="anl_test_002",
                    step_id="extract_topic",
                    message_ko="Topic 세분화",
                    created_at="2026-03-30T00:00:01+00:00",
                ),
                AnalyzeLogEntry(
                    request_id="anl_test_002",
                    step_id="analyze_sentiment",
                    message_ko="Sentiment 세분화",
                    created_at="2026-03-30T00:00:02+00:00",
                ),
                AnalyzeLogEntry(
                    request_id="anl_test_002",
                    step_id="analyze_emotion",
                    message_ko="Emotion 세분화",
                    created_at="2026-03-30T00:00:03+00:00",
                ),
                AnalyzeLogEntry(
                    request_id="anl_test_002",
                    step_id="compose_response",
                    message_ko="Correlation 재조합",
                    created_at="2026-03-30T00:00:04+00:00",
                ),
            ],
        )

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _fake_run_analyze_pipeline)

    analyze_response = client.post("/api/v1/analyze", json=_payload())
    inspect_response = client.post("/api/v1/analyze/inspect", json=_payload())

    assert analyze_response.status_code == 200
    assert inspect_response.status_code == 200
    inspect_data = inspect_response.json()
    assert analyze_response.json() == inspect_data["result"]
    assert inspect_data["request_id"].startswith("anl_")
    assert len(inspect_data["logic_steps"]) == 5
    assert len(inspect_data["logs"]) == 5


def test_analyze_and_inspect_share_single_service_method(monkeypatch) -> None:
    call_count = {"count": 0}

    def _fake_run_analyze_pipeline(request) -> AnalyzeInspectResponse:
        call_count["count"] += 1
        assert request.meeting_id == "m_12345"
        return AnalyzeInspectResponse(
            request_id="anl_test_001",
            result=_sample_result(),
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
    assert inspect_response.json()["result"] == analyze_response.json()


def test_analyze_inspect_returns_502_on_llm_failure(monkeypatch) -> None:
    def _raise_error(request) -> AnalyzeInspectResponse:
        _ = request
        raise AnalyzeInferenceError(stage="sentiment", message="forced failure")

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _raise_error)

    response = client.post("/api/v1/analyze/inspect", json=_payload())

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "error_code": "ANALYZE_LLM_FAILURE",
        "message_ko": "LLM 기반 analyze 추론에 실패했습니다.",
        "message_en": "Analyze inference failed from LLM service.",
        "stage": "sentiment",
    }


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
            result=_sample_result(),
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
    assert events[3][1]["result"] == _sample_result().model_dump(mode="json")


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
