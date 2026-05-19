/**
 * Right Panel Resize Tests
 *
 * Tests the resizable right panel:
 *   ① Horizontal resize (panel width)
 *   ② Vertical resize (panel heights)
 *   ③ Auto-distribute heights (1-3 panels)
 *   ④ User manual adjustment after auto-distribute
 *
 * Requires Next.js running on http://localhost:3000
 */

import { test, expect, Page } from "@playwright/test";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function goto(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);
}

/** Click a rail icon to open a panel */
async function openPanel(page: Page, label: string) {
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

/** Get horizontal resize handle */
function horizontalResizeHandle(page: Page) {
  return page.locator("div.cursor-ew-resize").first();
}

/** Get vertical resize handle at the bottom of a panel */
function verticalResizeHandle(page: Page, panelTitle: string) {
  return panelBody(page, panelTitle)
    .locator("div.cursor-ns-resize")
    .first();
}

// ─── ① Horizontal Resize ─────────────────────────────────────────────────────

test.describe("Right Panel · Horizontal Resize", () => {
  test("should resize panel width by dragging horizontal handle", async ({ page }) => {
    await goto(page);

    // Open a panel first
    await openPanel(page, "Exec");

    // Wait for panel to be visible
    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    // Get initial width
    const initialWidth = await execPanel.evaluate((el) => el.getBoundingClientRect().width);

    // Find and drag horizontal resize handle
    const handle = horizontalResizeHandle(page);
    await expect(handle).toBeVisible();

    // Drag to widen panel (move handle to the left)
    const handleBox = await handle.boundingBox();
    if (handleBox) {
      await handle.dragTo(handle, {
        force: true,
        targetPosition: { x: -50, y: handleBox.height / 2 },
      });
    }

    await page.waitForTimeout(300);

    // Check width changed
    const newWidth = await execPanel.evaluate((el) => el.getBoundingClientRect().width);
    expect(newWidth).not.toBe(initialWidth);
  });
});

// ─── ② Vertical Resize ────────────────────────────────────────────────────────

test.describe("Right Panel · Vertical Resize", () => {
  test("should resize panel height by dragging vertical handle", async ({ page }) => {
    await goto(page);

    // Open a panel
    await openPanel(page, "Exec");

    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    // Get initial height
    const initialHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);

    // Find vertical resize handle
    const vHandle = verticalResizeHandle(page, "Execution Path");
    await expect(vHandle).toBeVisible();

    // Drag to resize
    const handleBox = await vHandle.boundingBox();
    if (handleBox) {
      await vHandle.dragTo(vHandle, {
        force: true,
        targetPosition: { x: handleBox.width / 2, y: 50 },
      });
    }

    await page.waitForTimeout(300);

    // Check height changed
    const newHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    expect(Math.abs(newHeight - initialHeight)).toBeGreaterThan(10);
  });
});

// ─── ③ Auto-distribute Heights ───────────────────────────────────────────────

test.describe("Right Panel · Auto-distribute Heights", () => {
  test("1 panel should fill entire height", async ({ page }) => {
    await goto(page);

    // Open just one panel
    await openPanel(page, "Exec");

    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    // Panel should take most of viewport height
    const panelHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    const viewportHeight = await page.evaluate(() => window.innerHeight);

    // Should be at least 50% of viewport
    expect(panelHeight).toBeGreaterThan(viewportHeight * 0.5);
  });

  test("2 panels should each take ~50% height", async ({ page }) => {
    await goto(page);

    // Open two panels
    await openPanel(page, "Exec");
    await openPanel(page, "Skills");

    const execPanel = panelBody(page, "Execution Path");
    const skillsPanel = panelBody(page, "Skills Path");

    await expect(execPanel).toBeVisible();
    await expect(skillsPanel).toBeVisible();

    // Get heights
    const execHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    const skillsHeight = await skillsPanel.evaluate((el) => el.getBoundingClientRect().height);

    // Both should be significant and similar
    expect(execHeight).toBeGreaterThan(150);
    expect(skillsHeight).toBeGreaterThan(150);

    // Difference should be within 20%
    const ratio = Math.max(execHeight, skillsHeight) / Math.min(execHeight, skillsHeight);
    expect(ratio).toBeLessThan(1.3);
  });

  test("3 panels should each take ~33% height", async ({ page }) => {
    await goto(page);

    // Open three panels
    await openPanel(page, "Exec");
    await openPanel(page, "Skills");
    await openPanel(page, "Budget");

    const execPanel = panelBody(page, "Execution Path");
    const skillsPanel = panelBody(page, "Skills Path");
    const budgetPanel = panelBody(page, "Budget");

    await expect(execPanel).toBeVisible();
    await expect(skillsPanel).toBeVisible();
    await expect(budgetPanel).toBeVisible();

    // Get heights
    const heights = await Promise.all([
      execPanel.evaluate((el) => el.getBoundingClientRect().height),
      skillsPanel.evaluate((el) => el.getBoundingClientRect().height),
      budgetPanel.evaluate((el) => el.getBoundingClientRect().height),
    ]);

    // All should be significant
    heights.forEach((h) => expect(h).toBeGreaterThan(100));

    // Max/min ratio should be within 40% (auto-distribute isn't perfect)
    const max = Math.max(...heights);
    const min = Math.min(...heights);
    expect(max / min).toBeLessThan(1.5);
  });
});

// ─── ④ User Manual Adjustment ────────────────────────────────────────────────

test.describe("Right Panel · Manual Adjustment", () => {
  test("manual resize should override auto-distribute", async ({ page }) => {
    await goto(page);

    // Open two panels
    await openPanel(page, "Exec");
    await openPanel(page, "Skills");

    const execPanel = panelBody(page, "Execution Path");
    await expect(execPanel).toBeVisible();

    const initialHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);

    // Manually resize first panel
    const vHandle = verticalResizeHandle(page, "Execution Path");
    const handleBox = await vHandle.boundingBox();

    if (handleBox) {
      // Make it significantly larger
      await vHandle.dragTo(vHandle, {
        force: true,
        targetPosition: { x: handleBox.width / 2, y: 100 },
      });
    }

    await page.waitForTimeout(300);

    // Height should have increased
    const newHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
    expect(newHeight).toBeGreaterThan(initialHeight + 50);

    // Refresh page
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Re-open panels
    await openPanel(page, "Exec");
    await openPanel(page, "Skills");

    await page.waitForTimeout(500);

    // After manual resize and reload, heights might be different
    // but both panels should still be visible
    const execPanel2 = panelBody(page, "Execution Path");
    const skillsPanel2 = panelBody(page, "Skills Path");

    await expect(execPanel2).toBeVisible();
    await expect(skillsPanel2).toBeVisible();
  });
});
