"""Analyze 파이프라인 공통 실행 로직."""

import json
import math
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from openai import AzureOpenAI

from app.service.llm_config_service import get_llm_config
from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeLogicStep,
)
from app.types.analyze_llm import (
    EmotionExtractionResult,
    SentimentExtractionResult,
    TopicExtractionResult,
)
from app.types.emotion import BASE_EMOTION_LABELS
from app.types.llm_config import LlmConfigResponse
from app.types.mood import (
    AnalyzeCorrelation,
    AnalyzeEmotion,
    AnalyzeEmotionDistribution,
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeSentiment,
    AnalyzeSentimentDistribution,
    AnalyzeTopic,
    AnalyzeTopicCandidate,
)

DEFAULT_AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
TOPIC_REASONING_EFFORT = "none"
SENTIMENT_REASONING_EFFORT = "minimal"
EMOTION_REASONING_EFFORT = "minimal"
MAX_ANALYZE_LOG_BUFFER_SIZE = 200

TOPIC_MAX_OUTPUT_TOKENS = 120
SENTIMENT_MAX_OUTPUT_TOKENS = 80
EMOTION_MAX_OUTPUT_TOKENS = 180

TOPIC_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_topic_facets",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "topics": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "label": {"type": "string", "minLength": 1, "maxLength": 60},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    },
                    "required": ["label", "confidence"],
                },
            }
        },
        "required": ["topics"],
    },
}

SENTIMENT_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_sentiment_distribution_compact",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "sentiment": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "positive": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "negative": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "neutral": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                },
                "required": ["positive", "negative", "neutral"],
            }
        },
        "required": ["sentiment"],
    },
}

EMOTION_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_emotion_distribution_compact",
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
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "joy": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "sadness": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "neutral": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "anxiety": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "frustration": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "excitement": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
                        "required": ["confidence"],
                    },
                    "confusion": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"confidence": {"type": "number"}},
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
            }
        },
        "required": ["emotions"],
    },
}

_TOPIC_STOPWORD_PATTERN = re.compile(
    r"(?i)\b(?:um+|uh+|like|you know|i mean|sort of|kind of)\b|"
    r"(?:음+|어+|그냥|약간|뭐랄까|저기|일단)"
)
_TOPIC_ALLOWED_CHARS_PATTERN = re.compile(r"[^0-9A-Za-z가-힣\s.,!?/&()_-]")
_MULTI_SPACE_PATTERN = re.compile(r"\s+")

_SENTIMENT_AXIS_ORDER: tuple[str, ...] = ("positive", "negative", "neutral")
_POSITIVE_EMOTIONS: tuple[str, ...] = ("joy", "excitement")
_NEGATIVE_EMOTIONS: tuple[str, ...] = (
    "anger",
    "sadness",
    "anxiety",
    "frustration",
    "confusion",
)

_analyze_log_buffer: deque[AnalyzeLogEntry] = deque(maxlen=MAX_ANALYZE_LOG_BUFFER_SIZE)
_analyze_log_lock = Lock()

_ANALYZE_LOGIC_STEPS: tuple[AnalyzeLogicStep, ...] = (
    AnalyzeLogicStep(
        step_id="receive_request",
        title_ko="입력 수신",
        description_ko="요청 본문(meeting_id, text)을 수신하고 기본 메타를 확인합니다.",
    ),
    AnalyzeLogicStep(
        step_id="extract_topic",
        title_ko="Topic 세분화",
        description_ko="topic 후보와 confidence를 추출합니다.",
    ),
    AnalyzeLogicStep(
        step_id="analyze_sentiment",
        title_ko="Sentiment 세분화",
        description_ko="positive/negative/neutral 분포를 추출합니다.",
    ),
    AnalyzeLogicStep(
        step_id="analyze_emotion",
        title_ko="Emotion 세분화",
        description_ko="기본 8정서 분포를 추출합니다.",
    ),
    AnalyzeLogicStep(
        step_id="compose_response",
        title_ko="Correlation 재조합",
        description_ko="topic/sentiment/emotion 상관도를 계산해 최종 응답을 조합합니다.",
    ),
)


class AnalyzeInferenceError(Exception):
    """Analyze 파이프라인의 LLM 추론 단계에서 오류가 발생했을 때 사용한다."""

    def __init__(self, stage: str, message: str) -> None:
        """오류 단계와 상세 메시지를 보관한다."""
        self.stage = stage
        super().__init__(message)


def _now_iso_utc() -> str:
    """UTC 기준 ISO8601 타임스탬프 문자열을 생성한다."""
    return datetime.now(tz=timezone.utc).isoformat()


def _new_request_id() -> str:
    """analyze 요청 식별자를 생성한다."""
    return f"anl_{uuid4().hex[:12]}"


def create_analyze_request_id() -> str:
    """외부 호출자용 analyze 요청 식별자를 생성한다."""
    return _new_request_id()


def get_analyze_logic_steps() -> list[AnalyzeLogicStep]:
    """UI 표시용 analyze 로직 단계 목록을 복제해 반환한다."""
    return [step.model_copy(deep=True) for step in _ANALYZE_LOGIC_STEPS]


def _append_log(entry: AnalyzeLogEntry) -> None:
    """전역 링버퍼에 로그를 저장한다."""
    with _analyze_log_lock:
        _analyze_log_buffer.append(entry)


def list_recent_analyze_logs(
    limit: int = 50,
    request_id: str | None = None,
) -> list[AnalyzeLogEntry]:
    """메모리 링버퍼에 저장된 최근 로그를 반환한다."""
    normalized_limit = max(1, min(limit, MAX_ANALYZE_LOG_BUFFER_SIZE))
    with _analyze_log_lock:
        snapshot = list(_analyze_log_buffer)

    if request_id is not None and request_id.strip() != "":
        snapshot = [entry for entry in snapshot if entry.request_id == request_id]
    return snapshot[-normalized_limit:]


def _record_log(
    request_id: str,
    step_id: str,
    message_ko: str,
    collected_logs: list[AnalyzeLogEntry],
    on_log: Callable[[AnalyzeLogEntry], None] | None,
) -> None:
    """파이프라인 로그를 생성/버퍼링/콜백 전파한다."""
    entry = AnalyzeLogEntry(
        request_id=request_id,
        step_id=step_id,
        message_ko=message_ko,
        created_at=_now_iso_utc(),
    )
    _append_log(entry=entry)
    collected_logs.append(entry)
    if on_log is not None:
        on_log(entry)


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


def _build_azure_client(llm_config: LlmConfigResponse) -> AzureOpenAI:
    """검증된 LLM 설정으로 Azure OpenAI SDK 클라이언트를 생성한다."""
    return AzureOpenAI(
        api_key=llm_config.LLM_API_KEY,
        azure_endpoint=llm_config.LLM_ENDPOINT,
        api_version=_resolve_api_version(llm_config=llm_config),
    )


def preprocess_for_topic(text: str) -> str:
    """토픽 추출 품질을 높이기 위한 텍스트 전처리를 수행한다."""
    normalized_text = _TOPIC_ALLOWED_CHARS_PATTERN.sub(" ", text)
    without_stopwords = _TOPIC_STOPWORD_PATTERN.sub(" ", normalized_text)
    return _MULTI_SPACE_PATTERN.sub(" ", without_stopwords).strip()


def _build_topic_system_prompt() -> str:
    """Topic 세분화 추출용 시스템 프롬프트를 구성한다."""
    return (
        "Extract 1 to 3 concise meeting topics from the input text. "
        "Input can be Korean with mixed English. "
        "Return only JSON with topics[]. "
        "Each topic item must include label and confidence(0-100). "
        "Keep labels short noun phrases."
    )


def _build_topic_user_prompt(preprocessed_text: str) -> str:
    """Topic 추출용 사용자 프롬프트를 구성한다."""
    return "preprocessed_meeting_text:\n" + preprocessed_text


def _build_sentiment_system_prompt() -> str:
    """Sentiment 세분화 추출용 시스템 프롬프트를 구성한다."""
    return (
        "Analyze meeting sentiment distribution. "
        "Return only JSON with positive, negative, neutral confidence. "
        "Do not add explanations."
    )


def _build_sentiment_user_prompt(original_text: str) -> str:
    """Sentiment 추출용 사용자 프롬프트를 구성한다."""
    return "meeting_text:\n" + original_text


def _build_emotion_system_prompt() -> str:
    """Emotion 세분화 추출용 시스템 프롬프트를 구성한다."""
    return (
        "Analyze emotion distribution for one meeting text. "
        "Return only JSON with eight emotion confidences: "
        "anger, joy, sadness, neutral, anxiety, frustration, excitement, confusion. "
        "Use confidence 0-100."
    )


def _build_emotion_user_prompt(original_text: str) -> str:
    """Emotion 추출용 사용자 프롬프트를 구성한다."""
    return "meeting_text:\n" + original_text


def _extract_message_content(completion: Any, stage: str) -> str:
    """Chat completion 결과에서 비어 있지 않은 본문 문자열을 추출한다."""
    choices = getattr(completion, "choices", None)
    if not choices:
        raise AnalyzeInferenceError(stage=stage, message="LLM response has no choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None:
        raise AnalyzeInferenceError(stage=stage, message="LLM response has no message.")

    content = getattr(message, "content", None)
    if not isinstance(content, str) or content.strip() == "":
        raise AnalyzeInferenceError(stage=stage, message="LLM response content is empty.")

    return content


def _parse_json_payload(content: str, stage: str) -> dict[str, Any]:
    """LLM 본문 문자열을 JSON 객체로 파싱한다."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AnalyzeInferenceError(stage=stage, message="LLM response is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise AnalyzeInferenceError(stage=stage, message="LLM response payload must be object.")
    return payload


def _to_score_int(raw_score: float) -> int:
    """부동소수 원시 점수를 0~100 정수로 정규화한다."""
    if math.isnan(raw_score) or math.isinf(raw_score):
        return 0
    return int(round(min(100.0, max(0.0, raw_score))))


def _normalize_distribution(
    raw_scores: list[float],
    labels: tuple[str, ...],
    stage: str,
) -> dict[str, int]:
    """원시 점수를 합계 100 정수 분포로 정규화한다."""
    if len(raw_scores) != len(labels):
        raise AnalyzeInferenceError(stage=stage, message="Distribution length mismatch.")

    clamped = [max(0.0, score) for score in raw_scores]
    total = sum(clamped)
    if total <= 0:
        clamped = [1.0] * len(labels)
        total = float(len(labels))

    scaled = [(value / total) * 100.0 for value in clamped]
    floors = [math.floor(value) for value in scaled]
    fractions = [scaled[idx] - floors[idx] for idx in range(len(labels))]
    remainder = 100 - sum(floors)
    order = sorted(range(len(labels)), key=lambda idx: (-fractions[idx], idx))
    for idx in order[:remainder]:
        floors[idx] += 1

    return {label: floors[idx] for idx, label in enumerate(labels)}


def _normalize_topic_candidates(
    raw_topics: list[Any],
) -> list[AnalyzeTopicCandidate]:
    """Topic 후보 목록을 정규화한다."""
    candidates: list[AnalyzeTopicCandidate] = []
    seen: set[str] = set()

    for raw_item in raw_topics:
        label = raw_item.label.strip()
        if label == "":
            continue
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            AnalyzeTopicCandidate(
                label=label,
                confidence=_to_score_int(raw_item.confidence),
            )
        )
        if len(candidates) >= 3:
            break

    if not candidates:
        raise AnalyzeInferenceError(stage="topic", message="No valid topics extracted.")
    return candidates


def _pick_max_axis(
    values: dict[str, int],
    axis_order: tuple[str, ...],
) -> tuple[str, int]:
    """축 순서를 tie-break로 사용해 최댓값 축을 선택한다."""
    best_axis = axis_order[0]
    best_score = -1
    for axis in axis_order:
        score = values[axis]
        if score > best_score:
            best_axis = axis
            best_score = score
    return best_axis, best_score


def _build_correlation_summary(
    topic: AnalyzeTopic,
    sentiment: AnalyzeSentiment,
    emotion: AnalyzeEmotion,
    sentiment_emotion: int,
) -> str:
    """상관도 요약 문장을 생성한다."""
    if sentiment_emotion >= 70:
        level = "높은"
    elif sentiment_emotion >= 40:
        level = "중간"
    else:
        level = "낮은"

    return (
        f"주요 토픽 '{topic.primary}'에서 "
        f"{sentiment.polarity} 감성과 '{emotion.primary}' 감정의 상관도가 "
        f"{level} 수준으로 관찰되었습니다."
    )


def _compute_correlation(
    topic: AnalyzeTopic,
    sentiment: AnalyzeSentiment,
    emotion: AnalyzeEmotion,
) -> AnalyzeCorrelation:
    """세분화 결과를 상관도 중심으로 재조합한다."""
    topic_weight = topic.candidates[0].confidence
    sentiment_weight = sentiment.confidence
    emotion_weight = emotion.confidence

    sentiment_valence = sentiment.distribution.positive - sentiment.distribution.negative
    emotion_positive = sum(getattr(emotion.distribution, label) for label in _POSITIVE_EMOTIONS)
    emotion_negative = sum(getattr(emotion.distribution, label) for label in _NEGATIVE_EMOTIONS)
    emotion_valence = emotion_positive - emotion_negative
    alignment = 100 - min(100, abs(sentiment_valence - emotion_valence))

    topic_sentiment = _to_score_int((topic_weight + sentiment_weight) / 2.0)
    topic_emotion = _to_score_int((topic_weight + emotion_weight) / 2.0)
    sentiment_emotion = _to_score_int(
        (sentiment_weight + emotion_weight + alignment) / 3.0
    )

    return AnalyzeCorrelation(
        topic_sentiment=topic_sentiment,
        topic_emotion=topic_emotion,
        sentiment_emotion=sentiment_emotion,
        summary=_build_correlation_summary(
            topic=topic,
            sentiment=sentiment,
            emotion=emotion,
            sentiment_emotion=sentiment_emotion,
        ),
    )


def extract_topics_with_llm(
    client: AzureOpenAI,
    deployment_name: str,
    preprocessed_text: str,
) -> AnalyzeTopic:
    """Topic 세분화 결과를 LLM으로 추출한다."""
    if preprocessed_text.strip() == "":
        raise AnalyzeInferenceError(stage="topic", message="Preprocessed text is empty.")

    try:
        completion = client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=TOPIC_REASONING_EFFORT,
            max_completion_tokens=TOPIC_MAX_OUTPUT_TOKENS,
            response_format={
                "type": "json_schema",
                "json_schema": TOPIC_EXTRACTION_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_topic_system_prompt()},
                {
                    "role": "user",
                    "content": _build_topic_user_prompt(
                        preprocessed_text=preprocessed_text,
                    ),
                },
            ],
        )
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="topic",
            message="Failed to call Azure OpenAI for topic extraction.",
        ) from exc

    content = _extract_message_content(completion=completion, stage="topic")
    payload = _parse_json_payload(content=content, stage="topic")
    try:
        parsed = TopicExtractionResult.model_validate(payload)
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="topic",
            message="Topic extraction schema validation failed.",
        ) from exc

    candidates = _normalize_topic_candidates(raw_topics=parsed.topics)
    return AnalyzeTopic(primary=candidates[0].label, candidates=candidates)


def analyze_sentiment_with_llm(
    client: AzureOpenAI,
    deployment_name: str,
    original_text: str,
) -> AnalyzeSentiment:
    """Sentiment 세분화 결과를 LLM으로 추출한다."""
    if original_text.strip() == "":
        raise AnalyzeInferenceError(stage="sentiment", message="Original text is empty.")

    try:
        completion = client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=SENTIMENT_REASONING_EFFORT,
            max_completion_tokens=SENTIMENT_MAX_OUTPUT_TOKENS,
            response_format={
                "type": "json_schema",
                "json_schema": SENTIMENT_EXTRACTION_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_sentiment_system_prompt()},
                {"role": "user", "content": _build_sentiment_user_prompt(original_text)},
            ],
        )
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="sentiment",
            message="Failed to call Azure OpenAI for sentiment analysis.",
        ) from exc

    content = _extract_message_content(completion=completion, stage="sentiment")
    payload = _parse_json_payload(content=content, stage="sentiment")
    try:
        parsed = SentimentExtractionResult.model_validate(payload)
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="sentiment",
            message="Sentiment schema validation failed.",
        ) from exc

    normalized = _normalize_distribution(
        raw_scores=[
            parsed.sentiment.positive.confidence,
            parsed.sentiment.negative.confidence,
            parsed.sentiment.neutral.confidence,
        ],
        labels=_SENTIMENT_AXIS_ORDER,
        stage="sentiment",
    )
    distribution = AnalyzeSentimentDistribution(**normalized)
    polarity, confidence = _pick_max_axis(
        values=normalized,
        axis_order=_SENTIMENT_AXIS_ORDER,
    )
    return AnalyzeSentiment(
        distribution=distribution,
        polarity=polarity,  # type: ignore[arg-type]
        confidence=confidence,
    )


def analyze_emotion_with_llm(
    client: AzureOpenAI,
    deployment_name: str,
    original_text: str,
) -> AnalyzeEmotion:
    """Emotion 세분화 결과를 LLM으로 추출한다."""
    if original_text.strip() == "":
        raise AnalyzeInferenceError(stage="emotion", message="Original text is empty.")

    try:
        completion = client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=EMOTION_REASONING_EFFORT,
            max_completion_tokens=EMOTION_MAX_OUTPUT_TOKENS,
            response_format={
                "type": "json_schema",
                "json_schema": EMOTION_EXTRACTION_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_emotion_system_prompt()},
                {"role": "user", "content": _build_emotion_user_prompt(original_text)},
            ],
        )
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="emotion",
            message="Failed to call Azure OpenAI for emotion analysis.",
        ) from exc

    content = _extract_message_content(completion=completion, stage="emotion")
    payload = _parse_json_payload(content=content, stage="emotion")
    try:
        parsed = EmotionExtractionResult.model_validate(payload)
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="emotion",
            message="Emotion schema validation failed.",
        ) from exc

    normalized = _normalize_distribution(
        raw_scores=[getattr(parsed.emotions, label).confidence for label in BASE_EMOTION_LABELS],
        labels=BASE_EMOTION_LABELS,
        stage="emotion",
    )
    distribution = AnalyzeEmotionDistribution(**normalized)
    primary, confidence = _pick_max_axis(
        values=normalized,
        axis_order=BASE_EMOTION_LABELS,
    )
    return AnalyzeEmotion(
        distribution=distribution,
        primary=primary,  # type: ignore[arg-type]
        confidence=confidence,
    )


def run_analyze_pipeline(
    request: AnalyzeRequest,
    on_log: Callable[[AnalyzeLogEntry], None] | None = None,
    request_id: str | None = None,
) -> AnalyzeInspectResponse:
    """`/analyze`, `/inspect`, `/inspect/stream`가 공통으로 호출하는 단일 메서드."""
    resolved_request_id = request_id or create_analyze_request_id()
    collected_logs: list[AnalyzeLogEntry] = []

    _record_log(
        request_id=resolved_request_id,
        step_id="receive_request",
        message_ko=(
            f"요청 수신 완료: meeting_id={request.meeting_id}, "
            f"text_length={len(request.text)}"
        ),
        collected_logs=collected_logs,
        on_log=on_log,
    )

    try:
        llm_config = get_llm_config()
        topic_client = _build_azure_client(llm_config=llm_config)
        sentiment_client = _build_azure_client(llm_config=llm_config)
        emotion_client = _build_azure_client(llm_config=llm_config)
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="config",
            message="LLM 설정 로드 또는 클라이언트 생성에 실패했습니다.",
        ) from exc

    preprocessed_text = preprocess_for_topic(text=request.text)

    with ThreadPoolExecutor(max_workers=3) as executor:
        topic_future = executor.submit(
            extract_topics_with_llm,
            topic_client,
            llm_config.LLM_DEPLOYMENT_NAME,
            preprocessed_text,
        )
        sentiment_future = executor.submit(
            analyze_sentiment_with_llm,
            sentiment_client,
            llm_config.LLM_DEPLOYMENT_NAME,
            request.text,
        )
        emotion_future = executor.submit(
            analyze_emotion_with_llm,
            emotion_client,
            llm_config.LLM_DEPLOYMENT_NAME,
            request.text,
        )

        topic = topic_future.result()
        _record_log(
            request_id=resolved_request_id,
            step_id="extract_topic",
            message_ko=(
                "Topic 세분화 완료: "
                f"primary={topic.primary}, candidates={len(topic.candidates)}"
            ),
            collected_logs=collected_logs,
            on_log=on_log,
        )

        sentiment = sentiment_future.result()
        _record_log(
            request_id=resolved_request_id,
            step_id="analyze_sentiment",
            message_ko=(
                "Sentiment 세분화 완료: "
                f"polarity={sentiment.polarity}, confidence={sentiment.confidence}"
            ),
            collected_logs=collected_logs,
            on_log=on_log,
        )

        emotion = emotion_future.result()
        _record_log(
            request_id=resolved_request_id,
            step_id="analyze_emotion",
            message_ko=(
                "Emotion 세분화 완료: "
                f"primary={emotion.primary}, confidence={emotion.confidence}"
            ),
            collected_logs=collected_logs,
            on_log=on_log,
        )

    correlation = _compute_correlation(
        topic=topic,
        sentiment=sentiment,
        emotion=emotion,
    )

    result = AnalyzeResponse(
        topic=topic,
        sentiment=sentiment,
        emotion=emotion,
        correlation=correlation,
    )
    _record_log(
        request_id=resolved_request_id,
        step_id="compose_response",
        message_ko=(
            "Correlation 재조합 완료: "
            f"ts={correlation.topic_sentiment}, "
            f"te={correlation.topic_emotion}, "
            f"se={correlation.sentiment_emotion}"
        ),
        collected_logs=collected_logs,
        on_log=on_log,
    )

    return AnalyzeInspectResponse(
        request_id=resolved_request_id,
        result=result,
        logic_steps=get_analyze_logic_steps(),
        logs=collected_logs,
    )
