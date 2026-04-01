"""회의록 분석 엔드포인트의 요청/응답 타입 정의."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.types.emotion import TurnEmotionResponse


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


class MeetingRubrics(BaseModel):
    """추출된 모든 지표를 조합하여 도출한 화자/발화 평가 루브릭."""

    dominance: int = Field(
        ge=0, le=100, description="주도성: 대화를 이끌고 영향을 미치는 정도"
    )
    efficiency: int = Field(
        ge=0, le=100, description="효율성: 논의의 명확성 및 결론 도출 의지"
    )
    cohesion: int = Field(
        ge=0, le=100, description="결속력: 합의 도출 및 팀 분위기 기여도"
    )


class AnalyzeResponse(BaseModel):
    """회의록 분석 응답 스키마."""

    topic: str
    sentiment: AnalyzeSentiment
    emotion: TurnEmotionResponse
    rubric: MeetingRubrics
