import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.runtime.meeting_turns as meeting_turns_runtime
from app.main import app
from app.service.turn_ingest_service import TurnIngestInferenceError
from app.types.emotion import (
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionResponse,
)
from app.types.sentiment import TurnSentimentResponse
from app.types.storage import TurnAnalysisRecord

client = TestClient(app)


def _payload() -> dict[str, object]:
    return {
        "agent_id": "alice",
        "turn_id": "turn-001",
        "utterance_text": "QA를 한 번 더 확인하고 배포합시다.",
        "order": 1,
    }


def _sample_result() -> TurnAnalysisRecord:
    return TurnAnalysisRecord(
        project_id="project-alpha",
        meeting_id="meeting-001",
        agent_id="alice",
        turn_id="turn-001",
        utterance_text="QA를 한 번 더 확인하고 배포합시다.",
        created_at="2026-04-03T00:00:00+00:00",
        updated_at="2026-04-03T00:01:00+00:00",
        order=1,
        sentiment=TurnSentimentResponse(
            label="NEUTRAL",
            confidence=0.81,
            evidence="QA를 한 번 더 확인",
        ),
        emotion=TurnEmotionResponse(
            emotions=EmotionScores(
                anger=EmotionConfidenceValue(confidence=0),
                joy=EmotionConfidenceValue(confidence=10),
                sadness=EmotionConfidenceValue(confidence=0),
                neutral=EmotionConfidenceValue(confidence=50),
                anxiety=EmotionConfidenceValue(confidence=15),
                frustration=EmotionConfidenceValue(confidence=5),
                excitement=EmotionConfidenceValue(confidence=5),
                confusion=EmotionConfidenceValue(confidence=15),
            ),
            meeting_signals=MeetingSignals(
                tension=MeetingSignalConfidenceValue(confidence=20),
                alignment=MeetingSignalConfidenceValue(confidence=75),
                urgency=MeetingSignalConfidenceValue(confidence=60),
                clarity=MeetingSignalConfidenceValue(confidence=80),
                engagement=MeetingSignalConfidenceValue(confidence=65),
            ),
            emerging_emotions=[],
        ),
    )


def test_ingest_meeting_turn_returns_saved_record(monkeypatch) -> None:
    async def _fake_store_turn_analysis(
        project_id: str,
        meeting_id: str,
        request,
    ) -> TurnAnalysisRecord:
        assert project_id == "project-alpha"
        assert meeting_id == "meeting-001"
        assert request.agent_id == "alice"
        return _sample_result()

    monkeypatch.setattr(
        meeting_turns_runtime,
        "store_turn_analysis",
        _fake_store_turn_analysis,
    )

    response = client.post(
        "/api/v1/projects/project-alpha/meetings/meeting-001/turns",
        json=_payload(),
    )

    assert response.status_code == 200
    assert response.json() == _sample_result().model_dump(mode="json")


def test_ingest_meeting_turn_returns_502_on_inference_failure(monkeypatch) -> None:
    async def _raise_error(
        project_id: str,
        meeting_id: str,
        request,
    ) -> TurnAnalysisRecord:
        _ = (project_id, meeting_id, request)
        raise TurnIngestInferenceError(stage="emotion", message="boom")

    monkeypatch.setattr(
        meeting_turns_runtime,
        "store_turn_analysis",
        _raise_error,
    )

    response = client.post(
        "/api/v1/projects/project-alpha/meetings/meeting-001/turns",
        json=_payload(),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "error_code": "TURN_ANALYSIS_LLM_FAILURE",
        "message_ko": "LLM 기반 턴 분석 저장에 실패했습니다.",
        "message_en": "Turn analysis persistence failed from LLM service.",
        "stage": "emotion",
    }


@pytest.mark.asyncio
async def test_ingest_meeting_turn_returns_422_on_invalid_storage_identifier() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await meeting_turns_runtime.ingest_meeting_turn(
            project_id="..",
            meeting_id="meeting-001",
            request=meeting_turns_runtime.TurnIngestRequest.model_validate(_payload()),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error_code"] == "INVALID_STORAGE_IDENTIFIER"
