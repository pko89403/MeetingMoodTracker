"""발화 턴 감정분류 API 런타임 라우트."""

from fastapi import APIRouter, HTTPException

from app.service.sentiment_service import (
    SentimentInferenceError,
    classify_turn_sentiment,
)
from app.types.sentiment import TurnSentimentRequest, TurnSentimentResponse

router = APIRouter()


@router.post("/api/v1/sentiment/turn", response_model=TurnSentimentResponse)
def classify_turn(request: TurnSentimentRequest) -> TurnSentimentResponse:
    """한 개 발화 턴을 감정 라벨(POS/NEG/NEUTRAL)로 분류한다."""
    try:
        return classify_turn_sentiment(request=request)
    except SentimentInferenceError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": "SENTIMENT_LLM_FAILURE",
                "message_ko": "LLM 감정분류 서비스 호출에 실패했습니다.",
                "message_en": "Sentiment classification failed from LLM service.",
            },
        ) from exc
