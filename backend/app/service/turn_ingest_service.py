"""프로젝트/회의 턴 분석 저장 서비스."""

import asyncio
from datetime import datetime, timezone

from app.repo.meeting_storage import JsonTurnAnalysisRepository, TurnAnalysisRepository
from app.service.emotion_service import EmotionInferenceError, classify_turn_emotion
from app.service.sentiment_service import (
    SentimentInferenceError,
    classify_turn_sentiment,
)
from app.types.emotion import TurnEmotionRequest
from app.types.sentiment import TurnSentimentRequest
from app.types.storage import TurnAnalysisRecord, TurnIngestRequest


class TurnIngestInferenceError(Exception):
    """턴 분석 저장 파이프라인의 LLM 추론 단계 실패."""

    def __init__(self, stage: str, message: str) -> None:
        """오류 단계와 메시지를 함께 보관한다."""
        self.stage = stage
        super().__init__(message)


def _now_iso_utc() -> str:
    """UTC 기준 ISO8601 타임스탬프를 반환한다."""
    return datetime.now(tz=timezone.utc).isoformat()


async def store_turn_analysis(
    project_id: str,
    meeting_id: str,
    request: TurnIngestRequest,
    repository: TurnAnalysisRepository | None = None,
) -> TurnAnalysisRecord:
    """발화 단위 감정/정서 분석 후 JSON 저장소에 결과를 upsert한다."""
    sentiment_request = TurnSentimentRequest(
        meeting_id=meeting_id,
        turn_id=request.turn_id,
        agent_id=request.agent_id,
        utterance_text=request.utterance_text,
    )
    emotion_request = TurnEmotionRequest(
        meeting_id=meeting_id,
        turn_id=request.turn_id,
        agent_id=request.agent_id,
        utterance_text=request.utterance_text,
    )

    try:
        sentiment, emotion = await asyncio.gather(
            asyncio.to_thread(classify_turn_sentiment, sentiment_request),
            classify_turn_emotion(request=emotion_request),
        )
    except SentimentInferenceError as exc:
        raise TurnIngestInferenceError(stage="sentiment", message=str(exc)) from exc
    except EmotionInferenceError as exc:
        raise TurnIngestInferenceError(stage=exc.stage, message=str(exc)) from exc

    now = _now_iso_utc()
    record = TurnAnalysisRecord(
        project_id=project_id,
        meeting_id=meeting_id,
        agent_id=request.agent_id,
        turn_id=request.turn_id,
        utterance_text=request.utterance_text,
        created_at=now,
        updated_at=now,
        order=request.order,
        sentiment=sentiment,
        emotion=emotion,
    )
    resolved_repository = repository or JsonTurnAnalysisRepository()
    return resolved_repository.upsert_turn_analysis(record=record)
