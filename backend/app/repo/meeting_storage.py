"""프로젝트/회의/에이전트/턴 JSON 저장소 구현."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from app.config.storage import get_projects_data_root
from app.types.storage import (
    UNASSIGNED_AGENT_ID,
    AgentTurnsDocument,
    MeetingMeta,
    ProjectMeta,
    TurnAnalysisRecord,
    TurnIdentity,
)


def _now_iso_utc() -> str:
    """UTC 기준 ISO8601 타임스탬프를 반환한다."""
    return datetime.now(tz=timezone.utc).isoformat()


class TurnAnalysisRepository(Protocol):
    """향후 DB 교체를 고려한 project-aware 저장소 추상화."""

    def upsert_turn_analysis(self, record: TurnAnalysisRecord) -> TurnAnalysisRecord:
        """턴 분석 결과를 복합 식별자 기준 idempotent upsert로 저장한다."""

    def get_turn_analysis(
        self,
        turn_identity: TurnIdentity,
    ) -> TurnAnalysisRecord | None:
        """저장된 턴 분석 결과 한 건을 복합 식별자로 조회한다."""

    def get_project_meta(self, project_id: str) -> ProjectMeta | None:
        """프로젝트 메타데이터를 조회한다."""

    def get_meeting_meta(self, project_id: str, meeting_id: str) -> MeetingMeta | None:
        """회의 메타데이터를 조회한다."""


class JsonTurnAnalysisRepository:
    """프로젝트 계층 구조를 JSON 파일로 저장하는 저장소 구현."""

    def __init__(self, data_root: Path | None = None) -> None:
        """테스트 편의를 위해 data_root를 주입 가능하게 둔다."""
        self._data_root = data_root or get_projects_data_root()

    def upsert_turn_analysis(self, record: TurnAnalysisRecord) -> TurnAnalysisRecord:
        """project/meeting/agent/turn 복합 식별자로 분석 결과를 저장 또는 교체한다."""
        now = _now_iso_utc()
        turns_path = self._turns_path(
            project_id=record.project_id,
            meeting_id=record.meeting_id,
            agent_id=record.storage_agent_id(),
        )
        project_meta_path = self._project_meta_path(project_id=record.project_id)
        meeting_meta_path = self._meeting_meta_path(
            project_id=record.project_id,
            meeting_id=record.meeting_id,
        )

        meeting_was_missing = not meeting_meta_path.exists()
        saved_record = self._upsert_turn_document(
            turns_path=turns_path,
            record=record,
            updated_at=now,
        )
        all_turns = self._read_all_meeting_turns(
            project_id=record.project_id,
            meeting_id=record.meeting_id,
        )
        self._upsert_project_meta(
            project_meta_path=project_meta_path,
            project_id=record.project_id,
            meeting_was_missing=meeting_was_missing,
            updated_at=now,
        )
        self._upsert_meeting_meta(
            meeting_meta_path=meeting_meta_path,
            record=saved_record,
            updated_at=now,
            all_turns=all_turns,
        )
        return saved_record

    def get_turn_analysis(
        self,
        turn_identity: TurnIdentity,
    ) -> TurnAnalysisRecord | None:
        """에이전트 컬렉션에서 해당 turn_id 레코드를 조회한다."""
        turns_path = self._turns_path(
            project_id=turn_identity.project_id,
            meeting_id=turn_identity.meeting_id,
            agent_id=turn_identity.storage_agent_id(),
        )
        document = self._read_turns_document(
            turns_path=turns_path,
            project_id=turn_identity.project_id,
            meeting_id=turn_identity.meeting_id,
            agent_id=turn_identity.storage_agent_id(),
        )
        for item in document.turns:
            if item.turn_id == turn_identity.turn_id:
                return item
        return None

    def get_project_meta(self, project_id: str) -> ProjectMeta | None:
        """프로젝트 meta.json을 읽어 반환한다."""
        project_meta_path = self._project_meta_path(project_id=project_id)
        if not project_meta_path.exists():
            return None
        return ProjectMeta.model_validate_json(project_meta_path.read_text("utf-8"))

    def get_meeting_meta(self, project_id: str, meeting_id: str) -> MeetingMeta | None:
        """회의 meta.json을 읽어 반환한다."""
        meeting_meta_path = self._meeting_meta_path(
            project_id=project_id,
            meeting_id=meeting_id,
        )
        if not meeting_meta_path.exists():
            return None
        return MeetingMeta.model_validate_json(meeting_meta_path.read_text("utf-8"))

    def _project_dir(self, project_id: str) -> Path:
        """프로젝트 디렉터리 경로를 계산한다."""
        return self._data_root / project_id

    def _meeting_dir(self, project_id: str, meeting_id: str) -> Path:
        """회의 디렉터리 경로를 계산한다."""
        return self._project_dir(project_id=project_id) / "meetings" / meeting_id

    def _project_meta_path(self, project_id: str) -> Path:
        """프로젝트 meta.json 경로를 계산한다."""
        return self._project_dir(project_id=project_id) / "meta.json"

    def _meeting_meta_path(self, project_id: str, meeting_id: str) -> Path:
        """회의 meta.json 경로를 계산한다."""
        return self._meeting_dir(project_id=project_id, meeting_id=meeting_id) / "meta.json"

    def _turns_path(self, project_id: str, meeting_id: str, agent_id: str) -> Path:
        """에이전트별 turns.json 경로를 계산한다."""
        return (
            self._meeting_dir(project_id=project_id, meeting_id=meeting_id)
            / "agents"
            / agent_id
            / "turns.json"
        )

    def _read_project_meta(
        self,
        project_meta_path: Path,
        project_id: str,
        updated_at: str,
    ) -> ProjectMeta:
        """프로젝트 메타 파일이 없으면 기본 메타를 생성해 반환한다."""
        if project_meta_path.exists():
            return ProjectMeta.model_validate_json(project_meta_path.read_text("utf-8"))
        return ProjectMeta(
            project_id=project_id,
            created_at=updated_at,
            updated_at=updated_at,
            meeting_count=0,
        )

    def _read_meeting_meta(
        self,
        meeting_meta_path: Path,
        record: TurnAnalysisRecord,
        updated_at: str,
    ) -> MeetingMeta:
        """회의 메타 파일이 없으면 기본 메타를 생성해 반환한다."""
        if meeting_meta_path.exists():
            return MeetingMeta.model_validate_json(meeting_meta_path.read_text("utf-8"))
        return MeetingMeta(
            project_id=record.project_id,
            meeting_id=record.meeting_id,
            created_at=updated_at,
            updated_at=updated_at,
            turn_count=0,
            agent_ids=[],
        )

    def _read_turns_document(
        self,
        turns_path: Path,
        project_id: str,
        meeting_id: str,
        agent_id: str,
    ) -> AgentTurnsDocument:
        """에이전트별 턴 문서를 읽고 없으면 빈 문서를 반환한다."""
        resolved_agent_id = agent_id or UNASSIGNED_AGENT_ID
        if turns_path.exists():
            return AgentTurnsDocument.model_validate_json(turns_path.read_text("utf-8"))
        return AgentTurnsDocument(
            project_id=project_id,
            meeting_id=meeting_id,
            agent_id=resolved_agent_id,
            updated_at=_now_iso_utc(),
            turns=[],
        )

    def _upsert_project_meta(
        self,
        project_meta_path: Path,
        project_id: str,
        meeting_was_missing: bool,
        updated_at: str,
    ) -> None:
        """프로젝트 메타를 생성하거나 meeting_count를 갱신한다."""
        project_meta = self._read_project_meta(
            project_meta_path=project_meta_path,
            project_id=project_id,
            updated_at=updated_at,
        )
        project_meta.updated_at = updated_at
        if meeting_was_missing:
            project_meta.meeting_count += 1
        self._write_json(project_meta_path, project_meta.model_dump(mode="json"))

    def _upsert_meeting_meta(
        self,
        meeting_meta_path: Path,
        record: TurnAnalysisRecord,
        updated_at: str,
        all_turns: list[TurnAnalysisRecord],
    ) -> None:
        """회의 메타를 생성하거나 turn_count/agent_ids를 전체 회의 기준으로 갱신한다."""
        meeting_meta = self._read_meeting_meta(
            meeting_meta_path=meeting_meta_path,
            record=record,
            updated_at=updated_at,
        )
        meeting_meta.updated_at = updated_at
        meeting_meta.turn_count = len(all_turns)
        meeting_meta.agent_ids = self._collect_agent_ids(all_turns=all_turns)
        self._write_json(meeting_meta_path, meeting_meta.model_dump(mode="json"))

    def _upsert_turn_document(
        self,
        turns_path: Path,
        record: TurnAnalysisRecord,
        updated_at: str,
    ) -> TurnAnalysisRecord:
        """에이전트 turns 문서에 turn_id 기준 upsert를 수행한다."""
        document = self._read_turns_document(
            turns_path=turns_path,
            project_id=record.project_id,
            meeting_id=record.meeting_id,
            agent_id=record.storage_agent_id(),
        )
        saved_record = record.model_copy(update={"updated_at": updated_at})

        for index, existing in enumerate(document.turns):
            if existing.turn_id != record.turn_id:
                continue
            saved_record = saved_record.model_copy(
                update={"created_at": existing.created_at}
            )
            document.turns[index] = saved_record
            break
        else:
            document.turns.append(saved_record)

        document.updated_at = updated_at
        document.turns = self._sort_turns(document.turns)
        self._write_json(turns_path, document.model_dump(mode="json"))
        return saved_record

    def _read_all_meeting_turns(
        self,
        project_id: str,
        meeting_id: str,
    ) -> list[TurnAnalysisRecord]:
        """회의 하위 모든 agent turns.json을 읽어 전체 턴 목록을 수집한다."""
        agents_dir = self._meeting_dir(project_id=project_id, meeting_id=meeting_id) / "agents"
        if not agents_dir.exists():
            return []

        all_turns: list[TurnAnalysisRecord] = []
        for turns_path in sorted(agents_dir.glob("*/turns.json")):
            document = AgentTurnsDocument.model_validate_json(turns_path.read_text("utf-8"))
            all_turns.extend(document.turns)
        return self._sort_turns(all_turns)

    def _collect_agent_ids(self, all_turns: list[TurnAnalysisRecord]) -> list[str]:
        """회의 메타에 기록할 agent_id 버킷 목록을 중복 없이 수집한다."""
        collected: list[str] = []
        seen: set[str] = set()
        for turn in all_turns:
            storage_agent_id = turn.storage_agent_id()
            if storage_agent_id in seen:
                continue
            seen.add(storage_agent_id)
            collected.append(storage_agent_id)
        return collected

    def _sort_turns(self, turns: list[TurnAnalysisRecord]) -> list[TurnAnalysisRecord]:
        """order 우선, 생성시각/turn_id 보조키로 턴 순서를 정렬한다."""
        return sorted(
            turns,
            key=lambda turn: (
                turn.order is None,
                turn.order if turn.order is not None else 0,
                turn.created_at,
                turn.turn_id,
            ),
        )

    def _write_json(self, path: Path, payload: dict[str, object]) -> None:
        """부모 디렉터리를 준비한 뒤 JSON 파일을 UTF-8로 저장한다."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
