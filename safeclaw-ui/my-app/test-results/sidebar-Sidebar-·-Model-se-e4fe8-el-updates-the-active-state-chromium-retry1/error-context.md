# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: sidebar.spec.ts >> Sidebar · Model section >> Selecting a different model updates the active state
- Location: tests/e2e/sidebar.spec.ts:382:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e6]:
    - heading "无法访问此网站" [level=1] [ref=e7]
    - paragraph [ref=e8]:
      - strong [ref=e9]: localhost
      - text: 拒绝了我们的连接请求。
    - generic [ref=e10]:
      - paragraph [ref=e11]: 请试试以下办法：
      - list [ref=e12]:
        - listitem [ref=e13]: 检查网络连接
        - listitem [ref=e14]:
          - link "检查代理服务器和防火墙" [ref=e15] [cursor=pointer]:
            - /url: "#buttons"
    - generic [ref=e16]: ERR_CONNECTION_REFUSED
  - generic [ref=e17]:
    - button "重新加载" [ref=e19] [cursor=pointer]
    - button "详情" [ref=e20] [cursor=pointer]
```

# Test source

```ts
  1   | /**
  2   |  * Sidebar UI Tests
  3   |  *
  4   |  * Tests the new vertical collapsible-section sidebar:
  5   |  *   ① Chats section  — New Chat, Delete Chat, section collapse/expand
  6   |  *   ② Skill Tree     — default open, skill toggle switch
  7   |  *   ③ Tool Tree      — default collapsed, folder open/close, tool visibility
  8   |  *   ④ Model section  — default collapsed, model selection
  9   |  *
  10  |  * Requires Next.js running on http://localhost:3000
  11  |  */
  12  | 
  13  | import { test, expect, Page } from "@playwright/test";
  14  | 
  15  | // ─── Helpers ──────────────────────────────────────────────────────────────────
  16  | 
  17  | async function goto(page: Page) {
> 18  |   await page.goto("/");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  19  |   await page.waitForLoadState("networkidle");
  20  |   await page.waitForTimeout(500);
  21  | }
  22  | 
  23  | /** Click the header of a sidebar section by its title text */
  24  | async function clickSectionHeader(page: Page, title: string) {
  25  |   await page
  26  |     .locator("button")
  27  |     .filter({ hasText: new RegExp(title, "i") })
  28  |     .first()
  29  |     .click();
  30  | }
  31  | 
  32  | /** Return the body div directly after the section header button */
  33  | function sectionBody(page: Page, title: string) {
  34  |   // The SbSection renders: <div.border-b> <button>…title…</button> <div>children</div> </div>
  35  |   return page
  36  |     .locator("button")
  37  |     .filter({ hasText: new RegExp(title, "i") })
  38  |     .first()
  39  |     .locator("xpath=following-sibling::div[1]");
  40  | }
  41  | 
  42  | // ─── ① Chats section ─────────────────────────────────────────────────────────
  43  | 
  44  | test.describe("Sidebar · Chats section", () => {
  45  |   test("Chats section is open by default and shows New Chat button", async ({ page }) => {
  46  |     await goto(page);
  47  |     // "New Chat" button should be visible in the sidebar without any click
  48  |     const newChatBtn = page
  49  |       .locator("div.border-b")           // sb-section wrapper
  50  |       .filter({ hasText: /Chats/i })
  51  |       .locator("button")
  52  |       .filter({ hasText: /New Chat/i })
  53  |       .first();
  54  |     await expect(newChatBtn).toBeVisible({ timeout: 5000 });
  55  |   });
  56  | 
  57  |   test("New Chat creates a session that appears in the list", async ({ page }) => {
  58  |     await goto(page);
  59  | 
  60  |     // Count sessions before
  61  |     const sessionsBefore = await page
  62  |       .locator("div.border-b")
  63  |       .filter({ hasText: /Chats/i })
  64  |       .locator("[data-role='session-item'], button")
  65  |       .filter({ hasText: /Chat|Untitled/i })
  66  |       .count();
  67  | 
  68  |     // Click New Chat
  69  |     await page
  70  |       .locator("div.border-b")
  71  |       .filter({ hasText: /Chats/i })
  72  |       .locator("button")
  73  |       .filter({ hasText: /New Chat/i })
  74  |       .first()
  75  |       .click();
  76  | 
  77  |     await page.waitForTimeout(1200);
  78  | 
  79  |     // At least one session item should be visible
  80  |     const sessionItem = page.locator("[data-testid='session-item']").first();
  81  |     const byTitle = page.getByText(/New Chat|Untitled/i).first();
  82  |     // Either a data-testid or text is acceptable
  83  |     const visible =
  84  |       (await sessionItem.isVisible().catch(() => false)) ||
  85  |       (await byTitle.isVisible().catch(() => false));
  86  |     expect(visible).toBe(true);
  87  |   });
  88  | 
  89  |   test("Delete Chat button removes the session", async ({ page }) => {
  90  |     await goto(page);
  91  | 
  92  |     // Ensure at least one session exists
  93  |     const newChatBtn = page
  94  |       .locator("div.border-b")
  95  |       .filter({ hasText: /Chats/i })
  96  |       .locator("button")
  97  |       .filter({ hasText: /New Chat/i })
  98  |       .first();
  99  |     await newChatBtn.click();
  100 |     await page.waitForTimeout(1200);
  101 | 
  102 |     // Hover over first session item to reveal delete button
  103 |     const sessionRow = page.locator(".group").first();
  104 |     await sessionRow.hover();
  105 | 
  106 |     // Click the trash / delete button (appears on hover)
  107 |     const deleteBtn = sessionRow.locator("button, div[role='button']").filter({
  108 |       has: page.locator("svg"),
  109 |     }).last();
  110 | 
  111 |     if (await deleteBtn.isVisible()) {
  112 |       await deleteBtn.click();
  113 |       await page.waitForTimeout(800);
  114 |       // Page should not crash
  115 |       await expect(page.locator("body")).toBeVisible();
  116 |     }
  117 |   });
  118 | 
```