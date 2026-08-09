/**
 * Memory panel + /remember slash — requires API + UI.
 */

import { test, expect, Page } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";

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

test.describe("Memory panel", () => {
  test("API-written memory appears in Memory panel", async ({ page, request }) => {
    const token = `e2e-memory-${Date.now()}`;
    const created = await request.post(`${API}/memory`, {
      data: {
        content: `Panel visibility token ${token}`,
        importance: 0.95,
        keywords: ["e2e", "panel"],
      },
    });
    expect(created.ok()).toBeTruthy();

    await waitForApp(page);
    await ensureSession(page);

    // Open Memory rail
    const memoryRail = page.getByTitle("Memory");
    await memoryRail.click();
    await page.waitForTimeout(600);

    const panel = page.getByTestId("memory-panel");
    await expect(panel).toBeVisible({ timeout: 10000 });
    await expect(panel.getByText(token, { exact: false })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Porsche Macan")).toHaveCount(0);
  });

  test("/remember writes memory and shows notice", async ({ page, request }) => {
    await waitForApp(page);
    await ensureSession(page);

    const token = `remember-${Date.now()}`;
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill(`/remember Keep this secret ${token}`);
    await page.waitForTimeout(200);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(800);

    await expect(page.getByTestId("slash-notice")).toHaveText(/Remembered/i);

    const listed = await request.get(`${API}/memory?search=${encodeURIComponent(token)}`);
    expect(listed.ok()).toBeTruthy();
    const body = await listed.json();
    expect(body.total).toBeGreaterThanOrEqual(1);
  });
});
