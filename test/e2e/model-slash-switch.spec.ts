/**
 * /model slash command — quick model switch from chat input
 */

import { test, expect, Page } from "@playwright/test";

async function waitForApp(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
}

async function ensureSession(page: Page) {
  const textarea = page.locator("textarea").first();
  if (await textarea.isDisabled().catch(() => true)) {
    await page.getByText("New Chat").first().click();
    await page.waitForTimeout(1000);
  }
}

test.describe("Slash /model switch", () => {
  test("typing /model opens model picker and selects DeepSeek V4 Flash", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);

    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/model");
    await page.waitForTimeout(400);

    const dropdown = page.getByTestId("model-autocomplete-dropdown");
    await expect(dropdown).toBeVisible({ timeout: 10000 });
    await expect(dropdown.getByText("DeepSeek V4 Flash").first()).toBeVisible();

    await dropdown.getByText("DeepSeek V4 Flash").first().click();
    await page.waitForTimeout(400);

    await expect(dropdown).not.toBeVisible();
    // Slash command should be cleared from the input
    await expect(textarea).toHaveValue("");

    // Persisted globally
    const res = await page.request.get("http://localhost:8000/settings/model");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.model).toBe("deepseek-v4-flash");
  });

  test("typing /mo suggests the model command", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);

    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/mo");
    await page.waitForTimeout(300);

    const cmd = page.getByTestId("slash-command-dropdown");
    await expect(cmd).toBeVisible();
    await expect(cmd.getByText("/model")).toBeVisible();

    await cmd.getByText("/model").click();
    await page.waitForTimeout(300);

    await expect(page.getByTestId("model-autocomplete-dropdown")).toBeVisible();
    await expect(textarea).toHaveValue(/\/model\s/);
  });
});
