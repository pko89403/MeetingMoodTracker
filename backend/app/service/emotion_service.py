"""발화 턴 정서 추출을 수행하는 서비스 레이어."""

import json
import math
from typing import Any

from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field, field_validator

from app.service.llm_config_service import get_llm_config
from app.types.emotion import (
    BASE_EMOTION_LABELS,
    EMERGING_SIGNAL_LABEL_SET,
    EMERGING_SIGNAL_LABELS,
    EmergingEmotion,
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
    TurnEmotionRequest,
    TurnEmotionResponse,
)
from app.types.llm_config import LlmConfigResponse

DEFAULT_AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
EMOTION_REASONING_EFFORT = "none"
EMOTION_MAX_OUTPUT_TOKENS = 2048


INTEGRATED_EMOTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_turn_all_emotions",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "emotions": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "anger": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "joy": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "sadness": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "neutral": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "anxiety": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "frustration": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "excitement": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "confusion": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                },
                "required": [
                    "anger",
                    "joy",
                    "sadness",
                    "neutral",
                    "anxiety",
                    "frustration",
                    "excitement",
                    "confusion",
                ],
            },
            "meeting_signals": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tension": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "alignment": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "urgency": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "clarity": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                    "engagement": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["confidence"],
                    },
                },
                "required": [
                    "tension",
                    "alignment",
                    "urgency",
                    "clarity",
                    "engagement",
                ],
            },
            "emerging_emotions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "label": {
                            "type": "string",
                            "enum": list(EMERGING_SIGNAL_LABELS),
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    },
                    "required": ["label", "confidence"],
                },
            },
        },
        "required": ["emotions", "meeting_signals", "emerging_emotions"],
    },
}


class _RawEmotionConfidence(BaseModel):
    """LLM 정서 항목 원시 타입 (confidence만 추출)."""

    confidence: float


class _RawBaseEmotionScores(BaseModel):
    """LLM 기본 정서 원시 스키마."""

    anger: _RawEmotionConfidence
    joy: _RawEmotionConfidence
    sadness: _RawEmotionConfidence
    neutral: _RawEmotionConfidence
    anxiety: _RawEmotionConfidence
    frustration: _RawEmotionConfidence
    excitement: _RawEmotionConfidence
    confusion: _RawEmotionConfidence


class _RawMeetingSignals(BaseModel):
    """LLM 회의 시그널 원시 스키마."""

    tension: _RawEmotionConfidence
    alignment: _RawEmotionConfidence
    urgency: _RawEmotionConfidence
    clarity: _RawEmotionConfidence
    engagement: _RawEmotionConfidence


class _RawEmergingEmotion(BaseModel):
    """LLM 추가 발굴 정서 원시 스키마."""

    label: str = Field(min_length=1)
    confidence: float

    @field_validator("label")
    @classmethod
    def validate_non_blank_label(cls, value: str) -> str:
        """label 문자열을 trim한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("label must not be blank.")
        return normalized


class _RawIntegratedEmotionPayload(BaseModel):
    """LLM 통합 응답 전체 원시 스키마."""

    emotions: _RawBaseEmotionScores
    meeting_signals: _RawMeetingSignals
    emerging_emotions: list[_RawEmergingEmotion] = Field(default_factory=list)


class EmotionInferenceError(Exception):
    """LLM 호출 또는 응답 파싱 단계에서 정서 추출이 실패했을 때 발생한다."""

    def __init__(self, stage: str, message: str) -> None:
        """오류 단계(`config`/`inference`)와 상세 메시지를 보관한다."""
        self.stage = stage
        super().__init__(message)


def _resolve_api_version(llm_config: LlmConfigResponse) -> str:
    """설정값에서 API 버전을 우선순위에 따라 선택한다."""
    if (
        llm_config.LLM_API_VERSION is not None
        and llm_config.LLM_API_VERSION.strip() != ""
    ):
        return llm_config.LLM_API_VERSION
    if (
        llm_config.LLM_MODEL_VERSION is not None
        and llm_config.LLM_MODEL_VERSION.strip() != ""
    ):
        return llm_config.LLM_MODEL_VERSION
    return DEFAULT_AZURE_OPENAI_API_VERSION


def _build_async_azure_client(llm_config: LlmConfigResponse) -> AsyncAzureOpenAI:
    """검증된 LLM 설정으로 Azure OpenAI SDK 비동기 클라이언트를 생성한다."""
    return AsyncAzureOpenAI(
        api_key=llm_config.LLM_API_KEY,
        azure_endpoint=llm_config.LLM_ENDPOINT,
        api_version=_resolve_api_version(llm_config=llm_config),
    )


def _build_integrated_system_prompt() -> str:
    """통합 정서(기본 8개 + 회의 시그널 + 추가 발굴) 추출 시스템 프롬프트를 구성한다."""
    allowed_labels = ", ".join(EMERGING_SIGNAL_LABELS)
    return (
        "You analyze one meeting turn and extract emotions and meeting-specific signals. "
        "1. Base Emotions: Always return eight labels (anger, joy, sadness, neutral, "
        "anxiety, frustration, excitement, confusion). "
        "2. Meeting Signals: Return five axes (tension, alignment, urgency, clarity, engagement). "
        "3. Emerging Emotions: Return up to 3 additional emotions beyond the base labels. "
        f"Allowed emerging labels set: {allowed_labels}. "
        "For all items, return confidence 0-100 only. "
        "Do not provide any textual evidence or explanation."
    )


def _build_user_prompt(request: TurnEmotionRequest) -> str:
    """요청 필드를 일관된 포맷의 사용자 프롬프트 문자열로 변환한다."""
    agent_text = request.agent_id if request.agent_id is not None else "N/A"
    return (
        f"meeting_id={request.meeting_id}\n"
        f"turn_id={request.turn_id}\n"
        f"agent_id={agent_text}\n"
        "utterance:\n"
        f"{request.utterance_text}"
    )


def _extract_message_content(completion: Any, stage: str) -> str:
    """Chat completion 결과에서 비어 있지 않은 본문 문자열을 추출한다."""
    choices = getattr(completion, "choices", None)
    if not choices:
        raise EmotionInferenceError(stage=stage, message="LLM response has no choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None:
        raise EmotionInferenceError(stage=stage, message="LLM response has no message.")

    content = getattr(message, "content", None)
    if not isinstance(content, str) or content.strip() == "":
        raise EmotionInferenceError(
            stage=stage, message="LLM response content is empty."
        )

    return content


def _parse_json_payload(content: str, stage: str) -> dict[str, Any]:
    """LLM 본문 문자열을 JSON 객체로 파싱한다."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise EmotionInferenceError(
            stage=stage,
            message="LLM response is not valid JSON.",
        ) from exc

    if not isinstance(payload, dict):
        raise EmotionInferenceError(
            stage=stage,
            message="LLM response payload must be object.",
        )
    return payload


def _to_score_int(raw_score: float, stage: str) -> int:
    """부동소수 원시 점수를 0~100 정수로 정규화한다."""
    if math.isnan(raw_score) or math.isinf(raw_score):
        raise EmotionInferenceError(stage=stage, message="Score must be finite number.")
    return int(round(min(100.0, max(0.0, raw_score))))


def _convert_base_emotions(raw_scores: _RawBaseEmotionScores) -> EmotionScores:
    """원시 응답을 API 응답용 기본 정서 스키마로 변환한다."""
    emotion_data: dict[str, EmotionConfidenceValue] = {}
    for label in BASE_EMOTION_LABELS:
        raw_item = getattr(raw_scores, label)
        emotion_data[label] = EmotionConfidenceValue(
            confidence=_to_score_int(raw_item.confidence, stage="inference"),
        )
    return EmotionScores(**emotion_data)


def _convert_meeting_signals(raw_signals: _RawMeetingSignals) -> MeetingSignals:
    """원시 회의 시그널을 API 응답 스키마로 변환한다."""
    return MeetingSignals(
        tension=MeetingSignalConfidenceValue(
            confidence=_to_score_int(raw_signals.tension.confidence, stage="inference"),
        ),
        alignment=MeetingSignalConfidenceValue(
            confidence=_to_score_int(
                raw_signals.alignment.confidence, stage="inference"
            ),
        ),
        urgency=MeetingSignalConfidenceValue(
            confidence=_to_score_int(raw_signals.urgency.confidence, stage="inference"),
        ),
        clarity=MeetingSignalConfidenceValue(
            confidence=_to_score_int(raw_signals.clarity.confidence, stage="inference"),
        ),
        engagement=MeetingSignalConfidenceValue(
            confidence=_to_score_int(
                raw_signals.engagement.confidence, stage="inference"
            ),
        ),
    )


def _normalize_emerging_emotions(
    raw_items: list[_RawEmergingEmotion],
) -> list[EmergingEmotion]:
    """추가 발굴 정서를 필터링/정규화한다(기본 정서 제외, 순서 유지, 최대 3개)."""
    base_label_set = {label.casefold() for label in BASE_EMOTION_LABELS}
    seen: set[str] = set()
    normalized: list[EmergingEmotion] = []

    for item in raw_items:
        normalized_label = item.label.casefold()
        key = normalized_label
        if key not in EMERGING_SIGNAL_LABEL_SET:
            continue
        if key in base_label_set or key in seen:
            continue
        seen.add(key)
        normalized.append(
            EmergingEmotion(
                label=normalized_label,
                confidence=_to_score_int(item.confidence, stage="inference"),
            )
        )
        if len(normalized) >= 3:
            break

    return normalized


async def extract_all_emotions_with_llm(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    request: TurnEmotionRequest,
    max_completion_tokens: int = EMOTION_MAX_OUTPUT_TOKENS,
) -> tuple[EmotionScores, MeetingSignals, list[EmergingEmotion]]:
    """통합 비동기 LLM 호출로 모든 정서 정보를 한 번에 추출한다."""
    try:
        completion = await client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=EMOTION_REASONING_EFFORT,
            max_completion_tokens=max_completion_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": INTEGRATED_EMOTION_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_integrated_system_prompt()},
                {"role": "user", "content": _build_user_prompt(request=request)},
            ],
        )
    except Exception as exc:
        raise EmotionInferenceError(
            stage="inference",
            message="Failed to call Azure OpenAI for integrated emotions.",
        ) from exc

    content = _extract_message_content(completion=completion, stage="inference")
    payload = _parse_json_payload(content=content, stage="inference")

    try:
        parsed = _RawIntegratedEmotionPayload.model_validate(payload)
    except Exception as exc:
        raise EmotionInferenceError(
            stage="inference",
            message="Integrated emotion schema validation failed.",
        ) from exc

    base_emotions = _convert_base_emotions(raw_scores=parsed.emotions)
    meeting_signals = _convert_meeting_signals(raw_signals=parsed.meeting_signals)
    emerging_emotions = _normalize_emerging_emotions(raw_items=parsed.emerging_emotions)

    return base_emotions, meeting_signals, emerging_emotions


async def classify_turn_emotion(request: TurnEmotionRequest) -> TurnEmotionResponse:
    """Azure OpenAI 통합 1단계 비동기 추론으로 단일 발화 턴의 정서 정보를 추출한다."""
    try:
        llm_config = get_llm_config()
        client = _build_async_azure_client(llm_config=llm_config)
    except Exception as exc:
        raise EmotionInferenceError(
            stage="config",
            message="LLM configuration loading failed.",
        ) from exc

    (
        base_emotions,
        meeting_signals,
        emerging_emotions,
    ) = await extract_all_emotions_with_llm(
        client=client,
        deployment_name=llm_config.LLM_DEPLOYMENT_NAME,
        request=request,
    )

    return TurnEmotionResponse(
        emotions=base_emotions,
        meeting_signals=meeting_signals,
        emerging_emotions=emerging_emotions,
    )
