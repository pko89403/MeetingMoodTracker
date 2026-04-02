export type Speaker = {
  id: string;
  name: string;
  role: string;
  turnCount: number;
  avgSentiment: { pos: number; neu: number; neg: number };
  primaryEmotion: string;
  primarySignal: string;
  emergingEmotions: string[];
  summary: string;
};

export type Turn = {
  turn_id: string;
  order: number;
  speaker_id: string;
  text: string;
  sentiment: { score: number; pos: number; neu: number; neg: number }; // score: -1 to 1
  baseEmotions: { joy: number; anger: number; sadness: number; neutral: number; anxiety: number; frustration: number; excitement: number; confusion: number }; // 0 to 100
  meetingSignals: { tension: number; alignment: number; urgency: number; clarity: number; engagement: number }; // 0 to 100
  emergingEmotions: string[];
  dominantEmotion: string;
  dominantSignal: string;
};

export type MeetingSummary = {
  meetingId: string;
  title: string;
  status: string;
  totalTurns: number;
  lastUpdated: string;
  topics: string[];
  sentimentDist: { pos: number; neu: number; neg: number };
  dominantEmotion: string;
  dominantSignal: string;
  oneLineSummary: string;
};

export const MOCK_MEETING_SUMMARY: MeetingSummary = {
  meetingId: "MTG-2026-Q2-774A",
  title: "Q3 Roadmap Alignment & Tech Debt",
  status: "Analyzed",
  totalTurns: 25,
  lastUpdated: "2026-04-01T09:30:00Z",
  topics: ["Roadmap", "Tech Debt", "Resource Allocation", "Design System"],
  sentimentDist: { pos: 35, neu: 45, neg: 20 },
  dominantEmotion: "Anticipation",
  dominantSignal: "Engagement",
  oneLineSummary: "초기 기술 부채에 대한 우려로 긴장도가 높았으나, 명확한 리소스 배분 합의를 통해 긍정적으로 마무리된 회의입니다.",
};

export const MOCK_SPEAKERS: Speaker[] = [
  {
    id: "spk_1",
    name: "Alice Kim",
    role: "Product Manager",
    turnCount: 9,
    avgSentiment: { pos: 40, neu: 50, neg: 10 },
    primaryEmotion: "Anticipation",
    primarySignal: "Clarity",
    emergingEmotions: ["Optimism", "Determination"],
    summary: "회의의 방향성을 주도하며, 모호한 상황에서 Clarity를 높이는데 집중함. 갈등 상황을 긍정적으로 중재하는 패턴을 보임.",
  },
  {
    id: "spk_2",
    name: "Bob Lee",
    role: "Engineering Lead",
    turnCount: 9,
    avgSentiment: { pos: 20, neu: 40, neg: 40 },
    primaryEmotion: "Frustration",
    primarySignal: "Urgency",
    emergingEmotions: ["Concern", "Relief"],
    summary: "기술 부채 관련 논의에서 강한 Tension과 Urgency를 보이나, 합의 도출 후 안도감을 나타냄.",
  },
  {
    id: "spk_3",
    name: "Charlie Park",
    role: "Product Designer",
    turnCount: 7,
    avgSentiment: { pos: 50, neu: 40, neg: 10 },
    primaryEmotion: "Joy",
    primarySignal: "Engagement",
    emergingEmotions: ["Inspiration", "Curiosity"],
    summary: "디자인 시스템 논의 시 매우 높은 Engagement를 보이며, 전반적으로 긍정적이고 협력적인 태도를 유지함.",
  }
];

// Generate 25 turns with a story arc
export const MOCK_TURNS: Turn[] = [
  {
    turn_id: "t_01", order: 1, speaker_id: "spk_1",
    text: "모두 참석해주셔서 감사합니다. 오늘 Q3 로드맵 논의를 시작해볼까요?",
    sentiment: { score: 0.5, pos: 60, neu: 40, neg: 0 },
    baseEmotions: { joy: 40, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 10, alignment: 60, urgency: 30, clarity: 80, engagement: 50 },
    emergingEmotions: ["Welcoming"], dominantEmotion: "Joy", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_02", order: 2, speaker_id: "spk_2",
    text: "네, 시작하시죠. 다만 이번 분기에는 기술 부채 해결이 꼭 우선순위에 들어가야 합니다.",
    sentiment: { score: 0.1, pos: 20, neu: 60, neg: 20 },
    baseEmotions: { joy: 0, anger: 10, sadness: 0, neutral: 0, anxiety: 10, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 40, alignment: 50, urgency: 70, clarity: 70, engagement: 60 },
    emergingEmotions: ["Determined"], dominantEmotion: "Anticipation", dominantSignal: "Urgency"
  },
  {
    turn_id: "t_03", order: 3, speaker_id: "spk_1",
    text: "맞습니다. 그 부분도 오늘 안건에 포함되어 있습니다. 일단 찰리가 준비한 디자인 시스템 개편안부터 볼까요?",
    sentiment: { score: 0.3, pos: 40, neu: 50, neg: 10 },
    baseEmotions: { joy: 20, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 20, alignment: 60, urgency: 40, clarity: 70, engagement: 60 },
    emergingEmotions: ["Reassuring"], dominantEmotion: "Anticipation", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_04", order: 4, speaker_id: "spk_3",
    text: "화면 공유하겠습니다. 이번 개편의 핵심은 컴포넌트 재사용성을 높여서 개발 속도를 끌어올리는 겁니다.",
    sentiment: { score: 0.6, pos: 70, neu: 30, neg: 0 },
    baseEmotions: { joy: 50, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 10, alignment: 70, urgency: 30, clarity: 80, engagement: 80 },
    emergingEmotions: ["Excitement"], dominantEmotion: "Joy", dominantSignal: "Engagement"
  },
  {
    turn_id: "t_05", order: 5, speaker_id: "spk_2",
    text: "방향성은 좋은데, 지금 당장 저걸 적용하려면 기존 코드를 다 갈아엎어야 해요. 당장 리소스가 없습니다.",
    sentiment: { score: -0.6, pos: 0, neu: 20, neg: 80 },
    baseEmotions: { joy: 0, anger: 40, sadness: 10, neutral: 0, anxiety: 30, frustration: 10, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 75, alignment: 30, urgency: 80, clarity: 60, engagement: 70 },
    emergingEmotions: ["Frustration", "Overwhelmed"], dominantEmotion: "Anger", dominantSignal: "Tension"
  },
  {
    turn_id: "t_06", order: 6, speaker_id: "spk_3",
    text: "전체를 한 번에 갈아엎자는 게 아닙니다. 신규 피처부터 점진적으로 적용하는 방안을 고려했어요.",
    sentiment: { score: 0.1, pos: 30, neu: 50, neg: 20 },
    baseEmotions: { joy: 10, anger: 10, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 50, alignment: 40, urgency: 40, clarity: 85, engagement: 70 },
    emergingEmotions: ["Defensive"], dominantEmotion: "Anticipation", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_07", order: 7, speaker_id: "spk_2",
    text: "그래도 마이그레이션 전략이 너무 모호합니다. 이대로면 개발팀 일정 맞추기 불가능해요.",
    sentiment: { score: -0.7, pos: 0, neu: 20, neg: 80 },
    baseEmotions: { joy: 0, anger: 50, sadness: 0, neutral: 0, anxiety: 40, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 85, alignment: 20, urgency: 90, clarity: 40, engagement: 80 },
    emergingEmotions: ["Stress", "Anxiety"], dominantEmotion: "Fear", dominantSignal: "Urgency"
  },
  {
    turn_id: "t_08", order: 8, speaker_id: "spk_1",
    text: "잠깐만요, 밥의 우려가 이해됩니다. 디자인 시스템 마이그레이션을 위한 별도 스프린트를 할당하면 어떨까요?",
    sentiment: { score: 0.2, pos: 30, neu: 60, neg: 10 },
    baseEmotions: { joy: 0, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 60, alignment: 40, urgency: 50, clarity: 70, engagement: 70 },
    emergingEmotions: ["Mediating"], dominantEmotion: "Anticipation", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_09", order: 9, speaker_id: "spk_2",
    text: "별도 스프린트요? 그럼 Q3 신규 피처 런칭 일정이 밀릴 텐데요. 비즈니스 쪽에서 오케이 할까요?",
    sentiment: { score: -0.2, pos: 0, neu: 50, neg: 50 },
    baseEmotions: { joy: 0, anger: 20, sadness: 0, neutral: 0, anxiety: 30, frustration: 0, excitement: 20, confusion: 0 },
    meetingSignals: { tension: 70, alignment: 30, urgency: 60, clarity: 60, engagement: 80 },
    emergingEmotions: ["Skeptical"], dominantEmotion: "Fear", dominantSignal: "Tension"
  },
  {
    turn_id: "t_10", order: 10, speaker_id: "spk_1",
    text: "제가 설득하겠습니다. 기술 부채가 더 쌓이면 Q4에는 아예 속도를 낼 수 없다는 걸 어필할게요.",
    sentiment: { score: 0.4, pos: 50, neu: 40, neg: 10 },
    baseEmotions: { joy: 10, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 40, alignment: 60, urgency: 50, clarity: 90, engagement: 80 },
    emergingEmotions: ["Confident", "Supportive"], dominantEmotion: "Joy", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_11", order: 11, speaker_id: "spk_3",
    text: "디자인 파트에서도 개발팀이 마이그레이션하기 편하도록 가이드를 상세히 작성해 두겠습니다.",
    sentiment: { score: 0.5, pos: 60, neu: 40, neg: 0 },
    baseEmotions: { joy: 30, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 30, alignment: 80, urgency: 30, clarity: 70, engagement: 70 },
    emergingEmotions: ["Helpful"], dominantEmotion: "Joy", dominantSignal: "Alignment"
  },
  {
    turn_id: "t_12", order: 12, speaker_id: "spk_2",
    text: "음... 만약 첫 2주를 마이그레이션 전용으로 빼주신다면 해볼 만할 것 같습니다.",
    sentiment: { score: 0.3, pos: 40, neu: 50, neg: 10 },
    baseEmotions: { joy: 20, anger: 0, sadness: 0, neutral: 0, anxiety: 10, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 40, alignment: 70, urgency: 40, clarity: 70, engagement: 60 },
    emergingEmotions: ["Relieved", "Cautiously Optimistic"], dominantEmotion: "Joy", dominantSignal: "Alignment"
  },
  {
    turn_id: "t_13", order: 13, speaker_id: "spk_1",
    text: "좋습니다. 그럼 첫 2주는 디자인 시스템 적용 및 리팩토링으로 픽스하시죠.",
    sentiment: { score: 0.7, pos: 80, neu: 20, neg: 0 },
    baseEmotions: { joy: 60, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 20, alignment: 90, urgency: 30, clarity: 90, engagement: 70 },
    emergingEmotions: ["Satisfied"], dominantEmotion: "Joy", dominantSignal: "Alignment"
  },
  {
    turn_id: "t_14", order: 14, speaker_id: "spk_3",
    text: "다행이네요. 그럼 다음 안건인 결제 플로우 개선 건으로 넘어가도 될까요?",
    sentiment: { score: 0.4, pos: 50, neu: 50, neg: 0 },
    baseEmotions: { joy: 30, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 15, alignment: 85, urgency: 20, clarity: 80, engagement: 60 },
    emergingEmotions: ["Eager"], dominantEmotion: "Joy", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_15", order: 15, speaker_id: "spk_1",
    text: "네. 결제 플로우는 지난주 데이터 보니까 이탈률이 여전히 높더라고요.",
    sentiment: { score: -0.2, pos: 10, neu: 60, neg: 30 },
    baseEmotions: { joy: 0, anger: 0, sadness: 20, neutral: 0, anxiety: 10, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 35, alignment: 70, urgency: 60, clarity: 80, engagement: 70 },
    emergingEmotions: ["Concerned"], dominantEmotion: "Sadness", dominantSignal: "Urgency"
  },
  {
    turn_id: "t_16", order: 16, speaker_id: "spk_3",
    text: "맞아요. 단계가 너무 많아서 그렇습니다. 원클릭 결제 도입이 시급해요.",
    sentiment: { score: 0.1, pos: 30, neu: 40, neg: 30 },
    baseEmotions: { joy: 0, anger: 10, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 40, alignment: 75, urgency: 85, clarity: 80, engagement: 80 },
    emergingEmotions: ["Urgent"], dominantEmotion: "Anticipation", dominantSignal: "Urgency"
  },
  {
    turn_id: "t_17", order: 17, speaker_id: "spk_2",
    text: "원클릭 결제는 PG사 연동 쪽 보안 이슈를 먼저 해결해야 해서 당장 3분기는 좀 리스크가 있습니다.",
    sentiment: { score: -0.4, pos: 0, neu: 40, neg: 60 },
    baseEmotions: { joy: 0, anger: 10, sadness: 0, neutral: 0, anxiety: 40, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 65, alignment: 40, urgency: 70, clarity: 75, engagement: 75 },
    emergingEmotions: ["Apprehensive"], dominantEmotion: "Fear", dominantSignal: "Tension"
  },
  {
    turn_id: "t_18", order: 18, speaker_id: "spk_1",
    text: "음, 보안 검토에 시간이 얼마나 걸릴까요?",
    sentiment: { score: 0.0, pos: 20, neu: 70, neg: 10 },
    baseEmotions: { joy: 0, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 50, alignment: 50, urgency: 50, clarity: 70, engagement: 60 },
    emergingEmotions: ["Inquisitive"], dominantEmotion: "Anticipation", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_19", order: 19, speaker_id: "spk_2",
    text: "최소 3주는 봐야 합니다. 외부 보안 감사도 받아야 하고요.",
    sentiment: { score: -0.1, pos: 10, neu: 60, neg: 30 },
    baseEmotions: { joy: 0, anger: 0, sadness: 0, neutral: 0, anxiety: 20, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 55, alignment: 50, urgency: 40, clarity: 85, engagement: 60 },
    emergingEmotions: ["Serious"], dominantEmotion: "Anticipation", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_20", order: 20, speaker_id: "spk_1",
    text: "알겠습니다. 그럼 원클릭 결제는 Q4로 넘기고, 이번 분기에는 결제 수단 추가까지만 하죠.",
    sentiment: { score: 0.3, pos: 40, neu: 50, neg: 10 },
    baseEmotions: { joy: 10, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 30, alignment: 80, urgency: 20, clarity: 90, engagement: 60 },
    emergingEmotions: ["Decisive"], dominantEmotion: "Anticipation", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_21", order: 21, speaker_id: "spk_3",
    text: "네, 결제 수단 UI 업데이트는 바로 작업 가능합니다.",
    sentiment: { score: 0.5, pos: 60, neu: 40, neg: 0 },
    baseEmotions: { joy: 30, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 15, alignment: 85, urgency: 20, clarity: 80, engagement: 60 },
    emergingEmotions: ["Willing"], dominantEmotion: "Joy", dominantSignal: "Alignment"
  },
  {
    turn_id: "t_22", order: 22, speaker_id: "spk_2",
    text: "네, 그 정도 스코프면 개발 일정 내에 소화 가능합니다.",
    sentiment: { score: 0.4, pos: 50, neu: 50, neg: 0 },
    baseEmotions: { joy: 20, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 10, alignment: 90, urgency: 10, clarity: 85, engagement: 50 },
    emergingEmotions: ["Content"], dominantEmotion: "Joy", dominantSignal: "Alignment"
  },
  {
    turn_id: "t_23", order: 23, speaker_id: "spk_1",
    text: "훌륭합니다. 주요 안건들은 다 정리가 된 것 같네요.",
    sentiment: { score: 0.8, pos: 80, neu: 20, neg: 0 },
    baseEmotions: { joy: 70, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 5, alignment: 95, urgency: 10, clarity: 95, engagement: 60 },
    emergingEmotions: ["Satisfied", "Accomplished"], dominantEmotion: "Joy", dominantSignal: "Clarity"
  },
  {
    turn_id: "t_24", order: 24, speaker_id: "spk_3",
    text: "네, 오늘 회의 아주 생산적이었습니다. 회의록은 제가 슬랙에 공유할게요.",
    sentiment: { score: 0.7, pos: 70, neu: 30, neg: 0 },
    baseEmotions: { joy: 60, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 5, alignment: 90, urgency: 10, clarity: 80, engagement: 70 },
    emergingEmotions: ["Helpful"], dominantEmotion: "Joy", dominantSignal: "Engagement"
  },
  {
    turn_id: "t_25", order: 25, speaker_id: "spk_1",
    text: "감사합니다. 다들 수고 많으셨습니다!",
    sentiment: { score: 0.9, pos: 90, neu: 10, neg: 0 },
    baseEmotions: { joy: 80, anger: 0, sadness: 0, neutral: 0, anxiety: 0, frustration: 0, excitement: 0, confusion: 0 },
    meetingSignals: { tension: 0, alignment: 95, urgency: 0, clarity: 80, engagement: 80 },
    emergingEmotions: ["Grateful"], dominantEmotion: "Joy", dominantSignal: "Alignment"
  }
];
