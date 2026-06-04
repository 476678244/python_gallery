/**
 * Right Panel Toggle Tests
 *
 * Design: 2-state model — rail icon is an on/off switch.
 *   Closed  → not rendered in DOM at all.
 *   Open    → rendered in DOM; can be expanded or collapsed via header click.
 *
 * State transitions:
 *   ① Click rail icon  → open panel (expanded by default)
 *   ② Click header     → collapse (37px header-only, still in DOM)
 *   ③ Click header     → expand back
 *   ④ Click rail icon  → close panel (removed from DOM entirely)
 *
 * Requires Next.js running on http://localhost:3000
 */

import { test, expect, Page } from "@playwright/test";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function goto(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  // Reset persisted UI state so no panels leak from previous tests
  await page.evaluate(() => localStorage.removeItem("safeclaw-ui-store"));
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);
}

/** Click a rail icon to toggle a panel */
async function togglePanel(page: Page, label: string) {
  const railBtn = page.locator("nav button[title]").filter({ hasText: new RegExp(label, "i") }).first();
  await railBtn.click();
  await page.waitForTimeout(300);
}

/** Get panel body by title */
function panelBody(page: Page, title: string) {
  return page
    .locator("div.border-b")
    .filter({ hasText: new RegExp(title, "i") })
    .first();
}

/** Get panel header button by title */
function panelHeader(page: Page, title: string) {
  return panelBody(page, title).locator("button").first();
}

/** Check if panel is expanded (has visible body content) */
async function isPanelExpanded(page: Page, title: string): Promise<boolean> {
  const panel = panelBody(page, title);
  const height = await panel.evaluate((el) => el.getBoundingClientRect().height);
  return height > 40; // Expanded panels are taller than just header (37px)
}

/** Check if a panel title is completely absent from the DOM (not just hidden) */
async function isPanelAbsent(page: Page, title: string): Promise<boolean> {
  const panels = page.locator("div.border-b").filter({ hasText: new RegExp(title, "i") });
  return (await panels.count()) === 0;
}

// ─── ① Basic Toggle ─────────────────────────────────────────────────────────

test.describe("Right Panel · Basic Toggle", () => {
  test("should open panel when clicking rail icon", async ({ page }) => {
    await goto(page);

    // Initially no panels should be visible
    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).not.toBeVisible();

    // Click Exec rail button
    await togglePanel(page, "Exec");

    // Panel should now be visible
    await expect(execPanel).toBeVisible();

    // Should be expanded (showing content)
    const expanded = await isPanelExpanded(page, "Execution Path");
    expect(expanded).toBe(true);
  });

  test("should only show opened panels and hide all others", async ({ page }) => {
    await goto(page);

    // Open only Skills panel
    await togglePanel(page, "Skills");

    // Skills should be visible
    const skillsPanel = panelBody(page, "Skills Path");
    await expect(skillsPanel).toBeVisible();

    // All other panels should be completely absent from DOM
    const otherTitles = ["Execution Path", "Prompt Budget", "Backend Log", "Shell", "Prompt Inspect", "Memory"];
    for (const title of otherTitles) {
      const absent = await isPanelAbsent(page, title);
      expect(absent, `Expected "${title}" to be absent when only Skills is open`).toBe(true);
    }
  });

  test("should collapse panel when clicking header", async ({ page }) => {
    await goto(page);

    // Open panel
    await togglePanel(page, "Exec");
    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    // Verify expanded
    const initialHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    expect(initialHeight).toBeGreaterThan(100);

    // Click header to collapse
    const header = panelHeader(page, "Execution Path");
    await header.click();
    await page.waitForTimeout(300);

    // Should be collapsed (just header height ~37px)
    const collapsedHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    expect(collapsedHeight).toBeLessThan(50);
  });

  test("should expand collapsed panel when clicking header again", async ({ page }) => {
    await goto(page);

    // Open and collapse
    await togglePanel(page, "Exec");
    const header = panelHeader(page, "Execution Path");
    await header.click();
    await page.waitForTimeout(300);

    // Click again to expand
    await header.click();
    await page.waitForTimeout(300);

    // Should be expanded again
    const expanded = await isPanelExpanded(page, "Execution Path");
    expect(expanded).toBe(true);
  });

  test("should close panel when clicking rail icon again", async ({ page }) => {
    await goto(page);

    // Open panel
    await togglePanel(page, "Exec");
    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    // Click rail button again to close
    await togglePanel(page, "Exec");

    // Panel should be completely removed from DOM, not just hidden
    const absent = await isPanelAbsent(page, "Execution Path");
    expect(absent).toBe(true);
  });

  test("should close a collapsed panel when clicking rail icon", async ({ page }) => {
    await goto(page);

    // Open and then collapse via header click
    await togglePanel(page, "Exec");
    const header = panelHeader(page, "Execution Path");
    await header.click();
    await page.waitForTimeout(300);

    // Collapsed panel is still in DOM (37px header only)
    const execPanel = panelBody(page, "Execution Path");
    const collapsedHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    expect(collapsedHeight).toBeLessThan(50);

    // Click rail icon → panel is closed entirely (removed from DOM)
    await togglePanel(page, "Exec");
    const absent = await isPanelAbsent(page, "Execution Path");
    expect(absent).toBe(true);
  });
});

// ─── ② Multiple Panels ───────────────────────────────────────────────────────

test.describe("Right Panel · Multiple Panels", () => {
  test("should allow multiple panels open simultaneously", async ({ page }) => {
    await goto(page);

    // Open two panels
    await togglePanel(page, "Exec");
    await togglePanel(page, "Skills");

    const execPanel = panelBody(page, "Execution Path");
    const skillsPanel = panelBody(page, "Skills Path");

    await expect(execPanel).toBeVisible();
    await expect(skillsPanel).toBeVisible();

    // Both should be expanded
    const execExpanded = await isPanelExpanded(page, "Execution Path");
    const skillsExpanded = await isPanelExpanded(page, "Skills Path");
    expect(execExpanded).toBe(true);
    expect(skillsExpanded).toBe(true);
  });

  test("should collapse one panel while keeping other expanded", async ({ page }) => {
    await goto(page);

    // Open two panels
    await togglePanel(page, "Exec");
    await togglePanel(page, "Skills");

    // Collapse first panel
    const execHeader = panelHeader(page, "Execution Path");
    await execHeader.click();
    await page.waitForTimeout(300);

    // Exec should be collapsed
    const execExpanded = await isPanelExpanded(page, "Execution Path");
    expect(execExpanded).toBe(false);

    // Skills should still be expanded
    const skillsExpanded = await isPanelExpanded(page, "Skills Path");
    expect(skillsExpanded).toBe(true);
  });

  test("should close one panel while keeping other open", async ({ page }) => {
    await goto(page);

    // Open two panels
    await togglePanel(page, "Exec");
    await togglePanel(page, "Skills");

    // Close first panel
    await togglePanel(page, "Exec");

    const execPanel = panelBody(page, "Execution Path");
    const skillsPanel = panelBody(page, "Skills Path");

    // Exec should be gone
    await expect(execPanel).not.toBeVisible();

    // Skills should still be visible
    await expect(skillsPanel).toBeVisible();
  });
});

// ─── ③ Panel Toggle from Chat Header ───────────────────────────────────────

test.describe("Right Panel · Chat Header Toggle", () => {
  test("should toggle right panel from chat header button", async ({ page }) => {
    await goto(page);

    // Find the right panel toggle button in chat header (PanelRight icon)
    const headerToggleBtn = page.locator("header button").filter({ has: page.locator("svg").filter({ hasText: /panel/i }) }).first();

    // If button exists (might be hidden on mobile), test it
    const isVisible = await headerToggleBtn.isVisible().catch(() => false);

    if (isVisible) {
      // Click to open panel
      await headerToggleBtn.click();
      await page.waitForTimeout(300);

      // A panel should be visible (likely Exec since that's the default)
      const execPanel = panelBody(page, "Execution Path");
      await expect(execPanel).toBeVisible();

      // Click again to close
      await headerToggleBtn.click();
      await page.waitForTimeout(300);

      await expect(execPanel).not.toBeVisible();
    }
  });
});

// ─── ④ Persistence ───────────────────────────────────────────────────────────

test.describe("Right Panel · State Persistence", () => {
  test("should persist open panels after page reload", async ({ page }) => {
    await goto(page);

    // Open a panel
    await togglePanel(page, "Exec");

    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    // Reload page
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Panel should still be visible (persisted in localStorage)
    const execPanelAfterReload = panelBody(page, "Execution Path");
    await expect(execPanelAfterReload).toBeVisible();
  });
});
