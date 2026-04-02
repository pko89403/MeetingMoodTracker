import { useState, useEffect } from "react";
import {
  api,
  MeetingOverviewResponse,
  TurnResponse,
  SpeakerResponse,
  EmotionScoresRaw,
  MeetingSignalsRaw,
} from "../lib/api";
import {
  MOCK_MEETING_SUMMARY,
  MOCK_TURNS,
  MOCK_SPEAKERS,
  MeetingSummary,
  Turn,
  Speaker,
} from "../mockData";

// 백엔드 confidence 객체 → 평탄화된 숫자값
function flattenEmotions(raw: EmotionScoresRaw): Turn["baseEmotions"] {
  return {
    joy:        raw.joy.confidence,
    anger:      raw.anger.confidence,
    sadness:    raw.sadness.confidence,
    neutral:    raw.neutral.confidence,
    anxiety:    raw.anxiety.confidence,
    frustration: raw.frustration.confidence,
    excitement: raw.excitement.confidence,
    confusion:  raw.confusion.confidence,
  };
}

function flattenSignals(raw: MeetingSignalsRaw): Turn["meetingSignals"] {
  return {
    tension:    raw.tension.confidence,
    alignment:  raw.alignment.confidence,
    urgency:    raw.urgency.confidence,
    clarity:    raw.clarity.confidence,
    engagement: raw.engagement.confidence,
  };
}

function getDominantKey(obj: Record<string, number>): string {
  return Object.entries(obj).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "";
}

function toMeetingSummary(r: MeetingOverviewResponse): MeetingSummary {
  return {
    meetingId:    r.meeting_id,
    title:        `회의 ${r.meeting_id}`,
    status:       "Analyzed",
    totalTurns:   r.turn_count,
    lastUpdated:  r.updated_at,
    topics:       r.topics,
    sentimentDist: {
      pos: Math.round(r.sentiment.positive.confidence),
      neu: Math.round(r.sentiment.neutral.confidence),
      neg: Math.round(r.sentiment.negative.confidence),
    },
    dominantEmotion: getDominantKey({
      joy:        r.emotions.joy.confidence,
      anger:      r.emotions.anger.confidence,
      sadness:    r.emotions.sadness.confidence,
      anxiety:    r.emotions.anxiety.confidence,
      excitement: r.emotions.excitement.confidence,
    }),
    dominantSignal: getDominantKey({
      tension:    r.signals.tension.confidence,
      alignment:  r.signals.alignment.confidence,
      urgency:    r.signals.urgency.confidence,
      clarity:    r.signals.clarity.confidence,
      engagement: r.signals.engagement.confidence,
    }),
    oneLineSummary: r.one_line_summary ?? "",
  };
}

function toTurn(r: TurnResponse): Turn {
  return {
    turn_id:    r.turn_id,
    order:      r.order,
    speaker_id: r.speaker_id,
    text:       r.utterance_text,
    sentiment: {
      score: (r.sentiment.positive - r.sentiment.negative) / 100,
      pos:   r.sentiment.positive,
      neu:   r.sentiment.neutral,
      neg:   r.sentiment.negative,
    },
    baseEmotions:    flattenEmotions(r.emotions),
    meetingSignals:  flattenSignals(r.signals),
    emergingEmotions: r.emerging_emotions.map((e) => e.label),
    dominantEmotion: r.dominant_emotion,
    dominantSignal:  r.dominant_signal,
  };
}

function toSpeaker(r: SpeakerResponse): Speaker {
  return {
    id:              r.speaker_id,
    name:            r.speaker_id,
    role:            "",
    turnCount:       r.turn_count,
    avgSentiment:    r.avg_sentiment,
    primaryEmotion:  r.primary_emotion,
    primarySignal:   r.primary_signal,
    emergingEmotions: r.emerging_emotions,
    summary:         r.summary ?? "",
  };
}

type FetchState<T> = { data: T; loading: boolean; error: string | null };

function useFetch<T>(
  meetingId: string | undefined,
  fetcher: (id: string) => Promise<T>,
  fallback: T
): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: fallback,
    loading: Boolean(meetingId),
    error: null,
  });

  useEffect(() => {
    if (!meetingId) {
      setState({ data: fallback, loading: false, error: null });
      return;
    }
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    fetcher(meetingId)
      .then((data) => { if (!cancelled) setState({ data, loading: false, error: null }); })
      .catch((err: Error) => {
        if (!cancelled) setState({ data: fallback, loading: false, error: err.message });
      });
    return () => { cancelled = true; };
  }, [meetingId]); // eslint-disable-line react-hooks/exhaustive-deps

  return state;
}

export function useMeetingOverview(meetingId: string | undefined) {
  return useFetch(
    meetingId,
    (id) => api.getMeetingOverview(id).then(toMeetingSummary),
    MOCK_MEETING_SUMMARY
  );
}

export function useMeetingTurns(meetingId: string | undefined) {
  return useFetch(
    meetingId,
    (id) => api.getMeetingTurns(id).then((ts) => ts.map(toTurn)),
    MOCK_TURNS
  );
}

export function useSpeakers(meetingId: string | undefined) {
  return useFetch(
    meetingId,
    (id) => api.getSpeakers(id).then((ss) => ss.map(toSpeaker)),
    MOCK_SPEAKERS
  );
}
