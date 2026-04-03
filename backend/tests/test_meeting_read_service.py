import pytest

from app.repo.meeting_storage import JsonTurnAnalysisRepository
from app.service import meeting_read_service
from app.types.emotion import (
    EmergingEmotion,
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionResponse,
)
from app.types.sentiment import TurnSentimentResponse
from app.types.storage import TurnAnalysisRecord


def _record(
    *,
    agent_id: str | None,
    turn_id: str,
    order: int,
    utterance_text: str,
    sentiment_label: str,
    sentiment_confidence: float,
    joy: int,
    neutral: int,
    alignment: int,
    urgency: int,
    emerging_labels: list[str] | None = None,
) -> TurnAnalysisRecord:
    labels = emerging_labels or []
    return TurnAnalysisRecord(
        project_id="project-alpha",
        meeting_id="meeting-001",
        agent_id=agent_id,
        turn_id=turn_id,
        utterance_text=utterance_text,
        created_at=f"2026-04-03T00:0{order}:00+00:00",
        updated_at=f"2026-04-03T00:0{order}:00+00:00",
        order=order,
        sentiment=TurnSentimentResponse(
            label=sentiment_label,
            confidence=sentiment_confidence,
            evidence=utterance_text[:8],
        ),
        emotion=TurnEmotionResponse(
            emotions=EmotionScores(
                anger=EmotionConfidenceValue(confidence=0),
                joy=EmotionConfidenceValue(confidence=joy),
                sadness=EmotionConfidenceValue(confidence=0),
                neutral=EmotionConfidenceValue(confidence=neutral),
                anxiety=EmotionConfidenceValue(confidence=10),
                frustration=EmotionConfidenceValue(confidence=5),
                excitement=EmotionConfidenceValue(confidence=10),
                confusion=EmotionConfidenceValue(confidence=5),
            ),
            meeting_signals=MeetingSignals(
                tension=MeetingSignalConfidenceValue(confidence=10),
                alignment=MeetingSignalConfidenceValue(confidence=alignment),
                urgency=MeetingSignalConfidenceValue(confidence=urgency),
                clarity=MeetingSignalConfidenceValue(confidence=70),
                engagement=MeetingSignalConfidenceValue(confidence=65),
            ),
            emerging_emotions=[
                EmergingEmotion(label=label, confidence=70 - index * 10)
                for index, label in enumerate(labels)
            ],
        ),
    )


@pytest.mark.asyncio
async def test_get_meeting_overview_aggregates_topics_and_scores(monkeypatch, tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")
    repository.upsert_turn_analysis(
        _record(
            agent_id="alice",
            turn_id="turn-001",
            order=1,
            utterance_text="배포 일정과 QA 리스크를 정리합시다.",
            sentiment_label="POS",
            sentiment_confidence=0.9,
            joy=70,
            neutral=20,
            alignment=85,
            urgency=55,
            emerging_labels=["optimism"],
        )
    )
    repository.upsert_turn_analysis(
        _record(
            agent_id="bob",
            turn_id="turn-002",
            order=2,
            utterance_text="QA 누락이 다시 생기면 일정이 밀릴 수 있어요.",
            sentiment_label="NEG",
            sentiment_confidence=0.6,
            joy=20,
            neutral=40,
            alignment=45,
            urgency=80,
            emerging_labels=["concern"],
        )
    )

    async def _fake_extract_topics(text: str) -> list[str]:
        assert "배포 일정" in text
        return ["배포 일정", "QA 리스크"]

    monkeypatch.setattr(meeting_read_service, "extract_meeting_topics", _fake_extract_topics)

    overview = await meeting_read_service.get_meeting_overview(
        project_id="project-alpha",
        meeting_id="meeting-001",
        repository=repository,
    )

    assert overview.turn_count == 2
    assert overview.agent_count == 2
    assert overview.topics == ["배포 일정", "QA 리스크"]
    assert overview.sentiment.positive.confidence == 60
    assert overview.sentiment.negative.confidence == 40
    assert overview.sentiment.neutral.confidence == 0
    assert overview.emotions.joy.confidence == 45
    assert overview.signals.urgency.confidence == 68
    assert overview.rubric.dominance == 63
    assert overview.rubric.efficiency == 78
    assert overview.rubric.cohesion == 66
    assert overview.one_line_summary == "2개 발화에서 배포 일정, QA 리스크 중심으로 논의가 진행됐습니다."


def test_get_meeting_agents_builds_agent_summaries(tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")
    repository.upsert_turn_analysis(
        _record(
            agent_id="alice",
            turn_id="turn-001",
            order=1,
            utterance_text="QA 리스크를 먼저 정리하겠습니다.",
            sentiment_label="POS",
            sentiment_confidence=0.8,
            joy=65,
            neutral=20,
            alignment=90,
            urgency=40,
            emerging_labels=["optimism"],
        )
    )
    repository.upsert_turn_analysis(
        _record(
            agent_id="alice",
            turn_id="turn-003",
            order=3,
            utterance_text="남은 이슈는 제가 정리해서 공유할게요.",
            sentiment_label="NEUTRAL",
            sentiment_confidence=0.7,
            joy=55,
            neutral=30,
            alignment=80,
            urgency=35,
            emerging_labels=["relief"],
        )
    )
    repository.upsert_turn_analysis(
        _record(
            agent_id=None,
            turn_id="turn-002",
            order=2,
            utterance_text="일정 압박이 커지고 있습니다.",
            sentiment_label="NEG",
            sentiment_confidence=0.9,
            joy=10,
            neutral=25,
            alignment=20,
            urgency=95,
            emerging_labels=["concern"],
        )
    )

    response = meeting_read_service.get_meeting_agents(
        project_id="project-alpha",
        meeting_id="meeting-001",
        repository=repository,
    )

    assert response.total_count == 2
    assert response.agents[0].agent_id == "alice"
    assert response.agents[0].turn_count == 2
    assert response.agents[0].turn_ids == ["turn-001", "turn-003"]
    assert response.agents[0].primary_emotion == "joy"
    assert response.agents[0].primary_signal == "alignment"
    assert response.agents[0].emerging_emotions == ["optimism", "relief"]
    assert response.agents[1].agent_id is None
    assert response.agents[1].primary_signal == "urgency"


def test_get_meeting_turns_returns_sorted_turns(tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")
    repository.upsert_turn_analysis(
        _record(
            agent_id="bob",
            turn_id="turn-002",
            order=2,
            utterance_text="두 번째 발화입니다.",
            sentiment_label="NEG",
            sentiment_confidence=0.6,
            joy=5,
            neutral=60,
            alignment=30,
            urgency=70,
        )
    )
    repository.upsert_turn_analysis(
        _record(
            agent_id="alice",
            turn_id="turn-001",
            order=1,
            utterance_text="첫 번째 발화입니다.",
            sentiment_label="POS",
            sentiment_confidence=0.7,
            joy=70,
            neutral=20,
            alignment=90,
            urgency=40,
        )
    )

    response = meeting_read_service.get_meeting_turns(
        project_id="project-alpha",
        meeting_id="meeting-001",
        repository=repository,
    )

    assert response.total_count == 2
    assert [turn.turn_id for turn in response.turns] == ["turn-001", "turn-002"]
    assert response.turns[0].rubric is not None
    assert response.turns[0].rubric.dominance == 59
    assert response.turns[0].rubric.efficiency == 60
    assert response.turns[0].rubric.cohesion == 78
    assert response.turns[1].rubric is not None
    assert response.turns[1].rubric.dominance == 55
    assert response.turns[1].rubric.efficiency == 69
    assert response.turns[1].rubric.cohesion == 40


@pytest.mark.asyncio
async def test_get_meeting_overview_raises_not_found_for_missing_meeting(tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")

    with pytest.raises(meeting_read_service.MeetingReadNotFoundError):
        await meeting_read_service.get_meeting_overview(
            project_id="project-alpha",
            meeting_id="meeting-404",
            repository=repository,
        )
