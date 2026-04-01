"""발화 턴 정서 추출 API 런타임 라우트."""

from fastapi import APIRouter, HTTPException

from app.service.emotion_service import EmotionInferenceError, classify_turn_emotion
from app.types.emotion import TurnEmotionRequest, TurnEmotionResponse

router = APIRouter()


@router.post("/api/v1/emotion/turn", response_model=TurnEmotionResponse)
async def classify_emotion_turn(request: TurnEmotionRequest) -> TurnEmotionResponse:
    """한 개 발화 턴에서 기본 정서/회의 시그널/추가 정서를 추출한다."""
    try:
        return await classify_turn_emotion(request=request)
    except EmotionInferenceError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": "EMOTION_LLM_FAILURE",
                "message_ko": "LLM 정서추출 서비스 호출에 실패했습니다.",
                "message_en": "Emotion extraction failed from LLM service.",
                "stage": exc.stage,
            },
        ) from exc
