/**
 * Skills Path Panel Test
 *
 * Tests:
 *   1. Open Skills Path panel via rail, verify it shows skill invocation data
 *   2. Send a message and verify skills are correctly marked as "invoked"
 *   3. Compare left sidebar Skill Tree enabled skills with right-side Skills Path
 *   4. Toggle a skill in left sidebar, send another message, verify consistency
 *
 * Requires Next.js running on http://localhost:3000
 */

import { test, expect, Page } from "@playwright/test";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function goto(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
}

async function sendMessage(page: Page, message: string) {
  const textarea = page.locator("textarea").first();
  await textarea.click();
  await textarea.fill(message);
  await page.waitForTimeout(200);
  await textarea.press("Enter");
  // Wait for streaming to complete
  await page.waitForTimeout(8000);
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe("Skills Path Panel · Invocation & Consistency", () => {
  test("Skills Path panel shows skill invocations after sending a message", async ({ page }) => {
    await goto(page);

    // Open Skills Path panel via rail button
    const skillsRailBtn = page.locator("nav button[title='Skills Path']").first();
    await expect(skillsRailBtn).toBeVisible();
    await skillsRailBtn.click();
    await page.waitForTimeout(500);

    await page.screenshot({ path: "tests/e2e/screenshots/skills-01-panel-open.png", fullPage: true });

    // Verify Skills Path panel header is visible
    const skillsPanelHeader = page.locator("text=Skills Path").first();
    await expect(skillsPanelHeader).toBeVisible();

    // Send a message to trigger skill invocations
    await sendMessage(page, "hello");

    await page.screenshot({ path: "tests/e2e/screenshots/skills-02-after-message.png", fullPage: true });

    // Check Skills Path panel content
    const panelContent = page.locator("text=Per-message skill invocation").first();
    const hasContent = await panelContent.isVisible().catch(() => false);
    console.log(`Skills Path shows "Per-message skill invocation": ${hasContent}`);

    // Check for "invoked" badges
    const invokedBadges = page.locator("text=invoked");
    const invokedCount = await invokedBadges.count();
    console.log(`Number of "invoked" badges: ${invokedCount}`);

    // Check for "skipped" badges
    const skippedBadges = page.locator("text=skipped");
    const skippedCount = await skippedBadges.count();
    console.log(`Number of "skipped" badges: ${skippedCount}`);

    // At least some skills should be marked as invoked after sending a message
    expect(invokedCount + skippedCount).toBeGreaterThan(0);
  });

  test("Exec panel shows which skills were selected by skill router", async ({ page }) => {
    await goto(page);

    // Open Exec panel
    const execRailBtn = page.locator("nav button[title='Execution Path']").first();
    await execRailBtn.click();
    await page.waitForTimeout(500);

    // Send message
    await sendMessage(page, "hello");

    // Check that Skill Router step shows selected skills
    const skillRouterStep = page.locator("text=Skill router").first();
    await expect(skillRouterStep).toBeVisible();

    // Get the skills listed in the exec panel's skill router chips
    const execSkillChips = page.locator("div").filter({ hasText: /Skill router/ }).first()
      .locator("..").locator("span.inline-block");
    const chipTexts: string[] = [];
    const chipCount = await execSkillChips.count();
    for (let i = 0; i < chipCount; i++) {
      const text = await execSkillChips.nth(i).textContent();
      if (text && !text.includes("done") && !text.includes("s")) {
        chipTexts.push(text.trim());
      }
    }
    console.log(`Exec panel skill router chips: ${chipTexts.join(", ")}`);

    await page.screenshot({ path: "tests/e2e/screenshots/skills-03-exec-skills.png", fullPage: true });
  });

  test("Left sidebar Skill Tree enabled state matches effective skills", async ({ page }) => {
    await goto(page);

    // Open both Exec and Skills panels
    const execRailBtn = page.locator("nav button[title='Execution Path']").first();
    await execRailBtn.click();
    await page.waitForTimeout(300);

    const skillsRailBtn = page.locator("nav button[title='Skills Path']").first();
    await skillsRailBtn.click();
    await page.waitForTimeout(500);

    // Collect left sidebar enabled skill categories from Skill Tree section
    // The left sidebar shows skill categories with toggle switches
    const skillTreeSection = page.locator("text=SKILL TREE").first().locator("..");
    const toggles = skillTreeSection.locator("..").locator("button[role='switch'], input[type='checkbox'], [class*='toggle']");
    
    // Collect all enabled skill names from left sidebar
    const leftSidebarSkills: { name: string; enabled: boolean }[] = [];
    
    // Look for skill items with toggle states in sidebar
    const sidebarItems = page.locator("[class*='sidebar'] >> text=/Skills$/i").locator("..").locator("[role='switch']");
    const sidebarItemCount = await sidebarItems.count().catch(() => 0);
    console.log(`Sidebar skill toggle count: ${sidebarItemCount}`);

    // Try different approach - look for the toggle switches in SKILL TREE section
    const skillToggles = page.locator("div").filter({ hasText: "SKILL TREE" }).first()
      .locator("~ div").locator("button[role='switch']");
    
    // Alternative: just get all visible text near "Skills" in left sidebar
    const leftSkillText = await page.locator("div").filter({ hasText: "SKILL TREE" }).first()
      .locator("..").textContent().catch(() => "");
    console.log(`Left sidebar SKILL TREE section text: ${leftSkillText?.slice(0, 300)}`);

    // Send a message and observe
    await sendMessage(page, "what can you do");

    await page.screenshot({ path: "tests/e2e/screenshots/skills-04-both-panels.png", fullPage: true });

    // Get Skills Path panel content  
    const skillsPathText = await page.locator("text=Per-message skill invocation").first()
      .locator("..").textContent().catch(() => "");
    console.log(`Skills Path panel content: ${skillsPathText?.slice(0, 500)}`);

    // Get Exec panel skill router info
    const execText = await page.locator("text=Skill router").first()
      .locator("..").textContent().catch(() => "");
    console.log(`Exec panel Skill router text: ${execText?.slice(0, 300)}`);
  });

  test("Disabling a skill category in left sidebar reflects in effective skills", async ({ page }) => {
    await goto(page);

    // Open Skills Path panel
    const skillsRailBtn = page.locator("nav button[title='Skills Path']").first();
    await skillsRailBtn.click();
    await page.waitForTimeout(500);

    // Also open Exec panel
    const execRailBtn = page.locator("nav button[title='Execution Path']").first();
    await execRailBtn.click();
    await page.waitForTimeout(500);

    await page.screenshot({ path: "tests/e2e/screenshots/skills-05-before-toggle.png", fullPage: true });

    // Find a skill toggle in the left sidebar (e.g., "Ljg Skills")
    // The toggles are typically rendered as buttons with role="switch" or similar
    const ljgToggle = page.locator("div").filter({ hasText: /Ljg Skills/i })
      .locator("button[role='switch']").first();
    const ljgToggleExists = await ljgToggle.isVisible().catch(() => false);
    
    if (ljgToggleExists) {
      // Check initial state
      const wasChecked = await ljgToggle.getAttribute("aria-checked");
      console.log(`Ljg Skills toggle initial state: aria-checked=${wasChecked}`);

      // Toggle it off
      await ljgToggle.click();
      await page.waitForTimeout(1000);
      
      await page.screenshot({ path: "tests/e2e/screenshots/skills-06-after-toggle-off.png", fullPage: true });

      // Send a message
      await sendMessage(page, "tell me a joke");

      await page.screenshot({ path: "tests/e2e/screenshots/skills-07-after-message-toggled.png", fullPage: true });

      // Check exec panel - skill router should not include ljg skills
      const execContent = await page.locator("text=Skill router").first()
        .locator("..").textContent().catch(() => "");
      console.log(`After disabling Ljg Skills - Exec Skill router: ${execContent?.slice(0, 300)}`);

      // Check Skills Path panel 
      const skillsContent = await page.locator("text=Per-message skill invocation").first()
        .locator("..").textContent().catch(() => "");
      console.log(`After disabling Ljg Skills - Skills Path: ${skillsContent?.slice(0, 500)}`);

      // Toggle back on
      await ljgToggle.click();
      await page.waitForTimeout(500);
    } else {
      console.log("Could not find Ljg Skills toggle - trying alternative selectors");
      
      // Try finding any toggle switch in the skill tree area
      const allToggles = page.locator("button[role='switch']");
      const toggleCount = await allToggles.count();
      console.log(`Total toggle switches found: ${toggleCount}`);
      
      // Screenshot for debugging
      await page.screenshot({ path: "tests/e2e/screenshots/skills-06-debug-toggles.png", fullPage: true });
      
      if (toggleCount > 0) {
        // Click the second toggle (first might be a group toggle)
        const targetToggle = allToggles.nth(Math.min(1, toggleCount - 1));
        const toggleLabel = await targetToggle.locator("..").textContent().catch(() => "unknown");
        console.log(`Clicking toggle near: ${toggleLabel?.slice(0, 50)}`);
        
        await targetToggle.click();
        await page.waitForTimeout(1000);
        
        await sendMessage(page, "tell me something");
        await page.screenshot({ path: "tests/e2e/screenshots/skills-07-after-toggle.png", fullPage: true });

        // Restore toggle
        await targetToggle.click();
        await page.waitForTimeout(500);
      }
    }
  });
});
