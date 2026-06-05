/**
 * Skill Tree Reload Consistency Test
 *
 * Tests whether skill tree state persists correctly across:
 *   1. Page reload (hard refresh)
 *   2. API re-fetch (loadSkills called again)
 *   3. Session switch with forced skill reload
 *
 * This tests the specific bug where the skill tree state
 * becomes inconsistent between sessions.
 *
 * Requires Next.js + backend on http://localhost:3000
 */

import { test, expect, Page } from "@playwright/test";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function goto(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
}

async function getSkillTreeStates(page: Page): Promise<Record<string, boolean>> {
  const states: Record<string, boolean> = {};
  const toggles = page.locator("button[role='switch']");
  const count = await toggles.count();
  
  for (let i = 0; i < count; i++) {
    const toggle = toggles.nth(i);
    const checked = await toggle.getAttribute("aria-checked");
    const parent = toggle.locator("..");
    const label = await parent.textContent().catch(() => `toggle-${i}`);
    const cleanLabel = label?.trim().replace(/\s+/g, " ").slice(0, 40) || `toggle-${i}`;
    states[cleanLabel] = checked === "true";
  }
  
  return states;
}

async function switchToSession(page: Page, index: number) {
  const sessionButtons = page.locator("div.group.relative button").filter({ hasText: /New Chat|Untitled/ });
  const count = await sessionButtons.count();
  console.log(`  switchToSession(${index}): ${count} sessions available`);
  if (index < count) {
    await sessionButtons.nth(index).click();
    await page.waitForTimeout(1000);
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe("Skill Tree · Reload & API Consistency", () => {

  test("skill toggle persists after page reload", async ({ page }) => {
    await goto(page);
    
    // Record initial
    const initial = await getSkillTreeStates(page);
    console.log("Initial states:", JSON.stringify(initial));
    
    // Toggle first skill OFF
    const firstToggle = page.locator("button[role='switch']").first();
    const firstLabel = await firstToggle.locator("..").textContent().catch(() => "unknown");
    const wasChecked = await firstToggle.getAttribute("aria-checked");
    console.log(`Toggling "${firstLabel?.trim().slice(0,30)}": ${wasChecked} -> ${wasChecked === "true" ? "false" : "true"}`);
    await firstToggle.click();
    await page.waitForTimeout(1000);

    // Verify toggle happened
    const afterToggle = await getSkillTreeStates(page);
    console.log("After toggle:", JSON.stringify(afterToggle));
    await page.screenshot({ path: "tests/e2e/screenshots/reload-01-after-toggle.png", fullPage: true });

    // Hard reload
    console.log("--- Page reload ---");
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000); // Wait for skill store hydration + API call

    const afterReload = await getSkillTreeStates(page);
    console.log("After reload:", JSON.stringify(afterReload));
    await page.screenshot({ path: "tests/e2e/screenshots/reload-02-after-reload.png", fullPage: true });

    // Compare
    const keys = Object.keys(afterToggle);
    let differences: string[] = [];
    for (const key of keys) {
      if (afterReload[key] !== afterToggle[key]) {
        differences.push(`"${key}": before-reload=${afterToggle[key]}, after-reload=${afterReload[key]}`);
      }
    }
    
    if (differences.length > 0) {
      console.log("❌ STATE CHANGED after reload:");
      differences.forEach(d => console.log(`  - ${d}`));
      console.log("  → This means the API/backend did NOT persist the toggle correctly!");
    } else {
      console.log("✓ State persisted correctly after reload");
    }

    // Restore
    if (wasChecked === "true") {
      await page.locator("button[role='switch']").first().click();
      await page.waitForTimeout(500);
    }
  });

  test("skill state is consistent during rapid session switching with skills API calls", async ({ page }) => {
    await goto(page);

    // Make sure we have at least 2 sessions
    const sessionCount = await page.locator("div.group.relative button").filter({ hasText: /New Chat|Untitled/ }).count();
    if (sessionCount < 2) {
      // Create a new session
      const addBtn = page.locator("button").filter({ hasText: /New Chat/ }).filter({ has: page.locator("svg") }).first();
      await addBtn.click();
      await page.waitForTimeout(1500);
    }

    // Toggle a skill OFF in session A
    const toggle = page.locator("button[role='switch']").nth(0);
    const initialState = await toggle.getAttribute("aria-checked");
    console.log(`Initial state of first toggle: ${initialState}`);
    
    if (initialState === "true") {
      await toggle.click();
      await page.waitForTimeout(800);
    }
    
    const expectedState = "false"; // We turned it off
    console.log(`Expected state after toggle: ${expectedState}`);

    // Now rapidly switch sessions and check state each time
    const results: { session: number; state: string | null }[] = [];
    
    for (let round = 0; round < 6; round++) {
      const targetSession = round % 2; // Alternate between 0 and 1
      await switchToSession(page, targetSession);
      await page.waitForTimeout(500);
      
      const currentState = await page.locator("button[role='switch']").nth(0).getAttribute("aria-checked");
      results.push({ session: targetSession, state: currentState });
      console.log(`  Round ${round}: session=${targetSession}, state=${currentState}`);
    }

    await page.screenshot({ path: "tests/e2e/screenshots/reload-03-rapid-switch.png", fullPage: true });

    // Check for inconsistencies
    const inconsistent = results.filter(r => r.state !== expectedState);
    if (inconsistent.length > 0) {
      console.log(`❌ ${inconsistent.length} INCONSISTENCIES during rapid switching:`);
      inconsistent.forEach((r, i) => {
        console.log(`  Round: session=${r.session}, expected=${expectedState}, got=${r.state}`);
      });
    } else {
      console.log("✓ State remained consistent during all rapid switches");
    }

    // Restore
    const finalState = await page.locator("button[role='switch']").nth(0).getAttribute("aria-checked");
    if (finalState !== initialState) {
      await page.locator("button[role='switch']").nth(0).click();
      await page.waitForTimeout(500);
    }
  });

  test("skill API response matches UI state after toggle", async ({ page }) => {
    await goto(page);

    // Toggle a skill
    const toggle = page.locator("button[role='switch']").nth(2); // 3rd toggle (e.g., Superpowers)
    const label = await toggle.locator("..").textContent().catch(() => "");
    const before = await toggle.getAttribute("aria-checked");
    console.log(`Target: "${label?.trim().slice(0,30)}", before: ${before}`);

    await toggle.click();
    await page.waitForTimeout(1000);

    const after = await toggle.getAttribute("aria-checked");
    console.log(`After UI toggle: ${after}`);

    // Now call the skills API directly and check what it returns
    const apiResponse = await page.evaluate(async () => {
      const res = await fetch("/api/skills");
      return res.json();
    });
    
    console.log(`API reports ${apiResponse.total} total skills`);
    
    // Check if the toggled skill's state in the API matches the UI
    // The API returns a tree - we need to check the enabled state
    const allNodes: any[] = [];
    function flatten(nodes: any[]) {
      for (const n of nodes) {
        allNodes.push(n);
        if (n.children) flatten(n.children);
      }
    }
    flatten(apiResponse.tree || []);
    
    // Log enabled state of first few leaf skills
    const leafSkills = allNodes.filter((n: any) => !n.isFolder);
    console.log(`API leaf skills (first 10):`);
    leafSkills.slice(0, 10).forEach((s: any) => {
      console.log(`  - ${s.name}: enabled=${s.enabled}`);
    });

    // Check if any folder matches our toggled label
    const folderNodes = allNodes.filter((n: any) => n.isFolder);
    console.log(`API folder nodes:`);
    folderNodes.forEach((f: any) => {
      const childEnabled = (f.children || []).filter((c: any) => !c.isFolder && c.enabled).length;
      const childTotal = (f.children || []).filter((c: any) => !c.isFolder).length;
      console.log(`  - ${f.name}: ${childEnabled}/${childTotal} enabled`);
    });

    await page.screenshot({ path: "tests/e2e/screenshots/reload-04-api-check.png", fullPage: true });

    // Restore
    await toggle.click();
    await page.waitForTimeout(500);
  });
});
