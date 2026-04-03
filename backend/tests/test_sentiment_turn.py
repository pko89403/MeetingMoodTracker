from fastapi.testclient import TestClient

import app.runtime.sentiment as sentiment_runtime
from app.main import app
from app.service.sentiment_service import SentimentInferenceError
from app.types.sentiment import TurnSentimentResponse

client = TestClient(app)


def test_turn_sentiment_endpoint_success_with_mixed_language(monkeypatch) -> None:
    def _fake_classify_turn_sentiment(
        request,
    ) -> TurnSentimentResponse:
        assert request.meeting_id == "m_001"
        assert request.turn_id == "t_001"
        return TurnSentimentResponse(
            label="POS",
            confidence=0.93,
            evidence="좋은 접근 같아요 let's proceed",
        )

    monkeypatch.setattr(
        sentiment_runtime,
        "classify_turn_sentiment",
        _fake_classify_turn_sentiment,
    )

    response = client.post(
        "/api/v1/sentiment/turn",
        json={
            "meeting_id": "m_001",
            "turn_id": "t_001",
            "agent_id": "alice",
            "utterance_text": "좋은 접근 같아요, let's proceed.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "label": "POS",
        "confidence": 0.93,
        "evidence": "좋은 접근 같아요 let's proceed",
    }


def test_turn_sentiment_endpoint_returns_422_on_empty_utterance() -> None:
    response = client.post(
        "/api/v1/sentiment/turn",
        json={
            "meeting_id": "m_001",
            "turn_id": "t_001",
            "agent_id": "alice",
            "utterance_text": "",
        },
    )

    assert response.status_code == 422


def test_turn_sentiment_endpoint_returns_502_on_inference_failure(
    monkeypatch,
) -> None:
    def _raise_sentiment_error(request) -> TurnSentimentResponse:
        assert request.turn_id == "t_001"
        raise SentimentInferenceError("boom")

    monkeypatch.setattr(
        sentiment_runtime,
        "classify_turn_sentiment",
        _raise_sentiment_error,
    )

    response = client.post(
        "/api/v1/sentiment/turn",
        json={
            "meeting_id": "m_001",
            "turn_id": "t_001",
            "agent_id": "alice",
            "utterance_text": "이건 별로예요.",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error_code"] == "SENTIMENT_LLM_FAILURE"
    assert (
        response.json()["detail"]["message_ko"]
        == "LLM 감정분류 서비스 호출에 실패했습니다."
    )
