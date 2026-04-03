"""프로젝트/회의/에이전트/턴 저장 모델 정의."""

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from app.types.emotion import EmotionScores, MeetingSignals, TurnEmotionResponse
from app.types.identifiers import (
    UNASSIGNED_AGENT_ID,
    normalize_optional_agent_id,
    normalize_required_identifier,
    normalize_storage_segment,
)
from app.types.mood import AnalyzeSentiment
from app.types.sentiment import TurnSentimentResponse


class ProjectMeta(BaseModel):
    """프로젝트 단위 저장 메타 정보."""

    project_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    meeting_count: int = Field(ge=0)


class MeetingMeta(BaseModel):
    """회의 단위 저장 메타 정보."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    turn_count: int = Field(ge=0)
    agent_ids: list[str] = Field(default_factory=list)


class TurnIdentity(BaseModel):
    """project_id + meeting_id + agent_id + turn_id 복합 식별자 경계를 표현한다."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    agent_id: str | None = Field(default=None)
    turn_id: str = Field(min_length=1)

    @field_validator("project_id", "meeting_id")
    @classmethod
    def validate_storage_identifier(cls, value: str, info: ValidationInfo) -> str:
        """저장 경로에 반영되는 식별자는 안전한 단일 segment만 허용한다."""
        return normalize_storage_segment(value, field_name=info.field_name)

    @field_validator("turn_id")
    @classmethod
    def validate_turn_id(cls, value: str) -> str:
        """turn_id는 공백만 제거하고 빈 문자열만 금지한다."""
        return normalize_required_identifier(value, field_name="turn_id")

    @field_validator("agent_id", mode="before")
    @classmethod
    def validate_agent_id(cls, value: str | None) -> str | None:
        """agent_id는 비어 있으면 None으로 유지하고 예약값 충돌을 막는다."""
        return normalize_optional_agent_id(value)

    def storage_agent_id(self) -> str:
        """저장 경로에서 사용할 agent 버킷 식별자를 반환한다."""
        if self.agent_id is None:
            return UNASSIGNED_AGENT_ID
        return self.agent_id


class TurnIngestRequest(BaseModel):
    """프로젝트/회의 경로 아래 개별 발화를 수집하고 저장하는 요청 스키마."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "alice",
                "turn_id": "t_014",
                "utterance_text": "배포 전에 QA를 한 번 더 확인해야 할 것 같아요.",
                "order": 14,
            }
        }
    )

    agent_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("agent_id", "speaker_id"),
    )
    turn_id: str = Field(min_length=1)
    utterance_text: str = Field(min_length=1, max_length=4000)
    order: int | None = Field(default=None, ge=0)

    @field_validator("agent_id", mode="before")
    @classmethod
    def validate_ingest_agent_id(cls, value: str | None) -> str | None:
        """레거시 speaker_id 입력을 agent_id로 정규화한다."""
        return normalize_optional_agent_id(value)


class Project(BaseModel):
    """프로젝트 도메인 경계를 표현한다."""

    meta: ProjectMeta


class Meeting(BaseModel):
    """회의 도메인 경계를 표현한다."""

    meta: MeetingMeta


class Turn(TurnIdentity):
    """저장 가능한 발화 턴 기본 레코드."""

    utterance_text: str = Field(min_length=1, max_length=4000)
    created_at: str = Field(min_length=1)
    order: int | None = Field(default=None, ge=0)


class TurnAnalysis(BaseModel):
    """발화 분석 결과 도메인 경계를 표현한다."""

    sentiment: TurnSentimentResponse
    emotion: TurnEmotionResponse


class TurnAnalysisRecord(Turn):
    """발화 원문과 분석 결과를 함께 보관하는 저장 레코드."""

    updated_at: str = Field(min_length=1)
    sentiment: TurnSentimentResponse
    emotion: TurnEmotionResponse


class AgentAggregate(BaseModel):
    """에이전트 단위 집계 경계를 표현한다."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    agent_id: str | None = Field(default=None)
    turn_count: int = Field(ge=0)
    turn_ids: list[str] = Field(default_factory=list)
    avg_sentiment: AnalyzeSentiment
    primary_emotion: str | None = Field(default=None)
    primary_signal: str | None = Field(default=None)
    emerging_emotions: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)


class MeetingAggregate(BaseModel):
    """회의 단위 집계 경계를 표현한다."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    turn_count: int = Field(ge=0)
    agent_aggregates: list[AgentAggregate] = Field(default_factory=list)


class MeetingOverviewResponse(BaseModel):
    """회의 overview 조회 응답 스키마."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    turn_count: int = Field(ge=0)
    agent_count: int = Field(ge=0)
    topics: list[str] = Field(default_factory=list)
    sentiment: AnalyzeSentiment
    emotions: EmotionScores
    signals: MeetingSignals
    one_line_summary: str | None = Field(default=None)


class MeetingTurnsResponse(BaseModel):
    """회의 발화 목록 조회 응답 스키마."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    total_count: int = Field(ge=0)
    turns: list[TurnAnalysisRecord] = Field(default_factory=list)


class MeetingAgentsResponse(BaseModel):
    """회의 에이전트 집계 조회 응답 스키마."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    total_count: int = Field(ge=0)
    agents: list[AgentAggregate] = Field(default_factory=list)


class AgentTurnsDocument(BaseModel):
    """에이전트별 turns.json 직렬화 문서."""

    project_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    turns: list[TurnAnalysisRecord] = Field(default_factory=list)
