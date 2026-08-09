/**
 * Agent Modes — slash + badge + request mode (UI contract).
 * Full write-gate paths covered by API/unit tests; this asserts session sticky UX.
 */
import { test, expect } from "@playwright/test";

test.describe("agent-modes", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("S0 slash lists mode commands and /ask sets badge", async ({ page }) => {
    const input = page.locator("textarea").first();
    await expect(input).toBeVisible({ timeout: 30_000 });

    // Ensure a session exists
    const newChat = page.getByRole("button", { name: /new chat/i }).first();
    if (await newChat.isVisible().catch(() => false)) {
      await newChat.click();
      await page.waitForTimeout(500);
    }

    await input.click();
    await input.fill("/");
    const dropdown = page.getByTestId("slash-command-dropdown");
    await expect(dropdown).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("slash-cmd-ask")).toBeVisible();
    await expect(page.getByTestId("slash-cmd-safe")).toBeVisible();
    await expect(page.getByTestId("slash-cmd-debug")).toBeVisible();
    await expect(page.getByTestId("slash-cmd-subagent")).toBeVisible();
    await expect(page.getByTestId("slash-cmd-loop")).toBeVisible();

    await page.getByTestId("slash-cmd-ask").click();
    await expect(page.getByTestId("mode-badge")).toHaveText(/ask/i, {
      timeout: 5_000,
    });
    await expect(page.getByTestId("mode-policy-chips")).toContainText("c✗");
  });

  test("S0b /safe shows create-only chips", async ({ page }) => {
    const input = page.locator("textarea").first();
    await expect(input).toBeVisible({ timeout: 30_000 });
    await input.fill("/safe");
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("mode-badge")).toHaveText(/safe/i, {
      timeout: 5_000,
    });
    await expect(page.getByTestId("mode-policy-chips")).toContainText("c✓");
    await expect(page.getByTestId("mode-policy-chips")).toContainText("u✗");
  });

  test("S4 loop requires done/stop condition before arm", async ({ page }) => {
    const input = page.locator("textarea").first();
    await expect(input).toBeVisible({ timeout: 30_000 });
    await input.fill("/loop 30s check status");
    await page.keyboard.press("Enter");

    const modal = page.getByTestId("loop-confirm-modal");
    await expect(modal).toBeVisible({ timeout: 5_000 });
    const arm = page.getByTestId("loop-confirm-arm");
    await expect(arm).toBeDisabled();

    await page.getByTestId("loop-done-condition").fill("max 2 ticks");
    await expect(arm).toBeEnabled();
    await page.getByTestId("loop-confirm-cancel").click();
    await expect(modal).toBeHidden();
    await expect(page.getByTestId("loop-status")).toHaveCount(0);
  });

  test("S3 Plan artifact card from structured assistant reply", async ({
    page,
  }) => {
    const planBody = [
      "Here is a cautious approach.",
      "",
      "### Plan",
      "1. Map existing streamChat mode field",
      "2. Add ModePolicy hard gates",
      "3. Wire UI badge",
      "",
      "### Risks",
      "- Prompt-only gates look green but still write",
      "",
      "### Pending confirmation",
      "- Confirm explore-only spawn later",
    ].join("\n");

    await page.route("**/chat/stream", async (route) => {
      const body = [
        { type: "content", content: planBody },
        {
          type: "done",
          session_id: "e2e-plan",
          message_id: "msg-plan",
          skills_loaded: [],
          skills_invoked: [],
        },
      ]
        .map((e) => `data: ${JSON.stringify(e)}\n\n`)
        .join("");
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body,
      });
    });

    const input = page.locator("textarea").first();
    await expect(input).toBeVisible({ timeout: 30_000 });
    const newChat = page.getByRole("button", { name: /new chat/i }).first();
    if (await newChat.isVisible().catch(() => false)) {
      await newChat.click();
      await page.waitForTimeout(400);
    }

    await input.fill("/plan");
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("mode-badge")).toHaveText(/plan/i, {
      timeout: 5_000,
    });

    await input.fill("规划如何加 mode，先不要改代码");
    await input.press("Enter");

    await expect(page.getByTestId("plan-artifact")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("plan-step")).toHaveCount(3);
    await expect(page.getByTestId("plan-risks")).toContainText("Prompt-only");
    await expect(page.getByTestId("plan-pending")).toContainText("explore-only");
    await expect(page.getByTestId("plan-switch-agent")).toBeVisible();
    await expect(page.getByTestId("plan-switch-safe")).toBeVisible();

    await page.getByTestId("plan-switch-agent").click();
    await expect(page.getByTestId("mode-badge")).toHaveText(/agent/i, {
      timeout: 5_000,
    });
  });
});
