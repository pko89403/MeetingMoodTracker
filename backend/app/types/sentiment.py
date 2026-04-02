"""발화 턴 감정분류 요청/응답 타입 정의."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SentimentLabel = Literal["POS", "NEG", "NEUTRAL"]


class TurnSentimentRequest(BaseModel):
    """발화 턴 단위 감정분류 요청 스키마."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meeting_id": "m_20260401_003",
                "turn_id": "t_021",
                "speaker_id": "bob",
                "utterance_text": "이 접근은 좋아요. But we need tighter QA before release.",
            }
        }
    )

    meeting_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    speaker_id: str | None = None
    utterance_text: str = Field(min_length=1, max_length=4000)


class TurnSentimentResponse(BaseModel):
    """발화 턴 단위 감정분류 응답 스키마."""

    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(min_length=1)
