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
        "text": "오늘 회의에서는 새로운 서버 아키텍처와 예산 조정을 함께 논의했습니다.",
    }


def _sample_result() -> AnalyzeResponse:
    return AnalyzeResponse(
        topic=AnalyzeTopic(
            primary="Architecture",
            candidates=[
                AnalyzeTopicCandidate(label="Architecture", confidence=82),
                AnalyzeTopicCandidate(label="Budget", confidence=64),
            ],
        ),
        sentiment=AnalyzeSentiment(
            distribution=AnalyzeSentimentDistribution(
                positive=63,
                negative=12,
                neutral=25,
            ),
            polarity="positive",
            confidence=63,
        ),
        emotion=AnalyzeEmotion(
            distribution=AnalyzeEmotionDistribution(
                anger=10,
                joy=35,
                sadness=5,
                neutral=10,
                anxiety=20,
                frustration=8,
                excitement=7,
                confusion=5,
            ),
            primary="joy",
            confidence=35,
        ),
        correlation=AnalyzeCorrelation(
            topic_sentiment=73,
            topic_emotion=59,
            sentiment_emotion=69,
            summary="주요 토픽과 감성/감정 사이에 중간 이상 상관이 관찰됩니다.",
        ),
    )


def test_analyze_meeting_returns_pipeline_result(monkeypatch) -> None:
    def _fake_run_analyze_pipeline(request) -> AnalyzeInspectResponse:
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
                    step_id="compose_response",
                    message_ko="응답 조합",
                    created_at="2026-03-30T00:00:00+00:00",
                )
            ],
        )

    monkeypatch.setattr(analyze_runtime, "run_analyze_pipeline", _fake_run_analyze_pipeline)

    response = client.post("/api/v1/analyze", json=_payload())

    assert response.status_code == 200
    assert response.json() == _sample_result().model_dump(mode="json")


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
