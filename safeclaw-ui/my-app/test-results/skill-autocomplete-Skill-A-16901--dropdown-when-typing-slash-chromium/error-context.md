# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: skill-autocomplete.spec.ts >> Skill Autocomplete >> shows autocomplete dropdown when typing slash
- Location: tests/e2e/skill-autocomplete.spec.ts:113:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('div').filter({ has: getByText(/Available Skills \(\d+\)/) })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('div').filter({ has: getByText(/Available Skills \(\d+\)/) })

```

```yaml
- complementary:
  - img
  - text: SafeClaw
  - button "💬 Chats 1":
    - text: 💬 Chats 1
    - img
  - button "New Chat":
    - img
    - text: New Chat
  - button "New Chat 32m ago 2":
    - img
    - paragraph: New Chat
    - paragraph: 32m ago
    - text: "2"
    - button:
      - img
  - button "🛠 Skill Tree":
    - text: 🛠 Skill Tree
    - img
  - img
  - text: Anthropic Skills
  - switch [checked]
  - img
  - text: Ljg Skills
  - switch [checked]
  - img
  - text: Superpowers Skills
  - switch [checked]
  - img
  - text: Private Skills
  - switch [checked]
  - button "🔧 Tool Tree":
    - text: 🔧 Tool Tree
    - img
  - button "🤖 Model":
    - text: 🤖 Model
    - img
  - text: "N"
  - paragraph: Nicole
  - text: All systems online
- main:
  - heading "New Chat" [level=1]
  - paragraph: 2 messages
  - combobox:
    - option "Qwen3.5 9B" [selected]
    - option "Gemma 4 E4B"
    - option "Gemma 4 31B"
    - option "Qwen3.6 27B"
    - option "Qwen3.5 35B A3B"
    - option "Nomic Embed v1.5"
  - img
  - button "Web":
    - img
    - text: Web
  - button:
    - img
  - img
  - text: hello
  - img
  - text: Hello! How can I help you today?
  - button "Research":
    - img
    - text: Research
  - button "Analyze":
    - img
    - text: Analyze
  - button "Code":
    - img
    - text: Code
  - button "Context":
    - img
    - text: Context
  - button "Attach files":
    - img
  - textbox "Ask anything... Use / for skills": /
  - button "Voice input":
    - img
  - button:
    - img
- navigation:
  - button "Exec":
    - img
    - text: Exec
  - button "Skills":
    - img
    - text: Skills
  - button "Budget":
    - img
    - text: Budget
  - button "Log":
    - img
    - text: Log
  - button "Shell":
    - img
    - text: Shell
  - button "Context":
    - img
    - text: Context
  - button "Memory":
    - img
    - text: Memory
- alert
```

# Test source

```ts
  21  | 
  22  | /** Ensure there is an active session; creates one if the list is empty */
  23  | async function ensureSession(page: Page) {
  24  |   const textarea = page.locator("textarea").first();
  25  |   const isDisabled = await textarea.isDisabled().catch(() => true);
  26  |   if (isDisabled) {
  27  |     const newChatBtn = page.getByText("New Chat").first();
  28  |     await newChatBtn.click();
  29  |     await page.waitForTimeout(1200);
  30  |   }
  31  | }
  32  | 
  33  | /** Type a slash and wait for autocomplete dropdown */
  34  | async function openSkillAutocomplete(page: Page) {
  35  |   const textarea = page.locator("textarea").first();
  36  |   await textarea.click();
  37  |   await textarea.fill("/");
  38  |   // Wait longer for skills to load from API and dropdown to render
  39  |   await page.waitForTimeout(1000);
  40  | }
  41  | 
  42  | /** Get dropdown locator */
  43  | function getDropdownLocator(page: Page) {
  44  |   // Use regex to match "Available Skills (N)" where N is a number
  45  |   return page.locator("div").filter({
  46  |     has: page.getByText(/Available Skills \(\d+\)/),
  47  |   });
  48  | }
  49  | 
  50  | /** Get all skill names from the autocomplete dropdown */
  51  | async function getDropdownSkillNames(page: Page): Promise<string[]> {
  52  |   const dropdown = getDropdownLocator(page);
  53  |   
  54  |   // Wait for dropdown to be visible
  55  |   await expect(dropdown).toBeVisible({ timeout: 10000 });
  56  |   
  57  |   // Get all skill buttons in the dropdown (buttons inside the dropdown that have skill names)
  58  |   const skillButtons = dropdown.locator("button");
  59  |   const count = await skillButtons.count();
  60  |   
  61  |   const names: string[] = [];
  62  |   for (let i = 0; i < count; i++) {
  63  |     const name = await skillButtons.nth(i).locator("div.font-medium").textContent().catch(() => null);
  64  |     if (name) names.push(name.trim());
  65  |   }
  66  |   return names;
  67  | }
  68  | 
  69  | /** Get skills data from API */
  70  | async function getSkillsFromAPI(page: Page): Promise<{
  71  |   builtin: string[];
  72  |   private: string[];
  73  |   linked: string[];
  74  |   marketplace: string[];
  75  | }> {
  76  |   const response = await page.request.get("http://localhost:8000/skills");
  77  |   const data = await response.json();
  78  |   
  79  |   const skills = {
  80  |     builtin: [] as string[],
  81  |     private: [] as string[],
  82  |     linked: [] as string[],
  83  |     marketplace: [] as string[],
  84  |   };
  85  |   
  86  |   // Parse skill tree
  87  |   for (const node of data.tree || []) {
  88  |     const category = node.id?.startsWith("linked/") ? "linked" : 
  89  |                      node.id === "private" ? "private" : 
  90  |                      node.id === "builtin" ? "builtin" : "other";
  91  |     
  92  |     for (const child of node.children || []) {
  93  |       if (!child.is_folder) {
  94  |         const skillName = child.name;
  95  |         if (category === "linked" || category === "private" || category === "builtin") {
  96  |           skills[category].push(skillName);
  97  |         }
  98  |       }
  99  |     }
  100 |   }
  101 |   
  102 |   return skills;
  103 | }
  104 | 
  105 | // ─── Test Suite ─────────────────────────────────────────────────────────────
  106 | 
  107 | test.describe("Skill Autocomplete", () => {
  108 |   test.beforeEach(async ({ page }) => {
  109 |     await waitForApp(page);
  110 |     await ensureSession(page);
  111 |   });
  112 | 
  113 |   test("shows autocomplete dropdown when typing slash", async ({ page }) => {
  114 |     // Wait for skills to be loaded from API first
  115 |     await page.waitForTimeout(500);
  116 |     
  117 |     await openSkillAutocomplete(page);
  118 |     
  119 |     // Verify dropdown is visible using regex matcher
  120 |     const dropdown = getDropdownLocator(page);
> 121 |     await expect(dropdown).toBeVisible({ timeout: 10000 });
      |                            ^ Error: expect(locator).toBeVisible() failed
  122 |     
  123 |     // Verify dropdown header shows count
  124 |     const header = page.getByText(/Available Skills \(\d+\)/);
  125 |     await expect(header).toBeVisible();
  126 |   });
  127 | 
  128 |   test("autocomplete contains skills from all categories", async ({ page }) => {
  129 |     // Get skills from API for comparison
  130 |     const apiSkills = await getSkillsFromAPI(page);
  131 |     console.log("API skills by category:", apiSkills);
  132 |     
  133 |     // Wait for skills to be loaded from API
  134 |     await page.waitForTimeout(500);
  135 |     
  136 |     // Open autocomplete
  137 |     await openSkillAutocomplete(page);
  138 |     
  139 |     // Get skills from dropdown
  140 |     const dropdownSkills = await getDropdownSkillNames(page);
  141 |     console.log("Dropdown skills:", dropdownSkills);
  142 |     
  143 |     // Verify that skills from each category are represented
  144 |     const totalApiSkills = 
  145 |       apiSkills.builtin.length + 
  146 |       apiSkills.private.length + 
  147 |       apiSkills.linked.length;
  148 |     
  149 |     if (totalApiSkills > 0) {
  150 |       expect(dropdownSkills.length).toBeGreaterThan(0);
  151 |       expect(dropdownSkills.length).toBeLessThanOrEqual(totalApiSkills);
  152 |     }
  153 |     
  154 |     // Check that at least some skills from each category are present
  155 |     for (const category of ["builtin", "private", "linked"] as const) {
  156 |       if (apiSkills[category].length > 0) {
  157 |         const hasSkillFromCategory = apiSkills[category].some(
  158 |           skillName => dropdownSkills.includes(skillName)
  159 |         );
  160 |         console.log(`Category ${category}: ${hasSkillFromCategory ? "✅ found" : "❌ not found"}`);
  161 |       }
  162 |     }
  163 |   });
  164 | 
  165 |   test("autocomplete filters when typing after slash", async ({ page }) => {
  166 |     await openSkillAutocomplete(page);
  167 |     
  168 |     const textarea = page.locator("textarea").first();
  169 |     
  170 |     // Type a filter term
  171 |     await textarea.fill("/test");
  172 |     await page.waitForTimeout(300);
  173 |     
  174 |     // Get filtered skills
  175 |     const filteredSkills = await getDropdownSkillNames(page);
  176 |     
  177 |     // All filtered skills should contain the filter term (case insensitive)
  178 |     for (const skill of filteredSkills) {
  179 |       expect(skill.toLowerCase()).toContain("test");
  180 |     }
  181 |   });
  182 | 
  183 |   test("keyboard navigation works in dropdown", async ({ page }) => {
  184 |     await page.waitForTimeout(500);
  185 |     await openSkillAutocomplete(page);
  186 |     
  187 |     const dropdown = getDropdownLocator(page);
  188 |     await expect(dropdown).toBeVisible({ timeout: 10000 });
  189 |     
  190 |     // Press arrow down to navigate
  191 |     await page.keyboard.press("ArrowDown");
  192 |     await page.waitForTimeout(100);
  193 |     
  194 |     // Press arrow up to navigate back
  195 |     await page.keyboard.press("ArrowUp");
  196 |     await page.waitForTimeout(100);
  197 |     
  198 |     // Press Escape to close dropdown
  199 |     await page.keyboard.press("Escape");
  200 |     await page.waitForTimeout(100);
  201 |     
  202 |     // Dropdown should be closed
  203 |     await expect(dropdown).not.toBeVisible();
  204 |   });
  205 | 
  206 |   test("selecting skill from dropdown inserts it into input", async ({ page }) => {
  207 |     await page.waitForTimeout(500);
  208 |     await openSkillAutocomplete(page);
  209 |     
  210 |     // Get first skill from dropdown
  211 |     const dropdown = getDropdownLocator(page);
  212 |     const firstSkill = dropdown.locator("button").first();
  213 |     
  214 |     // Get the skill name
  215 |     const skillName = await firstSkill.locator("div.font-medium").textContent();
  216 |     
  217 |     if (skillName) {
  218 |       // Click the skill
  219 |       await firstSkill.click();
  220 |       await page.waitForTimeout(200);
  221 |       
```