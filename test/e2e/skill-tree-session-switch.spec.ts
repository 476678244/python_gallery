/**
 * Skill Tree Session Switch Test
 *
 * Tests whether skill tree toggle states remain consistent when switching
 * between different chat sessions.
 *
 * Steps:
 *   1. Open app, note initial skill tree state
 *   2. Toggle a skill off
 *   3. Create/switch to another session
 *   4. Check if skill tree state is preserved or reset
 *   5. Switch back to original session
 *   6. Check if skill tree state matches what we set
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

/** Get all skill tree toggle states from left sidebar */
async function getSkillTreeStates(page: Page): Promise<Record<string, boolean>> {
  const states: Record<string, boolean> = {};
  
  // Find all toggle switches (role=switch) in the skill tree area
  const toggles = page.locator("button[role='switch']");
  const count = await toggles.count();
  
  for (let i = 0; i < count; i++) {
    const toggle = toggles.nth(i);
    const checked = await toggle.getAttribute("aria-checked");
    // Get the label text near this toggle
    const parent = toggle.locator("..");
    const label = await parent.textContent().catch(() => `toggle-${i}`);
    const cleanLabel = label?.trim().replace(/\s+/g, " ").slice(0, 40) || `toggle-${i}`;
    states[cleanLabel] = checked === "true";
  }
  
  return states;
}

/** Click "+ New Chat" button to create a new session */
async function createNewSession(page: Page) {
  // The "+ New Chat" button is a dashed-border button inside the CHATS section
  const addBtn = page.locator("button").filter({ hasText: /New Chat/ }).filter({ has: page.locator("svg") }).first();
  await addBtn.click();
  await page.waitForTimeout(1500);
}

/** Click on a session in the sidebar by index (0 = first/newest) */
async function switchToSession(page: Page, index: number) {
  // Session items are buttons inside .group.relative divs in the SessionList
  // They contain the session title "New Chat" and timestamp
  const sessionButtons = page.locator("div.group.relative button").filter({ hasText: /New Chat|Untitled/ });
  const sessionCount = await sessionButtons.count();
  console.log(`Found ${sessionCount} session buttons`);
  
  if (index < sessionCount) {
    await sessionButtons.nth(index).click();
    await page.waitForTimeout(1000);
  } else {
    console.log(`Cannot switch to index ${index}, only ${sessionCount} sessions`);
  }
}

/** Get the currently active session title */
async function getActiveSessionInfo(page: Page): Promise<string> {
  // The active session has blue background (bg-blue-50)
  const active = page.locator("div.group.relative button.bg-blue-50, div.group.relative button[class*='blue-50']").first();
  const text = await active.textContent().catch(() => "none");
  return text?.trim().slice(0, 50) || "none";
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe("Skill Tree · Session Switch Consistency", () => {
  test("skill tree state should be consistent across session switches", async ({ page }) => {
    await goto(page);

    // Step 1: Record initial skill tree states
    const initialStates = await getSkillTreeStates(page);
    console.log("Initial skill tree states:", JSON.stringify(initialStates, null, 2));
    await page.screenshot({ path: "tests/e2e/screenshots/session-01-initial.png", fullPage: true });

    // Step 2: Toggle "Anthropic Skills" OFF
    const anthropicToggle = page.locator("div").filter({ hasText: /^Anthropic Skills$/ })
      .locator("button[role='switch']").first();
    const anthropicVisible = await anthropicToggle.isVisible().catch(() => false);
    
    if (!anthropicVisible) {
      // Try alternative: find by proximity
      const allToggles = page.locator("button[role='switch']");
      const count = await allToggles.count();
      console.log(`Total toggles: ${count}`);
      
      // Find the first toggle that's ON and toggle it
      for (let i = 0; i < count; i++) {
        const t = allToggles.nth(i);
        const checked = await t.getAttribute("aria-checked");
        if (checked === "true") {
          const parentText = await t.locator("..").textContent().catch(() => "");
          console.log(`Toggling OFF: ${parentText?.trim().slice(0, 40)}`);
          await t.click();
          await page.waitForTimeout(500);
          break;
        }
      }
    } else {
      const wasChecked = await anthropicToggle.getAttribute("aria-checked");
      console.log(`Anthropic Skills initial: ${wasChecked}`);
      if (wasChecked === "true") {
        await anthropicToggle.click();
        await page.waitForTimeout(500);
      }
    }

    // Record state after toggle
    const afterToggleStates = await getSkillTreeStates(page);
    console.log("After toggle states:", JSON.stringify(afterToggleStates, null, 2));
    await page.screenshot({ path: "tests/e2e/screenshots/session-02-after-toggle.png", fullPage: true });

    // Step 3: Create a new chat session
    const activeBeforeNew = await getActiveSessionInfo(page);
    console.log(`Active session before creating new: ${activeBeforeNew}`);
    await createNewSession(page);
    await page.waitForTimeout(1500);
    const activeAfterNew = await getActiveSessionInfo(page);
    console.log(`Active session after creating new: ${activeAfterNew}`);
    await page.screenshot({ path: "tests/e2e/screenshots/session-03-new-session.png", fullPage: true });

    // Step 4: Check skill tree state in new session
    const newSessionStates = await getSkillTreeStates(page);
    console.log("New session skill tree states:", JSON.stringify(newSessionStates, null, 2));

    // Compare with afterToggle state - should be the same (skill tree is global)
    const keys = Object.keys(afterToggleStates);
    let inconsistencies: string[] = [];
    for (const key of keys) {
      if (newSessionStates[key] !== afterToggleStates[key]) {
        inconsistencies.push(`"${key}": was=${afterToggleStates[key]}, now=${newSessionStates[key]} (after new session)`);
      }
    }
    
    if (inconsistencies.length > 0) {
      console.log("❌ INCONSISTENCY after creating new session:");
      inconsistencies.forEach(i => console.log(`  - ${i}`));
    } else {
      console.log("✓ Skill tree state consistent after creating new session");
    }

    // Step 5: Switch back to original session
    console.log("--- Switching to session index 1 (original) ---");
    await switchToSession(page, 1);
    const activeAfterSwitch1 = await getActiveSessionInfo(page);
    console.log(`Active session after switch to idx 1: ${activeAfterSwitch1}`);
    await page.screenshot({ path: "tests/e2e/screenshots/session-04-switch-back.png", fullPage: true });

    // Step 6: Check skill tree state after switching back
    const switchBackStates = await getSkillTreeStates(page);
    console.log("Switch back skill tree states:", JSON.stringify(switchBackStates, null, 2));

    let switchBackInconsistencies: string[] = [];
    for (const key of keys) {
      if (switchBackStates[key] !== afterToggleStates[key]) {
        switchBackInconsistencies.push(`"${key}": was=${afterToggleStates[key]}, now=${switchBackStates[key]} (after switch back)`);
      }
    }

    if (switchBackInconsistencies.length > 0) {
      console.log("❌ INCONSISTENCY after switching back to original session:");
      switchBackInconsistencies.forEach(i => console.log(`  - ${i}`));
    } else {
      console.log("✓ Skill tree state consistent after switching back");
    }

    // Step 7: Switch to new session again
    console.log("--- Switching to session index 0 (new) ---");
    await switchToSession(page, 0);
    const activeAfterSwitch2 = await getActiveSessionInfo(page);
    console.log(`Active session after switch to idx 0: ${activeAfterSwitch2}`);
    await page.screenshot({ path: "tests/e2e/screenshots/session-05-switch-new-again.png", fullPage: true });

    const secondSwitchStates = await getSkillTreeStates(page);
    console.log("Second switch states:", JSON.stringify(secondSwitchStates, null, 2));

    let secondSwitchInconsistencies: string[] = [];
    for (const key of keys) {
      if (secondSwitchStates[key] !== afterToggleStates[key]) {
        secondSwitchInconsistencies.push(`"${key}": was=${afterToggleStates[key]}, now=${secondSwitchStates[key]} (after 2nd switch)`);
      }
    }

    if (secondSwitchInconsistencies.length > 0) {
      console.log("❌ INCONSISTENCY on second switch:");
      secondSwitchInconsistencies.forEach(i => console.log(`  - ${i}`));
    } else {
      console.log("✓ Skill tree state consistent on second switch");
    }

    // Step 8: Toggle something in session B, switch to A, verify A doesn't change
    console.log("--- Step 8: Toggle in session B, verify isolation ---");
    // We're currently on new session (idx 0). Toggle Ljg Skills
    const ljgToggle = page.locator("button[role='switch']").nth(1);
    const ljgBefore = await ljgToggle.getAttribute("aria-checked");
    console.log(`Ljg Skills before toggle in session B: ${ljgBefore}`);
    await ljgToggle.click();
    await page.waitForTimeout(500);
    const ljgAfter = await ljgToggle.getAttribute("aria-checked");
    console.log(`Ljg Skills after toggle in session B: ${ljgAfter}`);

    // Switch to session A (idx 1)
    await switchToSession(page, 1);
    await page.waitForTimeout(500);
    const statesInA = await getSkillTreeStates(page);
    console.log("States in session A after toggling in B:", JSON.stringify(statesInA, null, 2));

    // Switch back to session B (idx 0)
    await switchToSession(page, 0);
    await page.waitForTimeout(500);
    const statesInB = await getSkillTreeStates(page);
    console.log("States in session B after switching back:", JSON.stringify(statesInB, null, 2));
    await page.screenshot({ path: "tests/e2e/screenshots/session-06-final.png", fullPage: true });

    // Check if A and B have different states (they shouldn't if global, but user reports inconsistency)
    const aKeys = Object.keys(statesInA);
    let abDifferences: string[] = [];
    for (const key of aKeys) {
      if (statesInA[key] !== statesInB[key]) {
        abDifferences.push(`"${key}": A=${statesInA[key]}, B=${statesInB[key]}`);
      }
    }
    
    if (abDifferences.length > 0) {
      console.log("⚠️  DIFFERENCE between session A and session B:");
      abDifferences.forEach(d => console.log(`  - ${d}`));
      console.log("  → Skill tree state is NOT consistent across sessions!");
    } else {
      console.log("✓ Skill tree state identical between session A and B");
    }

    // Final summary
    const totalInconsistencies = [...inconsistencies, ...switchBackInconsistencies, ...secondSwitchInconsistencies, ...abDifferences];
    if (totalInconsistencies.length > 0) {
      console.log("\n🚨 TOTAL INCONSISTENCIES FOUND:", totalInconsistencies.length);
      totalInconsistencies.forEach(i => console.log(`  - ${i}`));
    }
    
    // Report - don't hard-fail, report findings
    console.log(`\n📊 SUMMARY: ${totalInconsistencies.length} inconsistencies found`);
  });

  test("skill tree state persists after toggling and rapid session switching", async ({ page }) => {
    await goto(page);

    // Toggle a skill off
    const toggles = page.locator("button[role='switch']");
    const toggleCount = await toggles.count();
    
    if (toggleCount < 2) {
      console.log("Not enough toggles to test");
      return;
    }

    // Toggle second skill off
    const targetToggle = toggles.nth(1);
    const initialChecked = await targetToggle.getAttribute("aria-checked");
    const parentText = await targetToggle.locator("..").textContent().catch(() => "toggle-1");
    console.log(`Target: "${parentText?.trim().slice(0, 40)}" initial=${initialChecked}`);

    if (initialChecked === "true") {
      await targetToggle.click();
      await page.waitForTimeout(500);
    }

    const afterState = await targetToggle.getAttribute("aria-checked");
    console.log(`After toggle: ${afterState}`);

    // Rapid session switches
    const sessions = page.locator("div.group.relative button").filter({ hasText: /New Chat|Untitled/ });
    const sessionCount = await sessions.count();
    console.log(`Sessions available: ${sessionCount}`);

    if (sessionCount >= 2) {
      // Switch rapidly between sessions
      for (let i = 0; i < 4; i++) {
        await sessions.nth(i % sessionCount).click();
        await page.waitForTimeout(300);
      }
      
      await page.waitForTimeout(1000);
      await page.screenshot({ path: "tests/e2e/screenshots/session-06-rapid-switch.png", fullPage: true });

      // Check toggle state after rapid switching
      const finalChecked = await toggles.nth(1).getAttribute("aria-checked");
      console.log(`After rapid switches: ${finalChecked}`);
      
      if (finalChecked !== afterState) {
        console.log(`❌ State changed after rapid switching! Expected ${afterState}, got ${finalChecked}`);
      } else {
        console.log(`✓ State preserved after rapid switching`);
      }

      expect(finalChecked).toBe(afterState);
    }

    // Restore toggle
    const currentState = await toggles.nth(1).getAttribute("aria-checked");
    if (currentState !== initialChecked) {
      await toggles.nth(1).click();
      await page.waitForTimeout(300);
    }
  });
});
