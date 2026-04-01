import threading
from typing import Any, Callable

import pytest

import app.service.analyze_service as analyze_service
from app.service.analyze_service import (
    DEFAULT_AZURE_OPENAI_API_VERSION,
    EMOTION_MAX_OUTPUT_TOKENS,
    SENTIMENT_MAX_OUTPUT_TOKENS,
    TOPIC_MAX_OUTPUT_TOKENS,
    AnalyzeInferenceError,
    _resolve_api_version,
    analyze_emotion_with_llm,
    analyze_sentiment_with_llm,
    extract_topics_with_llm,
    preprocess_for_topic,
    run_analyze_pipeline,
)
from app.types.llm_config import LlmConfigResponse
from app.types.mood import AnalyzeRequest


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content=content)


class _FakeCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content=content)]


class _FakeCompletionsApi:
    def __init__(
        self,
        responses: list[str],
        raise_on_call_index: int | None = None,
        on_call_start: Callable[[int], None] | None = None,
    ) -> None:
        self.responses = responses
        self.raise_on_call_index = raise_on_call_index
        self.on_call_start = on_call_start
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeCompletion:
        self.calls.append(kwargs)
        call_index = len(self.calls) - 1
        if self.on_call_start is not None:
            self.on_call_start(call_index)
        if (
            self.raise_on_call_index is not None
            and call_index == self.raise_on_call_index
        ):
            raise RuntimeError("upstream error")
        if call_index >= len(self.responses):
            raise RuntimeError("response not prepared for this call")
        return _FakeCompletion(content=self.responses[call_index])


class _FakeChatApi:
    def __init__(
        self,
        responses: list[str],
        raise_on_call_index: int | None = None,
        on_call_start: Callable[[int], None] | None = None,
    ) -> None:
        self.completions = _FakeCompletionsApi(
            responses=responses,
            raise_on_call_index=raise_on_call_index,
            on_call_start=on_call_start,
        )


class _FakeClient:
    def __init__(
        self,
        responses: list[str],
        raise_on_call_index: int | None = None,
        on_call_start: Callable[[int], None] | None = None,
    ) -> None:
        self.chat = _FakeChatApi(
            responses=responses,
            raise_on_call_index=raise_on_call_index,
            on_call_start=on_call_start,
        )


def _build_client_factory(
    *clients: _FakeClient,
) -> Callable[[LlmConfigResponse], _FakeClient]:
    client_queue = list(clients)

    def _factory(llm_config: LlmConfigResponse) -> _FakeClient:
        del llm_config
        if not client_queue:
            raise AssertionError("no fake client remaining")
        return client_queue.pop(0)

    return _factory


def _mock_llm_config() -> LlmConfigResponse:
    return LlmConfigResponse(
        LLM_API_KEY="test-key",
        LLM_ENDPOINT="https://aoai.example.azure.com",
        LLM_MODEL_NAME="gpt-5-mini",
        LLM_DEPLOYMENT_NAME="gpt-5-mini",
        LLM_API_VERSION=None,
        LLM_MODEL_VERSION="2025-08-07",
    )


def _sample_request() -> AnalyzeRequest:
    return AnalyzeRequest(
        meeting_id="m_001",
        text="음, 저기 오늘은 architecture 개선과 budget 재분배를 논의해요.",
    )


def _valid_topic_payload() -> str:
    return (
        '{"topics":['
        '{"label":"Architecture","confidence":82.2},'
        '{"label":"Budget","confidence":63.4}'
        "]}"
    )


def _valid_sentiment_payload() -> str:
    return (
        '{"sentiment":{'
        '"positive":{"confidence":62.5},'
        '"negative":{"confidence":12.5},'
        '"neutral":{"confidence":25.0}'
        "}}"
    )


def _valid_emotion_payload() -> str:
    return (
        '{"emotions":{'
        '"anger":{"confidence":10},'
        '"joy":{"confidence":35},'
        '"sadness":{"confidence":5},'
        '"neutral":{"confidence":10},'
        '"anxiety":{"confidence":20},'
        '"frustration":{"confidence":8},'
        '"excitement":{"confidence":7},'
        '"confusion":{"confidence":5}'
        "}}"
    )


def test_run_analyze_pipeline_uses_fanout_and_token_limits(monkeypatch) -> None:
    topic_client = _FakeClient(responses=[_valid_topic_payload()])
    sentiment_client = _FakeClient(responses=[_valid_sentiment_payload()])
    emotion_client = _FakeClient(responses=[_valid_emotion_payload()])

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        _build_client_factory(topic_client, sentiment_client, emotion_client),
    )

    response = run_analyze_pipeline(request=_sample_request())

    assert response.result.topic.primary == "Architecture"
    assert len(response.result.topic.candidates) == 2
    assert response.result.sentiment.polarity == "positive"
    assert response.result.sentiment.distribution.positive == 63
    assert response.result.sentiment.distribution.negative == 12
    assert response.result.sentiment.distribution.neutral == 25
    assert response.result.emotion.primary == "joy"
    assert response.result.emotion.confidence == 35
    assert response.result.correlation.sentiment_emotion >= 0
    assert response.result.correlation.sentiment_emotion <= 100

    assert len(topic_client.chat.completions.calls) == 1
    assert len(sentiment_client.chat.completions.calls) == 1
    assert len(emotion_client.chat.completions.calls) == 1

    assert (
        topic_client.chat.completions.calls[0]["max_completion_tokens"]
        == TOPIC_MAX_OUTPUT_TOKENS
    )
    assert (
        sentiment_client.chat.completions.calls[0]["max_completion_tokens"]
        == SENTIMENT_MAX_OUTPUT_TOKENS
    )
    assert (
        emotion_client.chat.completions.calls[0]["max_completion_tokens"]
        == EMOTION_MAX_OUTPUT_TOKENS
    )


def test_run_analyze_pipeline_executes_three_branches_in_parallel(monkeypatch) -> None:
    start_barrier = threading.Barrier(3, timeout=1.0)

    def _wait_parallel_start(call_index: int) -> None:
        if call_index == 0:
            start_barrier.wait()

    topic_client = _FakeClient(
        responses=[_valid_topic_payload()],
        on_call_start=_wait_parallel_start,
    )
    sentiment_client = _FakeClient(
        responses=[_valid_sentiment_payload()],
        on_call_start=_wait_parallel_start,
    )
    emotion_client = _FakeClient(
        responses=[_valid_emotion_payload()],
        on_call_start=_wait_parallel_start,
    )

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        _build_client_factory(topic_client, sentiment_client, emotion_client),
    )

    response = run_analyze_pipeline(request=_sample_request())
    assert response.result.topic.primary == "Architecture"


def test_preprocess_for_topic_removes_stopwords_and_keeps_keywords() -> None:
    preprocessed = preprocess_for_topic("음 저기 um architecture 개선은 꼭 필요합니다.")
    assert "음" not in preprocessed
    assert "저기" not in preprocessed
    assert "um" not in preprocessed.casefold()
    assert "architecture" in preprocessed.casefold()


def test_extract_topics_with_llm_raises_on_non_json() -> None:
    fake_client = _FakeClient(responses=["not-json"])

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        extract_topics_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            preprocessed_text="architecture discussion",
        )

    assert exc_info.value.stage == "topic"


def test_extract_topics_with_llm_raises_on_empty_topics() -> None:
    fake_client = _FakeClient(responses=['{"topics":[]}'])

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        extract_topics_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            preprocessed_text="architecture discussion",
        )

    assert exc_info.value.stage == "topic"


def test_analyze_sentiment_with_llm_raises_on_schema_mismatch() -> None:
    fake_client = _FakeClient(
        responses=['{"sentiment":{"positive":{"confidence":"bad"}}}']
    )

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        analyze_sentiment_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            original_text="meeting text",
        )

    assert exc_info.value.stage == "sentiment"


def test_analyze_emotion_with_llm_raises_on_schema_mismatch() -> None:
    fake_client = _FakeClient(responses=['{"emotions":{"anger":{"confidence":"bad"}}}'])

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        analyze_emotion_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            original_text="meeting text",
        )

    assert exc_info.value.stage == "emotion"


def test_run_analyze_pipeline_raises_when_sentiment_branch_fails(monkeypatch) -> None:
    topic_client = _FakeClient(responses=[_valid_topic_payload()])
    sentiment_client = _FakeClient(
        responses=[_valid_sentiment_payload()],
        raise_on_call_index=0,
    )
    emotion_client = _FakeClient(responses=[_valid_emotion_payload()])

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        _build_client_factory(topic_client, sentiment_client, emotion_client),
    )

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        run_analyze_pipeline(request=_sample_request())

    assert exc_info.value.stage == "sentiment"


def test_run_analyze_pipeline_raises_when_emotion_branch_fails(monkeypatch) -> None:
    topic_client = _FakeClient(responses=[_valid_topic_payload()])
    sentiment_client = _FakeClient(responses=[_valid_sentiment_payload()])
    emotion_client = _FakeClient(
        responses=[_valid_emotion_payload()],
        raise_on_call_index=0,
    )

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        _build_client_factory(topic_client, sentiment_client, emotion_client),
    )

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        run_analyze_pipeline(request=_sample_request())

    assert exc_info.value.stage == "emotion"


def test_resolve_api_version_prefers_llm_api_version_when_present() -> None:
    cfg = _mock_llm_config()
    cfg.LLM_API_VERSION = "2025-04-01-preview"
    cfg.LLM_MODEL_VERSION = "2025-08-07"

    assert _resolve_api_version(llm_config=cfg) == "2025-04-01-preview"


def test_resolve_api_version_falls_back_to_model_version_when_api_version_missing() -> (
    None
):
    cfg = _mock_llm_config()
    cfg.LLM_API_VERSION = None
    cfg.LLM_MODEL_VERSION = "2025-08-07"

    assert _resolve_api_version(llm_config=cfg) == "2025-08-07"


def test_resolve_api_version_uses_default_when_all_config_missing() -> None:
    cfg = _mock_llm_config()
    cfg.LLM_API_VERSION = None
    cfg.LLM_MODEL_VERSION = None

    assert _resolve_api_version(llm_config=cfg) == DEFAULT_AZURE_OPENAI_API_VERSION
