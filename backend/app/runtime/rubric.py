"""루브릭 지수 산출 API 런타임 라우트."""

from fastapi import APIRouter

from app.service.analyze_service import calculate_final_rubrics
from app.types.emotion import (
    EmotionConfidenceValue,
    EmotionScores,
    TurnEmotionResponse,
)
from app.types.rubric import RubricCalculateRequest, RubricCalculateResponse

router = APIRouter(prefix="/api/v1/rubric", tags=["rubric"])


@router.post("/calculate", response_model=RubricCalculateResponse)
async def calculate_rubric_endpoint(
    request: RubricCalculateRequest,
) -> RubricCalculateResponse:
    """추출된 지표들을 기반으로 루브릭 지수(주도성, 효율성, 결속력)를 산출한다."""

    # calculate_final_rubrics는 TurnEmotionResponse 객체를 기대하므로 변환
    # (실제 계산에는 meeting_signals만 사용되므로 더미 데이터를 포함하여 생성)
    dummy_emotions = EmotionScores(
        anger=EmotionConfidenceValue(confidence=0),
        joy=EmotionConfidenceValue(confidence=0),
        sadness=EmotionConfidenceValue(confidence=0),
        neutral=EmotionConfidenceValue(confidence=0),
        anxiety=EmotionConfidenceValue(confidence=0),
        frustration=EmotionConfidenceValue(confidence=0),
        excitement=EmotionConfidenceValue(confidence=0),
        confusion=EmotionConfidenceValue(confidence=0),
    )

    emotion_obj = TurnEmotionResponse(
        emotions=dummy_emotions,
        meeting_signals=request.meeting_signals,
        emerging_emotions=[],
    )

    rubric = calculate_final_rubrics(
        topics=request.topics, sentiment=request.sentiment, emotion=emotion_obj
    )

    return RubricCalculateResponse(rubric=rubric)
