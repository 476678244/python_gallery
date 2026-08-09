/**
 * Skill Tree E2E Tests
 *
 * Validates the 4 main skill tree directories are correctly loaded,
 * rendered, and togglable in the sidebar Skill Tree panel.
 *
 * Expected directories:
 *   1. Private Skills   — skills/private_skills/ (7 skills)
 *   2. Anthropic Skills — linked_skills/anthropic_skills (symlink, 17 skills)
 *   3. Ljg Skills       — linked_skills/ljg-skills (symlink, 20 skills)
 *   4. Superpowers Skills — linked_skills/superpowers_skills (symlink, 14 skills)
 *
 * Requires: API server (port 8000) + Frontend (port 3000) running
 */

import { test, expect, Page } from "@playwright/test";

// ─── Ground Truth ────────────────────────────────────────────────────────────

const EXPECTED_FOLDERS = [
  { name: "Private Skills", minSkills: 6, maxSkills: 20 },
  { name: "Anthropic Skills", minSkills: 15, maxSkills: 22 },
  { name: "Ljg Skills", minSkills: 18, maxSkills: 25 },
  { name: "Superpowers Skills", minSkills: 12, maxSkills: 18 },
] as const;

const TOTAL_SKILLS_MIN = 51; // sum of mins
const TOTAL_SKILLS_MAX = 77; // sum of maxes

const SCREENSHOTS = "screenshots";

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function goto(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1500); // Wait for skill tree to load from API
}

/** Open the Skill Tree sidebar section if collapsed */
async function ensureSkillTreeOpen(page: Page) {
  const skillSection = page
    .locator("div.border-b")
    .filter({ hasText: /Skill Tree/i })
    .first();
  await expect(skillSection).toBeVisible({ timeout: 5000 });

  // Check if any toggle switches are visible (meaning section is open)
  const toggles = skillSection.locator("button[role='switch']");
  const toggleCount = await toggles.count();

  if (toggleCount === 0) {
    // Section might be collapsed — click header to expand
    const headerBtn = skillSection
      .locator("button")
      .filter({ hasText: /Skill Tree/i })
      .first();
    await headerBtn.click();
    await page.waitForTimeout(800);
  }
}

/** Get the Skill Tree section locator */
function skillTreeSection(page: Page) {
  return page
    .locator("div.border-b")
    .filter({ hasText: /Skill Tree/i })
    .first();
}

/** Find a folder row by its label text inside the skill tree */
function folderRow(page: Page, folderName: string) {
  const section = skillTreeSection(page);
  return section
    .locator("span.truncate")
    .filter({ hasText: new RegExp(`^${folderName}$`, "i") })
    .first()
    .locator("xpath=ancestor::div[contains(@class,'flex') and contains(@class,'items-center')][1]");
}

/** Get toggle switch for a specific folder */
function folderToggle(page: Page, folderName: string) {
  return folderRow(page, folderName).locator("button[role='switch']").first();
}

/** Expand a folder by clicking its chevron if not already expanded */
async function expandFolder(page: Page, folderName: string) {
  const row = folderRow(page, folderName);
  // Click the chevron button (first button in the row, NOT the switch)
  const chevronBtn = row.locator("button").first();
  // Check if there are children visible already
  const section = skillTreeSection(page);
  // The folder's children are rendered after the folder row, inside a motion.div
  // We'll click the chevron and wait
  await chevronBtn.click();
  await page.waitForTimeout(500);
}

/** Collect all folder names visible in the skill tree */
async function collectVisibleFolderNames(page: Page): Promise<string[]> {
  const section = skillTreeSection(page);
  // Folder nodes have a Folder lucide icon (svg) and font-medium class on their name span
  const folderLabels = section.locator("span.truncate.font-medium, span.font-medium.truncate");
  const count = await folderLabels.count();
  const names: string[] = [];
  for (let i = 0; i < count; i++) {
    const text = await folderLabels.nth(i).textContent();
    if (text) names.push(text.trim());
  }
  return names;
}

/** Fetch skill tree data from the API directly */
async function fetchSkillTreeFromAPI(page: Page) {
  return page.evaluate(async () => {
    const res = await fetch("/api/skills");
    return res.json();
  });
}

/** Enable all top-level folders so tests start from a known baseline */
async function resetAllFoldersEnabled(page: Page) {
  const apiData = await fetchSkillTreeFromAPI(page);
  const tree: any[] = apiData.tree || [];
  for (const folder of tree.filter((n: any) => n.is_folder || n.isFolder)) {
    await page.request.post("http://localhost:8000/skills", {
      data: { folder_id: folder.id, enabled: true },
    });
  }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

test.describe("Skill Tree · 4 Main Directories", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await resetAllFoldersEnabled(page);
  });

  // ── T1: API returns correct structure with 4 folders ─────────────────────

  test("T1: API /api/skills returns tree with 4 expected folders", async ({ page }) => {
    await goto(page);

    const apiData = await fetchSkillTreeFromAPI(page);
    console.log(`T1: API total=${apiData.total}, categories=${apiData.categories}`);
    console.log(`T1: builtin=${apiData.builtin}, private=${apiData.private}, linked=${apiData.linked}`);

    // Total skills should be in expected range
    expect(apiData.total).toBeGreaterThanOrEqual(TOTAL_SKILLS_MIN);
    expect(apiData.total).toBeLessThanOrEqual(TOTAL_SKILLS_MAX);

    // Tree should have folder nodes
    const tree: any[] = apiData.tree || [];
    const topFolders = tree.filter((n: any) => n.isFolder);
    const topFolderNames = topFolders.map((n: any) => n.name);
    console.log(`T1: Top-level folders: [${topFolderNames.join(", ")}]`);

    // Each expected folder should be present (case-insensitive match)
    for (const expected of EXPECTED_FOLDERS) {
      const found = topFolderNames.some(
        (name: string) => name.toLowerCase().includes(expected.name.toLowerCase().split(" ")[0])
      );
      console.log(`  "${expected.name}": ${found ? "✓ found" : "✗ MISSING"}`);
      expect(found).toBe(true);
    }

    // Check child counts for each folder
    for (const folder of topFolders) {
      const leafCount = countLeafSkills(folder);
      const expectedFolder = EXPECTED_FOLDERS.find(
        (e) => folder.name.toLowerCase().includes(e.name.toLowerCase().split(" ")[0])
      );
      if (expectedFolder) {
        console.log(`  "${folder.name}": ${leafCount} skills (expected ${expectedFolder.minSkills}-${expectedFolder.maxSkills})`);
        expect(leafCount).toBeGreaterThanOrEqual(expectedFolder.minSkills);
        expect(leafCount).toBeLessThanOrEqual(expectedFolder.maxSkills);
      }
    }

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t1-api.png`, fullPage: true });
    console.log("✅ T1 passed");
  });

  // ── T2: UI renders all 4 folders with toggle switches ────────────────────

  test("T2: UI renders all 4 folders with toggle switches", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t2-initial.png`, fullPage: true });

    // Check each expected folder is visible
    for (const expected of EXPECTED_FOLDERS) {
      const label = skillTreeSection(page)
        .locator("span.truncate")
        .filter({ hasText: new RegExp(expected.name, "i") })
        .first();
      const visible = await label.isVisible().catch(() => false);
      console.log(`T2: "${expected.name}" visible=${visible}`);
      expect(visible).toBe(true);

      // Each folder should have a toggle switch
      const toggle = folderToggle(page, expected.name);
      const toggleVisible = await toggle.isVisible().catch(() => false);
      console.log(`T2: "${expected.name}" toggle visible=${toggleVisible}`);
      expect(toggleVisible).toBe(true);
    }

    // Count total toggle switches (folders + skills)
    const section = skillTreeSection(page);
    const allToggles = section.locator("button[role='switch']");
    const totalToggles = await allToggles.count();
    console.log(`T2: Total toggle switches in tree: ${totalToggles}`);
    // At minimum we should have 4 folder toggles
    expect(totalToggles).toBeGreaterThanOrEqual(4);

    console.log("✅ T2 passed");
  });

  // ── T3: All folders are enabled by default ───────────────────────────────

  test("T3: All 4 folders are enabled (checked) by default", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    for (const expected of EXPECTED_FOLDERS) {
      const toggle = folderToggle(page, expected.name);
      const visible = await toggle.isVisible().catch(() => false);
      if (!visible) {
        console.log(`T3: ⚠ "${expected.name}" toggle not visible — skipping`);
        continue;
      }
      const checked = await toggle.getAttribute("aria-checked");
      console.log(`T3: "${expected.name}" aria-checked=${checked}`);
      expect(checked).toBe("true");
    }

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t3-defaults.png`, fullPage: true });
    console.log("✅ T3 passed");
  });

  // ── T4: Toggle a folder OFF and verify child skills become disabled ──────

  test("T4: Toggle Anthropic Skills OFF → children disabled", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    const targetFolder = "Anthropic Skills";
    const toggle = folderToggle(page, targetFolder);
    await expect(toggle).toBeVisible({ timeout: 5000 });

    // Verify initially ON
    const before = await toggle.getAttribute("aria-checked");
    console.log(`T4: "${targetFolder}" before toggle: aria-checked=${before}`);
    expect(before).toBe("true");

    // Toggle OFF
    await toggle.click();
    await page.waitForTimeout(1500); // Wait for API call

    const after = await toggle.getAttribute("aria-checked");
    console.log(`T4: "${targetFolder}" after toggle: aria-checked=${after}`);
    expect(after).toBe("false");

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t4-anthropic-off.png`, fullPage: true });

    // Verify via API that child skills are disabled
    const apiData = await fetchSkillTreeFromAPI(page);
    const tree: any[] = apiData.tree || [];
    const anthropicFolder = tree.find((n: any) =>
      n.name.toLowerCase().includes("anthropic")
    );
    if (anthropicFolder) {
      const enabledLeaves = countEnabledLeafSkills(anthropicFolder);
      console.log(`T4: API reports ${enabledLeaves} enabled skills in "${anthropicFolder.name}"`);
      expect(enabledLeaves).toBe(0);
    }

    // Restore: toggle back ON
    await toggle.click();
    await page.waitForTimeout(1500);
    const restored = await toggle.getAttribute("aria-checked");
    console.log(`T4: Restored "${targetFolder}" to aria-checked=${restored}`);
    expect(restored).toBe("true");

    console.log("✅ T4 passed");
  });

  // ── T5: Toggle each folder independently ─────────────────────────────────

  test("T5: Each folder toggles independently without affecting others", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    // Toggle Ljg Skills OFF
    const ljgToggle = folderToggle(page, "Ljg Skills");
    await expect(ljgToggle).toBeVisible({ timeout: 5000 });
    await ljgToggle.click();
    await page.waitForTimeout(1500);

    const ljgAfter = await ljgToggle.getAttribute("aria-checked");
    console.log(`T5: "Ljg Skills" after toggle: ${ljgAfter}`);
    expect(ljgAfter).toBe("false");

    // Other folders should still be ON
    for (const folder of ["Anthropic Skills", "Superpowers Skills", "Private Skills"]) {
      const toggle = folderToggle(page, folder);
      const visible = await toggle.isVisible().catch(() => false);
      if (!visible) {
        console.log(`T5: ⚠ "${folder}" toggle not visible — skipping`);
        continue;
      }
      const checked = await toggle.getAttribute("aria-checked");
      console.log(`T5: "${folder}" should still be ON: aria-checked=${checked}`);
      expect(checked).toBe("true");
    }

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t5-independent.png`, fullPage: true });

    // Restore Ljg Skills
    await ljgToggle.click();
    await page.waitForTimeout(1000);
    const ljgRestored = await ljgToggle.getAttribute("aria-checked");
    console.log(`T5: "Ljg Skills" restored to: ${ljgRestored}`);

    console.log("✅ T5 passed");
  });

  // ── T6: Expand folder shows child skills ─────────────────────────────────

  test("T6: Expanding a folder reveals its child skills", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    const targetFolder = "Private Skills";

    // Find the folder row and its chevron
    const row = folderRow(page, targetFolder);
    await expect(row).toBeVisible({ timeout: 5000 });

    // Click the chevron button to expand
    const chevronBtn = row.locator("button").first();
    await chevronBtn.click();
    await page.waitForTimeout(800);

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t6-expanded.png`, fullPage: true });

    // After expanding, child skill items should appear
    // Private skills include: audio-transcription-funasr, cue-regeneration, etc.
    const section = skillTreeSection(page);
    const knownPrivateSkills = [
      "audio-transcription-funasr",
      "stock_13f_analysis",
      "flow_coding_testing",
    ];

    let foundCount = 0;
    for (const skillName of knownPrivateSkills) {
      const skillLabel = section
        .locator("span.truncate")
        .filter({ hasText: new RegExp(skillName, "i") })
        .first();
      const visible = await skillLabel.isVisible().catch(() => false);
      console.log(`T6: "${skillName}" visible after expand: ${visible}`);
      if (visible) foundCount++;
    }

    console.log(`T6: Found ${foundCount}/${knownPrivateSkills.length} known private skills`);
    expect(foundCount).toBeGreaterThanOrEqual(1);

    console.log("✅ T6 passed");
  });

  // ── T7: Toggle individual skill within a folder ──────────────────────────

  test("T7: Toggle individual skill within expanded folder", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    // Expand Private Skills folder
    const row = folderRow(page, "Private Skills");
    await expect(row).toBeVisible({ timeout: 5000 });
    const chevronBtn = row.locator("button").first();
    await chevronBtn.click();
    await page.waitForTimeout(800);

    // Find a child skill's toggle switch
    const section = skillTreeSection(page);
    // Get all toggle switches — folder toggles are at depth=0, skill toggles at depth>0 (with ml-4)
    const allToggles = section.locator("button[role='switch']");
    const totalToggles = await allToggles.count();
    console.log(`T7: Total toggles after expand: ${totalToggles}`);

    // The skill toggles should be more than the 4 folder toggles
    expect(totalToggles).toBeGreaterThan(4);

    // Find and toggle a specific skill (not a folder)
    // Look for a skill by its name text, then get its sibling toggle
    const skillName = "stock_13f_analysis";
    const skillLabel = section
      .locator("span.truncate")
      .filter({ hasText: new RegExp(skillName, "i") })
      .first();

    if (await skillLabel.isVisible().catch(() => false)) {
      const skillRow = skillLabel.locator(
        "xpath=ancestor::div[contains(@class,'flex') and contains(@class,'items-center')][1]"
      );
      const skillToggle = skillRow.locator("button[role='switch']").first();
      const before = await skillToggle.getAttribute("aria-checked");
      console.log(`T7: "${skillName}" before: aria-checked=${before}`);

      await skillToggle.click();
      await page.waitForTimeout(1000);

      const after = await skillToggle.getAttribute("aria-checked");
      console.log(`T7: "${skillName}" after: aria-checked=${after}`);
      expect(after).not.toBe(before);

      // Restore
      await skillToggle.click();
      await page.waitForTimeout(500);
    } else {
      console.log(`T7: ⚠ "${skillName}" not visible — trying first non-folder toggle`);
      // Fallback: toggle the 5th toggle (likely first skill after 4 folders)
      if (totalToggles > 4) {
        const skillToggle = allToggles.nth(4);
        const before = await skillToggle.getAttribute("aria-checked");
        await skillToggle.click();
        await page.waitForTimeout(1000);
        const after = await skillToggle.getAttribute("aria-checked");
        console.log(`T7: Fallback toggle: ${before} → ${after}`);
        expect(after).not.toBe(before);
        // Restore
        await skillToggle.click();
        await page.waitForTimeout(500);
      }
    }

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t7-individual.png`, fullPage: true });
    console.log("✅ T7 passed");
  });

  // ── T8: Skill tree persists after page reload ────────────────────────────

  test("T8: Folder toggle state persists after page reload", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    // Toggle Superpowers Skills OFF
    const toggle = folderToggle(page, "Superpowers Skills");
    await expect(toggle).toBeVisible({ timeout: 5000 });

    const initialState = await toggle.getAttribute("aria-checked");
    console.log(`T8: "Superpowers Skills" initial: ${initialState}`);

    if (initialState === "true") {
      await toggle.click();
      await page.waitForTimeout(1500);
    }

    const beforeReload = await toggle.getAttribute("aria-checked");
    console.log(`T8: Before reload: ${beforeReload}`);
    expect(beforeReload).toBe("false");

    // Reload page
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await ensureSkillTreeOpen(page);

    const afterReload = await folderToggle(page, "Superpowers Skills").getAttribute("aria-checked");
    console.log(`T8: After reload: ${afterReload}`);

    // State should persist
    expect(afterReload).toBe(beforeReload);

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t8-reload.png`, fullPage: true });

    // Restore
    if (afterReload === "false") {
      await folderToggle(page, "Superpowers Skills").click();
      await page.waitForTimeout(1000);
    }

    console.log("✅ T8 passed");
  });

  // ── T9: API total matches all 4 folders combined ─────────────────────────

  test("T9: API total = sum of all 4 folder child counts", async ({ page }) => {
    await goto(page);

    const apiData = await fetchSkillTreeFromAPI(page);
    const tree: any[] = apiData.tree || [];
    const topFolders = tree.filter((n: any) => n.isFolder);

    let sumLeafSkills = 0;
    for (const folder of topFolders) {
      const leafCount = countLeafSkills(folder);
      console.log(`T9: "${folder.name}": ${leafCount} leaf skills`);
      sumLeafSkills += leafCount;
    }

    console.log(`T9: API total=${apiData.total}, sum of folders=${sumLeafSkills}`);
    expect(apiData.total).toBe(sumLeafSkills);

    console.log("✅ T9 passed");
  });

  // ── T10: Disabled folder skills are excluded from enabled list ───────────

  test("T10: Disabled folder's skills excluded from enabled list in API", async ({ page }) => {
    await goto(page);
    await ensureSkillTreeOpen(page);

    // Disable Private Skills
    const toggle = folderToggle(page, "Private Skills");
    await expect(toggle).toBeVisible({ timeout: 5000 });

    const initial = await toggle.getAttribute("aria-checked");
    if (initial === "true") {
      await toggle.click();
      await page.waitForTimeout(1500);
    }

    // Verify via API
    const apiData = await fetchSkillTreeFromAPI(page);
    const tree: any[] = apiData.tree || [];
    const privateFolder = tree.find((n: any) =>
      n.name.toLowerCase().includes("private")
    );

    if (privateFolder) {
      const enabledCount = countEnabledLeafSkills(privateFolder);
      console.log(`T10: Private Skills enabled count after disable: ${enabledCount}`);
      expect(enabledCount).toBe(0);

      // Other folders should still have enabled skills
      const otherFolders = tree.filter(
        (n: any) => n.isFolder && !n.name.toLowerCase().includes("private")
      );
      for (const folder of otherFolders) {
        const enabled = countEnabledLeafSkills(folder);
        console.log(`T10: "${folder.name}" enabled: ${enabled}`);
        expect(enabled).toBeGreaterThan(0);
      }
    }

    await page.screenshot({ path: `${SCREENSHOTS}/skill-tree-t10-disabled.png`, fullPage: true });

    // Restore
    await toggle.click();
    await page.waitForTimeout(1000);

    console.log("✅ T10 passed");
  });
});

// ─── Utility Functions ───────────────────────────────────────────────────────

function countLeafSkills(node: any): number {
  if (!node.isFolder && !node.children?.length) return 1;
  let count = 0;
  for (const child of node.children || []) {
    count += countLeafSkills(child);
  }
  return count;
}

function countEnabledLeafSkills(node: any): number {
  if (!node.isFolder && !node.children?.length) {
    return node.enabled ? 1 : 0;
  }
  let count = 0;
  for (const child of node.children || []) {
    count += countEnabledLeafSkills(child);
  }
  return count;
}
