"""발화 턴 감정분류를 수행하는 서비스 레이어."""

import json
from typing import Any

from openai import AzureOpenAI

from app.service.llm_config_service import get_llm_config
from app.types.llm_config import LlmConfigResponse
from app.types.sentiment import TurnSentimentRequest, TurnSentimentResponse

DEFAULT_AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
SUPPORTED_SENTIMENT_LABELS: tuple[str, str, str] = ("POS", "NEG", "NEUTRAL")

SENTIMENT_JSON_SCHEMA: dict[str, Any] = {
    "name": "turn_sentiment_classification",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "label": {
                "type": "string",
                "enum": list(SUPPORTED_SENTIMENT_LABELS),
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "evidence": {"type": "string"},
        },
        "required": ["label", "confidence", "evidence"],
    },
}


class SentimentInferenceError(Exception):
    """LLM 호출 또는 응답 파싱 단계에서 감정분류가 실패했을 때 발생한다."""

    pass


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


def _build_system_prompt() -> str:
    """모델에 전달할 감정분류 시스템 프롬프트를 구성한다."""
    return (
        "You classify one meeting turn sentiment. "
        "Input may be Korean with mixed English. "
        "Return only POS, NEG, or NEUTRAL. "
        "POS means positive/constructive/supportive tone. "
        "NEG means negative/hostile/frustrated/conflictual tone. "
        "NEUTRAL means factual, mixed, or emotionally flat tone. "
        "Evidence must quote a short phrase from the utterance. "
        "Evidence must be written in Korean only. "
        "Do not output English words or mixed-language evidence."
    )


def _build_user_prompt(request: TurnSentimentRequest) -> str:
    """요청 필드를 일관된 포맷의 사용자 프롬프트 문자열로 변환한다."""
    agent_text = request.agent_id if request.agent_id is not None else "N/A"
    return (
        f"meeting_id={request.meeting_id}\n"
        f"turn_id={request.turn_id}\n"
        f"agent_id={agent_text}\n"
        "utterance:\n"
        f"{request.utterance_text}"
    )


def _extract_message_content(completion: Any) -> str:
    """Chat completion 결과에서 비어 있지 않은 본문 문자열을 추출한다."""
    choices = getattr(completion, "choices", None)
    if not choices:
        raise SentimentInferenceError("LLM response has no choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None:
        raise SentimentInferenceError("LLM response has no message.")

    content = getattr(message, "content", None)
    if not isinstance(content, str) or content.strip() == "":
        raise SentimentInferenceError("LLM response content is empty.")

    return content


def _parse_response_payload(content: str) -> TurnSentimentResponse:
    """JSON 문자열을 파싱하고 응답 스키마로 검증한다."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SentimentInferenceError("LLM response is not valid JSON.") from exc

    try:
        return TurnSentimentResponse.model_validate(payload)
    except Exception as exc:
        raise SentimentInferenceError("LLM response failed schema validation.") from exc


def classify_turn_sentiment(request: TurnSentimentRequest) -> TurnSentimentResponse:
    """Azure OpenAI를 사용해 단일 발화 턴의 감정을 분류한다."""
    llm_config = get_llm_config()
    client = _build_azure_client(llm_config=llm_config)

    try:
        completion = client.chat.completions.create(
            model=llm_config.LLM_DEPLOYMENT_NAME,
            response_format={
                "type": "json_schema",
                "json_schema": SENTIMENT_JSON_SCHEMA,
            },
            messages=[
                {"role": "system", "content": _build_system_prompt()},
                {"role": "user", "content": _build_user_prompt(request=request)},
            ],
        )
    except Exception as exc:
        raise SentimentInferenceError(
            "Failed to call Azure OpenAI for sentiment."
        ) from exc

    content = _extract_message_content(completion=completion)
    return _parse_response_payload(content=content)
