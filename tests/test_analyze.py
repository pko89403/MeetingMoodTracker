from fastapi.testclient import TestClient

import app.runtime.analyze as analyze_runtime
from app.main import app
from app.service.analyze_service import AnalyzeInferenceError
from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeLogicStep,
)
from app.types.mood import AnalyzeResponse, AnalyzeSentiment, SentimentConfidence

client = TestClient(app)


def _payload() -> dict[str, str]:
    return {
        "meeting_id": "m_12345",
        "text": "오늘 회의에서는 새로운 서버 아키텍처와 예산 조정을 함께 논의했습니다.",
    }


def test_analyze_meeting_returns_pipeline_result(monkeypatch) -> None:
    def _fake_run_analyze_pipeline(request) -> AnalyzeInspectResponse:
        assert request.meeting_id == "m_12345"
        return AnalyzeInspectResponse(
            request_id="anl_test_001",
            result=AnalyzeResponse(
                topic="Architecture, Budget",
                sentiment=AnalyzeSentiment(
                    positive=SentimentConfidence(confidence=72),
                    negative=SentimentConfidence(confidence=10),
                    neutral=SentimentConfidence(confidence=18),
                ),
            ),
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
                    step_id="compose_response",
                    message_ko="응답 조합",
                    created_at="2026-03-30T00:00:00+00:00",
                )
            ],
        )

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _fake_run_analyze_pipeline)

    response = client.post("/api/v1/analyze", json=_payload())

    assert response.status_code == 200
    assert response.json() == {
        "topic": "Architecture, Budget",
        "sentiment": {
            "positive": {"confidence": 72},
            "negative": {"confidence": 10},
            "neutral": {"confidence": 18},
        },
    }


def test_analyze_meeting_returns_502_on_llm_failure(monkeypatch) -> None:
    def _raise_error(request) -> AnalyzeInspectResponse:
        _ = request
        raise AnalyzeInferenceError(stage="topic", message="failed")

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _raise_error)

    response = client.post("/api/v1/analyze", json=_payload())

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "error_code": "ANALYZE_LLM_FAILURE",
        "message_ko": "LLM 기반 analyze 추론에 실패했습니다.",
        "message_en": "Analyze inference failed from LLM service.",
        "stage": "topic",
    }
