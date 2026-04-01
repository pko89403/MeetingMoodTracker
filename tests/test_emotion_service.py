from unittest.mock import AsyncMock, patch

import pytest

from app.service.emotion_service import classify_turn_emotion
from app.types.emotion import (
    EmergingEmotion,
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionRequest,
)


@pytest.mark.asyncio
async def test_classify_turn_emotion_calls_single_integrated_stage():
    # Given
    request = TurnEmotionRequest(
        meeting_id="m1",
        turn_id="t1",
        utterance_text="테스트 문장입니다."
    )
    
    mock_base = EmotionScores(
        anger=EmotionConfidenceValue(confidence=10),
        joy=EmotionConfidenceValue(confidence=20),
        sadness=EmotionConfidenceValue(confidence=0),
        neutral=EmotionConfidenceValue(confidence=70),
        anxiety=EmotionConfidenceValue(confidence=0),
        frustration=EmotionConfidenceValue(confidence=0),
        excitement=EmotionConfidenceValue(confidence=0),
        confusion=EmotionConfidenceValue(confidence=0)
    )
    
    mock_signals = MeetingSignals(
        tension=MeetingSignalConfidenceValue(confidence=10),
        alignment=MeetingSignalConfidenceValue(confidence=80),
        urgency=MeetingSignalConfidenceValue(confidence=20),
        clarity=MeetingSignalConfidenceValue(confidence=90),
        engagement=MeetingSignalConfidenceValue(confidence=70)
    )
    
    mock_emerging = [
        EmergingEmotion(label="relief", confidence=30)
    ]

    with patch("app.service.emotion_service.get_llm_config") as mock_get_config, \
         patch("app.service.emotion_service._build_async_azure_client"), \
         patch("app.service.emotion_service.extract_all_emotions_with_llm", new_callable=AsyncMock) as mock_extract:
        
        mock_get_config.return_value.LLM_DEPLOYMENT_NAME = "gpt-4o"
        mock_extract.return_value = (mock_base, mock_signals, mock_emerging)
        
        # When
        response = await classify_turn_emotion(request)
        
        # Then
        assert response.emotions == mock_base
        assert response.meeting_signals == mock_signals
        assert response.emerging_emotions == mock_emerging
        
        # 단일 호출 확인
        mock_extract.assert_awaited_once()
