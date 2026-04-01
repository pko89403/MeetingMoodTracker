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
    EmotionConfidenceEvidence,
    EmotionScores,
    MeetingSignalConfidenceEvidence,
    MeetingSignals,
    TurnEmotionRequest,
    TurnEmotionResponse,
)
from app.types.llm_config import LlmConfigResponse

DEFAULT_AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
EMOTION_REASONING_EFFORT = "minimal"

BASE_EMOTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_turn_base_emotions",
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
            }
        },
        "required": ["emotions"],
    },
}

MEETING_SIGNALS_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_turn_signals_and_emerging_emotions",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                            "evidence": {"type": "string", "minLength": 1},
                        },
                        "required": ["confidence", "evidence"],
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
                        "evidence": {"type": "string", "minLength": 1},
                    },
                    "required": ["label", "confidence", "evidence"],
                },
            },
        },
        "required": ["meeting_signals", "emerging_emotions"],
    },
}


class _RawEmotionEvidence(BaseModel):
    """LLM 정서 항목 원시 타입."""

    confidence: float
    evidence: str = Field(min_length=1)

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, value: str) -> str:
        """evidence 문자열을 trim한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("evidence must not be blank.")
        return normalized


class _RawBaseEmotionScores(BaseModel):
    """LLM 1단계 기본 정서 원시 스키마."""

    anger: _RawEmotionEvidence
    joy: _RawEmotionEvidence
    sadness: _RawEmotionEvidence
    neutral: _RawEmotionEvidence
    anxiety: _RawEmotionEvidence
    frustration: _RawEmotionEvidence
    excitement: _RawEmotionEvidence
    confusion: _RawEmotionEvidence


class _RawBaseEmotionPayload(BaseModel):
    """LLM 1단계 응답 전체 원시 스키마."""

    emotions: _RawBaseEmotionScores


class _RawMeetingSignals(BaseModel):
    """LLM 2단계 회의 시그널 원시 스키마."""

    tension: _RawEmotionEvidence
    alignment: _RawEmotionEvidence
    urgency: _RawEmotionEvidence
    clarity: _RawEmotionEvidence
    engagement: _RawEmotionEvidence


class _RawEmergingEmotion(BaseModel):
    """LLM 2단계 추가 발굴 정서 원시 스키마."""

    label: str = Field(min_length=1)
    confidence: float
    evidence: str = Field(min_length=1)

    @field_validator("label", "evidence")
    @classmethod
    def validate_non_blank_text(cls, value: str) -> str:
        """label/evidence 문자열을 trim한다."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("text field must not be blank.")
        return normalized


class _RawMeetingSignalsPayload(BaseModel):
    """LLM 2단계 응답 전체 원시 스키마."""

    meeting_signals: _RawMeetingSignals
    emerging_emotions: list[_RawEmergingEmotion] = Field(default_factory=list)


class EmotionInferenceError(Exception):
    """LLM 호출 또는 응답 파싱 단계에서 정서 추출이 실패했을 때 발생한다."""

    def __init__(self, stage: str, message: str) -> None:
        """오류 단계(`config`/`base`/`signals`)와 상세 메시지를 보관한다."""
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


def _build_base_emotion_system_prompt() -> str:
    """1단계(기본 정서 8개) 추출 시스템 프롬프트를 구성한다."""
    return (
        "You analyze one meeting turn and extract eight base emotions. "
        "Input can be Korean with mixed English. "
        "Always return all eight labels: anger, joy, sadness, neutral, anxiety, "
        "frustration, excitement, confusion. "
        "For each label, return confidence 0-100 and one short evidence phrase "
        "quoted from the utterance. "
        "All evidence fields must be written in Korean only. "
        "Do not output English words or mixed-language evidence."
    )


def _build_meeting_signal_system_prompt() -> str:
    """2단계(회의 시그널/추가 정서) 추출 시스템 프롬프트를 구성한다."""
    allowed_labels = ", ".join(EMERGING_SIGNAL_LABELS)
    return (
        "You analyze meeting-specific signals and emerging emotions from one turn. "
        "Return meeting_signals with five axes: tension, alignment, urgency, "
        "clarity, engagement. "
        "For each meeting_signals axis, return confidence 0-100 and evidence. "
        "Return emerging_emotions as additional emotions beyond the eight base labels. "
        "Each emerging item needs label, confidence 0-100, and evidence. "
        "All evidence fields must be written in Korean only. "
        "Do not output English words or mixed-language evidence. "
        "Do not repeat the eight base labels in emerging_emotions. "
        f"Allowed emerging labels set: {allowed_labels}."
    )


def _build_user_prompt(request: TurnEmotionRequest) -> str:
    """요청 필드를 일관된 포맷의 사용자 프롬프트 문자열로 변환한다."""
    speaker_text = request.speaker_id if request.speaker_id is not None else "N/A"
    return (
        f"meeting_id={request.meeting_id}\n"
        f"turn_id={request.turn_id}\n"
        f"speaker_id={speaker_text}\n"
        "utterance:\n"
        f"{request.utterance_text}"
    )


def _build_stage2_user_prompt(
    request: TurnEmotionRequest,
    base_emotions: EmotionScores,
) -> str:
    """2단계 입력용 사용자 프롬프트를 구성한다."""
    emotion_lines = [
        (
            f"- {label}: confidence={getattr(base_emotions, label).confidence}, "
            f"evidence={getattr(base_emotions, label).evidence}"
        )
        for label in BASE_EMOTION_LABELS
    ]
    return (
        _build_user_prompt(request=request)
        + "\n\nbase_emotions:\n"
        + "\n".join(emotion_lines)
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


def _convert_base_emotions(raw_payload: _RawBaseEmotionPayload) -> EmotionScores:
    """1단계 원시 응답을 API 응답용 기본 정서 스키마로 변환한다."""
    emotion_data: dict[str, EmotionConfidenceEvidence] = {}
    for label in BASE_EMOTION_LABELS:
        raw_item = getattr(raw_payload.emotions, label)
        emotion_data[label] = EmotionConfidenceEvidence(
            confidence=_to_score_int(raw_item.confidence, stage="base"),
            evidence=raw_item.evidence,
        )
    return EmotionScores(**emotion_data)


def _convert_meeting_signals(raw_signals: _RawMeetingSignals) -> MeetingSignals:
    """2단계 원시 회의 시그널을 API 응답 스키마로 변환한다."""
    return MeetingSignals(
        tension=MeetingSignalConfidenceEvidence(
            confidence=_to_score_int(raw_signals.tension.confidence, stage="signals"),
            evidence=raw_signals.tension.evidence,
        ),
        alignment=MeetingSignalConfidenceEvidence(
            confidence=_to_score_int(raw_signals.alignment.confidence, stage="signals"),
            evidence=raw_signals.alignment.evidence,
        ),
        urgency=MeetingSignalConfidenceEvidence(
            confidence=_to_score_int(raw_signals.urgency.confidence, stage="signals"),
            evidence=raw_signals.urgency.evidence,
        ),
        clarity=MeetingSignalConfidenceEvidence(
            confidence=_to_score_int(raw_signals.clarity.confidence, stage="signals"),
            evidence=raw_signals.clarity.evidence,
        ),
        engagement=MeetingSignalConfidenceEvidence(
            confidence=_to_score_int(
                raw_signals.engagement.confidence, stage="signals"
            ),
            evidence=raw_signals.engagement.evidence,
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
                confidence=_to_score_int(item.confidence, stage="signals"),
                evidence=item.evidence,
            )
        )
        if len(normalized) >= 3:
            break

    return normalized


async def extract_base_emotions_with_llm(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    request: TurnEmotionRequest,
) -> EmotionScores:
    """1단계 비동기 LLM 호출로 기본 정서 8개를 추출한다."""
    try:
        completion = await client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=EMOTION_REASONING_EFFORT,
            response_format={
                "type": "json_schema",
                "json_schema": BASE_EMOTION_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_base_emotion_system_prompt()},
                {"role": "user", "content": _build_user_prompt(request=request)},
            ],
        )
    except Exception as exc:
        raise EmotionInferenceError(
            stage="base",
            message="Failed to call Azure OpenAI for base emotions.",
        ) from exc

    content = _extract_message_content(completion=completion, stage="base")
    payload = _parse_json_payload(content=content, stage="base")

    try:
        parsed = _RawBaseEmotionPayload.model_validate(payload)
    except Exception as exc:
        raise EmotionInferenceError(
            stage="base",
            message="Base emotion schema validation failed.",
        ) from exc

    return _convert_base_emotions(raw_payload=parsed)


async def extract_meeting_signals_with_llm(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    request: TurnEmotionRequest,
    base_emotions: EmotionScores,
) -> tuple[MeetingSignals, list[EmergingEmotion]]:
    """2단계 비동기 LLM 호출로 회의 시그널 및 추가 발굴 정서를 추출한다."""
    try:
        completion = await client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=EMOTION_REASONING_EFFORT,
            response_format={
                "type": "json_schema",
                "json_schema": MEETING_SIGNALS_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_meeting_signal_system_prompt()},
                {
                    "role": "user",
                    "content": _build_stage2_user_prompt(
                        request=request,
                        base_emotions=base_emotions,
                    ),
                },
            ],
        )
    except Exception as exc:
        raise EmotionInferenceError(
            stage="signals",
            message="Failed to call Azure OpenAI for meeting signals.",
        ) from exc

    content = _extract_message_content(completion=completion, stage="signals")
    payload = _parse_json_payload(content=content, stage="signals")

    try:
        parsed = _RawMeetingSignalsPayload.model_validate(payload)
    except Exception as exc:
        raise EmotionInferenceError(
            stage="signals",
            message="Meeting signal schema validation failed.",
        ) from exc

    meeting_signals = _convert_meeting_signals(raw_signals=parsed.meeting_signals)
    emerging_emotions = _normalize_emerging_emotions(raw_items=parsed.emerging_emotions)
    return meeting_signals, emerging_emotions


async def classify_turn_emotion(request: TurnEmotionRequest) -> TurnEmotionResponse:
    """Azure OpenAI 2단계 비동기 추론으로 단일 발화 턴의 정서 정보를 추출한다."""
    try:
        llm_config = get_llm_config()
        client = _build_async_azure_client(llm_config=llm_config)
    except Exception as exc:
        raise EmotionInferenceError(
            stage="config",
            message="LLM configuration loading failed.",
        ) from exc

    base_emotions = await extract_base_emotions_with_llm(
        client=client,
        deployment_name=llm_config.LLM_DEPLOYMENT_NAME,
        request=request,
    )
    meeting_signals, emerging_emotions = await extract_meeting_signals_with_llm(
        client=client,
        deployment_name=llm_config.LLM_DEPLOYMENT_NAME,
        request=request,
        base_emotions=base_emotions,
    )

    return TurnEmotionResponse(
        emotions=base_emotions,
        meeting_signals=meeting_signals,
        emerging_emotions=emerging_emotions,
    )
