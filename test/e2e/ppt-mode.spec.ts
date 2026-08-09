/**
 * PPT Mode — slash + pack + outline + preview thumbs + sticky mode.
 * SoT: docs/features/ppt-mode/e2e.md
 */
import { test, expect } from "@playwright/test";

/** 1×1 PNG */
const TINY_PNG =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

async function ensureSession(page: import("@playwright/test").Page) {
  const input = page.locator("textarea").first();
  await expect(input).toBeVisible({ timeout: 30_000 });
  const newChat = page.getByRole("button", { name: /new chat/i }).first();
  if (await newChat.isVisible().catch(() => false)) {
    await newChat.click();
    await page.waitForTimeout(400);
  }
  return input;
}

test.describe("ppt-mode", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("S0 /ppt sets badge and create-only chips", async ({ page }) => {
    const input = await ensureSession(page);

    await input.click();
    await input.fill("/");
    const dropdown = page.getByTestId("slash-command-dropdown");
    await expect(dropdown).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("slash-cmd-ppt")).toBeVisible();

    await page.getByTestId("slash-cmd-ppt").click();
    await expect(page.getByTestId("mode-badge")).toHaveText(/ppt/i, {
      timeout: 5_000,
    });
    await expect(page.getByTestId("mode-policy-chips")).toContainText("c✓");
    await expect(page.getByTestId("mode-policy-chips")).toContainText("u✗");
  });

  test("S0b /ppt forces Deck Preview panel", async ({ page }) => {
    const input = await ensureSession(page);
    await input.fill("/ppt");
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("mode-badge")).toHaveText(/ppt/i, {
      timeout: 5_000,
    });
    await expect(page.getByTestId("deck-preview-panel")).toBeVisible({
      timeout: 5_000,
    });
  });

  test("S2 deck outline card + confirm CTA streams generate prompt", async ({
    page,
  }) => {
    // Match real LLM headings with Chinese suffix (sess-1786243607 regression)
    const deckBody = [
      "先给你结构。",
      "",
      "### Deck Outline（共 6 页，约 2 分钟）",
      "1. **封面**：开场",
      "2. **结尾**：结论",
      "",
      "### Slide Storyboard（每页：标题 + 要点 + 画面）",
      "| 页 | 标题 | 要点 | 画面 |",
      "|---|---|---|---|",
      "| 1 | 标题页 | 要点 | 视觉 |",
      "| 2 | 结论页 | 三点 | 左文右图 |",
      "",
      "### Pending confirmation（请确认以下 3 点）",
      "1. **小朋友几年级？**",
      "2. **场景选哪个**",
    ].join("\n");

    let generateTurn = false;
    await page.route("**/chat/stream", async (route) => {
      if (!generateTurn) {
        const body = [
          { type: "content", content: deckBody },
          {
            type: "done",
            session_id: "e2e-deck",
            message_id: "msg-deck",
          },
        ]
          .map((e) => `data: ${JSON.stringify(e)}\n\n`)
          .join("");
        await route.fulfill({
          status: 200,
          contentType: "text/event-stream",
          body,
        });
        return;
      }
      // Second turn after 确认出稿 — acknowledge
      const body = [
        { type: "content", content: "收到确认出稿，开始调用 safe_claw_ppt_*。" },
        { type: "done", session_id: "e2e-deck", message_id: "msg-gen" },
      ]
        .map((e) => `data: ${JSON.stringify(e)}\n\n`)
        .join("");
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body,
      });
    });

    const input = await ensureSession(page);
    await input.fill("/ppt");
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("mode-badge")).toHaveText(/ppt/i, {
      timeout: 5_000,
    });

    await input.fill("帮我做两页 PPT 大纲，先不要出稿");
    await input.press("Enter");

    await expect(page.getByTestId("deck-artifact")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("deck-outline")).toContainText("开场");
    await expect(page.getByTestId("deck-storyboard")).toContainText("结论页");
    await expect(page.getByTestId("deck-confirm-generate")).toBeVisible();

    // Capture next user message content via request
    const reqPromise = page.waitForRequest(
      (r) => r.url().includes("/chat/stream") && r.method() === "POST"
    );
    generateTurn = true;
    await page.getByTestId("deck-confirm-generate").click();
    const req = await reqPromise;
    const payload = req.postDataJSON() as {
      messages: { role: string; content: string }[];
    };
    const lastUser = [...payload.messages].reverse().find((m) => m.role === "user");
    expect(lastUser?.content || "").toMatch(/确认出稿/);
    expect(lastUser?.content || "").toMatch(/safe_claw_ppt_/);
  });

  test("S3 ppt_preview SSE refreshes Deck thumbs + version list", async ({
    page,
  }) => {
    await page.route("**/chat/stream", async (route) => {
      const body = [
        { type: "content", content: "已出稿并预览。" },
        {
          type: "ppt_preview",
          deck_id: "e2e-thumbs",
          version: 1,
          pptx_path: "ppt/e2e-thumbs_v1.pptx",
          slide_count: 2,
          preview_urls: [TINY_PNG, TINY_PNG],
        },
        {
          type: "ppt_preview",
          deck_id: "e2e-thumbs",
          version: 2,
          pptx_path: "ppt/e2e-thumbs_v2.pptx",
          slide_count: 2,
          preview_urls: [TINY_PNG, TINY_PNG],
        },
        {
          type: "done",
          session_id: "e2e-thumbs",
          message_id: "msg-thumbs",
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

    const input = await ensureSession(page);
    await input.fill("/ppt");
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("deck-preview-panel")).toBeVisible({
      timeout: 5_000,
    });

    await input.fill("直接出稿两页");
    await input.press("Enter");

    await expect(page.getByTestId("deck-preview-main")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("deck-thumb-1")).toBeVisible();
    await expect(page.getByTestId("deck-thumb-2")).toBeVisible();
    await expect(page.getByTestId("deck-version-list")).toBeVisible();
    await expect(page.getByTestId("deck-version-list")).toContainText("v1");
    await expect(page.getByTestId("deck-version-list")).toContainText("v2");
    await expect(page.getByTestId("deck-preview-panel")).toContainText(
      "e2e-thumbs"
    );
  });

  test("S4 /ppt mode sticky after reload", async ({ page }) => {
    const input = await ensureSession(page);
    await input.fill("/ppt");
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("mode-badge")).toHaveText(/ppt/i, {
      timeout: 5_000,
    });

    // Wait briefly for PATCH /sessions settings to land
    await page.waitForTimeout(800);
    await page.reload();
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("mode-badge")).toHaveText(/ppt/i, {
      timeout: 15_000,
    });
    await expect(page.getByTestId("deck-preview-panel")).toBeVisible({
      timeout: 10_000,
    });
  });
});
