from typing import Any

import pytest

import app.service.sentiment_service as sentiment_service
from app.service.sentiment_service import (
    DEFAULT_AZURE_OPENAI_API_VERSION,
    SentimentInferenceError,
    _resolve_api_version,
    classify_turn_sentiment,
)
from app.types.llm_config import LlmConfigResponse
from app.types.sentiment import TurnSentimentRequest


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
    def __init__(self, content: str, should_raise: bool = False) -> None:
        self.content = content
        self.should_raise = should_raise
        self.received_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _FakeCompletion:
        self.received_kwargs = kwargs
        if self.should_raise:
            raise RuntimeError("upstream error")
        return _FakeCompletion(content=self.content)


class _FakeChatApi:
    def __init__(self, content: str, should_raise: bool = False) -> None:
        self.completions = _FakeCompletionsApi(
            content=content,
            should_raise=should_raise,
        )


class _FakeClient:
    def __init__(self, content: str, should_raise: bool = False) -> None:
        self.chat = _FakeChatApi(content=content, should_raise=should_raise)


def _mock_llm_config() -> LlmConfigResponse:
    return LlmConfigResponse(
        LLM_API_KEY="test-key",
        LLM_ENDPOINT="https://aoai.example.azure.com",
        LLM_MODEL_NAME="gpt-5-mini",
        LLM_DEPLOYMENT_NAME="gpt-5-mini",
        LLM_API_VERSION=None,
        LLM_MODEL_VERSION="2025-08-07",
    )


def _sample_request() -> TurnSentimentRequest:
    return TurnSentimentRequest(
        meeting_id="m_001",
        turn_id="t_001",
        speaker_id="alice",
        utterance_text="좋아요. this looks good.",
    )


def test_classify_turn_sentiment_parses_valid_schema_response(monkeypatch) -> None:
    fake_client = _FakeClient(
        content='{"label":"POS","confidence":0.87,"evidence":"looks good"}'
    )
    llm_config = _mock_llm_config()
    monkeypatch.setattr(sentiment_service, "get_llm_config", lambda: llm_config)
    monkeypatch.setattr(
        sentiment_service,
        "_build_azure_client",
        lambda llm_config: fake_client,
    )

    response = classify_turn_sentiment(request=_sample_request())

    assert response.label == "POS"
    assert response.confidence == 0.87
    assert response.evidence == "looks good"
    assert fake_client.chat.completions.received_kwargs is not None
    assert fake_client.chat.completions.received_kwargs["model"] == "gpt-5-mini"
    assert (
        fake_client.chat.completions.received_kwargs["response_format"]["type"]
        == "json_schema"
    )


def test_classify_turn_sentiment_raises_on_invalid_label(monkeypatch) -> None:
    fake_client = _FakeClient(
        content='{"label":"MIXED","confidence":0.5,"evidence":"ambiguous"}'
    )
    monkeypatch.setattr(sentiment_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        sentiment_service,
        "_build_azure_client",
        lambda llm_config: fake_client,
    )

    with pytest.raises(SentimentInferenceError):
        classify_turn_sentiment(request=_sample_request())


def test_classify_turn_sentiment_raises_on_llm_call_error(monkeypatch) -> None:
    fake_client = _FakeClient(content="{}", should_raise=True)
    monkeypatch.setattr(sentiment_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        sentiment_service,
        "_build_azure_client",
        lambda llm_config: fake_client,
    )

    with pytest.raises(SentimentInferenceError):
        classify_turn_sentiment(request=_sample_request())


def test_resolve_api_version_prefers_llm_api_version_when_present() -> None:
    cfg = _mock_llm_config()
    cfg.LLM_API_VERSION = "2025-04-01-preview"
    cfg.LLM_MODEL_VERSION = "2025-08-07"
    assert _resolve_api_version(llm_config=cfg) == "2025-04-01-preview"


def test_resolve_api_version_falls_back_to_model_version_when_api_version_missing() -> None:
    cfg = _mock_llm_config()
    cfg.LLM_API_VERSION = None
    cfg.LLM_MODEL_VERSION = "2025-08-07"
    assert _resolve_api_version(llm_config=cfg) == "2025-08-07"


def test_resolve_api_version_uses_default_when_not_present() -> None:
    cfg = _mock_llm_config()
    cfg.LLM_MODEL_VERSION = None
    assert _resolve_api_version(llm_config=cfg) == DEFAULT_AZURE_OPENAI_API_VERSION
