import { expect, test } from "@playwright/test";

const DASHBOARD_URL =
  "http://localhost:5174/?project_id=project-frontend-demo&meeting_id=meeting-issue27-short-live";

test.use({
  viewport: { width: 1600, height: 2200 },
});

test("issue #28 flow board renders and links to timeline page", async ({
  page,
}) => {
  await page.goto(DASHBOARD_URL, { waitUntil: "domcontentloaded" });

  await expect(page.getByTestId("flow-dashboard-root")).toBeVisible();
  await expect(page.getByTestId("flow-stage-board")).toBeVisible();
  await expect(page.getByTestId("brand-mark-flow")).toBeVisible();
  await expect(page.locator(".react-flow").first()).toBeVisible();
  await expect(page.getByText("Meeting flow dashboard")).toBeVisible();
  await expect(page.getByText("Structured flow board")).toBeVisible();
  await expect(page.getByTestId("meeting-hub-node")).toBeVisible();
  await expect(page.getByTestId("flow-metric-overview")).toBeVisible();
  await expect(page.getByTestId("flow-metric-sentiment")).toBeVisible();
  await expect(page.getByTestId("flow-metric-rubric")).toBeVisible();
  await expect(page.getByTestId("flow-mini-chart")).toHaveCount(0);
  await expect(page.getByTestId("flow-view-tab")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByTestId("timeline-view-tab")).toBeVisible();

  await expect(page.getByTestId("flow-search-button")).toBeVisible();
  await expect(page.getByRole("button", { name: "전체 보기" })).toBeVisible();
  await expect(page.getByTestId("agent-filter-all")).toHaveAttribute("aria-pressed", "true");

  const aliceFilter = page.getByTestId("agent-filter-alice");
  await aliceFilter.click({ force: true });
  await expect(aliceFilter).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("agent-node-alice")).toBeVisible();

  const turnNode = page.getByTestId("turn-node-1");
  await turnNode.click({ force: true });
  await expect(page.getByTestId("flow-detail-panel")).toContainText("Turn 1");
  await expect(page.getByTestId("flow-detail-panel")).toContainText("Dominance");

  await page.getByTestId("timeline-view-tab").click();
  await expect(page.getByTestId("timeline-page-root")).toBeVisible();
  await expect(page.getByTestId("brand-mark-timeline")).toBeVisible();
  await expect(page.getByTestId("timeline-view-tab")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByTestId("timeline-page-chart")).toBeVisible();
  await expect(page.getByTestId("flow-view-tab")).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByTestId("flow-mini-chart-tab-sentiment")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("flow-mini-chart-tab-emotions")).toBeVisible();
  await page.getByTestId("flow-mini-chart-tab-signals").click();
  await expect(page.getByTestId("flow-mini-chart-tab-signals")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("timeline-page-chart").locator(".apexcharts-canvas")).toBeVisible();
  await expect(page).toHaveURL(/view=timeline/);

  const bobFilter = page.getByTestId("agent-filter-bob");
  await bobFilter.click({ force: true });
  await expect(bobFilter).toHaveAttribute("aria-pressed", "true");
});
