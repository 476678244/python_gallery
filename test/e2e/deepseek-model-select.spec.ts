/**
 * DeepSeek Model Selection E2E Test
 *
 * DeepSeek models live in the sidebar Model section (AVAILABLE_MODELS).
 * SettingsPanel is not mounted on the main page — API key is tested via /settings/deepseek.
 */

import { test, expect, Page } from "@playwright/test";

const DEEPSEEK_MODELS = [
  { id: "deepseek-v4-flash", name: "DeepSeek V4 Flash" },
  { id: "deepseek-v4-pro", name: "DeepSeek V4 Pro" },
];

async function openModelSection(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 10000 });

  await page
    .locator("div.border-b")
    .filter({ hasText: /^[\s\S]*Model[\s\S]*$/i })
    .locator("button")
    .filter({ hasText: /Model/i })
    .first()
    .click();
  await page.waitForTimeout(300);
}

test.describe("DeepSeek Model Selection", () => {
  test("should display DeepSeek models in the sidebar Model list", async ({ page }) => {
    await openModelSection(page);

    for (const model of DEEPSEEK_MODELS) {
      await expect(page.getByText(model.name).first()).toBeVisible();
    }
  });

  test("should select DeepSeek V4 Pro model", async ({ page }) => {
    await openModelSection(page);

    const proModel = page.locator("button").filter({ hasText: "DeepSeek V4 Pro" }).first();
    await proModel.click();
    await page.waitForTimeout(300);

    const cls = await proModel.getAttribute("class");
    expect(cls).toContain("bg-blue-50");
  });

  test("should expose DeepSeek API key settings endpoint", async ({ page }) => {
    const res = await page.request.get("http://localhost:8000/settings/deepseek");
    expect(res.ok()).toBeTruthy();
    const data = await res.json();
    expect(data).toHaveProperty("configured");
  });

  test("should not claim vision capability for DeepSeek models", async ({ page }) => {
    // Frontend entity: DeepSeek supportedModes must not include vision
    await openModelSection(page);
    await expect(page.getByText("DeepSeek V4 Pro").first()).toBeVisible();

    const response = await page.request.get("http://localhost:8000/settings/models");
    const data = await response.json();
    const deepseekFromApi = (data.models || []).filter((m: { id: string }) =>
      m.id.startsWith("deepseek")
    );
    for (const m of deepseekFromApi) {
      const caps = m.capabilities?.supportedModes || m.supportedModes || [];
      expect(caps).not.toContain("vision");
    }
  });

  test("should persist DeepSeek model selection after reload", async ({ page }) => {
    await openModelSection(page);

    await page.locator("button").filter({ hasText: "DeepSeek V4 Pro" }).first().click();
    await page.waitForTimeout(500);

    await page.reload();
    await page.waitForLoadState("networkidle");
    await openModelSection(page);

    const proModel = page.locator("button").filter({ hasText: "DeepSeek V4 Pro" }).first();
    const cls = await proModel.getAttribute("class");
    expect(cls).toContain("bg-blue-50");
  });
});

test.describe("DeepSeek Vision Capability Test", () => {
  test("verify DeepSeek models do not include vision in capabilities", async ({ page }) => {
    const response = await page.request.get("http://localhost:8000/settings/models");
    const data = await response.json();

    console.log("Available models from backend:", data.models);

    // DeepSeek may be frontend-only; if present in API, must not advertise vision
    for (const m of data.models || []) {
      if (String(m.id).startsWith("deepseek") || String(m.provider) === "deepseek") {
        const caps = m.capabilities?.supportedModes || [];
        expect(caps).not.toContain("vision");
      }
    }
  });
});
