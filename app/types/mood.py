"""회의록 분석 엔드포인트의 요청/응답 타입 정의."""

from pydantic import BaseModel, Field, model_validator


class AnalyzeRequest(BaseModel):
    """회의록 분석 요청 스키마."""

    meeting_id: str
    text: str


class SentimentConfidence(BaseModel):
    """단일 감정 축의 confidence 백분율 값."""

    confidence: int = Field(ge=0, le=100)


class AnalyzeSentiment(BaseModel):
    """Analyze 감정 분포(positive/negative/neutral) 스키마."""

    positive: SentimentConfidence
    negative: SentimentConfidence
    neutral: SentimentConfidence

    @model_validator(mode="after")
    def validate_total_confidence(self) -> "AnalyzeSentiment":
        """세 축 confidence 합계가 100인지 검증한다."""
        total = (
            self.positive.confidence
            + self.negative.confidence
            + self.neutral.confidence
        )
        if total != 100:
            raise ValueError("sentiment confidence total must be 100.")
        return self


class AnalyzeResponse(BaseModel):
    """회의록 분석 응답 스키마."""

    topic: str
    sentiment: AnalyzeSentiment
