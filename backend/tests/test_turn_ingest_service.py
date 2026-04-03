import pytest

import app.service.turn_ingest_service as turn_ingest_service
from app.service.turn_ingest_service import (
    store_turn_analysis,
)
from app.types.emotion import (
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionResponse,
)
from app.types.sentiment import TurnSentimentResponse
from app.types.storage import TurnAnalysisRecord, TurnIngestRequest


class _FakeRepository:
    def __init__(self) -> None:
        self.saved_record: TurnAnalysisRecord | None = None

    def upsert_turn_analysis(self, record: TurnAnalysisRecord) -> TurnAnalysisRecord:
        self.saved_record = record
        return record


def _sample_sentiment() -> TurnSentimentResponse:
    return TurnSentimentResponse(
        label="POS",
        confidence=0.87,
        evidence="좋은 접근",
    )


def _sample_emotion() -> TurnEmotionResponse:
    return TurnEmotionResponse(
        emotions=EmotionScores(
            anger=EmotionConfidenceValue(confidence=5),
            joy=EmotionConfidenceValue(confidence=60),
            sadness=EmotionConfidenceValue(confidence=0),
            neutral=EmotionConfidenceValue(confidence=10),
            anxiety=EmotionConfidenceValue(confidence=10),
            frustration=EmotionConfidenceValue(confidence=5),
            excitement=EmotionConfidenceValue(confidence=5),
            confusion=EmotionConfidenceValue(confidence=5),
        ),
        meeting_signals=MeetingSignals(
            tension=MeetingSignalConfidenceValue(confidence=10),
            alignment=MeetingSignalConfidenceValue(confidence=90),
            urgency=MeetingSignalConfidenceValue(confidence=30),
            clarity=MeetingSignalConfidenceValue(confidence=80),
            engagement=MeetingSignalConfidenceValue(confidence=70),
        ),
        emerging_emotions=[],
    )


@pytest.mark.asyncio
async def test_store_turn_analysis_persists_project_aware_record(monkeypatch) -> None:
    captured_requests: dict[str, object] = {}
    fake_repository = _FakeRepository()

    def _fake_classify_turn_sentiment(request) -> TurnSentimentResponse:
        captured_requests["sentiment"] = request
        return _sample_sentiment()

    async def _fake_classify_turn_emotion(request) -> TurnEmotionResponse:
        captured_requests["emotion"] = request
        return _sample_emotion()

    monkeypatch.setattr(
        turn_ingest_service,
        "classify_turn_sentiment",
        _fake_classify_turn_sentiment,
    )
    monkeypatch.setattr(
        turn_ingest_service,
        "classify_turn_emotion",
        _fake_classify_turn_emotion,
    )

    result = await store_turn_analysis(
        project_id="project-alpha",
        meeting_id="meeting-001",
        request=TurnIngestRequest(
            agent_id="alice",
            turn_id="turn-001",
            utterance_text="이 접근으로 진행하면 좋겠습니다.",
            order=1,
        ),
        repository=fake_repository,
    )

    assert result.project_id == "project-alpha"
    assert result.meeting_id == "meeting-001"
    assert result.agent_id == "alice"
    assert result.turn_id == "turn-001"
    assert result.order == 1
    assert result.updated_at != ""
    assert fake_repository.saved_record == result
    assert captured_requests["sentiment"].agent_id == "alice"
    assert captured_requests["emotion"].agent_id == "alice"


@pytest.mark.asyncio
async def test_store_turn_analysis_preserves_missing_agent_id_for_repository_boundary(
    monkeypatch,
) -> None:
    fake_repository = _FakeRepository()

    monkeypatch.setattr(
        turn_ingest_service,
        "classify_turn_sentiment",
        lambda request: _sample_sentiment(),
    )

    async def _fake_classify_turn_emotion(request) -> TurnEmotionResponse:
        return _sample_emotion()

    monkeypatch.setattr(
        turn_ingest_service,
        "classify_turn_emotion",
        _fake_classify_turn_emotion,
    )

    result = await store_turn_analysis(
        project_id="project-alpha",
        meeting_id="meeting-001",
        request=TurnIngestRequest(
            agent_id=None,
            turn_id="turn-002",
            utterance_text="담당자를 아직 지정하지 않았습니다.",
            order=2,
        ),
        repository=fake_repository,
    )

    assert result.agent_id is None


def test_turn_ingest_request_accepts_blank_legacy_speaker_id_as_unassigned() -> None:
    request = TurnIngestRequest.model_validate(
        {
            "speaker_id": "   ",
            "turn_id": "turn-003",
            "utterance_text": "담당자 미정 상태입니다.",
            "order": 3,
        }
    )

    assert request.agent_id is None
