/**
 * Sub-agents observability — S1 / S1b / S3 (mock SSE + Demo HTML)
 * Spec: docs/features/sub-agents/e2e.md
 *
 * S2 hard-gate unit coverage: pytest test/deepagents/test_spawn_brief.py
 *
 * Requires UI :3000 for S1/S3. S1b is file:// demo (no server).
 * Run: cd test/e2e && npx playwright test sub-agents.spec.ts --retries=0
 */

import { test, expect, Page } from "@playwright/test";
import path from "path";

const NESTED_TOOL_BODY_MARKER = "NESTED_TOOL_BODY_MARKER";
const SCREENSHOTS = "screenshots";
const DEMO_HTML = path.resolve(
  __dirname,
  "../../docs/features/sub-agents/demo-observability.html",
);

function sseBody(events: Record<string, unknown>[]): string {
  return events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
}

async function gotoFresh(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => localStorage.removeItem("safeclaw-ui-store"));
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(600);
}

async function ensureSession(page: Page) {
  const textarea = page.locator("textarea").first();
  if (await textarea.isDisabled().catch(() => true)) {
    const newChat = page.getByText("New Chat").first();
    if (await newChat.isVisible().catch(() => false)) {
      await newChat.click();
      await page.waitForTimeout(500);
    }
  }
  await expect(page.locator("textarea").first()).toBeEnabled({ timeout: 15000 });
}

async function openExecPanel(page: Page) {
  const execRail = page.locator("nav button[title='Execution Path']").first();
  await expect(execRail).toBeVisible({ timeout: 10000 });
  await execRail.click();
  await page.waitForTimeout(300);
}

async function mockSubagentStream(page: Page) {
  await page.route("**/chat/stream", async (route) => {
    const body = sseBody([
      {
        type: "execution_step",
        step_id: "parse",
        name: "Understanding request",
        step_type: "reasoning",
        status: "completed",
        chips: ["✓ done"],
      },
      {
        type: "execution_step",
        step_id: "sub-1",
        name: "Subagent · explore",
        step_type: "subagent",
        status: "running",
        agent_name: "explore",
        step_now: "调研主题 A",
        look_ahead: [
          "收集 A 的来源与时间线",
          "压缩成 5 条要点",
          "按 expected_output 交回主线程",
        ],
        expected_output: "JSON facts",
        chips: ["running", "look_ahead×3"],
      },
      {
        type: "execution_step",
        step_id: "tool-web",
        parent_step_id: "sub-1",
        name: "web_search",
        step_type: "tool_call",
        status: "completed",
        sub: `${NESTED_TOOL_BODY_MARKER} long nested transcript must not enter main bubble`,
        chips: ["✓ done"],
      },
      {
        type: "execution_step",
        step_id: "sub-1",
        name: "Subagent · explore",
        step_type: "subagent",
        status: "completed",
        chips: ["✓ done"],
      },
      {
        type: "content",
        content: "Main reply: brief summary only. No nested tool dump.",
      },
      {
        type: "done",
        session_id: "e2e-subagents",
        message_id: "msg-subagents-s1",
        skills_loaded: [],
        skills_invoked: [],
      },
    ]);
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body,
    });
  });
}

test.describe("Sub-agents S1 / S1b / S3", () => {
  test("S1: React Exec expanded foresight + nested tool (mock SSE)", async ({
    page,
  }) => {
    await mockSubagentStream(page);
    await gotoFresh(page);
    await ensureSession(page);
    await openExecPanel(page);

    const textarea = page.locator("textarea").first();
    await textarea.fill("spawn explore with brief");
    await textarea.press("Enter");

    await expect(page.getByTestId("exec-step-subagent")).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByTestId("look-ahead-item")).toHaveCount(3);
    await expect(page.getByTestId("exec-step-nested-tool")).toBeVisible();
    await expect(page.getByTestId("exec-btn-halt")).toBeVisible();
    await expect(page.getByTestId("exec-btn-steer")).toBeVisible();

    // Isolation: main assistant text must not contain nested marker
    const mainReply = page.getByText("Main reply: brief summary only").first();
    await expect(mainReply).toBeVisible({ timeout: 10000 });
    expect(await mainReply.innerText()).not.toContain(NESTED_TOOL_BODY_MARKER);
    await expect(page.getByTestId("exec-step-nested-tool")).toContainText(
      NESTED_TOOL_BODY_MARKER,
    );

    await page.screenshot({
      path: `${SCREENSHOTS}/sub-agents-s1.png`,
      fullPage: true,
    });
  });

  test("S1b: Demo HTML contract — S1 replay", async ({ page }) => {
    await page.goto(`file://${DEMO_HTML}`);
    await page.waitForLoadState("domcontentloaded");

    const s1 = page.locator("#btnHappy, button:has-text('S1')").first();
    await expect(s1).toBeVisible();
    await s1.click();

    await expect(page.getByTestId("exec-step-subagent")).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByTestId("look-ahead-item")).toHaveCount(3);
    await expect(page.getByTestId("exec-step-nested-tool")).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByTestId("exec-btn-halt")).toBeVisible();
    await expect(page.getByTestId("exec-btn-steer")).toBeVisible();

    await page.screenshot({
      path: `${SCREENSHOTS}/sub-agents-s1b-demo.png`,
      fullPage: true,
    });
  });

  test("S2b: Halt freezes world + banner; nested tree stays visible", async ({
    page,
  }) => {
    await mockSubagentStream(page);
    await gotoFresh(page);
    await ensureSession(page);
    await openExecPanel(page);

    await page.locator("textarea").first().fill("spawn then halt");
    await page.locator("textarea").first().press("Enter");

    await expect(page.getByTestId("exec-step-subagent")).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByTestId("exec-step-nested-tool")).toBeVisible();
    await expect(page.getByTestId("look-ahead-item")).toHaveCount(3);

    await page.getByTestId("exec-btn-halt").click();
    await expect(page.getByTestId("world-stopped-banner")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByTestId("exec-btn-steer")).toBeDisabled();
    // Nested foresight remains inspectable after halt
    await expect(page.getByTestId("look-ahead-item")).toHaveCount(3);
  });

  test("S3: isolation — nested marker not in main content event path", async ({
    page,
  }) => {
    await mockSubagentStream(page);
    await gotoFresh(page);
    await ensureSession(page);
    await openExecPanel(page);

    await page.locator("textarea").first().fill("isolation check");
    await page.locator("textarea").first().press("Enter");

    await expect(page.getByTestId("exec-step-nested-tool")).toBeVisible({
      timeout: 15000,
    });
    // Nested marker is allowed in Exec (observability)
    await expect(page.getByTestId("exec-step-nested-tool")).toContainText(
      NESTED_TOOL_BODY_MARKER,
    );
    // Main content string from mock must not include marker
    await expect(
      page.getByText("Main reply: brief summary only").first(),
    ).toBeVisible();
    const mainBubbleText = await page
      .getByText("Main reply: brief summary only")
      .first()
      .innerText();
    expect(mainBubbleText).not.toContain(NESTED_TOOL_BODY_MARKER);
    // Marker must appear in Exec, not as a second main-bubble dump
    await expect(page.getByTestId("exec-step-nested-tool")).toContainText(
      NESTED_TOOL_BODY_MARKER,
    );

    await page.screenshot({
      path: `${SCREENSHOTS}/sub-agents-s3.png`,
      fullPage: true,
    });
  });
});
