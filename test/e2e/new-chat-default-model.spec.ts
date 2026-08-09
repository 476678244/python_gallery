/**
 * New Chat must inherit the global default model (DeepSeek V4 Flash).
 * This is the human acceptance path that previously failed while E2E stayed green.
 */

import { test, expect } from "@playwright/test";

const API = process.env.SAFECLAW_API_URL || "http://localhost:8000";
const DEFAULT_MODEL = "deepseek-v4-flash";
const DEFAULT_LABEL = /DeepSeek V4 Flash/i;

test.describe("New Chat default model (DeepSeek global)", () => {
  test.beforeEach(async ({ request }) => {
    const put = await request.put(`${API}/settings/model`, {
      data: { model: DEFAULT_MODEL },
    });
    expect(put.ok()).toBeTruthy();
  });

  test("API: POST /sessions without model → deepseek-v4-flash", async ({ request }) => {
    const created = await request.post(`${API}/sessions`, {
      data: { title: "New Chat" },
    });
    expect(created.ok()).toBeTruthy();
    const body = await created.json();
    const session = body.session || body;
    expect(session.settings.model).toBe(DEFAULT_MODEL);
    await request.delete(`${API}/sessions/${session.id}`);
  });

  test("UI: New Chat shows DeepSeek in header + input chip", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 15000 });

    const newChat = page.getByTestId("new-chat-button");
    if (await newChat.count()) {
      await newChat.click();
    } else {
      await page.getByText("New Chat").first().click();
    }

    await expect(page.getByTestId("header-model-select")).toHaveValue(DEFAULT_MODEL, {
      timeout: 10000,
    });
    await expect(page.getByTestId("input-model-chip")).toContainText(DEFAULT_LABEL, {
      timeout: 10000,
    });
  });
});
