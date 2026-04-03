"""실제 LLM 분석 결과를 고정 fixture 회의 데이터로 시드한다."""

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

from app.config.storage import get_projects_data_root
from app.types.identifiers import normalize_storage_segment
from app.types.storage import (
    AgentTurnsDocument,
    MeetingMeta,
    ProjectMeta,
    TurnAnalysisRecord,
)

FIXTURE_PROJECT_ID = "project-frontend-demo"
FIXTURE_MEETING_ID = "meeting-issue27-short-live"
FIXTURE_CREATED_AT = "2026-04-03T01:35:30.772795+00:00"
FIXTURE_UPDATED_AT = "2026-04-03T01:36:02.401998+00:00"
FIXTURE_AGENT_IDS = ["alice", "bob", "carol"]
FIXTURE_TURNS: list[dict[str, object]] = [
    {
        "project_id": "project-alpha",
        "meeting_id": "meeting-issue27-short-live",
        "agent_id": "alice",
        "turn_id": "turn-001",
        "utterance_text": "오늘은 금요일 배포 전에 QA 리스크와 일정 상태를 짧게 점검합시다.",
        "created_at": "2026-04-03T01:35:30.772570+00:00",
        "order": 1,
        "updated_at": "2026-04-03T01:35:30.772795+00:00",
        "sentiment": {
            "label": "POS",
            "confidence": 0.92,
            "evidence": "짧게 점검합시다",
        },
        "emotion": {
            "emotions": {
                "anger": {"confidence": 2},
                "joy": {"confidence": 5},
                "sadness": {"confidence": 2},
                "neutral": {"confidence": 85},
                "anxiety": {"confidence": 10},
                "frustration": {"confidence": 5},
                "excitement": {"confidence": 8},
                "confusion": {"confidence": 5},
            },
            "meeting_signals": {
                "tension": {"confidence": 20},
                "alignment": {"confidence": 80},
                "urgency": {"confidence": 60},
                "clarity": {"confidence": 85},
                "engagement": {"confidence": 70},
            },
            "emerging_emotions": [
                {"label": "concern", "confidence": 55},
                {"label": "optimism", "confidence": 25},
            ],
        },
    },
    {
        "project_id": "project-alpha",
        "meeting_id": "meeting-issue27-short-live",
        "agent_id": "bob",
        "turn_id": "turn-002",
        "utterance_text": "핵심 기능은 준비됐지만 회귀 테스트가 아직 70퍼센트 정도만 끝났어요.",
        "created_at": "2026-04-03T01:35:37.076439+00:00",
        "order": 2,
        "updated_at": "2026-04-03T01:35:37.076605+00:00",
        "sentiment": {
            "label": "NEUTRAL",
            "confidence": 0.76,
            "evidence": "회귀 테스트가 아직 70퍼센트 정도만 끝났어요.",
        },
        "emotion": {
            "emotions": {
                "anger": {"confidence": 5},
                "joy": {"confidence": 10},
                "sadness": {"confidence": 15},
                "neutral": {"confidence": 50},
                "anxiety": {"confidence": 65},
                "frustration": {"confidence": 55},
                "excitement": {"confidence": 20},
                "confusion": {"confidence": 10},
            },
            "meeting_signals": {
                "tension": {"confidence": 45},
                "alignment": {"confidence": 60},
                "urgency": {"confidence": 75},
                "clarity": {"confidence": 70},
                "engagement": {"confidence": 55},
            },
            "emerging_emotions": [
                {"label": "concern", "confidence": 70},
                {"label": "impatience", "confidence": 45},
            ],
        },
    },
    {
        "project_id": "project-alpha",
        "meeting_id": "meeting-issue27-short-live",
        "agent_id": "carol",
        "turn_id": "turn-003",
        "utterance_text": "로그인 관련 이슈는 해결됐고 남은 건 결제 플로우 수동 검증입니다.",
        "created_at": "2026-04-03T01:35:43.476520+00:00",
        "order": 3,
        "updated_at": "2026-04-03T01:35:43.476805+00:00",
        "sentiment": {
            "label": "NEUTRAL",
            "confidence": 0.78,
            "evidence": "로그인 관련 이슈는 해결됐고",
        },
        "emotion": {
            "emotions": {
                "anger": {"confidence": 2},
                "joy": {"confidence": 10},
                "sadness": {"confidence": 3},
                "neutral": {"confidence": 70},
                "anxiety": {"confidence": 8},
                "frustration": {"confidence": 5},
                "excitement": {"confidence": 12},
                "confusion": {"confidence": 5},
            },
            "meeting_signals": {
                "tension": {"confidence": 15},
                "alignment": {"confidence": 75},
                "urgency": {"confidence": 40},
                "clarity": {"confidence": 80},
                "engagement": {"confidence": 50},
            },
            "emerging_emotions": [
                {"label": "relief", "confidence": 65},
            ],
        },
    },
    {
        "project_id": "project-alpha",
        "meeting_id": "meeting-issue27-short-live",
        "agent_id": "alice",
        "turn_id": "turn-004",
        "utterance_text": "좋아요. 그러면 결제 검증을 오늘 오후 안에 마치고 저녁에 배포 여부를 확정하죠.",
        "created_at": "2026-04-03T01:35:49.689951+00:00",
        "order": 4,
        "updated_at": "2026-04-03T01:35:49.690479+00:00",
        "sentiment": {
            "label": "POS",
            "confidence": 0.95,
            "evidence": "좋아요.",
        },
        "emotion": {
            "emotions": {
                "anger": {"confidence": 5},
                "joy": {"confidence": 20},
                "sadness": {"confidence": 5},
                "neutral": {"confidence": 65},
                "anxiety": {"confidence": 25},
                "frustration": {"confidence": 15},
                "excitement": {"confidence": 30},
                "confusion": {"confidence": 10},
            },
            "meeting_signals": {
                "tension": {"confidence": 30},
                "alignment": {"confidence": 75},
                "urgency": {"confidence": 85},
                "clarity": {"confidence": 70},
                "engagement": {"confidence": 60},
            },
            "emerging_emotions": [
                {"label": "concern", "confidence": 40},
                {"label": "impatience", "confidence": 35},
                {"label": "relief", "confidence": 20},
            ],
        },
    },
    {
        "project_id": "project-alpha",
        "meeting_id": "meeting-issue27-short-live",
        "agent_id": "bob",
        "turn_id": "turn-005",
        "utterance_text": "가능합니다. 다만 실패 케이스 두 개만 더 확인하면 마음이 놓일 것 같습니다.",
        "created_at": "2026-04-03T01:35:57.350963+00:00",
        "order": 5,
        "updated_at": "2026-04-03T01:35:57.351586+00:00",
        "sentiment": {
            "label": "POS",
            "confidence": 0.9,
            "evidence": "마음이 놓일 것 같습니다.",
        },
        "emotion": {
            "emotions": {
                "anger": {"confidence": 5},
                "joy": {"confidence": 10},
                "sadness": {"confidence": 5},
                "neutral": {"confidence": 40},
                "anxiety": {"confidence": 60},
                "frustration": {"confidence": 30},
                "excitement": {"confidence": 10},
                "confusion": {"confidence": 20},
            },
            "meeting_signals": {
                "tension": {"confidence": 45},
                "alignment": {"confidence": 65},
                "urgency": {"confidence": 55},
                "clarity": {"confidence": 60},
                "engagement": {"confidence": 70},
            },
            "emerging_emotions": [
                {"label": "concern", "confidence": 70},
                {"label": "doubt", "confidence": 40},
            ],
        },
    },
    {
        "project_id": "project-alpha",
        "meeting_id": "meeting-issue27-short-live",
        "agent_id": "carol",
        "turn_id": "turn-006",
        "utterance_text": "그 두 케이스는 제가 바로 확인하고 결과를 채널에 공유하겠습니다.",
        "created_at": "2026-04-03T01:36:02.401817+00:00",
        "order": 6,
        "updated_at": "2026-04-03T01:36:02.401998+00:00",
        "sentiment": {
            "label": "POS",
            "confidence": 0.9,
            "evidence": "바로 확인하고 결과를 채널에 공유하겠습니다.",
        },
        "emotion": {
            "emotions": {
                "anger": {"confidence": 2},
                "joy": {"confidence": 25},
                "sadness": {"confidence": 3},
                "neutral": {"confidence": 70},
                "anxiety": {"confidence": 5},
                "frustration": {"confidence": 4},
                "excitement": {"confidence": 10},
                "confusion": {"confidence": 3},
            },
            "meeting_signals": {
                "tension": {"confidence": 10},
                "alignment": {"confidence": 80},
                "urgency": {"confidence": 50},
                "clarity": {"confidence": 85},
                "engagement": {"confidence": 60},
            },
            "emerging_emotions": [
                {"label": "relief", "confidence": 30},
            ],
        },
    },
]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    """부모 디렉터리를 생성한 뒤 JSON 파일을 UTF-8로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _target_paths(project_id: str, meeting_id: str) -> tuple[Path, Path, Path]:
    """project/meeting fixture가 기록될 디렉터리와 메타 파일 경로를 계산한다."""
    projects_root = get_projects_data_root()
    project_dir = projects_root / project_id
    meeting_dir = project_dir / "meetings" / meeting_id
    return project_dir, meeting_dir, project_dir / "meta.json"


def _build_turn_records(project_id: str, meeting_id: str) -> list[TurnAnalysisRecord]:
    """고정 fixture turn payload를 target project/meeting ID로 치환해 검증한다."""
    records: list[TurnAnalysisRecord] = []
    for payload in FIXTURE_TURNS:
        resolved_payload = {
            **payload,
            "project_id": project_id,
            "meeting_id": meeting_id,
        }
        records.append(TurnAnalysisRecord.model_validate(resolved_payload))
    return records


def _build_agent_documents(
    project_id: str,
    meeting_id: str,
    turn_records: list[TurnAnalysisRecord],
) -> list[AgentTurnsDocument]:
    """턴 레코드를 agent별 turns.json 문서로 묶는다."""
    grouped_turns: dict[str, list[TurnAnalysisRecord]] = defaultdict(list)
    for record in turn_records:
        grouped_turns[record.storage_agent_id()].append(record)

    documents: list[AgentTurnsDocument] = []
    for agent_id in FIXTURE_AGENT_IDS:
        agent_turns = grouped_turns[agent_id]
        if not agent_turns:
            raise ValueError(
                f"FIXTURE_AGENT_IDS contains '{agent_id}' but FIXTURE_TURNS has no turns for it."
            )
        updated_at = agent_turns[-1].updated_at
        documents.append(
            AgentTurnsDocument(
                project_id=project_id,
                meeting_id=meeting_id,
                agent_id=agent_id,
                updated_at=updated_at,
                turns=agent_turns,
            )
        )
    return documents


def _load_existing_project_created_at(project_meta_path: Path) -> str:
    """기존 project meta가 있으면 created_at을 보존한다."""
    if not project_meta_path.exists():
        return FIXTURE_CREATED_AT
    payload = json.loads(project_meta_path.read_text("utf-8"))
    project_meta = ProjectMeta.model_validate(payload)
    return project_meta.created_at


def seed_demo_meeting(project_id: str, meeting_id: str) -> None:
    """고정 fixture 회의를 deterministic하게 data/projects 아래에 기록한다."""
    normalized_project_id = normalize_storage_segment(
        project_id,
        field_name="project_id",
    )
    normalized_meeting_id = normalize_storage_segment(
        meeting_id,
        field_name="meeting_id",
    )
    project_dir, meeting_dir, project_meta_path = _target_paths(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
    )
    if meeting_dir.exists():
        shutil.rmtree(meeting_dir)

    turn_records = _build_turn_records(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
    )
    meeting_meta = MeetingMeta(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        created_at=FIXTURE_CREATED_AT,
        updated_at=FIXTURE_UPDATED_AT,
        turn_count=len(turn_records),
        agent_ids=FIXTURE_AGENT_IDS,
    )
    for document in _build_agent_documents(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        turn_records=turn_records,
    ):
        turns_path = meeting_dir / "agents" / document.agent_id / "turns.json"
        _write_json(turns_path, document.model_dump(mode="json"))

    _write_json(
        meeting_dir / "meta.json",
        meeting_meta.model_dump(mode="json"),
    )

    meetings_dir = project_dir / "meetings"
    meeting_count = sum(1 for item in meetings_dir.iterdir() if item.is_dir())
    project_meta = ProjectMeta(
        project_id=normalized_project_id,
        created_at=_load_existing_project_created_at(project_meta_path),
        updated_at=FIXTURE_UPDATED_AT,
        meeting_count=meeting_count,
    )
    _write_json(project_meta_path, project_meta.model_dump(mode="json"))

    print(
        "[seed] fixture ready:",
        f"project_id={normalized_project_id}",
        f"meeting_id={normalized_meeting_id}",
        f"turn_count={len(turn_records)}",
        f"agents={','.join(FIXTURE_AGENT_IDS)}",
    )


def _parse_args() -> argparse.Namespace:
    """CLI 인자를 파싱한다."""
    parser = argparse.ArgumentParser(
        description="실제 LLM 분석 결과를 고정 fixture 회의 데이터로 시드합니다.",
    )
    parser.add_argument(
        "--project-id",
        default=FIXTURE_PROJECT_ID,
        help=f"대상 project_id (기본값: {FIXTURE_PROJECT_ID})",
    )
    parser.add_argument(
        "--meeting-id",
        default=FIXTURE_MEETING_ID,
        help=f"대상 meeting_id (기본값: {FIXTURE_MEETING_ID})",
    )
    return parser.parse_args()


def main() -> None:
    """CLI 엔트리포인트."""
    args = _parse_args()
    seed_demo_meeting(project_id=args.project_id, meeting_id=args.meeting_id)


if __name__ == "__main__":
    main()
