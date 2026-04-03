"""발화 턴 감정분류 요청/응답 타입 정의."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.types.identifiers import normalize_optional_agent_id

SentimentLabel = Literal["POS", "NEG", "NEUTRAL"]


class TurnSentimentRequest(BaseModel):
    """발화 턴 단위 감정분류 요청 스키마."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meeting_id": "m_20260401_003",
                "turn_id": "t_021",
                "agent_id": "bob",
                "utterance_text": "이 접근은 좋아요. But we need tighter QA before release.",
            }
        }
    )

    meeting_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    agent_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("agent_id", "speaker_id"),
    )
    utterance_text: str = Field(min_length=1, max_length=4000)

    @field_validator("agent_id", mode="before")
    @classmethod
    def normalize_agent_id(cls, value: str | None) -> str | None:
        """레거시 speaker_id 입력도 agent_id 규칙으로 정규화한다."""
        return normalize_optional_agent_id(value)


class TurnSentimentResponse(BaseModel):
    """발화 턴 단위 감정분류 응답 스키마."""

    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(min_length=1)
