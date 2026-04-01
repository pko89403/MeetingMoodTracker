"""발화 턴 정서 추출 요청/응답 타입 정의."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EmotionLabel = Literal[
    "anger",
    "joy",
    "sadness",
    "neutral",
    "anxiety",
    "frustration",
    "excitement",
    "confusion",
]
BASE_EMOTION_LABELS: tuple[EmotionLabel, ...] = (
    "anger",
    "joy",
    "sadness",
    "neutral",
    "anxiety",
    "frustration",
    "excitement",
    "confusion",
)
EMERGING_SIGNAL_LABELS: tuple[str, ...] = (
    "resentment",
    "skepticism",
    "discouragement",
    "resignation",
    "concern",
    "fatigue",
    "doubt",
    "defensiveness",
    "distrust",
    "impatience",
    "relief",
    "optimism",
)
EMERGING_SIGNAL_LABEL_SET = {label for label in EMERGING_SIGNAL_LABELS}


class TurnEmotionRequest(BaseModel):
    """발화 턴 단위 정서 추출 요청 스키마."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meeting_id": "m_20260401_001",
                "turn_id": "t_014",
                "speaker_id": "alice",
                "utterance_text": "이건 또 실패했어요. I'm worried about release risk.",
            }
        }
    )

    meeting_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    speaker_id: str | None = None
    utterance_text: str = Field(min_length=1, max_length=4000)


class EmotionConfidenceEvidence(BaseModel):
    """정서 라벨별 confidence/evidence 스키마."""

    confidence: int = Field(ge=0, le=100)
    evidence: str = Field(min_length=1)

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, value: str) -> str:
        """evidence 문자열을 trim하고 빈 문자열을 차단한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("evidence must not be blank.")
        return normalized


class EmotionScores(BaseModel):
    """고정 8개 기본 정서 점수/근거 스키마."""

    anger: EmotionConfidenceEvidence
    joy: EmotionConfidenceEvidence
    sadness: EmotionConfidenceEvidence
    neutral: EmotionConfidenceEvidence
    anxiety: EmotionConfidenceEvidence
    frustration: EmotionConfidenceEvidence
    excitement: EmotionConfidenceEvidence
    confusion: EmotionConfidenceEvidence


class MeetingSignalConfidenceEvidence(BaseModel):
    """회의 시그널 축별 confidence/evidence 스키마."""

    confidence: int = Field(ge=0, le=100)
    evidence: str = Field(min_length=1)

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, value: str) -> str:
        """evidence 문자열을 trim하고 빈 문자열을 차단한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("evidence must not be blank.")
        return normalized


class MeetingSignals(BaseModel):
    """회의 도메인 특화 시그널(5축) confidence/evidence 스키마."""

    tension: MeetingSignalConfidenceEvidence
    alignment: MeetingSignalConfidenceEvidence
    urgency: MeetingSignalConfidenceEvidence
    clarity: MeetingSignalConfidenceEvidence
    engagement: MeetingSignalConfidenceEvidence


class EmergingEmotion(BaseModel):
    """기본 8정서 외 추가 발굴 정서 스키마."""

    label: str = Field(min_length=1)
    confidence: int = Field(ge=0, le=100)
    evidence: str = Field(min_length=1)

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, value: str) -> str:
        """evidence 텍스트를 trim하고 빈 문자열을 차단한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("text field must not be blank.")
        return normalized

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        """label 텍스트를 trim하고 허용 signal 풀에서만 선택되도록 강제한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("text field must not be blank.")
        if normalized.casefold() not in EMERGING_SIGNAL_LABEL_SET:
            raise ValueError("label must be one of EMERGING_SIGNAL_LABELS.")
        if normalized.casefold() == normalized:
            return normalized
        return normalized.casefold()


class TurnEmotionResponse(BaseModel):
    """발화 턴 단위 정서 추출 응답 스키마."""

    emotions: EmotionScores
    meeting_signals: MeetingSignals
    emerging_emotions: list[EmergingEmotion] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_emerging_constraints(self) -> "TurnEmotionResponse":
        """추가 발굴 정서 목록의 라벨 제약(기본 정서 중복 금지/중복 금지)을 검증한다."""
        base_labels = {label.casefold() for label in BASE_EMOTION_LABELS}
        seen: set[str] = set()

        for item in self.emerging_emotions:
            key = item.label.casefold()
            if key in base_labels:
                raise ValueError("emerging emotion must not duplicate base emotions.")
            if key in seen:
                raise ValueError("emerging emotion labels must be unique.")
            seen.add(key)

        return self
