import { expect, test } from "@playwright/test";

const DASHBOARD_URL =
  "http://localhost:5174/?project_id=project-frontend-demo&meeting_id=meeting-issue27-short-live";

test.use({
  viewport: { width: 1600, height: 2200 },
});

test("issue #28 dashboard renders summary, charts, transcript timeline, and detail panel", async ({
  page,
}) => {
  await page.goto(DASHBOARD_URL, { waitUntil: "networkidle" });

  await expect(page.getByRole("heading", { name: "회의 핵심 요약" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "회의 흐름 탐색" })).toBeVisible();
  const timelineSection = page.locator("section").filter({
    has: page.getByRole("heading", { name: "회의 흐름 탐색" }),
  });

  await expect(page.getByRole("button", { name: "긍부정" })).toBeVisible();
  await expect(page.getByRole("button", { name: "기본 감정" })).toBeVisible();
  await expect(page.getByRole("button", { name: "회의 시그널" })).toBeVisible();
  await expect(page.getByRole("button", { name: "종합 시그널" })).toBeVisible();
  await expect(timelineSection.getByText("차트 해석 기준")).toHaveCount(0);
  await expect(timelineSection.locator(".apexcharts-canvas").first()).toBeVisible();
  const sentimentSeriesCount = await timelineSection.locator(".apexcharts-series").count();
  expect(sentimentSeriesCount).toBeGreaterThanOrEqual(3);
  await expect(timelineSection.getByText("positive", { exact: true })).toBeVisible();
  await expect(timelineSection.getByText("negative", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "기본 감정" }).click();
  await expect(timelineSection.locator(".apexcharts-canvas").first()).toBeVisible();
  const emotionCurveCount = await timelineSection.locator(".apexcharts-series").count();
  expect(emotionCurveCount).toBeGreaterThanOrEqual(8);
  await expect(timelineSection.getByText("joy")).toBeVisible();
  await expect(timelineSection.getByText("anger")).toBeVisible();

  await page.getByRole("button", { name: "회의 시그널" }).click();
  await expect(timelineSection.locator(".apexcharts-canvas").first()).toBeVisible();
  const signalCurveCount = await timelineSection.locator(".apexcharts-series").count();
  expect(signalCurveCount).toBeGreaterThanOrEqual(5);
  const engagementLegend = timelineSection.getByRole("button", { name: /^engagement$/i });
  await engagementLegend.click();
  await expect(engagementLegend).toHaveAttribute("aria-pressed", "true");
  await expect(timelineSection.locator(".apexcharts-series")).toHaveCount(1);
  await expect(timelineSection.getByRole("button", { name: "전체 지표 보기" })).toBeVisible();
  await engagementLegend.click();
  expect(await timelineSection.locator(".apexcharts-series").count()).toBeGreaterThanOrEqual(5);

  await page.getByRole("button", { name: "종합 시그널" }).click();
  await expect(timelineSection.locator(".apexcharts-canvas").first()).toBeVisible();
  const rubricCurveCount = await timelineSection.locator(".apexcharts-series").count();
  expect(rubricCurveCount).toBeGreaterThanOrEqual(3);

  const rightRail = page.locator("aside");

  const transcriptCards = rightRail
    .locator("button")
    .filter({ has: page.getByText(/^Turn \d+$/) });
  await expect(transcriptCards.first()).toBeVisible();
  expect(await transcriptCards.count()).toBeGreaterThan(0);

  await expect(rightRail.getByRole("heading", { name: "턴별 대화 내용과 감정 흐름" })).toBeVisible();

  await expect(page.getByRole("heading", { name: "발화 원문" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "시그널 분포" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "에이전트별 패턴 리포트" })).toHaveCount(0);

  await page.screenshot({
    path: "test-results/issue28-dashboard-full.png",
    fullPage: true,
  });
});
