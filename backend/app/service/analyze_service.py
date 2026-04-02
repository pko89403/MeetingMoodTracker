"""Analyze 파이프라인 공통 실행 로직."""

import asyncio
import json
import math
import re
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from openai import AsyncAzureOpenAI

from app.service.emotion_service import (
    EmotionInferenceError,
    extract_all_emotions_with_llm,
)
from app.service.llm_config_service import get_llm_config
from app.types.analyze_inspect import (
    AnalyzeInspectResponse,
    AnalyzeLogEntry,
    AnalyzeLogicStep,
)
from app.types.analyze_llm import SentimentExtractionResult, TopicExtractionResult
from app.types.emotion import TurnEmotionRequest, TurnEmotionResponse
from app.types.llm_config import LlmConfigResponse
from app.types.mood import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeSentiment,
    MeetingRubrics,
    SentimentConfidence,
)

DEFAULT_AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
TOPIC_REASONING_EFFORT = "none"
SENTIMENT_REASONING_EFFORT = "none"
MAX_ANALYZE_LOG_BUFFER_SIZE = 200
TOPIC_MAX_OUTPUT_TOKENS = 1024
SENTIMENT_MAX_OUTPUT_TOKENS = 1024
EMOTION_MAX_OUTPUT_TOKENS = 2048

TOPIC_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_topic_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "topics": {
                "type": "array",
                "items": {
                    "type": "string",
                    "minLength": 1,
                },
                "minItems": 1,
            }
        },
        "required": ["topics"],
    },
}

SENTIMENT_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "meeting_sentiment_distribution",
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

_TOPIC_STOPWORD_PATTERN = re.compile(
    r"(?i)\b(?:um+|uh+|like|you know|i mean|sort of|kind of)\b|"
    r"(?:음+|어+|그냥|약간|뭐랄까|저기|일단)"
)
_TOPIC_ALLOWED_CHARS_PATTERN = re.compile(r"[^0-9A-Za-z가-힣\s.,!?/&()_-]")
_MULTI_SPACE_PATTERN = re.compile(r"\s+")

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
        title_ko="의제 추론",
        description_ko="전처리된 텍스트를 기반으로 LLM이 topics 리스트를 구조화 추출합니다.",
    ),
    AnalyzeLogicStep(
        step_id="analyze_sentiment",
        title_ko="감정 분포 추론",
        description_ko=(
            "원문 텍스트와 topic 리스트(있을 경우)를 입력해 "
            "positive/negative/neutral confidence를 추론합니다."
        ),
    ),
    AnalyzeLogicStep(
        step_id="analyze_emotion",
        title_ko="정서 신호 추론",
        description_ko=(
            "원문 텍스트를 기반으로 기본 8정서, 회의 시그널, "
            "추가 발굴 정서를 2-stage로 추론합니다."
        ),
    ),
    AnalyzeLogicStep(
        step_id="compose_response",
        title_ko="응답 조합",
        description_ko="topics를 단일 topic 문자열로 결합해 API 응답 스키마를 조합합니다.",
    ),
)


class AnalyzeInferenceError(Exception):
    """Analyze 파이프라인의 LLM 추론 단계에서 오류가 발생했을 때 사용한다."""

    def __init__(self, stage: str, message: str) -> None:
        """오류 단계(`topic`/`sentiment`/`config`)와 상세 메시지를 보관한다."""
        self.stage = stage
        super().__init__(message)


def _build_analyze_turn_emotion_request(
    original_text: str, meeting_id: str | None = None
) -> TurnEmotionRequest:
    """분석 텍스트를 emotion 추론용 턴 요청 스키마로 변환한다."""
    return TurnEmotionRequest(
        meeting_id=meeting_id or "analyze_meeting",
        turn_id="analyze_turn",
        speaker_id=None,
        utterance_text=original_text,
    )


async def analyze_emotion_with_llm(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    original_text: str,
    meeting_id: str | None = None,
    max_completion_tokens: int = EMOTION_MAX_OUTPUT_TOKENS,
) -> TurnEmotionResponse:
    """emotion 서비스의 통합 1단계 비동기 추론을 analyze 파이프라인에 통합한다."""
    emotion_request = _build_analyze_turn_emotion_request(
        original_text=original_text, meeting_id=meeting_id
    )
    try:
        (
            base_emotions,
            meeting_signals,
            emerging_emotions,
        ) = await extract_all_emotions_with_llm(
            client=client,
            deployment_name=deployment_name,
            request=emotion_request,
            max_completion_tokens=max_completion_tokens,
        )
    except EmotionInferenceError as exc:
        raise AnalyzeInferenceError(
            stage=exc.stage,
            message=str(exc),
        ) from exc

    return TurnEmotionResponse(
        emotions=base_emotions,
        meeting_signals=meeting_signals,
        emerging_emotions=emerging_emotions,
    )


def calculate_final_rubrics(
    topics: list[str],
    sentiment: AnalyzeSentiment,
    emotion: TurnEmotionResponse,
) -> MeetingRubrics:
    """추출된 모든 지표(Topic, Sentiment, Emotion)를 조합하여 최종 루브릭 지수를 산출한다."""
    # 회의 시그널 데이터 확보
    sig = emotion.meeting_signals
    e = sig.engagement.confidence
    t = sig.tension.confidence
    c = sig.clarity.confidence
    a = sig.alignment.confidence
    u = sig.urgency.confidence

    # 1. Dominance (주도성): 대화 주도권 및 영향력
    # 로직: 기본 시그널 조합 + Sentiment의 Neutral이 낮을수록 주도적 분석으로 판단
    base_dominance = e * 0.35 + t * 0.25 + c * 0.20 + a * 0.10 + u * 0.10
    sentiment_bonus = (100.0 - sentiment.neutral.confidence) * 0.1
    final_dominance = base_dominance + sentiment_bonus

    # 2. Efficiency (효율성): 결론 도출 및 논의 생산성
    # 로직: Clarity/Urgency 조합 + Topic이 명확히 추출되었는지(갯수) 반영
    base_efficiency = c * 0.50 + u * 0.30 + e * 0.20
    topic_bonus = min(len(topics) * 5.0, 15.0)  # 주제가 구체적일수록 보너스
    final_efficiency = base_efficiency + topic_bonus

    # 3. Cohesion (결속력): 팀 내 합의 및 긍정적 에너지
    # 로직: Alignment/Engagement 조합 + Positive Sentiment 가중치 반영
    base_cohesion = a * 0.40 + e * 0.30 + (100.0 - t) * 0.10
    sentiment_positive_bonus = sentiment.positive.confidence * 0.2
    final_cohesion = base_cohesion + sentiment_positive_bonus

    return MeetingRubrics(
        dominance=int(round(min(100.0, max(0.0, final_dominance)))),
        efficiency=int(round(min(100.0, max(0.0, final_efficiency)))),
        cohesion=int(round(min(100.0, max(0.0, final_cohesion)))),
    )


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


def _build_azure_client(llm_config: LlmConfigResponse) -> AsyncAzureOpenAI:
    """검증된 LLM 설정으로 Azure OpenAI SDK 비동기 클라이언트를 생성한다."""
    return AsyncAzureOpenAI(
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
    """토픽 추출용 시스템 프롬프트를 구성한다."""
    return (
        "You extract concise meeting topics from transcript text. "
        "Input can be Korean and English mixed. "
        "Return 1-5 concrete topics ordered by relevance. "
        "Each topic should be short noun phrase."
    )


def _build_topic_user_prompt(preprocessed_text: str) -> str:
    """토픽 추출용 사용자 프롬프트를 구성한다."""
    return "preprocessed_meeting_text:\n" + preprocessed_text


def _build_sentiment_system_prompt() -> str:
    """감정 분포 추출용 시스템 프롬프트를 구성한다."""
    return (
        "You analyze meeting sentiment distribution. "
        "Use both meeting topics and original meeting text. "
        "Return positive, negative, and neutral confidence values. "
        "Confidence values can be raw scores and will be normalized by server."
    )


def _build_sentiment_user_prompt(
    original_text: str, topics: list[str] | None = None
) -> str:
    """감정 분포 추출용 사용자 프롬프트를 구성한다."""
    if topics:
        topic_lines = "\n".join(f"- {topic}" for topic in topics)
        return f"extracted_topics:\n{topic_lines}\n\nmeeting_text:\n{original_text}"
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
        raise AnalyzeInferenceError(
            stage=stage, message="LLM response content is empty."
        )

    return content


def _parse_json_payload(content: str, stage: str) -> dict[str, Any]:
    """LLM 본문 문자열을 JSON 객체로 파싱한다."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AnalyzeInferenceError(
            stage=stage, message="LLM response is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise AnalyzeInferenceError(
            stage=stage, message="LLM response payload must be object."
        )
    return payload


def _normalize_topics(raw_topics: list[str]) -> list[str]:
    """토픽 리스트를 정리하고 비어 있으면 오류를 발생시킨다."""
    cleaned_topics: list[str] = []
    seen: set[str] = set()

    for raw_topic in raw_topics:
        normalized = raw_topic.strip()
        if normalized == "":
            continue
        dedupe_key = normalized.casefold()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        cleaned_topics.append(normalized)

    if not cleaned_topics:
        raise AnalyzeInferenceError(stage="topic", message="No valid topics extracted.")
    return cleaned_topics


def _normalize_sentiment_confidences(
    positive_raw: float,
    negative_raw: float,
    neutral_raw: float,
) -> AnalyzeSentiment:
    """감정 confidence 원시값을 0~100 정수 퍼센트(합계 100)로 정규화한다."""
    axis_values = [
        max(0.0, positive_raw),
        max(0.0, negative_raw),
        max(0.0, neutral_raw),
    ]
    total = sum(axis_values)
    if total <= 0:
        axis_values = [1.0, 1.0, 1.0]
        total = 3.0

    scaled = [(value / total) * 100.0 for value in axis_values]
    floors = [math.floor(value) for value in scaled]
    fractions = [scaled[idx] - floors[idx] for idx in range(3)]
    remainder = 100 - sum(floors)

    # Largest Remainder + tie-break(positive -> negative -> neutral)
    order = sorted(range(3), key=lambda idx: (-fractions[idx], idx))
    for idx in order[:remainder]:
        floors[idx] += 1

    positive_value, negative_value, neutral_value = floors
    sentiment = AnalyzeSentiment(
        positive=SentimentConfidence(confidence=positive_value),
        negative=SentimentConfidence(confidence=negative_value),
        neutral=SentimentConfidence(confidence=neutral_value),
    )
    normalized_total = (
        sentiment.positive.confidence
        + sentiment.negative.confidence
        + sentiment.neutral.confidence
    )
    if normalized_total != 100:
        raise AnalyzeInferenceError(
            stage="sentiment",
            message="Normalized sentiment confidence total must be 100.",
        )
    return sentiment


async def extract_topics_with_llm(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    preprocessed_text: str,
    max_completion_tokens: int = TOPIC_MAX_OUTPUT_TOKENS,
) -> list[str]:
    """비동기 LLM JSON structured 출력으로 토픽 리스트를 추출한다."""
    if preprocessed_text.strip() == "":
        raise AnalyzeInferenceError(
            stage="topic", message="Preprocessed text is empty."
        )

    try:
        completion = await client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=TOPIC_REASONING_EFFORT,
            max_completion_tokens=max_completion_tokens,
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

    return _normalize_topics(raw_topics=parsed.topics)


async def analyze_sentiment_with_llm(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    original_text: str,
    topics: list[str] | None = None,
    max_completion_tokens: int = SENTIMENT_MAX_OUTPUT_TOKENS,
) -> AnalyzeSentiment:
    """토픽 컨텍스트(있을 경우)와 원문 텍스트를 사용해 감정 분포를 추출한다."""
    if original_text.strip() == "":
        raise AnalyzeInferenceError(
            stage="sentiment", message="Original text is empty."
        )

    try:
        completion = await client.chat.completions.create(
            model=deployment_name,
            reasoning_effort=SENTIMENT_REASONING_EFFORT,
            max_completion_tokens=max_completion_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": SENTIMENT_EXTRACTION_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_sentiment_system_prompt()},
                {
                    "role": "user",
                    "content": _build_sentiment_user_prompt(
                        original_text=original_text,
                        topics=topics,
                    ),
                },
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

    return _normalize_sentiment_confidences(
        positive_raw=parsed.sentiment.positive.confidence,
        negative_raw=parsed.sentiment.negative.confidence,
        neutral_raw=parsed.sentiment.neutral.confidence,
    )


def _compose_topic_string(topics: list[str]) -> str:
    """topics 리스트를 단일 응답 문자열로 결합한다."""
    if not topics:
        raise AnalyzeInferenceError(stage="topic", message="Topics are empty.")
    return ", ".join(topics)


async def run_analyze_pipeline(
    request: AnalyzeRequest,
    on_log: Callable[[AnalyzeLogEntry], None] | None = None,
    request_id: str | None = None,
) -> AnalyzeInspectResponse:
    """`/analyze`, `/inspect`, `/inspect/stream`가 공통으로 호출하는 비동기 메서드."""
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
        client = _build_azure_client(llm_config=llm_config)
    except Exception as exc:
        raise AnalyzeInferenceError(
            stage="config",
            message="LLM 설정 로드 또는 클라이언트 생성에 실패했습니다.",
        ) from exc

    preprocessed_text = preprocess_for_topic(text=request.text)

    # asyncio.gather를 통한 비동기 병렬 실행 (Fan-out)
    try:
        topic_task = extract_topics_with_llm(
            client,
            llm_config.LLM_DEPLOYMENT_NAME,
            preprocessed_text,
        )
        sentiment_task = analyze_sentiment_with_llm(
            client,
            llm_config.LLM_DEPLOYMENT_NAME,
            request.text,
            None,  # 병렬화를 위해 topics 의존성 제거
        )
        emotion_task = analyze_emotion_with_llm(
            client,
            llm_config.LLM_DEPLOYMENT_NAME,
            request.text,
            request.meeting_id,
            EMOTION_MAX_OUTPUT_TOKENS,
        )

        # 모든 추론 작업을 동시에 실행
        topics, sentiment, emotion = await asyncio.gather(
            topic_task, sentiment_task, emotion_task
        )
    except Exception as exc:
        if isinstance(exc, AnalyzeInferenceError):
            raise exc
        raise AnalyzeInferenceError(
            stage="pipeline",
            message=f"비동기 파이프라인 실행 중 오류 발생: {exc}",
        ) from exc

    # 결과 수집 및 로그 기록
    topic_str = _compose_topic_string(topics=topics)
    _record_log(
        request_id=resolved_request_id,
        step_id="extract_topic",
        message_ko=f"의제 추론 완료: topics={topics}",
        collected_logs=collected_logs,
        on_log=on_log,
    )

    _record_log(
        request_id=resolved_request_id,
        step_id="analyze_sentiment",
        message_ko=(
            "감정 분포 추론 완료: "
            "positive="
            f"{sentiment.positive.confidence}, "
            "negative="
            f"{sentiment.negative.confidence}, "
            "neutral="
            f"{sentiment.neutral.confidence}"
        ),
        collected_logs=collected_logs,
        on_log=on_log,
    )

    _record_log(
        request_id=resolved_request_id,
        step_id="analyze_emotion",
        message_ko=(
            "정서 신호 추론 완료: "
            "signals="
            f"{{tension:{emotion.meeting_signals.tension.confidence}, "
            f"alignment:{emotion.meeting_signals.alignment.confidence}, "
            f"urgency:{emotion.meeting_signals.urgency.confidence}, "
            f"clarity:{emotion.meeting_signals.clarity.confidence}, "
            f"engagement:{emotion.meeting_signals.engagement.confidence}}}, "
            f"emerging_count={len(emotion.emerging_emotions)}"
        ),
        collected_logs=collected_logs,
        on_log=on_log,
    )

    # [Rule-base Pipeline] 모든 지표를 조합하여 최종 루브릭 산출
    rubric = calculate_final_rubrics(
        topics=topics, sentiment=sentiment, emotion=emotion
    )

    result = AnalyzeResponse(
        topic=topic_str,
        sentiment=sentiment,
        emotion=emotion,
        rubric=rubric,
    )
    _record_log(
        request_id=resolved_request_id,
        step_id="compose_response",
        message_ko="응답 스키마 조합 완료",
        collected_logs=collected_logs,
        on_log=on_log,
    )

    return AnalyzeInspectResponse(
        request_id=resolved_request_id,
        result=result,
        logic_steps=get_analyze_logic_steps(),
        logs=collected_logs,
    )
