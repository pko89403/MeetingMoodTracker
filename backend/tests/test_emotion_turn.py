from fastapi.testclient import TestClient

import app.runtime.emotion as emotion_runtime
from app.main import app
from app.service.emotion_service import EmotionInferenceError
from app.types.emotion import (
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionResponse,
)

client = TestClient(app)


def _sample_response() -> TurnEmotionResponse:
    return TurnEmotionResponse(
        emotions=EmotionScores(
            anger=EmotionConfidenceValue(confidence=10),
            joy=EmotionConfidenceValue(confidence=40),
            sadness=EmotionConfidenceValue(confidence=5),
            neutral=EmotionConfidenceValue(confidence=15),
            anxiety=EmotionConfidenceValue(confidence=15),
            frustration=EmotionConfidenceValue(confidence=5),
            excitement=EmotionConfidenceValue(confidence=5),
            confusion=EmotionConfidenceValue(confidence=5),
        ),
        meeting_signals=MeetingSignals(
            tension=MeetingSignalConfidenceValue(confidence=35),
            alignment=MeetingSignalConfidenceValue(confidence=70),
            urgency=MeetingSignalConfidenceValue(confidence=65),
            clarity=MeetingSignalConfidenceValue(confidence=80),
            engagement=MeetingSignalConfidenceValue(confidence=75),
        ),
        emerging_emotions=[],
    )


def test_turn_emotion_endpoint_success_with_agent_id(monkeypatch) -> None:
    async def _fake_classify_turn_emotion(request) -> TurnEmotionResponse:
        assert request.meeting_id == 'm_001'
        assert request.turn_id == 't_001'
        assert request.agent_id == 'alice'
        return _sample_response()

    monkeypatch.setattr(
        emotion_runtime,
        'classify_turn_emotion',
        _fake_classify_turn_emotion,
    )

    response = client.post(
        '/api/v1/emotion/turn',
        json={
            'meeting_id': 'm_001',
            'turn_id': 't_001',
            'agent_id': 'alice',
            'utterance_text': '이 일정이면 배포 리스크가 조금 걱정됩니다.',
        },
    )

    assert response.status_code == 200
    assert response.json() == _sample_response().model_dump(mode='json')


def test_turn_emotion_endpoint_accepts_legacy_speaker_id_alias(monkeypatch) -> None:
    async def _fake_classify_turn_emotion(request) -> TurnEmotionResponse:
        assert request.agent_id == 'alice'
        return _sample_response()

    monkeypatch.setattr(
        emotion_runtime,
        'classify_turn_emotion',
        _fake_classify_turn_emotion,
    )

    response = client.post(
        '/api/v1/emotion/turn',
        json={
            'meeting_id': 'm_001',
            'turn_id': 't_001',
            'speaker_id': 'alice',
            'utterance_text': '이 일정이면 배포 리스크가 조금 걱정됩니다.',
        },
    )

    assert response.status_code == 200


def test_turn_emotion_endpoint_normalizes_blank_agent_id(monkeypatch) -> None:
    async def _fake_classify_turn_emotion(request) -> TurnEmotionResponse:
        assert request.agent_id is None
        return _sample_response()

    monkeypatch.setattr(
        emotion_runtime,
        'classify_turn_emotion',
        _fake_classify_turn_emotion,
    )

    response = client.post(
        '/api/v1/emotion/turn',
        json={
            'meeting_id': 'm_001',
            'turn_id': 't_001',
            'agent_id': '   ',
            'utterance_text': '이 일정이면 배포 리스크가 조금 걱정됩니다.',
        },
    )

    assert response.status_code == 200


def test_turn_emotion_endpoint_returns_502_on_inference_failure(monkeypatch) -> None:
    async def _raise_error(request) -> TurnEmotionResponse:
        assert request.turn_id == 't_001'
        raise EmotionInferenceError(stage='inference', message='boom')

    monkeypatch.setattr(
        emotion_runtime,
        'classify_turn_emotion',
        _raise_error,
    )

    response = client.post(
        '/api/v1/emotion/turn',
        json={
            'meeting_id': 'm_001',
            'turn_id': 't_001',
            'agent_id': 'alice',
            'utterance_text': '이건 별로예요.',
        },
    )

    assert response.status_code == 502
    assert response.json()['detail'] == {
        'error_code': 'EMOTION_LLM_FAILURE',
        'message_ko': 'LLM 정서추출 서비스 호출에 실패했습니다.',
        'message_en': 'Emotion extraction failed from LLM service.',
        'stage': 'inference',
    }
