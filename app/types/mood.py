"""회의록 분석 엔드포인트의 요청/응답 타입 정의."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.types.emotion import EmotionLabel


class AnalyzeRequest(BaseModel):
    """회의록 분석 요청 스키마."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meeting_id": "m_20260401_002",
                "text": (
                    "배포 일정이 다시 미뤄졌습니다. "
                    "원인과 리스크를 오늘 안에 정리하고 대응 계획을 확정합시다."
                ),
            }
        }
    )

    meeting_id: str
    text: str


class AnalyzeTopicCandidate(BaseModel):
    """세분화된 topic 후보 항목."""

    confidence: int = Field(ge=0, le=100)
    label: str = Field(min_length=1, max_length=60)


class AnalyzeTopic(BaseModel):
    """Topic 세분화 응답 스키마."""

    primary: str = Field(min_length=1, max_length=60)
    candidates: list[AnalyzeTopicCandidate] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_primary_in_candidates(self) -> "AnalyzeTopic":
        """primary topic이 candidates 중 하나인지 검증한다."""
        labels = [item.label.casefold() for item in self.candidates]
        if self.primary.casefold() not in labels:
            raise ValueError("topic primary must exist in candidates.")
        return self


SentimentPolarity = Literal["positive", "negative", "neutral"]


class AnalyzeSentimentDistribution(BaseModel):
    """Sentiment 세분화 분포 스키마."""

    positive: int = Field(ge=0, le=100)
    negative: int = Field(ge=0, le=100)
    neutral: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_total_confidence(self) -> "AnalyzeSentiment":
        """세 축 confidence 합계가 100인지 검증한다."""
        total = self.positive + self.negative + self.neutral
        if total != 100:
            raise ValueError("sentiment confidence total must be 100.")
        return self


class AnalyzeSentiment(BaseModel):
    """Sentiment 세분화 + 요약 스키마."""

    distribution: AnalyzeSentimentDistribution
    polarity: SentimentPolarity
    confidence: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_confidence_matches_polarity(self) -> "AnalyzeSentiment":
        """polarity confidence와 요약 confidence가 일치하는지 검증한다."""
        axis_value = getattr(self.distribution, self.polarity)
        if self.confidence != axis_value:
            raise ValueError("sentiment confidence must match polarity axis.")
        return self


class AnalyzeEmotionDistribution(BaseModel):
    """Emotion 세분화 분포 스키마(기본 8정서)."""

    anger: int = Field(ge=0, le=100)
    joy: int = Field(ge=0, le=100)
    sadness: int = Field(ge=0, le=100)
    neutral: int = Field(ge=0, le=100)
    anxiety: int = Field(ge=0, le=100)
    frustration: int = Field(ge=0, le=100)
    excitement: int = Field(ge=0, le=100)
    confusion: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_total_confidence(self) -> "AnalyzeEmotionDistribution":
        """8개 정서 confidence 합계가 100인지 검증한다."""
        total = (
            self.anger
            + self.joy
            + self.sadness
            + self.neutral
            + self.anxiety
            + self.frustration
            + self.excitement
            + self.confusion
        )
        if total != 100:
            raise ValueError("emotion confidence total must be 100.")
        return self


class AnalyzeEmotion(BaseModel):
    """Emotion 세분화 + 요약 스키마."""

    distribution: AnalyzeEmotionDistribution
    primary: EmotionLabel
    confidence: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_confidence_matches_primary(self) -> "AnalyzeEmotion":
        """primary emotion confidence와 요약 confidence가 일치하는지 검증한다."""
        axis_value = getattr(self.distribution, self.primary)
        if self.confidence != axis_value:
            raise ValueError("emotion confidence must match primary axis.")
        return self


class AnalyzeCorrelation(BaseModel):
    """세분화 결과 재조합 상관도 요약 스키마."""

    topic_sentiment: int = Field(ge=0, le=100)
    topic_emotion: int = Field(ge=0, le=100)
    sentiment_emotion: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=160)


class AnalyzeResponse(BaseModel):
    """회의록 분석 응답 스키마."""

    topic: AnalyzeTopic
    sentiment: AnalyzeSentiment
    emotion: AnalyzeEmotion
    correlation: AnalyzeCorrelation
