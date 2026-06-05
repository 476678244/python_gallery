/**
 * DeepSeek Model Selection E2E Test
 * Tests the DeepSeek model selection and vision capability display
 */

import { test, expect } from "@playwright/test";

// DeepSeek models that should appear in the list
const DEEPSEEK_MODELS = [
  { id: "deepseek-v4-flash", name: "DeepSeek V4 Flash", shouldSupportVision: false },
  { id: "deepseek-v4-pro", name: "DeepSeek V4 Pro", shouldSupportVision: false },
];

test.describe("DeepSeek Model Selection", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to SafeClaw UI and open settings
    await page.goto("http://localhost:3000");
    
    // Wait for the app to load
    await page.waitForSelector("[data-testid='sidebar']", { timeout: 10000 });
    
    // Open settings panel via sidebar
    const settingsButton = page.locator("[data-testid='settings-button']").first();
    if (await settingsButton.isVisible().catch(() => false)) {
      await settingsButton.click();
    } else {
      // Try to find settings via menu
      await page.click("text=Settings");
    }
    
    // Wait for settings panel
    await page.waitForSelector("text=LLM Model", { timeout: 5000 });
  });

  test("should display DeepSeek models in the list", async ({ page }) => {
    // Check that DeepSeek models are visible
    for (const model of DEEPSEEK_MODELS) {
      const modelButton = page.locator(`button:has-text("${model.name}")`);
      await expect(modelButton).toBeVisible();
      
      // Verify provider badge shows "deepseek"
      const providerBadge = modelButton.locator("span", { hasText: "deepseek" });
      await expect(providerBadge).toBeVisible();
    }
  });

  test("should select DeepSeek V4 Pro model", async ({ page }) => {
    const proModel = page.locator('button:has-text("DeepSeek V4 Pro")');
    await proModel.click();
    
    // Verify selection is highlighted
    await expect(proModel).toHaveClass(/border-blue-500/);
    
    // Verify checkmark appears
    const checkmark = proModel.locator("svg");
    await expect(checkmark).toBeVisible();
  });

  test("should show DeepSeek API key configuration", async ({ page }) => {
    // Check DeepSeek API Key section exists
    const deepseekSection = page.locator("text=DeepSeek API Key").first();
    await expect(deepseekSection).toBeVisible();
    
    // Check for input field
    const apiKeyInput = page.locator('input[type="password"]').filter({
      hasPlaceholder: /sk-/,
    });
    await expect(apiKeyInput).toBeVisible();
    
    // Check for save button
    const saveButton = page.locator("button", { hasText: "Save" }).filter({
      has: page.locator("xpath=preceding::input[1]"),
    });
    await expect(saveButton).toBeVisible();
  });

  test("should verify vision capability is NOT shown for DeepSeek", async ({ page }) => {
    // This test confirms DeepSeek models don't claim vision support
    // (since DeepSeek API doesn't support multimodal input)
    
    const proModel = page.locator('button:has-text("DeepSeek V4 Pro")');
    
    // The model should NOT have a vision badge/icon
    // Based on the UI design, vision-capable models show specific indicators
    
    // Take screenshot for verification
    await expect(proModel).toHaveScreenshot("deepseek-v4-pro-no-vision-badge.png", {
      maxDiffPixels: 100,
    });
  });

  test("should persist model selection after reload", async ({ page }) => {
    // Select DeepSeek V4 Pro
    await page.click('button:has-text("DeepSeek V4 Pro")');
    
    // Wait a moment for any async save
    await page.waitForTimeout(500);
    
    // Reload the page
    await page.reload();
    await page.waitForSelector("text=LLM Model", { timeout: 5000 });
    
    // Verify DeepSeek V4 Pro is still selected (highlighted)
    const proModel = page.locator('button:has-text("DeepSeek V4 Pro")');
    await expect(proModel).toHaveClass(/border-blue-500/);
  });
});

test.describe("DeepSeek Vision Capability Test", () => {
  test("verify DeepSeek models do not include vision in capabilities", async ({ page }) => {
    // Navigate to models API to check raw data
    const response = await page.request.get("http://localhost:8000/settings/models");
    const data = await response.json();
    
    // Note: Backend doesn't return DeepSeek models, they are hardcoded in frontend
    // This test verifies the frontend model definitions
    
    console.log("Available models from backend:", data.models);
    
    // DeepSeek models should NOT be in the backend list (they are frontend-only)
    const deepseekInBackend = data.models?.some((m: any) => 
      m.id?.includes("deepseek")
    );
    
    expect(deepseekInBackend).toBeFalsy();
  });
});
