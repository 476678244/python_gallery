# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: right-panel-resize.spec.ts >> Right Panel · Horizontal Resize >> should resize panel width by dragging horizontal handle
- Location: right-panel-resize.spec.ts:57:7

# Error details

```
Error: expect(received).not.toBe(expected) // Object.is equality

Expected: not 319
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]:
          - img [ref=e7]
          - generic [ref=e9]: SafeClaw
        - generic [ref=e10]:
          - generic [ref=e11]:
            - button "💬 Chats 1" [ref=e12]:
              - generic [ref=e13]: 💬
              - generic [ref=e14]: Chats
              - generic [ref=e15]: "1"
              - img [ref=e16]
            - generic [ref=e18]:
              - button "New Chat" [ref=e20]:
                - img [ref=e21]
                - text: New Chat
              - button "New Chat Just now" [ref=e24]:
                - img [ref=e25]
                - generic [ref=e27]:
                  - paragraph [ref=e28]: New Chat
                  - paragraph [ref=e29]: Just now
                - button [ref=e31] [cursor=pointer]:
                  - img [ref=e32]
          - generic [ref=e35]:
            - button "🛠 Skill Tree" [ref=e36]:
              - generic [ref=e37]: 🛠
              - generic [ref=e38]: Skill Tree
              - img [ref=e39]
            - generic [ref=e43]:
              - generic [ref=e45]:
                - button [ref=e46]:
                  - img [ref=e47]
                - img [ref=e49]
                - generic [ref=e51]: Anthropic Skills
                - switch [ref=e52]
              - generic [ref=e55]:
                - button [ref=e56]:
                  - img [ref=e57]
                - img [ref=e59]
                - generic [ref=e61]: Ljg Skills
                - switch [ref=e62]
              - generic [ref=e65]:
                - button [ref=e66]:
                  - img [ref=e67]
                - img [ref=e69]
                - generic [ref=e71]: Superpowers Skills
                - switch [ref=e72]
              - generic [ref=e75]:
                - button [ref=e76]:
                  - img [ref=e77]
                - img [ref=e79]
                - generic [ref=e81]: Private Skills
                - switch [checked] [ref=e82]
          - button "🔧 Tool Tree" [ref=e85]:
            - generic [ref=e86]: 🔧
            - generic [ref=e87]: Tool Tree
            - img [ref=e88]
          - button "🤖 Model" [ref=e91]:
            - generic [ref=e92]: 🤖
            - generic [ref=e93]: Model
            - img [ref=e94]
        - generic [ref=e96]:
          - generic [ref=e98]: "N"
          - generic [ref=e99]:
            - paragraph [ref=e100]: Nicole
            - generic [ref=e103]: All systems online
    - main [ref=e104]:
      - generic [ref=e105]:
        - generic [ref=e106]:
          - generic [ref=e108]:
            - heading "New Chat" [level=1] [ref=e109]
            - paragraph [ref=e110]: 0 messages
          - generic [ref=e111]:
            - generic [ref=e112]:
              - combobox [ref=e113]:
                - option "Qwen3.5 9B" [selected]
                - option "Gemma 4 E4B"
                - option "Gemma 4 31B"
                - option "Qwen3.6 27B"
                - option "Qwen3.5 35B A3B"
                - option "Nomic Embed v1.5"
              - img
            - button "Web" [ref=e114]:
              - img [ref=e115]
              - generic [ref=e118]: Web
            - button [ref=e119]:
              - img [ref=e120]
        - generic [ref=e124]:
          - generic [ref=e125]:
            - button "Research" [ref=e126]:
              - img [ref=e127]
              - generic [ref=e129]: Research
            - button "Analyze" [ref=e130]:
              - img [ref=e131]
              - generic [ref=e134]: Analyze
            - button "Code" [ref=e135]:
              - img [ref=e136]
              - generic [ref=e139]: Code
            - button "Context" [ref=e140]:
              - img [ref=e141]
              - generic [ref=e142]: Context
          - generic [ref=e143]:
            - button "Upload files to /tmp/uploaded" [ref=e144]:
              - img [ref=e145]
            - textbox "Ask anything... Use / for skills" [ref=e148]
            - generic [ref=e149]:
              - button "Voice input" [ref=e150]:
                - img [ref=e151]
              - button [disabled] [ref=e154]:
                - img [ref=e155]
    - generic [ref=e158]:
      - img [ref=e160]
      - generic [ref=e168]:
        - button "Execution Path ✓" [ref=e169]:
          - img [ref=e170]
          - generic [ref=e173]: Execution Path
          - generic [ref=e174]: ✓
          - img [ref=e175]
        - generic [ref=e178]: Send a message to see execution plan.
        - img [ref=e180]
      - navigation [ref=e187]:
        - button "Exec" [ref=e189]:
          - img [ref=e191]
          - generic [ref=e194]: Exec
        - button "Skills" [ref=e196]:
          - img [ref=e197]
          - generic [ref=e199]: Skills
        - button "Budget" [ref=e201]:
          - img [ref=e202]
          - generic [ref=e207]: Budget
        - button "Log" [ref=e210]:
          - img [ref=e211]
          - generic [ref=e214]: Log
        - button "Shell" [ref=e216]:
          - img [ref=e217]
          - generic [ref=e219]: Shell
        - button "Prompts" [ref=e222]:
          - img [ref=e223]
          - generic [ref=e226]: Prompts
        - button "Memory" [ref=e228]:
          - img [ref=e229]
          - generic [ref=e239]: Memory
  - button "Open Next.js Dev Tools" [ref=e245] [cursor=pointer]:
    - img [ref=e246]
  - alert [ref=e249]
```

# Test source

```ts
  1   | /**
  2   |  * Right Panel Resize Tests
  3   |  *
  4   |  * Tests the resizable right panel:
  5   |  *   ① Horizontal resize (panel width)
  6   |  *   ② Vertical resize (panel heights)
  7   |  *   ③ Auto-distribute heights (1-3 panels)
  8   |  *   ④ User manual adjustment after auto-distribute
  9   |  *
  10  |  * Requires Next.js running on http://localhost:3000
  11  |  */
  12  | 
  13  | import { test, expect, Page } from "@playwright/test";
  14  | 
  15  | // ─── Helpers ──────────────────────────────────────────────────────────────────
  16  | 
  17  | async function goto(page: Page) {
  18  |   await page.goto("/");
  19  |   await page.waitForLoadState("networkidle");
  20  |   // Reset persisted UI state so no panels leak from previous tests
  21  |   await page.evaluate(() => localStorage.removeItem("safeclaw-ui-store"));
  22  |   await page.reload();
  23  |   await page.waitForLoadState("networkidle");
  24  |   await page.waitForTimeout(500);
  25  | }
  26  | 
  27  | /** Click a rail icon to open a panel */
  28  | async function openPanel(page: Page, label: string) {
  29  |   const railBtn = page.locator("nav button[title]").filter({ hasText: new RegExp(label, "i") }).first();
  30  |   await railBtn.click();
  31  |   await page.waitForTimeout(300);
  32  | }
  33  | 
  34  | /** Get panel body by title */
  35  | function panelBody(page: Page, title: string) {
  36  |   return page
  37  |     .locator("div.border-b")
  38  |     .filter({ hasText: new RegExp(title, "i") })
  39  |     .first();
  40  | }
  41  | 
  42  | /** Get horizontal resize handle */
  43  | function horizontalResizeHandle(page: Page) {
  44  |   return page.locator("div.cursor-ew-resize").first();
  45  | }
  46  | 
  47  | /** Get vertical resize handle at the bottom of a panel */
  48  | function verticalResizeHandle(page: Page, panelTitle: string) {
  49  |   return panelBody(page, panelTitle)
  50  |     .locator("div.cursor-ns-resize")
  51  |     .first();
  52  | }
  53  | 
  54  | // ─── ① Horizontal Resize ─────────────────────────────────────────────────────
  55  | 
  56  | test.describe("Right Panel · Horizontal Resize", () => {
  57  |   test("should resize panel width by dragging horizontal handle", async ({ page }) => {
  58  |     await goto(page);
  59  | 
  60  |     // Open a panel first
  61  |     await openPanel(page, "Exec");
  62  | 
  63  |     // Wait for panel to be visible
  64  |     const execPanel = panelBody(page, "Execution Path");
  65  |     await expect(execPanel).toBeVisible();
  66  | 
  67  |     // Get initial width
  68  |     const initialWidth = await execPanel.evaluate((el) => el.getBoundingClientRect().width);
  69  | 
  70  |     // Find and drag horizontal resize handle
  71  |     const handle = horizontalResizeHandle(page);
  72  |     await expect(handle).toBeVisible();
  73  | 
  74  |     // Drag to widen panel (move handle to the left)
  75  |     const handleBox = await handle.boundingBox();
  76  |     if (handleBox) {
  77  |       await handle.dragTo(handle, {
  78  |         force: true,
  79  |         targetPosition: { x: -50, y: handleBox.height / 2 },
  80  |       });
  81  |     }
  82  | 
  83  |     await page.waitForTimeout(300);
  84  | 
  85  |     // Check width changed
  86  |     const newWidth = await execPanel.evaluate((el) => el.getBoundingClientRect().width);
> 87  |     expect(newWidth).not.toBe(initialWidth);
      |                          ^ Error: expect(received).not.toBe(expected) // Object.is equality
  88  |   });
  89  | });
  90  | 
  91  | // ─── ② Vertical Resize ────────────────────────────────────────────────────────
  92  | 
  93  | test.describe("Right Panel · Vertical Resize", () => {
  94  |   test("should resize panel height by dragging vertical handle", async ({ page }) => {
  95  |     await goto(page);
  96  | 
  97  |     // Open a panel
  98  |     await openPanel(page, "Exec");
  99  | 
  100 |     const execPanel = panelBody(page, "Execution Path");
  101 |     await expect(execPanel).toBeVisible();
  102 | 
  103 |     // Get initial height
  104 |     const initialHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
  105 | 
  106 |     // Find vertical resize handle
  107 |     const vHandle = verticalResizeHandle(page, "Execution Path");
  108 |     await expect(vHandle).toBeVisible();
  109 | 
  110 |     // Drag to resize
  111 |     const handleBox = await vHandle.boundingBox();
  112 |     if (handleBox) {
  113 |       await vHandle.dragTo(vHandle, {
  114 |         force: true,
  115 |         targetPosition: { x: handleBox.width / 2, y: 50 },
  116 |       });
  117 |     }
  118 | 
  119 |     await page.waitForTimeout(300);
  120 | 
  121 |     // Check height changed
  122 |     const newHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
  123 |     expect(Math.abs(newHeight - initialHeight)).toBeGreaterThan(10);
  124 |   });
  125 | });
  126 | 
  127 | // ─── ③ Auto-distribute Heights ───────────────────────────────────────────────
  128 | 
  129 | test.describe("Right Panel · Auto-distribute Heights", () => {
  130 |   test("1 panel should fill entire height", async ({ page }) => {
  131 |     await goto(page);
  132 | 
  133 |     // Open just one panel
  134 |     await openPanel(page, "Exec");
  135 | 
  136 |     const execPanel = panelBody(page, "Execution Path");
  137 |     await expect(execPanel).toBeVisible();
  138 | 
  139 |     // Panel should take most of viewport height
  140 |     const panelHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
  141 |     const viewportHeight = await page.evaluate(() => window.innerHeight);
  142 | 
  143 |     // Should be at least 50% of viewport
  144 |     expect(panelHeight).toBeGreaterThan(viewportHeight * 0.5);
  145 |   });
  146 | 
  147 |   test("2 panels should each take ~50% height", async ({ page }) => {
  148 |     await goto(page);
  149 | 
  150 |     // Open two panels
  151 |     await openPanel(page, "Exec");
  152 |     await openPanel(page, "Skills");
  153 | 
  154 |     const execPanel = panelBody(page, "Execution Path");
  155 |     const skillsPanel = panelBody(page, "Skills Path");
  156 | 
  157 |     await expect(execPanel).toBeVisible();
  158 |     await expect(skillsPanel).toBeVisible();
  159 | 
  160 |     // Get heights
  161 |     const execHeight = await execPanel.evaluate((el) => el.getBoundingClientRect().height);
  162 |     const skillsHeight = await skillsPanel.evaluate((el) => el.getBoundingClientRect().height);
  163 | 
  164 |     // Both should be significant and similar
  165 |     expect(execHeight).toBeGreaterThan(150);
  166 |     expect(skillsHeight).toBeGreaterThan(150);
  167 | 
  168 |     // Difference should be within 20%
  169 |     const ratio = Math.max(execHeight, skillsHeight) / Math.min(execHeight, skillsHeight);
  170 |     expect(ratio).toBeLessThan(1.3);
  171 |   });
  172 | 
  173 |   test("3 panels should each take ~33% height", async ({ page }) => {
  174 |     await goto(page);
  175 | 
  176 |     // Open three panels
  177 |     await openPanel(page, "Exec");
  178 |     await openPanel(page, "Skills");
  179 |     await openPanel(page, "Budget");
  180 | 
  181 |     const execPanel = panelBody(page, "Execution Path");
  182 |     const skillsPanel = panelBody(page, "Skills Path");
  183 |     const budgetPanel = panelBody(page, "Budget");
  184 | 
  185 |     await expect(execPanel).toBeVisible();
  186 |     await expect(skillsPanel).toBeVisible();
  187 |     await expect(budgetPanel).toBeVisible();
```