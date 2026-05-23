# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: basic-chat-flow-coding.spec.ts >> 🔄 Flow Coding: 基础对话功能 >> Phase 3: 多轮对话
- Location: tests/e2e/basic-chat-flow-coding.spec.ts:112:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1   | /**
  2   |  * Flow Coding E2E Test: 基础对话功能
  3   |  * 基于 /docs/flow_coding.md 的 5 阶段算法
  4   |  */
  5   | 
  6   | import { test, expect, Page } from "@playwright/test";
  7   | 
  8   | const BASE_URL = process.env.FRONTEND_URL || "http://localhost:3000";
  9   | const API_URL = process.env.API_URL || "http://localhost:8000";
  10  | 
  11  | // ─── Phase 1: Helpers ─────────────────────────────────────────────────────────
  12  | 
  13  | async function waitForApp(page: Page) {
> 14  |   await page.goto(BASE_URL);
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  15  |   await page.waitForLoadState("networkidle");
  16  |   await page.waitForSelector("textarea", { timeout: 10000 });
  17  |   await page.waitForTimeout(500);
  18  | }
  19  | 
  20  | async function ensureSession(page: Page) {
  21  |   const textarea = page.locator("textarea").first();
  22  |   const isDisabled = await textarea.isDisabled().catch(() => true);
  23  |   
  24  |   if (isDisabled) {
  25  |     const newChatBtn = page.getByText("New Chat").first();
  26  |     await newChatBtn.click();
  27  |     await page.waitForTimeout(1000);
  28  |   }
  29  |   
  30  |   await expect(textarea).not.toBeDisabled({ timeout: 5000 });
  31  | }
  32  | 
  33  | async function sendMessageAndWait(
  34  |   page: Page, 
  35  |   message: string, 
  36  |   options: { timeout?: number; retries?: number } = {}
  37  | ): Promise<string> {
  38  |   const { timeout = 30000, retries = 1 } = options;
  39  |   
  40  |   for (let attempt = 0; attempt <= retries; attempt++) {
  41  |     try {
  42  |       const textarea = page.locator("textarea").first();
  43  |       await textarea.clear();
  44  |       await textarea.fill(message);
  45  |       
  46  |       const beforeCount = await page.locator("[data-role='assistant']").count();
  47  |       await page.keyboard.press("Enter");
  48  |       
  49  |       await expect(
  50  |         page.locator("[data-role='assistant']")
  51  |       ).toHaveCount(beforeCount + 1, { timeout });
  52  |       
  53  |       const lastResponse = page.locator("[data-role='assistant']").last();
  54  |       return await lastResponse.textContent() || "";
  55  |       
  56  |     } catch (error) {
  57  |       if (attempt < retries) {
  58  |         console.log(`⚠️ Attempt ${attempt + 1} failed, retrying...`);
  59  |         await page.waitForTimeout(2000);
  60  |         await ensureSession(page);
  61  |       } else {
  62  |         throw error;
  63  |       }
  64  |     }
  65  |   }
  66  |   throw new Error("Failed after retries");
  67  | }
  68  | 
  69  | // ─── Flow Coding 5-Phase Test ───────────────────────────────────────────────
  70  | 
  71  | test.describe("🔄 Flow Coding: 基础对话功能", () => {
  72  |   
  73  |   /**
  74  |    * Phase 1: ESTABLISH THE VERIFICATION BASELINE
  75  |    */
  76  |   test("Phase 1: 验证基线 - 页面加载", async ({ page }) => {
  77  |     const errors: string[] = [];
  78  |     page.on("pageerror", (err) => errors.push(err.message));
  79  |     
  80  |     await waitForApp(page);
  81  |     await expect(page.locator("textarea").first()).toBeVisible();
  82  |     
  83  |     const fatal = errors.filter(e => !e.includes("Hydration"));
  84  |     expect(fatal).toHaveLength(0);
  85  |     
  86  |     console.log("✅ Phase 1: Verification baseline established");
  87  |   });
  88  | 
  89  |   /**
  90  |    * Phase 2: INTENT EXPRESSION & CODE GENERATION
  91  |    */
  92  |   test("Phase 2: 基础对话", async ({ page }) => {
  93  |     await waitForApp(page);
  94  |     await ensureSession(page);
  95  |     
  96  |     const response = await sendMessageAndWait(
  97  |       page, 
  98  |       "Hello SafeClaw! What can you help me with?",
  99  |       { timeout: 30000, retries: 1 }
  100 |     );
  101 |     
  102 |     expect(response.length).toBeGreaterThan(10);
  103 |     expect(response).not.toContain("Error");
  104 |     
  105 |     console.log(`📥 Response: ${response.slice(0, 80)}...`);
  106 |     console.log("✅ Phase 2: Intent expression works");
  107 |   });
  108 | 
  109 |   /**
  110 |    * Phase 3: TEST SPEC ADAPTATION
  111 |    */
  112 |   test("Phase 3: 多轮对话", async ({ page }) => {
  113 |     await waitForApp(page);
  114 |     await ensureSession(page);
```