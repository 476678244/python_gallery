/**
 * Exec Panel Chat Integration Test
 *
 * Opens the browser, sends simple messages ("hello", "what can you do"),
 * and observes the right-side Exec panel behavior.
 *
 * Requires Next.js running on http://localhost:3000
 */

import { test, expect } from "@playwright/test";

test.describe("Exec Panel · Chat Integration", () => {
  test("send messages and observe exec panel", async ({ page }) => {
    // Navigate to app
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    // Reset persisted UI state so no panels leak from previous tests
    await page.evaluate(() => localStorage.removeItem("safeclaw-ui-store"));
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    // Take a screenshot of initial state
    await page.screenshot({ path: "tests/e2e/screenshots/01-initial.png", fullPage: true });

    // Open the Exec panel via the rail button
    const execRailBtn = page.locator("nav button[title='Execution Path']").first();
    if (await execRailBtn.isVisible()) {
      await execRailBtn.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: "tests/e2e/screenshots/02-exec-panel-open.png", fullPage: true });
    }

    // Find the chat textarea
    const textarea = page.locator("textarea").first();
    await expect(textarea).toBeVisible({ timeout: 5000 });

    // --- Send "hello" ---
    await textarea.click();
    await textarea.fill("hello");
    await page.waitForTimeout(300);

    // Press Enter to send
    await textarea.press("Enter");
    await page.waitForTimeout(3000); // Wait for streaming response

    await page.screenshot({ path: "tests/e2e/screenshots/03-after-hello.png", fullPage: true });

    // Check if exec panel shows execution steps
    const execPanelContent = page.locator("text=Current run").first();
    const hasExecContent = await execPanelContent.isVisible().catch(() => false);
    console.log(`Exec panel shows execution steps after "hello": ${hasExecContent}`);

    // Wait for response to appear in chat
    await page.waitForTimeout(5000);
    await page.screenshot({ path: "tests/e2e/screenshots/04-hello-response.png", fullPage: true });

    // --- Send "what can you do" ---
    const textarea2 = page.locator("textarea").first();
    await textarea2.click();
    await textarea2.fill("what can you do");
    await page.waitForTimeout(300);

    await textarea2.press("Enter");
    await page.waitForTimeout(3000);

    await page.screenshot({ path: "tests/e2e/screenshots/05-after-whatcanyoudo.png", fullPage: true });

    // Wait for full response
    await page.waitForTimeout(8000);
    await page.screenshot({ path: "tests/e2e/screenshots/06-whatcanyoudo-response.png", fullPage: true });

    // Final state - check exec panel
    const finalExecContent = page.locator("text=Current run").first();
    const hasFinalExec = await finalExecContent.isVisible().catch(() => false);
    console.log(`Exec panel shows execution after "what can you do": ${hasFinalExec}`);

    // Log all visible text in exec panel area for debugging
    const rightPanelText = await page.locator("div.border-b").filter({ hasText: /Execution Path/i }).first().textContent().catch(() => "not found");
    console.log(`Exec panel text: ${rightPanelText?.slice(0, 200)}`);
  });
});
