import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.runtime.meeting_reads as meeting_reads_runtime
from app.main import app
from app.service.meeting_read_service import (
    MeetingReadInferenceError,
    MeetingReadNotFoundError,
)
from app.types.emotion import (
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionResponse,
)
from app.types.mood import AnalyzeSentiment, SentimentConfidence
from app.types.sentiment import TurnSentimentResponse
from app.types.storage import (
    AgentAggregate,
    MeetingAgentsResponse,
    MeetingOverviewResponse,
    MeetingTurnsResponse,
    TurnAnalysisRecord,
)

client = TestClient(app)


def _overview() -> MeetingOverviewResponse:
    return MeetingOverviewResponse(
        project_id="project-alpha",
        meeting_id="meeting-001",
        created_at="2026-04-03T00:00:00+00:00",
        updated_at="2026-04-03T00:10:00+00:00",
        turn_count=2,
        agent_count=2,
        topics=["배포 일정", "QA 리스크"],
        sentiment=AnalyzeSentiment(
            positive=SentimentConfidence(confidence=55),
            negative=SentimentConfidence(confidence=25),
            neutral=SentimentConfidence(confidence=20),
        ),
        emotions=EmotionScores(
            anger=EmotionConfidenceValue(confidence=0),
            joy=EmotionConfidenceValue(confidence=50),
            sadness=EmotionConfidenceValue(confidence=0),
            neutral=EmotionConfidenceValue(confidence=30),
            anxiety=EmotionConfidenceValue(confidence=10),
            frustration=EmotionConfidenceValue(confidence=5),
            excitement=EmotionConfidenceValue(confidence=3),
            confusion=EmotionConfidenceValue(confidence=2),
        ),
        signals=MeetingSignals(
            tension=MeetingSignalConfidenceValue(confidence=18),
            alignment=MeetingSignalConfidenceValue(confidence=72),
            urgency=MeetingSignalConfidenceValue(confidence=64),
            clarity=MeetingSignalConfidenceValue(confidence=78),
            engagement=MeetingSignalConfidenceValue(confidence=70),
        ),
        one_line_summary="2개 발화에서 배포 일정, QA 리스크 중심으로 논의가 진행됐습니다.",
    )


def _turns() -> MeetingTurnsResponse:
    return MeetingTurnsResponse(
        project_id="project-alpha",
        meeting_id="meeting-001",
        total_count=1,
        turns=[
            TurnAnalysisRecord(
                project_id="project-alpha",
                meeting_id="meeting-001",
                agent_id="alice",
                turn_id="turn-001",
                utterance_text="QA를 먼저 정리하겠습니다.",
                created_at="2026-04-03T00:00:00+00:00",
                updated_at="2026-04-03T00:01:00+00:00",
                order=1,
                sentiment=TurnSentimentResponse(
                    label="NEUTRAL",
                    confidence=0.8,
                    evidence="QA",
                ),
                emotion=TurnEmotionResponse(
                    emotions=_overview().emotions,
                    meeting_signals=_overview().signals,
                    emerging_emotions=[],
                ),
            )
        ],
    )


def _agents() -> MeetingAgentsResponse:
    return MeetingAgentsResponse(
        project_id="project-alpha",
        meeting_id="meeting-001",
        total_count=1,
        agents=[
            AgentAggregate(
                project_id="project-alpha",
                meeting_id="meeting-001",
                agent_id="alice",
                turn_count=1,
                turn_ids=["turn-001"],
                avg_sentiment=AnalyzeSentiment(
                    positive=SentimentConfidence(confidence=0),
                    negative=SentimentConfidence(confidence=0),
                    neutral=SentimentConfidence(confidence=100),
                ),
                primary_emotion="joy",
                primary_signal="alignment",
                emerging_emotions=["optimism"],
            )
        ],
    )


def test_read_meeting_overview_returns_response(monkeypatch) -> None:
    async def _fake_get_meeting_overview(project_id: str, meeting_id: str):
        assert project_id == "project-alpha"
        assert meeting_id == "meeting-001"
        return _overview()

    monkeypatch.setattr(
        meeting_reads_runtime,
        "get_meeting_overview",
        _fake_get_meeting_overview,
    )

    response = client.get("/api/v1/projects/project-alpha/meetings/meeting-001")

    assert response.status_code == 200
    assert response.json() == _overview().model_dump(mode="json")


def test_read_meeting_turns_returns_response(monkeypatch) -> None:
    def _fake_get_meeting_turns(project_id: str, meeting_id: str):
        assert project_id == "project-alpha"
        assert meeting_id == "meeting-001"
        return _turns()

    monkeypatch.setattr(
        meeting_reads_runtime,
        "get_meeting_turns",
        _fake_get_meeting_turns,
    )

    response = client.get("/api/v1/projects/project-alpha/meetings/meeting-001/turns")

    assert response.status_code == 200
    assert response.json() == _turns().model_dump(mode="json")


def test_read_meeting_agents_returns_response(monkeypatch) -> None:
    def _fake_get_meeting_agents(project_id: str, meeting_id: str):
        assert project_id == "project-alpha"
        assert meeting_id == "meeting-001"
        return _agents()

    monkeypatch.setattr(
        meeting_reads_runtime,
        "get_meeting_agents",
        _fake_get_meeting_agents,
    )

    response = client.get("/api/v1/projects/project-alpha/meetings/meeting-001/agents")

    assert response.status_code == 200
    assert response.json() == _agents().model_dump(mode="json")


def test_read_meeting_overview_returns_502_on_topic_failure(monkeypatch) -> None:
    async def _raise_error(project_id: str, meeting_id: str):
        _ = (project_id, meeting_id)
        raise MeetingReadInferenceError(stage="topic", message="boom")

    monkeypatch.setattr(
        meeting_reads_runtime,
        "get_meeting_overview",
        _raise_error,
    )

    response = client.get("/api/v1/projects/project-alpha/meetings/meeting-001")

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "error_code": "MEETING_READ_LLM_FAILURE",
        "message_ko": "회의 overview aggregate 계산에 실패했습니다.",
        "message_en": "Meeting overview aggregate inference failed.",
        "stage": "topic",
    }


def test_read_meeting_turns_returns_404_on_missing_meeting(monkeypatch) -> None:
    def _raise_not_found(project_id: str, meeting_id: str):
        _ = (project_id, meeting_id)
        raise MeetingReadNotFoundError("missing")

    monkeypatch.setattr(
        meeting_reads_runtime,
        "get_meeting_turns",
        _raise_not_found,
    )

    response = client.get("/api/v1/projects/project-alpha/meetings/meeting-404/turns")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "MEETING_NOT_FOUND"


@pytest.mark.asyncio
async def test_read_meeting_agents_returns_422_on_invalid_storage_identifier() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await meeting_reads_runtime.read_meeting_agents(
            project_id="..",
            meeting_id="meeting-001",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error_code"] == "INVALID_STORAGE_IDENTIFIER"
