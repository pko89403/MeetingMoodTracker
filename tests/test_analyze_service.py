import asyncio
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
        on_call_start: Callable[[int], Any] | None = None,
    ) -> None:
        self.responses = responses
        self.raise_on_call_index = raise_on_call_index
        self.on_call_start = on_call_start
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> _FakeCompletion:
        self.calls.append(kwargs)
        call_index = len(self.calls) - 1
        if self.on_call_start is not None:
            res = self.on_call_start(call_index)
            if asyncio.iscoroutine(res):
                await res
        if (
            self.raise_on_call_index is not None
            and call_index == self.raise_on_call_index
        ):
            raise RuntimeError("upstream error")

        # 힌트: 시스템 프롬프트의 고유 문구를 보고 적절한 응답을 선택한다
        msgs = kwargs.get("messages", [])
        system_content = ""
        for m in msgs:
            if m.get("role") == "system":
                system_content = m.get("content", "").lower()
                break

        if "sentiment distribution" in system_content:
            return _FakeCompletion(
                content='{"sentiment":{"positive":{"confidence":62.5},"negative":{"confidence":12.5},"neutral":{"confidence":25.0}}}'
            )
        if "concise meeting topics" in system_content:
            return _FakeCompletion(content='{"topics":["Architecture", "Budget"]}')
        if "meeting-specific signals" in system_content:
            return _FakeCompletion(content=_valid_emotion_payload())

        if call_index < len(self.responses):
            return _FakeCompletion(content=self.responses[call_index])

        raise RuntimeError(
            f"response not prepared for system_content: {system_content[:50]}"
        )


class _FakeChatApi:
    def __init__(
        self,
        responses: list[str],
        raise_on_call_index: int | None = None,
        on_call_start: Callable[[int], Any] | None = None,
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
        on_call_start: Callable[[int], Any] | None = None,
    ) -> None:
        self.chat = _FakeChatApi(
            responses=responses,
            raise_on_call_index=raise_on_call_index,
            on_call_start=on_call_start,
        )


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
        "},"
        '"meeting_signals":{'
        '"tension":{"confidence":10},'
        '"alignment":{"confidence":80},'
        '"urgency":{"confidence":20},'
        '"clarity":{"confidence":90},'
        '"engagement":{"confidence":70}'
        "},"
        '"emerging_emotions": []'
        "}"
    )


@pytest.mark.asyncio
async def test_run_analyze_pipeline_uses_fanout_and_token_limits(monkeypatch) -> None:
    client = _FakeClient(responses=[])

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service, "_build_azure_client", lambda llm_config: client
    )

    response = await run_analyze_pipeline(request=_sample_request())

    assert response.result.topic == "Architecture, Budget"
    assert response.result.sentiment.positive.confidence == 63
    assert response.result.emotion.emotions.joy.confidence == 35
    assert response.result.rubric.dominance >= 0
    assert response.result.rubric.efficiency >= 0
    assert response.result.rubric.cohesion >= 0

    assert len(client.chat.completions.calls) == 3

    # 호출별 토큰 제한 확인
    topic_call = next(
        c for c in client.chat.completions.calls if "topics" in str(c).lower()
    )
    sentiment_call = next(
        c for c in client.chat.completions.calls if "sentiment" in str(c).lower()
    )
    emotion_call = next(
        c for c in client.chat.completions.calls if "signals" in str(c).lower()
    )

    assert topic_call["max_completion_tokens"] == TOPIC_MAX_OUTPUT_TOKENS
    assert sentiment_call["max_completion_tokens"] == SENTIMENT_MAX_OUTPUT_TOKENS
    assert emotion_call["max_completion_tokens"] == EMOTION_MAX_OUTPUT_TOKENS


@pytest.mark.asyncio
async def test_run_analyze_pipeline_executes_three_branches_in_parallel(
    monkeypatch,
) -> None:
    barrier = asyncio.Barrier(3)

    async def _wait_parallel_start(call_index: int) -> None:
        await barrier.wait()

    client = _FakeClient(
        responses=[],
        on_call_start=_wait_parallel_start,
    )

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service, "_build_azure_client", lambda llm_config: client
    )

    response = await run_analyze_pipeline(request=_sample_request())
    assert "Architecture" in response.result.topic


def test_preprocess_for_topic_removes_stopwords_and_keeps_keywords() -> None:
    preprocessed = preprocess_for_topic("음 저기 um architecture 개선은 꼭 필요합니다.")
    assert "음" not in preprocessed
    assert "저기" not in preprocessed
    assert "um" not in preprocessed.casefold()
    assert "architecture" in preprocessed.casefold()


@pytest.mark.asyncio
async def test_extract_topics_with_llm_raises_on_non_json() -> None:
    fake_client = _FakeClient(responses=[])

    async def mock_create(**kwargs):
        return _FakeCompletion(content="not-json")

    fake_client.chat.completions.create = mock_create

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        await extract_topics_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            preprocessed_text="architecture discussion",
        )

    assert exc_info.value.stage == "topic"


@pytest.mark.asyncio
async def test_extract_topics_with_llm_raises_on_empty_topics() -> None:
    fake_client = _FakeClient(responses=[])

    async def mock_create(**kwargs):
        return _FakeCompletion(content='{"topics":[]}')

    fake_client.chat.completions.create = mock_create

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        await extract_topics_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            preprocessed_text="architecture discussion",
        )

    assert exc_info.value.stage == "topic"


@pytest.mark.asyncio
async def test_analyze_sentiment_with_llm_raises_on_schema_mismatch() -> None:
    fake_client = _FakeClient(responses=[])

    async def mock_create(**kwargs):
        return _FakeCompletion(
            content='{"sentiment":{"positive":{"confidence":"bad"}}}'
        )

    fake_client.chat.completions.create = mock_create

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        await analyze_sentiment_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            original_text="meeting text",
        )

    assert exc_info.value.stage == "sentiment"


@pytest.mark.asyncio
async def test_analyze_emotion_with_llm_raises_on_schema_mismatch() -> None:
    fake_client = _FakeClient(responses=[])

    async def mock_create(**kwargs):
        return _FakeCompletion(content='{"emotions":{"anger":{"confidence":"bad"}}}')

    fake_client.chat.completions.create = mock_create

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        await analyze_emotion_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            original_text="meeting text",
        )

    assert exc_info.value.stage == "inference"


@pytest.mark.asyncio
async def test_run_analyze_pipeline_raises_when_sentiment_branch_fails(
    monkeypatch,
) -> None:
    client = _FakeClient(responses=[])

    async def mock_create(**kwargs):
        msgs = kwargs.get("messages", [])
        sys = next(
            (m.get("content", "").lower() for m in msgs if m.get("role") == "system"),
            "",
        )
        if "sentiment distribution" in sys:
            raise RuntimeError("upstream error")
        if "concise meeting topics" in sys:
            return _FakeCompletion(content='{"topics":["T"]}')
        return _FakeCompletion(content=_valid_emotion_payload())

    client.chat.completions.create = mock_create

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service, "_build_azure_client", lambda llm_config: client
    )

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        await run_analyze_pipeline(request=_sample_request())

    assert exc_info.value.stage == "sentiment"


@pytest.mark.asyncio
async def test_run_analyze_pipeline_raises_when_emotion_branch_fails(
    monkeypatch,
) -> None:
    client = _FakeClient(responses=[])

    async def mock_create(**kwargs):
        msgs = kwargs.get("messages", [])
        sys = next(
            (m.get("content", "").lower() for m in msgs if m.get("role") == "system"),
            "",
        )
        if "meeting-specific signals" in sys:
            raise RuntimeError("upstream error")
        if "concise meeting topics" in sys:
            return _FakeCompletion(content='{"topics":["T"]}')
        if "sentiment distribution" in sys:
            return _FakeCompletion(
                content='{"sentiment":{"positive":{"confidence":50},"negative":{"confidence":25},"neutral":{"confidence":25}}}'
            )
        return _FakeCompletion(content="{}")

    client.chat.completions.create = mock_create

    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service, "_build_azure_client", lambda llm_config: client
    )

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        await run_analyze_pipeline(request=_sample_request())

    assert exc_info.value.stage == "inference"


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
