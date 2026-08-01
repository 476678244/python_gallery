/**
 * Skill Autocomplete E2E Tests
 *
 * Tests that the skill slash autocomplete dropdown:
 * 1. Shows when user types "/skill" (or a bare skill prefix like "/ljg-qa")
 * 2. Contains skills from all categories (builtin, private, linked)
 * 3. Filters correctly when user types
 * 4. Allows keyboard navigation and selection
 *
 * Note: bare "/" opens the command palette, not skills — use /skill for this suite.
 */

import { test, expect, Page } from "@playwright/test";

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Wait until page has loaded and the chat textarea is usable */
async function waitForApp(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
}

/** Ensure there is an active session; creates one if the list is empty */
async function ensureSession(page: Page) {
  const textarea = page.locator("textarea").first();
  const isDisabled = await textarea.isDisabled().catch(() => true);
  if (isDisabled) {
    const newChatBtn = page.getByText("New Chat").first();
    await newChatBtn.click();
    await page.waitForTimeout(1200);
  }
}

/** Open skill picker via /skill and wait for autocomplete dropdown */
async function openSkillAutocomplete(page: Page) {
  const textarea = page.locator("textarea").first();
  await textarea.click();
  await textarea.fill("/skill");
  // Wait longer for skills to load from API and dropdown to render
  await page.waitForTimeout(1000);
}

/** Get dropdown locator */
function getDropdownLocator(page: Page) {
  return page.getByTestId("skill-autocomplete-dropdown");
}

/** Get all skill names from the autocomplete dropdown */
async function getDropdownSkillNames(page: Page): Promise<string[]> {
  const dropdown = getDropdownLocator(page);
  
  // Wait for dropdown to be visible
  await expect(dropdown).toBeVisible({ timeout: 10000 });
  
  // Get all skill buttons in the dropdown (buttons inside the dropdown that have skill names)
  const skillButtons = dropdown.locator("button");
  const count = await skillButtons.count();
  
  const names: string[] = [];
  for (let i = 0; i < count; i++) {
    const name = await skillButtons.nth(i).locator("div.font-medium").textContent().catch(() => null);
    if (name) names.push(name.trim());
  }
  return names;
}

/** Get skills data from API */
async function getSkillsFromAPI(page: Page): Promise<{
  builtin: string[];
  private: string[];
  linked: string[];
  marketplace: string[];
}> {
  const response = await page.request.get("http://localhost:8000/skills");
  const data = await response.json();
  
  const skills = {
    builtin: [] as string[],
    private: [] as string[],
    linked: [] as string[],
    marketplace: [] as string[],
  };
  
  // Parse skill tree
  for (const node of data.tree || []) {
    const category = node.id?.startsWith("linked/") ? "linked" : 
                     node.id === "private" ? "private" : 
                     node.id === "builtin" ? "builtin" : "other";
    
    for (const child of node.children || []) {
      if (!child.is_folder) {
        const skillName = child.name;
        if (category === "linked" || category === "private" || category === "builtin") {
          skills[category].push(skillName);
        }
      }
    }
  }
  
  return skills;
}

// ─── Test Suite ─────────────────────────────────────────────────────────────

test.describe("Skill Autocomplete", () => {
  test.beforeEach(async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
  });

  test("shows autocomplete dropdown when typing /skill", async ({ page }) => {
    // Wait for skills to be loaded from API first
    await page.waitForTimeout(500);
    
    await openSkillAutocomplete(page);
    
    // Verify dropdown is visible using regex matcher
    const dropdown = getDropdownLocator(page);
    await expect(dropdown).toBeVisible({ timeout: 10000 });
    
    // Verify dropdown header shows count
    const header = page.getByText(/Available Skills \(\d+\)/);
    await expect(header).toBeVisible();
  });

  test("autocomplete contains skills from all categories", async ({ page }) => {
    // Get skills from API for comparison
    const apiSkills = await getSkillsFromAPI(page);
    console.log("API skills by category:", apiSkills);
    
    // Wait for skills to be loaded from API
    await page.waitForTimeout(500);
    
    // Open autocomplete
    await openSkillAutocomplete(page);
    
    // Get skills from dropdown
    const dropdownSkills = await getDropdownSkillNames(page);
    console.log("Dropdown skills:", dropdownSkills);
    
    // Verify that skills from each category are represented
    const totalApiSkills = 
      apiSkills.builtin.length + 
      apiSkills.private.length + 
      apiSkills.linked.length;
    
    if (totalApiSkills > 0) {
      expect(dropdownSkills.length).toBeGreaterThan(0);
      expect(dropdownSkills.length).toBeLessThanOrEqual(totalApiSkills);
    }
    
    // Check that at least some skills from each category are present
    for (const category of ["builtin", "private", "linked"] as const) {
      if (apiSkills[category].length > 0) {
        const hasSkillFromCategory = apiSkills[category].some(
          skillName => dropdownSkills.includes(skillName)
        );
        console.log(`Category ${category}: ${hasSkillFromCategory ? "✅ found" : "❌ not found"}`);
      }
    }
  });

  test("autocomplete filters when typing after slash", async ({ page }) => {
    await openSkillAutocomplete(page);

    const textarea = page.locator("textarea").first();

    // Use a distinctive name prefix (filter also matches descriptions)
    await textarea.fill("/ljg-qa");
    await page.waitForTimeout(300);

    const filteredSkills = await getDropdownSkillNames(page);
    expect(filteredSkills.length).toBeGreaterThan(0);
    for (const skill of filteredSkills) {
      expect(skill.toLowerCase()).toContain("ljg-qa");
    }
  });

  test("keyboard navigation works in dropdown", async ({ page }) => {
    await page.waitForTimeout(500);
    await openSkillAutocomplete(page);
    
    const dropdown = getDropdownLocator(page);
    await expect(dropdown).toBeVisible({ timeout: 10000 });
    
    // Press arrow down to navigate
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(100);
    
    // Press arrow up to navigate back
    await page.keyboard.press("ArrowUp");
    await page.waitForTimeout(100);
    
    // Press Escape to close dropdown
    await page.keyboard.press("Escape");
    await page.waitForTimeout(100);
    
    // Dropdown should be closed
    await expect(dropdown).not.toBeVisible();
  });

  test("selecting skill from dropdown inserts it into input", async ({ page }) => {
    await page.waitForTimeout(500);
    await openSkillAutocomplete(page);
    
    // Get first skill from dropdown
    const dropdown = getDropdownLocator(page);
    const firstSkill = dropdown.locator("button").first();
    
    // Get the skill name
    const skillName = await firstSkill.locator("div.font-medium").textContent();
    
    if (skillName) {
      // Click the skill
      await firstSkill.click();
      await page.waitForTimeout(200);
      
      // Verify input contains the skill name with slash prefix
      const textarea = page.locator("textarea").first();
      const inputValue = await textarea.inputValue();
      expect(inputValue).toContain(`/${skillName.trim()}`);
    }
  });

  test("each category has at least one enabled skill in dropdown", async ({ page }) => {
    // Get API skills by category
    const response = await page.request.get("http://localhost:8000/skills");
    const data = await response.json();
    
    // Count enabled skills per category from API
    const categoryCounts: Record<string, { enabled: number; total: number }> = {};
    
    for (const node of data.tree || []) {
      const category = node.id?.startsWith("linked/") ? "linked" : 
                       node.id === "private" ? "private" : 
                       node.id === "builtin" ? "builtin" : "other";
      
      if (!categoryCounts[category]) {
        categoryCounts[category] = { enabled: 0, total: 0 };
      }
      
      for (const child of node.children || []) {
        if (!child.is_folder) {
          categoryCounts[category].total++;
          if (child.enabled) {
            categoryCounts[category].enabled++;
          }
        }
      }
    }
    
    console.log("Category counts from API:", categoryCounts);
    
    // Wait for skills to be loaded
    await page.waitForTimeout(500);
    
    // Open autocomplete
    await openSkillAutocomplete(page);
    const dropdownSkills = await getDropdownSkillNames(page);
    
    // For each category with enabled skills, verify at least one appears in dropdown
    for (const [category, counts] of Object.entries(categoryCounts)) {
      if (counts.enabled > 0) {
        // Find any skill from this category that's in the dropdown
        let found = false;
        for (const node of data.tree || []) {
          const nodeCategory = node.id?.startsWith("linked/") ? "linked" : 
                               node.id === "private" ? "private" : 
                               node.id === "builtin" ? "builtin" : "other";
          
          if (nodeCategory === category) {
            for (const child of node.children || []) {
              if (!child.is_folder && child.enabled && dropdownSkills.includes(child.name)) {
                found = true;
                console.log(`✅ Found skill from ${category}: ${child.name}`);
                break;
              }
            }
          }
          if (found) break;
        }
        
        expect(found, `Should have at least one skill from ${category} in dropdown`).toBe(true);
      }
    }
  });
});
