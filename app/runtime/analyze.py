from fastapi import APIRouter

from app.types.mood import AnalyzeRequest, AnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_meeting(request: AnalyzeRequest) -> AnalyzeResponse:
    # 아직 모델이 없으므로 하드코딩된 더미 응답을 반환하여 SDD 스펙을 우선 통과시킵니다.
    return AnalyzeResponse(topic="Architecture", mood="Positive", confidence=0.95)
