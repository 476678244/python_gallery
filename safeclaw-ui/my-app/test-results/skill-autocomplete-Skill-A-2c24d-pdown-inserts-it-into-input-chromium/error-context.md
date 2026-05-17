# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: skill-autocomplete.spec.ts >> Skill Autocomplete >> selecting skill from dropdown inserts it into input
- Location: tests/e2e/skill-autocomplete.spec.ts:206:7

# Error details

```
Test timeout of 150000ms exceeded.
```

```
Error: locator.textContent: Test timeout of 150000ms exceeded.
Call log:
  - waiting for locator('div').filter({ has: getByText(/Available Skills \(\d+\)/) }).locator('button').first().locator('div.font-medium')

```

# Page snapshot

```yaml
- generic [ref=e1]:
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
              - button "New Chat 33m ago 2" [ref=e24]:
                - img [ref=e25]
                - generic [ref=e27]:
                  - paragraph [ref=e28]: New Chat
                  - paragraph [ref=e29]: 33m ago
                - generic [ref=e30]:
                  - generic [ref=e31]: "2"
                  - button [ref=e32] [cursor=pointer]:
                    - img [ref=e33]
          - generic [ref=e36]:
            - button "🛠 Skill Tree" [ref=e37]:
              - generic [ref=e38]: 🛠
              - generic [ref=e39]: Skill Tree
              - img [ref=e40]
            - generic [ref=e44]:
              - generic [ref=e46]:
                - img [ref=e47]
                - generic [ref=e52]: Anthropic Skills
                - switch [checked] [ref=e53]
              - generic [ref=e56]:
                - img [ref=e57]
                - generic [ref=e62]: Ljg Skills
                - switch [checked] [ref=e63]
              - generic [ref=e66]:
                - img [ref=e67]
                - generic [ref=e72]: Superpowers Skills
                - switch [checked] [ref=e73]
              - generic [ref=e76]:
                - img [ref=e77]
                - generic [ref=e82]: Private Skills
                - switch [checked] [ref=e83]
          - button "🔧 Tool Tree" [ref=e86]:
            - generic [ref=e87]: 🔧
            - generic [ref=e88]: Tool Tree
            - img [ref=e89]
          - button "🤖 Model" [ref=e92]:
            - generic [ref=e93]: 🤖
            - generic [ref=e94]: Model
            - img [ref=e95]
        - generic [ref=e97]:
          - generic [ref=e99]: "N"
          - generic [ref=e100]:
            - paragraph [ref=e101]: Nicole
            - generic [ref=e104]: All systems online
    - main [ref=e105]:
      - generic [ref=e106]:
        - generic [ref=e107]:
          - generic [ref=e109]:
            - heading "New Chat" [level=1] [ref=e110]
            - paragraph [ref=e111]: 2 messages
          - generic [ref=e112]:
            - generic [ref=e113]:
              - combobox [ref=e114]:
                - option "Qwen3.5 9B" [selected]
                - option "Gemma 4 E4B"
                - option "Gemma 4 31B"
                - option "Qwen3.6 27B"
                - option "Qwen3.5 35B A3B"
                - option "Nomic Embed v1.5"
              - img
            - button "Web" [ref=e115]:
              - img [ref=e116]
              - generic [ref=e119]: Web
            - button [ref=e120]:
              - img [ref=e121]
        - generic [ref=e124]:
          - generic [ref=e125]:
            - img [ref=e127]
            - generic [ref=e131]: hello
          - generic [ref=e132]:
            - img [ref=e134]
            - generic [ref=e138]: Hello! How can I help you today?
        - generic [ref=e140]:
          - generic [ref=e141]:
            - button "Research" [ref=e142]:
              - img [ref=e143]
              - generic [ref=e145]: Research
            - button "Analyze" [ref=e146]:
              - img [ref=e147]
              - generic [ref=e150]: Analyze
            - button "Code" [ref=e151]:
              - img [ref=e152]
              - generic [ref=e155]: Code
            - button "Context" [ref=e156]:
              - img [ref=e157]
              - generic [ref=e158]: Context
          - generic [ref=e159]:
            - button "Attach files" [ref=e160]:
              - img [ref=e161]
            - textbox "Ask anything... Use / for skills" [active] [ref=e164]: /
            - generic [ref=e165]:
              - button "Voice input" [ref=e166]:
                - img [ref=e167]
              - button [ref=e170]:
                - img [ref=e171]
    - navigation [ref=e176]:
      - button "Exec" [ref=e178]:
        - img [ref=e179]
        - generic [ref=e182]: Exec
      - button "Skills" [ref=e184]:
        - img [ref=e185]
        - generic [ref=e187]: Skills
      - button "Budget" [ref=e189]:
        - img [ref=e190]
        - generic [ref=e195]: Budget
      - button "Log" [ref=e198]:
        - img [ref=e199]
        - generic [ref=e202]: Log
      - button "Shell" [ref=e204]:
        - img [ref=e205]
        - generic [ref=e207]: Shell
      - button "Context" [ref=e210]:
        - img [ref=e211]
        - generic [ref=e214]: Context
      - button "Memory" [ref=e216]:
        - img [ref=e217]
        - generic [ref=e227]: Memory
  - button "Open Next.js Dev Tools" [ref=e233] [cursor=pointer]:
    - img [ref=e234]
  - alert [ref=e237]
```

# Test source

```ts
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
> 215 |     const skillName = await firstSkill.locator("div.font-medium").textContent();
      |                                                                   ^ Error: locator.textContent: Test timeout of 150000ms exceeded.
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
  289 |     }
  290 |   });
  291 | });
  292 | 
```