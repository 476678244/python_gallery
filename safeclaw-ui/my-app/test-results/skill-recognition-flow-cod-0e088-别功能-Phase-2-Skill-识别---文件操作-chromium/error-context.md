# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: skill-recognition-flow-coding.spec.ts >> 🔄 Flow Coding: LLM Skill 识别功能 >> Phase 2: Skill 识别 - 文件操作
- Location: tests/e2e/skill-recognition-flow-coding.spec.ts:182:9

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  locator('[data-role=\'assistant\']')
Expected: 1
Received: 0
Timeout:  30000ms

Call log:
  - Expect "toHaveCount" with timeout 30000ms
  - waiting for locator('[data-role=\'assistant\']')
    64 × locator resolved to 0 elements
       - unexpected value "0"

```

# Test source

```ts
  1   | /**
  2   |  * Flow Coding E2E Test: LLM Skill 识别功能
  3   |  *
  4   |  * 基于 /docs/flow_coding.md 的 5 阶段算法:
  5   |  * 1. ESTABLISH THE VERIFICATION BASELINE
  6   |  * 2. INTENT EXPRESSION & CODE GENERATION
  7   |  * 3. TEST SPEC ADAPTATION
  8   |  * 4. SELF-HEALING LOOP
  9   |  * 5. FINAL CONVERGENCE & CONFIRMATION
  10  |  *
  11  |  * 测试 SafeClaw 的 Skill 路由和识别功能:
  12  |  * - 语义匹配是否能正确识别相关 skills
  13  |  * - Execution graph 是否正确记录 skill 调用
  14  |  * - Prompt inspect 是否显示 skill 调用详情
  15  |  */
  16  | 
  17  | import { test, expect, Page, Request } from "@playwright/test";
  18  | 
  19  | // ─── Phase 1: Helpers ─────────────────────────────────────────────────────────
  20  | 
  21  | async function waitForApp(page: Page) {
  22  |   await page.goto("/");
  23  |   await page.waitForLoadState("networkidle");
  24  |   await page.waitForSelector("textarea", { timeout: 10000 });
  25  |   await page.waitForTimeout(500);
  26  | }
  27  | 
  28  | async function ensureSession(page: Page) {
  29  |   const textarea = page.locator("textarea").first();
  30  |   const isDisabled = await textarea.isDisabled().catch(() => true);
  31  |   if (isDisabled) {
  32  |     const newChatBtn = page.getByText("New Chat").first();
  33  |     await newChatBtn.click();
  34  |     await page.waitForTimeout(1000);
  35  |   }
  36  |   await expect(textarea).not.toBeDisabled({ timeout: 5000 });
  37  | }
  38  | 
  39  | /**
  40  |  * 发送消息并捕获所有 SSE 事件
  41  |  * 返回解析后的事件数组
  42  |  */
  43  | async function sendMessageAndCaptureEvents(
  44  |   page: Page,
  45  |   message: string
  46  | ): Promise<any[]> {
  47  |   const events: any[] = [];
  48  |   
  49  |   // 设置响应拦截器来捕获 SSE
  50  |   await page.route("**/chat/stream", async (route) => {
  51  |     const response = await route.fetch();
  52  |     const body = await response.text();
  53  |     
  54  |     // 解析 SSE 数据
  55  |     const lines = body.split('\n');
  56  |     let currentData = '';
  57  |     
  58  |     for (const line of lines) {
  59  |       if (line.startsWith('data: ')) {
  60  |         currentData = line.slice(6);
  61  |         try {
  62  |           const event = JSON.parse(currentData);
  63  |           events.push(event);
  64  |         } catch (e) {
  65  |           // 忽略非 JSON 数据
  66  |         }
  67  |       }
  68  |     }
  69  |     
  70  |     await route.fulfill({
  71  |       response,
  72  |       body,
  73  |     });
  74  |   });
  75  |   
  76  |   // 发送消息
  77  |   const textarea = page.locator("textarea").first();
  78  |   await textarea.clear();
  79  |   await textarea.fill(message);
  80  |   
  81  |   const beforeCount = await page.locator("[data-role='assistant']").count();
  82  |   await page.keyboard.press("Enter");
  83  |   
  84  |   // 等待响应完成
  85  |   await expect(
  86  |     page.locator("[data-role='assistant']")
> 87  |   ).toHaveCount(beforeCount + 1, { timeout: 30000 });
      |     ^ Error: expect(locator).toHaveCount(expected) failed
  88  |   
  89  |   // 等待一小会儿确保所有事件都已被捕获
  90  |   await page.waitForTimeout(500);
  91  |   
  92  |   return events;
  93  | }
  94  | 
  95  | /**
  96  |  * 获取 Execution 面板中的技能调用信息
  97  |  */
  98  | async function getExecutionPanelSkills(page: Page): Promise<string[]> {
  99  |   // 打开右侧面板
  100 |   const panelBtn = page.locator("header button").filter({ has: page.locator("svg") }).last();
  101 |   if (await panelBtn.isVisible()) {
  102 |     await panelBtn.click({ force: true });
  103 |     await page.waitForTimeout(400);
  104 |   }
  105 |   
  106 |   // 点击 Execution tab
  107 |   const rightAside = page.locator("aside").nth(1);
  108 |   const executionTab = rightAside.getByRole("button", { name: /Execution/i }).first();
  109 |   if (await executionTab.isVisible()) {
  110 |     await executionTab.click({ force: true });
  111 |     await page.waitForTimeout(300);
  112 |   }
  113 |   
  114 |   // 查找显示的 skill 名称（通常在 LLM Calls 部分）
  115 |   const skillElements = rightAside.locator("[data-testid='skill-tag'], .skill-badge, [data-skill-name]");
  116 |   const skills: string[] = [];
  117 |   
  118 |   const count = await skillElements.count();
  119 |   for (let i = 0; i < count; i++) {
  120 |     const text = await skillElements.nth(i).textContent();
  121 |     if (text) skills.push(text.trim());
  122 |   }
  123 |   
  124 |   return skills;
  125 | }
  126 | 
  127 | // ─── Test Data: 各种 Skill 触发场景 ───────────────────────────────────────────
  128 | 
  129 | const SKILL_TEST_CASES = [
  130 |   {
  131 |     name: "文件操作",
  132 |     message: "帮我读取当前目录下的所有文件",
  133 |     expectedSkills: ["file", "list_files", "read_file"],
  134 |   },
  135 |   {
  136 |     name: "代码分析",
  137 |     message: "分析这个 Python 函数的性能问题",
  138 |     expectedSkills: ["code", "analyze", "python"],
  139 |   },
  140 |   {
  141 |     name: "数据处理",
  142 |     message: "把 CSV 文件转换成 JSON 格式",
  143 |     expectedSkills: ["data", "csv", "json", "convert"],
  144 |   },
  145 |   {
  146 |     name: "图片处理",
  147 |     message: "生成一张包含歌词的海报图片",
  148 |     expectedSkills: ["image", "lyric", "generation", "poster"],
  149 |   },
  150 | ];
  151 | 
  152 | // ─── Flow Coding 5-Phase Test ───────────────────────────────────────────────
  153 | 
  154 | test.describe("🔄 Flow Coding: LLM Skill 识别功能", () => {
  155 |   
  156 |   /**
  157 |    * Phase 1: ESTABLISH THE VERIFICATION BASELINE
  158 |    * 验证技能系统已加载且有可用技能
  159 |    */
  160 |   test("Phase 1: 验证基线 - 技能系统可用", async ({ page }) => {
  161 |     await waitForApp(page);
  162 |     await ensureSession(page);
  163 |     
  164 |     // 验证技能 API 可访问
  165 |     const response = await page.request.get("http://localhost:8000/skills");
  166 |     expect(response.ok()).toBeTruthy();
  167 |     
  168 |     const data = await response.json();
  169 |     expect(data.total).toBeGreaterThan(0);
  170 |     expect(data.tree).toBeDefined();
  171 |     
  172 |     console.log(`✅ Phase 1: ${data.total} skills available`);
  173 |     console.log(`   Categories: ${data.categories}`);
  174 |     console.log(`   Private: ${data.private}, Linked: ${data.linked}`);
  175 |   });
  176 | 
  177 |   /**
  178 |    * Phase 2: INTENT EXPRESSION & CODE GENERATION
  179 |    * 发送各种意图的消息，验证技能路由正确识别
  180 |    */
  181 |   for (const testCase of SKILL_TEST_CASES) {
  182 |     test(`Phase 2: Skill 识别 - ${testCase.name}`, async ({ page }) => {
  183 |       await waitForApp(page);
  184 |       await ensureSession(page);
  185 |       
  186 |       console.log(`\n📤 Testing: "${testCase.message}"`);
  187 |       
```