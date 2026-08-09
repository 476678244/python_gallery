/**
 * Slash command palette — /help /skill /clear /new and discovery via /
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

test.describe("Slash command palette", () => {
  test.beforeEach(async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
  });

  test("typing / opens command palette with core commands", async ({ page }) => {
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/");
    await page.waitForTimeout(300);

    const cmd = page.getByTestId("slash-command-dropdown");
    await expect(cmd).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-help")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-model")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-skill")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-clear")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-new")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-remember")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-memory")).toBeVisible();
  });

  test("/help lists all commands", async ({ page }) => {
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/help");
    await page.waitForTimeout(300);

    const cmd = page.getByTestId("slash-command-dropdown");
    await expect(cmd).toBeVisible();
    await expect(cmd.getByText("All Commands")).toBeVisible();
    await expect(cmd.getByTestId("slash-cmd-clear")).toBeVisible();
  });

  test("selecting /skill from palette opens skill picker", async ({ page }) => {
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/");
    await page.waitForTimeout(300);

    await page.getByTestId("slash-cmd-skill").click();
    await page.waitForTimeout(500);

    await expect(page.getByTestId("skill-autocomplete-dropdown")).toBeVisible({
      timeout: 10000,
    });
    await expect(textarea).toHaveValue(/\/skill\s/);
  });

  test("/clear clears chat and shows notice", async ({ page }) => {
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/clear");
    await page.waitForTimeout(200);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(400);

    await expect(page.getByTestId("slash-notice")).toHaveText("Chat cleared");
    await expect(textarea).toHaveValue("");
  });

  test("/new creates a session and shows notice", async ({ page }) => {
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill("/new");
    await page.waitForTimeout(200);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1200);

    await expect(page.getByTestId("slash-notice")).toHaveText("New chat started");
  });

  test("model chip opens /model picker", async ({ page }) => {
    const chip = page.getByTestId("model-chip");
    await expect(chip).toBeVisible();
    await chip.click();
    await page.waitForTimeout(300);

    await expect(page.getByTestId("model-autocomplete-dropdown")).toBeVisible();
    const textarea = page.locator("textarea").first();
    await expect(textarea).toHaveValue(/\/model\s/);
  });
});
