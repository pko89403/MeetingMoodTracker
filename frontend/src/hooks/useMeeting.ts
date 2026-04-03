import { useCallback, useEffect, useState } from "react";
import {
  api,
  EmotionScoresRaw,
  MeetingAgentResponse,
  MeetingOverviewResponse,
  MeetingSignalsRaw,
  MeetingTurnRecordResponse,
  SentimentLabel,
} from "../lib/api";
import {
  BaseEmotionValues,
  calculateMeetingRubric,
  calculateTurnRubric,
  dominantKey,
  formatAgentLabel,
  formatMetricLabel,
  MeetingAgent,
  MeetingRubricValues,
  MeetingSignalValues,
  MeetingSummary,
  MeetingTurn,
} from "../lib/meetingDashboard";

type FetchState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  empty: boolean;
};

function flattenEmotions(raw: EmotionScoresRaw): BaseEmotionValues {
  return {
    joy: raw.joy.confidence,
    anger: raw.anger.confidence,
    sadness: raw.sadness.confidence,
    neutral: raw.neutral.confidence,
    anxiety: raw.anxiety.confidence,
    frustration: raw.frustration.confidence,
    excitement: raw.excitement.confidence,
    confusion: raw.confusion.confidence,
  };
}

function flattenSignals(raw: MeetingSignalsRaw): MeetingSignalValues {
  return {
    tension: raw.tension.confidence,
    alignment: raw.alignment.confidence,
    urgency: raw.urgency.confidence,
    clarity: raw.clarity.confidence,
    engagement: raw.engagement.confidence,
  };
}

function toRubric(
  signalValues: MeetingSignalValues,
  topics: string[],
  sentiment: MeetingSummary["sentimentDist"],
  rubric?: MeetingRubricValues | null,
): MeetingRubricValues {
  if (rubric) {
    return rubric;
  }

  return calculateMeetingRubric({
    topicsCount: topics.length,
    sentiment,
    signals: signalValues,
  });
}

function toSentimentScore(label: SentimentLabel, confidence: number): number {
  if (label === "POS") {
    return confidence;
  }
  if (label === "NEG") {
    return confidence * -1;
  }
  return 0;
}

function buildAgentFallbackSummary(response: MeetingAgentResponse): string {
  const agentLabel = formatAgentLabel(response.agent_id);
  const primaryEmotion = formatMetricLabel(response.primary_emotion, "");
  const primarySignal = formatMetricLabel(response.primary_signal, "");
  const emerging = response.emerging_emotions
    .slice(0, 2)
    .map((item) => formatMetricLabel(item))
    .filter(Boolean);

  const highlights = [primarySignal && `${primarySignal} 시그널`, primaryEmotion && `${primaryEmotion} 감정`]
    .filter(Boolean)
    .join(" / ");

  if (highlights && emerging.length > 0) {
    return `${agentLabel}는 ${response.turn_count}개 발화에서 ${highlights}이 두드러졌고, ${emerging.join(", ")} 흐름이 함께 관찰됩니다.`;
  }

  if (highlights) {
    return `${agentLabel}는 ${response.turn_count}개 발화에서 ${highlights}이 두드러졌습니다.`;
  }

  if (emerging.length > 0) {
    return `${agentLabel}는 ${response.turn_count}개 발화에서 ${emerging.join(", ")} 흐름이 관찰됩니다.`;
  }

  return `${agentLabel}는 ${response.turn_count}개 발화에 참여한 에이전트입니다.`;
}

function toMeetingSummary(response: MeetingOverviewResponse): MeetingSummary {
  const emotionValues = flattenEmotions(response.emotions);
  const signalValues = flattenSignals(response.signals);
  const sentimentDist = {
    pos: response.sentiment.positive.confidence,
    neu: response.sentiment.neutral.confidence,
    neg: response.sentiment.negative.confidence,
  };

  return {
    projectId: response.project_id,
    meetingId: response.meeting_id,
    title: `Meeting ${response.meeting_id}`,
    totalTurns: response.turn_count,
    totalAgents: response.agent_count,
    lastUpdated: response.updated_at,
    createdAt: response.created_at,
    topics: response.topics,
    sentimentDist,
    dominantEmotion: formatMetricLabel(dominantKey(emotionValues), "N/A"),
    dominantSignal: formatMetricLabel(dominantKey(signalValues), "N/A"),
    rubric: toRubric(signalValues, response.topics, sentimentDist, response.rubric ?? null),
    oneLineSummary:
      response.one_line_summary ?? "회의 요약이 아직 생성되지 않았습니다.",
  };
}

function toTurn(response: MeetingTurnRecordResponse): MeetingTurn {
  const baseEmotions = flattenEmotions(response.emotion.emotions);
  const meetingSignals = flattenSignals(response.emotion.meeting_signals);

  return {
    turnId: response.turn_id,
    order: response.order,
    agentId: response.agent_id,
    agentLabel: formatAgentLabel(response.agent_id),
    text: response.utterance_text,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    sentimentLabel: response.sentiment.label,
    sentimentConfidence: response.sentiment.confidence,
    sentimentScore: toSentimentScore(response.sentiment.label, response.sentiment.confidence),
    baseEmotions,
    meetingSignals,
    rubric:
      response.rubric ??
      calculateTurnRubric({
        sentimentLabel: response.sentiment.label,
        sentimentConfidence: response.sentiment.confidence,
        signals: meetingSignals,
      }),
    emergingEmotions: response.emotion.emerging_emotions.map((item) => formatMetricLabel(item.label)),
    dominantEmotion: formatMetricLabel(dominantKey(baseEmotions), "N/A"),
    dominantSignal: formatMetricLabel(dominantKey(meetingSignals), "N/A"),
  };
}

function toAgent(response: MeetingAgentResponse): MeetingAgent {
  return {
    id: response.agent_id,
    label: formatAgentLabel(response.agent_id),
    turnCount: response.turn_count,
    turnIds: response.turn_ids,
    avgSentiment: {
      pos: response.avg_sentiment.positive.confidence,
      neu: response.avg_sentiment.neutral.confidence,
      neg: response.avg_sentiment.negative.confidence,
    },
    primaryEmotion: formatMetricLabel(response.primary_emotion, "N/A"),
    primarySignal: formatMetricLabel(response.primary_signal, "N/A"),
    emergingEmotions: response.emerging_emotions.map((item) => formatMetricLabel(item)),
    summary: response.summary?.trim() || buildAgentFallbackSummary(response),
  };
}

function useMeetingResource<T>(options: {
  projectId?: string;
  meetingId?: string;
  fetcher: (projectId: string, meetingId: string, signal: AbortSignal) => Promise<T>;
  isEmpty: (data: T) => boolean;
}): FetchState<T> {
  const { projectId, meetingId, fetcher, isEmpty } = options;
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: Boolean(projectId && meetingId),
    error: null,
    empty: false,
  });

  useEffect(() => {
    if (!projectId || !meetingId) {
      setState({ data: null, loading: false, error: null, empty: false });
      return;
    }

    const controller = new AbortController();
    setState((previous) => ({ ...previous, loading: true, error: null }));

    fetcher(projectId, meetingId, controller.signal)
      .then((data) => {
        setState({
          data,
          loading: false,
          error: null,
          empty: isEmpty(data),
        });
      })
      .catch((error: Error) => {
        if (error.name === "AbortError") {
          return;
        }

        setState({
          data: null,
          loading: false,
          error: error.message,
          empty: false,
        });
      });

    return () => {
      controller.abort();
    };
  }, [fetcher, isEmpty, meetingId, projectId]);

  return state;
}

const isOverviewEmpty = (summary: MeetingSummary) => summary.totalTurns === 0;
const isTurnsEmpty = (turns: MeetingTurn[]) => turns.length === 0;
const isAgentsEmpty = (agents: MeetingAgent[]) => agents.length === 0;

export function useMeetingOverview(projectId?: string, meetingId?: string) {
  const fetchOverview = useCallback(
    (resolvedProjectId: string, resolvedMeetingId: string, signal: AbortSignal) =>
      api
        .getMeetingOverview(resolvedProjectId, resolvedMeetingId, signal)
        .then(toMeetingSummary),
    []
  );

  return useMeetingResource({
    projectId,
    meetingId,
    fetcher: fetchOverview,
    isEmpty: isOverviewEmpty,
  });
}

export function useMeetingTurns(projectId?: string, meetingId?: string) {
  const fetchTurns = useCallback(
    (resolvedProjectId: string, resolvedMeetingId: string, signal: AbortSignal) =>
      api
        .getMeetingTurns(resolvedProjectId, resolvedMeetingId, signal)
        .then((response) => response.turns.map(toTurn)),
    []
  );

  return useMeetingResource({
    projectId,
    meetingId,
    fetcher: fetchTurns,
    isEmpty: isTurnsEmpty,
  });
}

export function useMeetingAgents(projectId?: string, meetingId?: string) {
  const fetchAgents = useCallback(
    (resolvedProjectId: string, resolvedMeetingId: string, signal: AbortSignal) =>
      api
        .getMeetingAgents(resolvedProjectId, resolvedMeetingId, signal)
        .then((response) => response.agents.map(toAgent)),
    []
  );

  return useMeetingResource({
    projectId,
    meetingId,
    fetcher: fetchAgents,
    isEmpty: isAgentsEmpty,
  });
}
