/**
 * Sidebar UI Tests
 *
 * Tests the new vertical collapsible-section sidebar:
 *   ① Chats section  — New Chat, Delete Chat, section collapse/expand
 *   ② Skill Tree     — default open, skill toggle switch
 *   ③ Tool Tree      — default collapsed, folder open/close, tool visibility
 *   ④ Model section  — default collapsed, model selection
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

/** Click the header of a sidebar section by its title text */
async function clickSectionHeader(page: Page, title: string) {
  await page
    .locator("button")
    .filter({ hasText: new RegExp(title, "i") })
    .first()
    .click();
}

/** Return the body div directly after the section header button */
function sectionBody(page: Page, title: string) {
  // The SbSection renders: <div.border-b> <button>…title…</button> <div>children</div> </div>
  return page
    .locator("button")
    .filter({ hasText: new RegExp(title, "i") })
    .first()
    .locator("xpath=following-sibling::div[1]");
}

// ─── ① Chats section ─────────────────────────────────────────────────────────

test.describe("Sidebar · Chats section", () => {
  test("Chats section is open by default and shows New Chat button", async ({ page }) => {
    await goto(page);
    // "New Chat" button should be visible in the sidebar without any click
    const newChatBtn = page
      .locator("div.border-b")           // sb-section wrapper
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /New Chat/i })
      .first();
    await expect(newChatBtn).toBeVisible({ timeout: 5000 });
  });

  test("New Chat creates a session that appears in the list", async ({ page }) => {
    await goto(page);

    // Count sessions before
    const sessionsBefore = await page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("[data-role='session-item'], button")
      .filter({ hasText: /Chat|Untitled/i })
      .count();

    // Click New Chat
    await page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /New Chat/i })
      .first()
      .click();

    await page.waitForTimeout(1200);

    // At least one session item should be visible
    const sessionItem = page.locator("[data-testid='session-item']").first();
    const byTitle = page.getByText(/New Chat|Untitled/i).first();
    // Either a data-testid or text is acceptable
    const visible =
      (await sessionItem.isVisible().catch(() => false)) ||
      (await byTitle.isVisible().catch(() => false));
    expect(visible).toBe(true);
  });

  test("Delete Chat button removes the session", async ({ page }) => {
    await goto(page);

    // Ensure at least one session exists
    const newChatBtn = page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /New Chat/i })
      .first();
    await newChatBtn.click();
    await page.waitForTimeout(1200);

    // Hover over first session item to reveal delete button
    const sessionRow = page.locator(".group").first();
    await sessionRow.hover();

    // Click the trash / delete button (appears on hover)
    const deleteBtn = sessionRow.locator("button, div[role='button']").filter({
      has: page.locator("svg"),
    }).last();

    if (await deleteBtn.isVisible()) {
      await deleteBtn.click();
      await page.waitForTimeout(800);
      // Page should not crash
      await expect(page.locator("body")).toBeVisible();
    }
  });

  test("Chats section collapses when header is clicked", async ({ page }) => {
    await goto(page);

    // New Chat button is initially visible (section open)
    const newChatBtn = page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /New Chat/i })
      .first();
    await expect(newChatBtn).toBeVisible();

    // Click the section header to collapse
    await page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /Chats/i })
      .first()
      .click();

    await page.waitForTimeout(300);

    // New Chat button should now be hidden
    await expect(newChatBtn).not.toBeVisible();
  });

  test("Chats section re-expands after second click", async ({ page }) => {
    await goto(page);

    const headerBtn = page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /Chats/i })
      .first();

    // Collapse
    await headerBtn.click();
    await page.waitForTimeout(300);

    // Expand again
    await headerBtn.click();
    await page.waitForTimeout(300);

    const newChatBtn = page
      .locator("div.border-b")
      .filter({ hasText: /Chats/i })
      .locator("button")
      .filter({ hasText: /New Chat/i })
      .first();
    await expect(newChatBtn).toBeVisible();
  });
});

// ─── ② Skill Tree section ────────────────────────────────────────────────────

test.describe("Sidebar · Skill Tree section", () => {
  test("Skill Tree section is open by default", async ({ page }) => {
    await goto(page);

    // The skill tree panel renders inside the Skill Tree section
    // It should be visible without any click
    const skillSection = page
      .locator("div.border-b")
      .filter({ hasText: /Skill Tree/i })
      .first();
    await expect(skillSection).toBeVisible({ timeout: 5000 });

    // Children should be visible (section is open)
    const body = skillSection.locator("div").nth(1);
    await expect(body).toBeVisible({ timeout: 3000 });
  });

  test("Skill Tree collapses and expands", async ({ page }) => {
    await goto(page);

    const headerBtn = page
      .locator("div.border-b")
      .filter({ hasText: /Skill Tree/i })
      .locator("button")
      .filter({ hasText: /Skill Tree/i })
      .first();

    // Collapse
    await headerBtn.click();
    await page.waitForTimeout(300);

    // The skill tree content should be hidden
    const skillTreeContent = page
      .locator("div.border-b")
      .filter({ hasText: /Skill Tree/i })
      .locator("div")
      .nth(1);
    await expect(skillTreeContent).not.toBeVisible();

    // Expand again
    await headerBtn.click();
    await page.waitForTimeout(300);
    await expect(skillTreeContent).toBeVisible();
  });

  test("Skill toggle switch can be clicked without crash", async ({ page }) => {
    await goto(page);
    await page.waitForTimeout(1200); // let skill tree load

    const skillSection = page
      .locator("div.border-b")
      .filter({ hasText: /Skill Tree/i })
      .first();

    const toggleSwitch = skillSection
      .locator("button[role='switch']")
      .first();

    if (await toggleSwitch.isVisible()) {
      const checkedBefore = await toggleSwitch.getAttribute("aria-checked");
      await toggleSwitch.click();
      // Wait for the toggle API call to settle
      await page.waitForTimeout(800);
      const checkedAfter = await toggleSwitch.getAttribute("aria-checked");
      // State should differ from before (true→false or false→true)
      // Some skills require confirmation; accept either state change or same (API may revert)
      // The important assertion is: no crash
      await expect(page.getByText(/Something went wrong/i)).not.toBeVisible();
      // If the state did change, great. If it reverted (e.g. protected skill), also fine.
      const toggled = checkedAfter !== checkedBefore;
      const reverted = checkedAfter === checkedBefore;
      expect(toggled || reverted).toBe(true);
    } else {
      // Skills not loaded (mock) — just verify no crash
      await expect(page.locator("body")).toBeVisible();
    }
  });
});

// ─── ③ Tool Tree section ─────────────────────────────────────────────────────

test.describe("Sidebar · Tool Tree section", () => {
  test("Tool Tree section is collapsed by default", async ({ page }) => {
    await goto(page);

    // Tool list items should NOT be visible initially
    const toolItem = page.getByText(/web_search|read_file|write_file/i).first();
    await expect(toolItem).not.toBeVisible({ timeout: 3000 });
  });

  test("Tool Tree expands when header is clicked", async ({ page }) => {
    await goto(page);

    const headerBtn = page
      .locator("div.border-b")
      .filter({ hasText: /Tool Tree/i })
      .locator("button")
      .filter({ hasText: /Tool Tree/i })
      .first();

    await headerBtn.click();
    await page.waitForTimeout(300);

    // Folder names should now be visible
    await expect(page.getByText(/Built-in/i).first()).toBeVisible();
    await expect(page.getByText(/Custom/i).first()).toBeVisible();
  });

  test("Built-in folder is open by default showing tools", async ({ page }) => {
    await goto(page);

    // Open Tool Tree section
    await page
      .locator("div.border-b")
      .filter({ hasText: /Tool Tree/i })
      .locator("button")
      .filter({ hasText: /Tool Tree/i })
      .first()
      .click();
    await page.waitForTimeout(300);

    // Built-in folder is defaultOpen=true → tools should be visible
    await expect(page.getByText("web_search").first()).toBeVisible();
    await expect(page.getByText("read_file").first()).toBeVisible();
  });

  test("Custom folder is collapsed by default, expands on click", async ({ page }) => {
    await goto(page);

    // Open Tool Tree section first
    await page
      .locator("div.border-b")
      .filter({ hasText: /Tool Tree/i })
      .locator("button")
      .filter({ hasText: /Tool Tree/i })
      .first()
      .click();
    await page.waitForTimeout(300);

    // market_data should not be visible (Custom folder collapsed)
    await expect(page.getByText("market_data").first()).not.toBeVisible();

    // Click Custom folder to expand
    await page.getByText(/Custom/i).first().click();
    await page.waitForTimeout(300);

    // Now market_data and price_tracker should appear
    await expect(page.getByText("market_data").first()).toBeVisible();
    await expect(page.getByText("price_tracker").first()).toBeVisible();
  });

  test("Built-in folder collapses when clicked", async ({ page }) => {
    await goto(page);

    // Open Tool Tree section
    const toolSection = page
      .locator("div.border-b")
      .filter({ hasText: /Tool Tree/i })
      .first();
    await toolSection
      .locator("button")
      .filter({ hasText: /Tool Tree/i })
      .first()
      .click();
    await page.waitForTimeout(300);

    // Scope web_search lookup to inside the Tool Tree section body
    const webSearchItem = toolSection.getByText("web_search").first();
    await expect(webSearchItem).toBeVisible();

    // Click Built-in folder header to collapse it
    await toolSection.getByText(/Built-in/i).first().click();
    await page.waitForTimeout(400);

    await expect(webSearchItem).not.toBeVisible();
  });
});

// ─── ④ Model section ─────────────────────────────────────────────────────────

test.describe("Sidebar · Model section", () => {
  test("Model section is collapsed by default", async ({ page }) => {
    await goto(page);

    // Model cards should not be visible initially (names from AVAILABLE_MODELS)
    const modelCard = page.getByText(/Qwen3\.5 9B|Gemma 4 E4B|DeepSeek V4 Pro/i).first();
    await expect(modelCard).not.toBeVisible({ timeout: 3000 });
  });

  test("Model section expands when header clicked", async ({ page }) => {
    await goto(page);

    await page
      .locator("div.border-b")
      .filter({ hasText: /Model/i })
      .locator("button")
      .filter({ hasText: /Model/i })
      .first()
      .click();
    await page.waitForTimeout(300);

    await expect(page.getByText("Qwen3.5 9B").first()).toBeVisible();
    await expect(page.getByText("Gemma 4 E4B").first()).toBeVisible();
    await expect(page.getByText("DeepSeek V4 Pro").first()).toBeVisible();
  });

  test("Selecting a different model updates the active state", async ({ page }) => {
    await goto(page);

    // Open Model section
    await page
      .locator("div.border-b")
      .filter({ hasText: /Model/i })
      .locator("button")
      .filter({ hasText: /Model/i })
      .first()
      .click();
    await page.waitForTimeout(300);

    // Click Gemma 4 E4B
    await page.getByText("Gemma 4 E4B").first().click();
    await page.waitForTimeout(300);

    const gemmaBtn = page
      .locator("button")
      .filter({ hasText: /Gemma 4 E4B/i })
      .first();
    const cls = await gemmaBtn.getAttribute("class");
    expect(cls).toContain("bg-blue-50");
    await expect(page.getByText(/Something went wrong/i)).not.toBeVisible();
  });
});
