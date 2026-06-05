/**
 * Flow Coding E2E Test: 基础对话功能
 * 基于 /docs/flow_coding.md 的 5 阶段算法
 */

import { test, expect, Page } from "@playwright/test";

const BASE_URL = process.env.FRONTEND_URL || "http://localhost:3000";
const API_URL = process.env.API_URL || "http://localhost:8000";

// ─── Phase 1: Helpers ─────────────────────────────────────────────────────────

async function waitForApp(page: Page) {
  await page.goto(BASE_URL);
  await page.waitForLoadState("networkidle");
  await page.waitForSelector("textarea", { timeout: 10000 });
  await page.waitForTimeout(500);
}

async function ensureSession(page: Page) {
  const textarea = page.locator("textarea").first();
  const isDisabled = await textarea.isDisabled().catch(() => true);

  if (isDisabled) {
    // Use API to create a session directly
    const response = await page.request.post(`${API_URL}/sessions`, {
      data: { title: "E2E Test Session" }
    });

    if (response.ok()) {
      const data = await response.json() as { session?: { id: string } };
      const sessionId = data.session?.id;
      if (sessionId) {
        // Navigate to the session
        await page.goto(`${BASE_URL}/?session=${sessionId}`);
        await page.waitForLoadState("networkidle");
      }
    }

    // Also try to click any "New Chat" button as fallback
    const newChatBtn = page.getByRole("button").filter({ hasText: /New Chat|New|新建|Start/i }).first();
    if (await newChatBtn.count() > 0) {
      await newChatBtn.click();
    }

    await page.waitForTimeout(2000);
  }

  // Wait for textarea to be enabled
  await expect(textarea).not.toBeDisabled({ timeout: 10000 });
}

async function sendMessageAndWait(
  page: Page, 
  message: string, 
  options: { timeout?: number; retries?: number } = {}
): Promise<string> {
  const { timeout = 30000, retries = 1 } = options;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const textarea = page.locator("textarea").first();
      await textarea.clear();
      await textarea.fill(message);
      
      const beforeCount = await page.locator("[data-role='assistant']").count();
      await page.keyboard.press("Enter");
      
      await expect(
        page.locator("[data-role='assistant']")
      ).toHaveCount(beforeCount + 1, { timeout });
      
      const lastResponse = page.locator("[data-role='assistant']").last();
      return await lastResponse.textContent() || "";
      
    } catch (error) {
      if (attempt < retries) {
        console.log(`⚠️ Attempt ${attempt + 1} failed, retrying...`);
        await page.waitForTimeout(2000);
        await ensureSession(page);
      } else {
        throw error;
      }
    }
  }
  throw new Error("Failed after retries");
}

// ─── Flow Coding 5-Phase Test ───────────────────────────────────────────────

test.describe("🔄 Flow Coding: 基础对话功能", () => {
  
  /**
   * Phase 1: ESTABLISH THE VERIFICATION BASELINE
   */
  test("Phase 1: 验证基线 - 页面加载", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    
    await waitForApp(page);
    await expect(page.locator("textarea").first()).toBeVisible();
    
    const fatal = errors.filter(e => !e.includes("Hydration"));
    expect(fatal).toHaveLength(0);
    
    console.log("✅ Phase 1: Verification baseline established");
  });

  /**
   * Phase 2: INTENT EXPRESSION & CODE GENERATION
   */
  test("Phase 2: 基础对话", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
    
    const response = await sendMessageAndWait(
      page, 
      "Hello SafeClaw! What can you help me with?",
      { timeout: 30000, retries: 1 }
    );
    
    expect(response.length).toBeGreaterThan(10);
    expect(response).not.toContain("Error");
    
    console.log(`📥 Response: ${response.slice(0, 80)}...`);
    console.log("✅ Phase 2: Intent expression works");
  });

  /**
   * Phase 3: TEST SPEC ADAPTATION
   */
  test("Phase 3: 多轮对话", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
    
    // 多轮对话
    const r1 = await sendMessageAndWait(page, "My name is Test User", { timeout: 20000 });
    expect(r1.length).toBeGreaterThan(0);
    
    const r2 = await sendMessageAndWait(page, "What's my name?", { timeout: 20000 });
    expect(r2.length).toBeGreaterThan(0);
    
    const userCount = await page.locator("[data-role='user']").count();
    const assistantCount = await page.locator("[data-role='assistant']").count();
    
    expect(userCount).toBeGreaterThanOrEqual(2);
    expect(assistantCount).toBeGreaterThanOrEqual(2);
    
    console.log(`✅ Phase 3: Multi-turn chat (${userCount} user, ${assistantCount} assistant)`);
  });

  /**
   * Phase 4: SELF-HEALING LOOP
   */
  test("Phase 4: 自我修复", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
    
    const messages = ["Test 1", "Test 2", "Test 3"];
    
    for (const msg of messages) {
      try {
        const r = await sendMessageAndWait(page, msg, { timeout: 20000, retries: 2 });
        expect(r.length).toBeGreaterThan(0);
      } catch (error) {
        // Self-heal: recreate session
        await ensureSession(page);
        const r = await sendMessageAndWait(page, msg, { timeout: 20000 });
        expect(r.length).toBeGreaterThan(0);
      }
    }
    
    console.log("✅ Phase 4: Self-healing loop completed");
  });

  /**
   * Phase 5: FINAL CONVERGENCE & CONFIRMATION
   */
  test("Phase 5: 最终验证", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
    
    const response = await sendMessageAndWait(
      page, 
      "Confirm you are working correctly.",
      { timeout: 30000 }
    );
    
    expect(response.length).toBeGreaterThan(20);
    
    // Screenshot
    await page.screenshot({ 
      path: "test-results/basic-chat-final.png",
      fullPage: true 
    });
    
    console.log(`📸 Screenshot saved`);
    console.log(`📥 Final response: ${response.slice(0, 80)}...`);
    console.log("✅ Phase 5: Final convergence complete");
  });
});

test.afterAll(async () => {
  console.log("\n" + "=".repeat(60));
  console.log("🎉 Flow Coding: 基础对话功能测试完成");
  console.log("=".repeat(60));
  
  // Auto-cleanup: shutdown temporary servers
  console.log("\n🧹 Auto-cleanup: Shutting down temporary servers...");
  try {
    const { execSync } = require("child_process");
    execSync("pkill -f 'uvicorn.*main:app' 2>/dev/null || true", { stdio: "ignore" });
    execSync("pkill -f 'start_api.py' 2>/dev/null || true", { stdio: "ignore" });
    execSync("pkill -f 'next dev' 2>/dev/null || true", { stdio: "ignore" });
    console.log("✅ Temporary servers shutdown complete");
  } catch (e) {
    // Ignore cleanup errors
  }
});
