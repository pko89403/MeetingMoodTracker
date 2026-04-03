"""프로젝트/회의 조회 및 aggregate 계산 서비스."""

import math
from collections import defaultdict

from app.repo.meeting_storage import JsonTurnAnalysisRepository, TurnAnalysisRepository
from app.service.analyze_service import AnalyzeInferenceError, extract_meeting_topics
from app.types.emotion import (
    BASE_EMOTION_LABELS,
    EmotionConfidenceValue,
    EmotionScores,
    MeetingSignalConfidenceValue,
    MeetingSignals,
)
from app.types.identifiers import normalize_storage_segment
from app.types.mood import AnalyzeSentiment, SentimentConfidence
from app.types.storage import (
    AgentAggregate,
    MeetingAgentsResponse,
    MeetingMeta,
    MeetingOverviewResponse,
    MeetingTurnsResponse,
    TurnAnalysisRecord,
)

MEETING_SIGNAL_LABELS: tuple[str, ...] = (
    "tension",
    "alignment",
    "urgency",
    "clarity",
    "engagement",
)


class MeetingReadNotFoundError(Exception):
    """요청한 project/meeting 경로에 저장된 회의를 찾지 못한 경우."""

    pass


class MeetingReadInferenceError(Exception):
    """조회 시점 aggregate 계산 중 LLM 추론이 실패한 경우."""

    def __init__(self, stage: str, message: str) -> None:
        """오류 단계와 메시지를 함께 보관한다."""
        self.stage = stage
        super().__init__(message)


def _normalize_meeting_path(project_id: str, meeting_id: str) -> tuple[str, str]:
    """project/meeting 경로 식별자를 저장 경로 규칙으로 정규화한다."""
    return (
        normalize_storage_segment(project_id, field_name="project_id"),
        normalize_storage_segment(meeting_id, field_name="meeting_id"),
    )


def _get_repository(
    repository: TurnAnalysisRepository | None = None,
) -> TurnAnalysisRepository:
    """외부 주입 저장소가 없으면 기본 JSON 저장소를 사용한다."""
    return repository or JsonTurnAnalysisRepository()


def _load_meeting_or_raise(
    project_id: str,
    meeting_id: str,
    repository: TurnAnalysisRepository,
) -> tuple[MeetingMeta, list[TurnAnalysisRecord]]:
    """회의 메타와 정렬된 턴 목록을 읽고, 없으면 not found 오류를 발생시킨다."""
    meeting_meta = repository.get_meeting_meta(project_id=project_id, meeting_id=meeting_id)
    if meeting_meta is None:
        raise MeetingReadNotFoundError(
            f"Meeting not found for project_id={project_id}, meeting_id={meeting_id}."
        )
    turns = repository.list_meeting_turns(project_id=project_id, meeting_id=meeting_id)
    return meeting_meta, turns


def _normalize_sentiment_distribution(
    positive_raw: float,
    negative_raw: float,
    neutral_raw: float,
) -> AnalyzeSentiment:
    """세 축 원시값을 합계 100의 정수 분포로 정규화한다."""
    axis_values = [
        max(0.0, positive_raw),
        max(0.0, negative_raw),
        max(0.0, neutral_raw),
    ]
    total = sum(axis_values)
    if total <= 0:
        axis_values = [0.0, 0.0, 1.0]
        total = 1.0

    scaled = [(value / total) * 100.0 for value in axis_values]
    floors = [math.floor(value) for value in scaled]
    fractions = [scaled[idx] - floors[idx] for idx in range(3)]
    remainder = 100 - sum(floors)
    order = sorted(range(3), key=lambda idx: (-fractions[idx], idx))
    for idx in order[:remainder]:
        floors[idx] += 1

    positive_value, negative_value, neutral_value = floors
    return AnalyzeSentiment(
        positive=SentimentConfidence(confidence=positive_value),
        negative=SentimentConfidence(confidence=negative_value),
        neutral=SentimentConfidence(confidence=neutral_value),
    )


def _aggregate_sentiment(turns: list[TurnAnalysisRecord]) -> AnalyzeSentiment:
    """턴별 label/confidence를 회의 단위 sentiment distribution으로 집계한다."""
    if not turns:
        return _normalize_sentiment_distribution(0.0, 0.0, 1.0)

    positive_raw = sum(
        turn.sentiment.confidence for turn in turns if turn.sentiment.label == "POS"
    )
    negative_raw = sum(
        turn.sentiment.confidence for turn in turns if turn.sentiment.label == "NEG"
    )
    neutral_raw = sum(
        turn.sentiment.confidence
        for turn in turns
        if turn.sentiment.label == "NEUTRAL"
    )
    return _normalize_sentiment_distribution(
        positive_raw=positive_raw,
        negative_raw=negative_raw,
        neutral_raw=neutral_raw,
    )


def _average_score(values: list[int]) -> int:
    """정수 confidence 목록의 산술평균을 반올림해 반환한다."""
    if not values:
        return 0
    return int(round(sum(values) / len(values)))


def _aggregate_emotions(turns: list[TurnAnalysisRecord]) -> EmotionScores:
    """회의 전체 턴의 기본 8정서를 평균 confidence로 집계한다."""
    emotion_scores = {
        label: [
            getattr(turn.emotion.emotions, label).confidence for turn in turns
        ]
        for label in BASE_EMOTION_LABELS
    }
    return EmotionScores(
        **{
            label: EmotionConfidenceValue(confidence=_average_score(values))
            for label, values in emotion_scores.items()
        }
    )


def _aggregate_signals(turns: list[TurnAnalysisRecord]) -> MeetingSignals:
    """회의 전체 턴의 회의 시그널 5축을 평균 confidence로 집계한다."""
    signal_scores = {
        label: [
            getattr(turn.emotion.meeting_signals, label).confidence for turn in turns
        ]
        for label in MEETING_SIGNAL_LABELS
    }
    return MeetingSignals(
        **{
            label: MeetingSignalConfidenceValue(confidence=_average_score(values))
            for label, values in signal_scores.items()
        }
    )


def _build_topic_source(turns: list[TurnAnalysisRecord]) -> str:
    """topic aggregate 계산용 meeting 텍스트를 턴 순서대로 직렬화한다."""
    ordered_lines = [turn.utterance_text.strip() for turn in turns if turn.utterance_text.strip()]
    return "\n".join(ordered_lines)


def _build_overview_summary(turn_count: int, topics: list[str]) -> str | None:
    """overview 카드용 one-line summary를 deterministic하게 구성한다."""
    if turn_count <= 0:
        return "아직 저장된 발화가 없습니다."
    if not topics:
        return f"{turn_count}개 발화를 수집한 회의입니다."
    if len(topics) == 1:
        return f"{turn_count}개 발화에서 {topics[0]} 중심으로 논의가 진행됐습니다."
    return (
        f"{turn_count}개 발화에서 {topics[0]}, {topics[1]} 중심으로 논의가 진행됐습니다."
    )


def _score_map_from_emotions(emotions: EmotionScores) -> dict[str, int]:
    """EmotionScores 모델을 label -> confidence 맵으로 변환한다."""
    return {
        label: getattr(emotions, label).confidence
        for label in BASE_EMOTION_LABELS
    }


def _score_map_from_signals(signals: MeetingSignals) -> dict[str, int]:
    """MeetingSignals 모델을 label -> confidence 맵으로 변환한다."""
    return {
        label: getattr(signals, label).confidence
        for label in MEETING_SIGNAL_LABELS
    }


def _pick_primary_label(score_map: dict[str, int], labels: tuple[str, ...]) -> str | None:
    """집계 점수가 가장 높은 대표 라벨을 결정한다."""
    if not labels:
        return None
    if all(score_map.get(label, 0) == 0 for label in labels):
        return None
    ordered = sorted(
        labels,
        key=lambda label: (-score_map.get(label, 0), labels.index(label)),
    )
    return ordered[0]


def _collect_emerging_emotions(turns: list[TurnAnalysisRecord]) -> list[str]:
    """추가 정서 라벨을 평균 confidence 기준으로 정렬해 반환한다."""
    scores_by_label: dict[str, list[int]] = defaultdict(list)
    for turn in turns:
        for item in turn.emotion.emerging_emotions:
            scores_by_label[item.label].append(item.confidence)
    ordered = sorted(
        scores_by_label.items(),
        key=lambda item: (-sum(item[1]) / len(item[1]), item[0]),
    )
    return [label for label, _ in ordered]


def _group_turns_by_agent(
    turns: list[TurnAnalysisRecord],
) -> dict[str | None, list[TurnAnalysisRecord]]:
    """실제 agent_id(None 포함) 기준으로 턴을 그룹화한다."""
    grouped: dict[str | None, list[TurnAnalysisRecord]] = defaultdict(list)
    for turn in turns:
        grouped[turn.agent_id].append(turn)
    return grouped


def get_meeting_turns(
    project_id: str,
    meeting_id: str,
    repository: TurnAnalysisRepository | None = None,
) -> MeetingTurnsResponse:
    """회의 턴 목록을 project-aware 경로 기준으로 조회한다."""
    normalized_project_id, normalized_meeting_id = _normalize_meeting_path(
        project_id=project_id,
        meeting_id=meeting_id,
    )
    resolved_repository = _get_repository(repository=repository)
    _, turns = _load_meeting_or_raise(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        repository=resolved_repository,
    )
    return MeetingTurnsResponse(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        total_count=len(turns),
        turns=turns,
    )


def get_meeting_agents(
    project_id: str,
    meeting_id: str,
    repository: TurnAnalysisRepository | None = None,
) -> MeetingAgentsResponse:
    """회의의 agent별 aggregate 요약을 계산해 반환한다."""
    normalized_project_id, normalized_meeting_id = _normalize_meeting_path(
        project_id=project_id,
        meeting_id=meeting_id,
    )
    resolved_repository = _get_repository(repository=repository)
    _, turns = _load_meeting_or_raise(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        repository=resolved_repository,
    )

    grouped_turns = _group_turns_by_agent(turns=turns)
    aggregates: list[AgentAggregate] = []
    for agent_id, agent_turns in grouped_turns.items():
        emotion_scores = _aggregate_emotions(turns=agent_turns)
        signal_scores = _aggregate_signals(turns=agent_turns)
        aggregates.append(
            AgentAggregate(
                project_id=normalized_project_id,
                meeting_id=normalized_meeting_id,
                agent_id=agent_id,
                turn_count=len(agent_turns),
                turn_ids=[turn.turn_id for turn in agent_turns],
                avg_sentiment=_aggregate_sentiment(turns=agent_turns),
                primary_emotion=_pick_primary_label(
                    score_map=_score_map_from_emotions(emotions=emotion_scores),
                    labels=BASE_EMOTION_LABELS,
                ),
                primary_signal=_pick_primary_label(
                    score_map=_score_map_from_signals(signals=signal_scores),
                    labels=MEETING_SIGNAL_LABELS,
                ),
                emerging_emotions=_collect_emerging_emotions(turns=agent_turns),
            )
        )

    sorted_aggregates = sorted(
        aggregates,
        key=lambda aggregate: (aggregate.agent_id is None, aggregate.agent_id or ""),
    )
    return MeetingAgentsResponse(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        total_count=len(sorted_aggregates),
        agents=sorted_aggregates,
    )


async def get_meeting_overview(
    project_id: str,
    meeting_id: str,
    repository: TurnAnalysisRepository | None = None,
) -> MeetingOverviewResponse:
    """회의 overview 응답에 필요한 aggregate를 project-aware 경로 기준으로 조회한다."""
    normalized_project_id, normalized_meeting_id = _normalize_meeting_path(
        project_id=project_id,
        meeting_id=meeting_id,
    )
    resolved_repository = _get_repository(repository=repository)
    meeting_meta, turns = _load_meeting_or_raise(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        repository=resolved_repository,
    )

    topics: list[str] = []
    topic_source = _build_topic_source(turns=turns)
    if topic_source != "":
        try:
            topics = await extract_meeting_topics(text=topic_source)
        except AnalyzeInferenceError as exc:
            raise MeetingReadInferenceError(stage=exc.stage, message=str(exc)) from exc

    return MeetingOverviewResponse(
        project_id=normalized_project_id,
        meeting_id=normalized_meeting_id,
        created_at=meeting_meta.created_at,
        updated_at=meeting_meta.updated_at,
        turn_count=meeting_meta.turn_count,
        agent_count=len(meeting_meta.agent_ids),
        topics=topics,
        sentiment=_aggregate_sentiment(turns=turns),
        emotions=_aggregate_emotions(turns=turns),
        signals=_aggregate_signals(turns=turns),
        one_line_summary=_build_overview_summary(
            turn_count=meeting_meta.turn_count,
            topics=topics,
        ),
    )
