# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: skill-autocomplete.spec.ts >> Skill Autocomplete >> keyboard navigation works in dropdown
- Location: tests/e2e/skill-autocomplete.spec.ts:183:7

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
  121 |     await expect(dropdown).toBeVisible({ timeout: 10000 });
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
> 188 |     await expect(dropdown).toBeVisible({ timeout: 10000 });
      |                            ^ Error: expect(locator).toBeVisible() failed
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
  222 |       // Verify input contains the skill name with slash prefix
  223 |       const textarea = page.locator("textarea").first();
  224 |       const inputValue = await textarea.inputValue();
  225 |       expect(inputValue).toContain(`/${skillName.trim()}`);
  226 |     }
  227 |   });
  228 | 
  229 |   test("each category has at least one enabled skill in dropdown", async ({ page }) => {
  230 |     // Get API skills by category
  231 |     const response = await page.request.get("http://localhost:8000/skills");
  232 |     const data = await response.json();
  233 |     
  234 |     // Count enabled skills per category from API
  235 |     const categoryCounts: Record<string, { enabled: number; total: number }> = {};
  236 |     
  237 |     for (const node of data.tree || []) {
  238 |       const category = node.id?.startsWith("linked/") ? "linked" : 
  239 |                        node.id === "private" ? "private" : 
  240 |                        node.id === "builtin" ? "builtin" : "other";
  241 |       
  242 |       if (!categoryCounts[category]) {
  243 |         categoryCounts[category] = { enabled: 0, total: 0 };
  244 |       }
  245 |       
  246 |       for (const child of node.children || []) {
  247 |         if (!child.is_folder) {
  248 |           categoryCounts[category].total++;
  249 |           if (child.enabled) {
  250 |             categoryCounts[category].enabled++;
  251 |           }
  252 |         }
  253 |       }
  254 |     }
  255 |     
  256 |     console.log("Category counts from API:", categoryCounts);
  257 |     
  258 |     // Wait for skills to be loaded
  259 |     await page.waitForTimeout(500);
  260 |     
  261 |     // Open autocomplete
  262 |     await openSkillAutocomplete(page);
  263 |     const dropdownSkills = await getDropdownSkillNames(page);
  264 |     
  265 |     // For each category with enabled skills, verify at least one appears in dropdown
  266 |     for (const [category, counts] of Object.entries(categoryCounts)) {
  267 |       if (counts.enabled > 0) {
  268 |         // Find any skill from this category that's in the dropdown
  269 |         let found = false;
  270 |         for (const node of data.tree || []) {
  271 |           const nodeCategory = node.id?.startsWith("linked/") ? "linked" : 
  272 |                                node.id === "private" ? "private" : 
  273 |                                node.id === "builtin" ? "builtin" : "other";
  274 |           
  275 |           if (nodeCategory === category) {
  276 |             for (const child of node.children || []) {
  277 |               if (!child.is_folder && child.enabled && dropdownSkills.includes(child.name)) {
  278 |                 found = true;
  279 |                 console.log(`✅ Found skill from ${category}: ${child.name}`);
  280 |                 break;
  281 |               }
  282 |             }
  283 |           }
  284 |           if (found) break;
  285 |         }
  286 |         
  287 |         expect(found, `Should have at least one skill from ${category} in dropdown`).toBe(true);
  288 |       }
```