import json

from app.repo.meeting_storage import JsonTurnAnalysisRepository
from app.types.emotion import (
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionResponse,
)
from app.types.sentiment import TurnSentimentResponse
from app.types.storage import UNASSIGNED_AGENT_ID, TurnAnalysisRecord, TurnIdentity


def _sample_record(*, created_at: str, evidence: str) -> TurnAnalysisRecord:
    return TurnAnalysisRecord(
        project_id="project-alpha",
        meeting_id="meeting-001",
        agent_id="alice",
        turn_id="turn-001",
        utterance_text="좋아요. 이 방향으로 갑시다.",
        created_at=created_at,
        updated_at=created_at,
        order=1,
        sentiment=TurnSentimentResponse(
            label="POS",
            confidence=0.91,
            evidence=evidence,
        ),
        emotion=TurnEmotionResponse(
            emotions=EmotionScores(
                anger=EmotionConfidenceValue(confidence=0),
                joy=EmotionConfidenceValue(confidence=70),
                sadness=EmotionConfidenceValue(confidence=0),
                neutral=EmotionConfidenceValue(confidence=10),
                anxiety=EmotionConfidenceValue(confidence=5),
                frustration=EmotionConfidenceValue(confidence=5),
                excitement=EmotionConfidenceValue(confidence=5),
                confusion=EmotionConfidenceValue(confidence=5),
            ),
            meeting_signals=MeetingSignals(
                tension=MeetingSignalConfidenceValue(confidence=10),
                alignment=MeetingSignalConfidenceValue(confidence=90),
                urgency=MeetingSignalConfidenceValue(confidence=20),
                clarity=MeetingSignalConfidenceValue(confidence=80),
                engagement=MeetingSignalConfidenceValue(confidence=75),
            ),
            emerging_emotions=[],
        ),
    )


def test_upsert_turn_analysis_creates_project_hierarchy_files(tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")

    saved = repository.upsert_turn_analysis(
        _sample_record(
            created_at="2026-04-03T00:00:00+00:00",
            evidence="좋아요",
        )
    )

    project_meta_path = tmp_path / "projects" / "project-alpha" / "meta.json"
    meeting_meta_path = (
        tmp_path / "projects" / "project-alpha" / "meetings" / "meeting-001" / "meta.json"
    )
    turns_path = (
        tmp_path
        / "projects"
        / "project-alpha"
        / "meetings"
        / "meeting-001"
        / "agents"
        / "alice"
        / "turns.json"
    )

    assert saved.turn_id == "turn-001"
    assert project_meta_path.exists()
    assert meeting_meta_path.exists()
    assert turns_path.exists()

    project_meta = json.loads(project_meta_path.read_text("utf-8"))
    meeting_meta = json.loads(meeting_meta_path.read_text("utf-8"))
    turns_document = json.loads(turns_path.read_text("utf-8"))
    saved_project_meta = repository.get_project_meta(project_id="project-alpha")
    saved_meeting_meta = repository.get_meeting_meta(
        project_id="project-alpha",
        meeting_id="meeting-001",
    )

    assert project_meta["meeting_count"] == 1
    assert meeting_meta["turn_count"] == 1
    assert meeting_meta["agent_ids"] == ["alice"]
    assert turns_document["turns"][0]["sentiment"]["evidence"] == "좋아요"
    assert turns_document["turns"][0]["updated_at"] != ""
    assert saved_project_meta is not None
    assert saved_project_meta.meeting_count == 1
    assert saved_meeting_meta is not None
    assert saved_meeting_meta.turn_count == 1


def test_upsert_turn_analysis_is_idempotent_for_same_agent_and_turn(tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")
    first = _sample_record(
        created_at="2026-04-03T00:00:00+00:00",
        evidence="좋아요",
    )
    second = _sample_record(
        created_at="2026-04-03T00:05:00+00:00",
        evidence="매우 좋아요",
    )

    repository.upsert_turn_analysis(first)
    saved = repository.upsert_turn_analysis(second)

    meeting_meta_path = (
        tmp_path / "projects" / "project-alpha" / "meetings" / "meeting-001" / "meta.json"
    )
    turns_path = (
        tmp_path
        / "projects"
        / "project-alpha"
        / "meetings"
        / "meeting-001"
        / "agents"
        / "alice"
        / "turns.json"
    )

    meeting_meta = json.loads(meeting_meta_path.read_text("utf-8"))
    turns_document = json.loads(turns_path.read_text("utf-8"))

    assert saved.created_at == "2026-04-03T00:00:00+00:00"
    assert saved.updated_at != "2026-04-03T00:00:00+00:00"
    assert meeting_meta["turn_count"] == 1
    assert len(turns_document["turns"]) == 1
    assert turns_document["turns"][0]["sentiment"]["evidence"] == "매우 좋아요"


def test_upsert_turn_analysis_tracks_unassigned_agent_bucket(tmp_path) -> None:
    repository = JsonTurnAnalysisRepository(data_root=tmp_path / "projects")
    record = _sample_record(
        created_at="2026-04-03T00:00:00+00:00",
        evidence="좋아요",
    ).model_copy(update={"agent_id": None, "turn_id": "turn-002"})

    repository.upsert_turn_analysis(record)
    saved = repository.get_turn_analysis(
        TurnIdentity(
            project_id="project-alpha",
            meeting_id="meeting-001",
            agent_id=None,
            turn_id="turn-002",
        )
    )

    turns_path = (
        tmp_path
        / "projects"
        / "project-alpha"
        / "meetings"
        / "meeting-001"
        / "agents"
        / UNASSIGNED_AGENT_ID
        / "turns.json"
    )
    meeting_meta_path = (
        tmp_path / "projects" / "project-alpha" / "meetings" / "meeting-001" / "meta.json"
    )
    meeting_meta = json.loads(meeting_meta_path.read_text("utf-8"))

    assert turns_path.exists()
    assert saved is not None
    assert saved.agent_id is None
    assert meeting_meta["agent_ids"] == [UNASSIGNED_AGENT_ID]
