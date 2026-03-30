from typing import Any

import pytest

import app.service.analyze_service as analyze_service
from app.service.analyze_service import (
    AnalyzeInferenceError,
    _normalize_sentiment_confidences,
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
    ) -> None:
        self.responses = responses
        self.raise_on_call_index = raise_on_call_index
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeCompletion:
        self.calls.append(kwargs)
        call_index = len(self.calls) - 1
        if self.raise_on_call_index is not None and call_index == self.raise_on_call_index:
            raise RuntimeError("upstream error")

        if call_index >= len(self.responses):
            raise RuntimeError("response not prepared for this call")
        return _FakeCompletion(content=self.responses[call_index])


class _FakeChatApi:
    def __init__(self, responses: list[str], raise_on_call_index: int | None = None) -> None:
        self.completions = _FakeCompletionsApi(
            responses=responses,
            raise_on_call_index=raise_on_call_index,
        )


class _FakeClient:
    def __init__(self, responses: list[str], raise_on_call_index: int | None = None) -> None:
        self.chat = _FakeChatApi(
            responses=responses,
            raise_on_call_index=raise_on_call_index,
        )


def _mock_llm_config() -> LlmConfigResponse:
    return LlmConfigResponse(
        LLM_API_KEY="test-key",
        LLM_ENDPOINT="https://aoai.example.azure.com",
        LLM_MODEL_NAME="gpt-5-mini",
        LLM_DEPLOYMENT_NAME="gpt-5-mini",
        LLM_MODEL_VERSION="2025-08-07",
    )


def _sample_request() -> AnalyzeRequest:
    return AnalyzeRequest(
        meeting_id="m_001",
        text="음, 저기 오늘은 architecture 개선과 budget 재분배를 논의해요.",
    )


def test_run_analyze_pipeline_uses_two_stage_reasoning_effort(monkeypatch) -> None:
    fake_client = _FakeClient(
        responses=[
            '{"topics":["Architecture","Budget"]}',
            (
                '{"sentiment":{"positive":{"confidence":70},'
                '"negative":{"confidence":10},"neutral":{"confidence":20}}}'
            ),
        ]
    )
    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        lambda llm_config: fake_client,
    )

    response = run_analyze_pipeline(request=_sample_request())

    assert response.result.topic == "Architecture, Budget"
    assert response.result.sentiment.positive.confidence == 70
    assert response.result.sentiment.negative.confidence == 10
    assert response.result.sentiment.neutral.confidence == 20
    assert (
        response.result.sentiment.positive.confidence
        + response.result.sentiment.negative.confidence
        + response.result.sentiment.neutral.confidence
        == 100
    )
    assert len(fake_client.chat.completions.calls) == 2
    assert fake_client.chat.completions.calls[0]["reasoning_effort"] == "none"
    assert fake_client.chat.completions.calls[1]["reasoning_effort"] == "minimal"
    assert fake_client.chat.completions.calls[0]["model"] == "gpt-5-mini"
    assert fake_client.chat.completions.calls[1]["model"] == "gpt-5-mini"


def test_run_analyze_pipeline_passes_topics_and_original_text_to_sentiment_stage(
    monkeypatch,
) -> None:
    original_text = "오늘 architecture 이슈랑 budget 조정 안건을 같이 이야기했습니다."
    fake_client = _FakeClient(
        responses=[
            '{"topics":["Architecture","Budget"]}',
            (
                '{"sentiment":{"positive":{"confidence":62.5},'
                '"negative":{"confidence":12.5},"neutral":{"confidence":25.0}}}'
            ),
        ]
    )
    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        lambda llm_config: fake_client,
    )

    run_analyze_pipeline(request=AnalyzeRequest(meeting_id="m_002", text=original_text))

    sentiment_user_prompt = fake_client.chat.completions.calls[1]["messages"][1]["content"]
    assert "extracted_topics:" in sentiment_user_prompt
    assert "- Architecture" in sentiment_user_prompt
    assert "- Budget" in sentiment_user_prompt
    assert original_text in sentiment_user_prompt


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
    fake_client = _FakeClient(responses=['{"sentiment":{"positive":{"confidence":"bad"}}}'])

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        analyze_sentiment_with_llm(
            client=fake_client,
            deployment_name="gpt-5-mini",
            original_text="meeting text",
            topics=["Architecture"],
        )

    assert exc_info.value.stage == "sentiment"


def test_run_analyze_pipeline_raises_when_second_stage_call_fails(monkeypatch) -> None:
    fake_client = _FakeClient(
        responses=[
            '{"topics":["Architecture"]}',
            (
                '{"sentiment":{"positive":{"confidence":60},'
                '"negative":{"confidence":20},"neutral":{"confidence":20}}}'
            ),
        ],
        raise_on_call_index=1,
    )
    monkeypatch.setattr(analyze_service, "get_llm_config", _mock_llm_config)
    monkeypatch.setattr(
        analyze_service,
        "_build_azure_client",
        lambda llm_config: fake_client,
    )

    with pytest.raises(AnalyzeInferenceError) as exc_info:
        run_analyze_pipeline(request=_sample_request())

    assert exc_info.value.stage == "sentiment"


def test_normalize_sentiment_confidence_sum_is_100_for_equal_input() -> None:
    sentiment = _normalize_sentiment_confidences(
        positive_raw=1.0,
        negative_raw=1.0,
        neutral_raw=1.0,
    )
    assert sentiment.positive.confidence == 34
    assert sentiment.negative.confidence == 33
    assert sentiment.neutral.confidence == 33


def test_normalize_sentiment_confidence_clamps_negative_values() -> None:
    sentiment = _normalize_sentiment_confidences(
        positive_raw=-10.0,
        negative_raw=1.0,
        neutral_raw=1.0,
    )
    assert sentiment.positive.confidence == 0
    assert sentiment.negative.confidence == 50
    assert sentiment.neutral.confidence == 50


def test_normalize_sentiment_confidence_handles_zero_total() -> None:
    sentiment = _normalize_sentiment_confidences(
        positive_raw=0.0,
        negative_raw=0.0,
        neutral_raw=0.0,
    )
    assert (
        sentiment.positive.confidence
        + sentiment.negative.confidence
        + sentiment.neutral.confidence
        == 100
    )
