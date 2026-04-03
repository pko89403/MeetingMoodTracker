"""회의/턴 루브릭 계산 공용 서비스."""

from app.service.analyze_service import calculate_final_rubrics
from app.types.emotion import TurnEmotionResponse
from app.types.mood import AnalyzeSentiment, MeetingRubrics, SentimentConfidence
from app.types.sentiment import TurnSentimentResponse
from app.types.storage import TurnAnalysisRecord


def build_turn_sentiment_distribution(
    sentiment: TurnSentimentResponse,
) -> AnalyzeSentiment:
    """단일 턴 sentiment label/confidence를 3축 분포로 변환한다."""
    scaled_confidence = int(round(max(0.0, min(1.0, sentiment.confidence)) * 100))

    if sentiment.label == "POS":
        return AnalyzeSentiment(
            positive=SentimentConfidence(confidence=scaled_confidence),
            negative=SentimentConfidence(confidence=0),
            neutral=SentimentConfidence(confidence=100 - scaled_confidence),
        )

    if sentiment.label == "NEG":
        return AnalyzeSentiment(
            positive=SentimentConfidence(confidence=0),
            negative=SentimentConfidence(confidence=scaled_confidence),
            neutral=SentimentConfidence(confidence=100 - scaled_confidence),
        )

    return AnalyzeSentiment(
        positive=SentimentConfidence(confidence=0),
        negative=SentimentConfidence(confidence=0),
        neutral=SentimentConfidence(confidence=100),
    )


def calculate_turn_rubric(
    sentiment: TurnSentimentResponse,
    emotion: TurnEmotionResponse,
) -> MeetingRubrics:
    """단일 턴의 sentiment와 meeting signals를 기반으로 루브릭을 계산한다."""
    return calculate_final_rubrics(
        topics=[],
        sentiment=build_turn_sentiment_distribution(sentiment=sentiment),
        emotion=emotion,
    )


def ensure_turn_rubric(record: TurnAnalysisRecord) -> TurnAnalysisRecord:
    """저장 레코드에 rubric이 비어 있으면 계산해 채운 복사본을 반환한다."""
    if record.rubric is not None:
        return record

    return record.model_copy(
        update={
            "rubric": calculate_turn_rubric(
                sentiment=record.sentiment,
                emotion=record.emotion,
            )
        }
    )
