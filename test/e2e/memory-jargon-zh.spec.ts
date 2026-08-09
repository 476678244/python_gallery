/**
 * Investment jargon Chinese Q&A — golden path for memory-system feature.
 *
 * Spec: docs/features/memory-system/e2e.md
 *
 * Prefers DeepSeek when configured; LLM answer assertions skip without key.
 * API + panel checks always run.
 *
 * Headed: HEADED=1 npx playwright test memory-jargon-zh.spec.ts
 */

import { test, expect, Page, APIRequestContext } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";
const MODEL = process.env.SAFECLAW_E2E_DEEPSEEK_MODEL || "deepseek-v4-flash";

const FALLBACK_MARKERS = [
  "fallback mode",
  "LLM service is currently unavailable",
  "LLM service is temporarily unavailable",
];

const ENCYCLOPEDIA_ONLY = [
  "大学课程",
  "导论课",
  "经济学导论",
  "highway 101",
  "route 101",
  "us route",
];

async function deepseekReady(request: APIRequestContext): Promise<boolean> {
  if (process.env.SAFECLAW_E2E_SKIP_DEEPSEEK === "1") return false;
  const res = await request.get(`${API}/settings/deepseek`);
  if (!res.ok()) return false;
  return Boolean((await res.json()).configured);
}

async function waitForApp(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
}

async function ensureSession(page: Page) {
  const textarea = page.locator("textarea").first();
  if (await textarea.isDisabled().catch(() => true)) {
    await page.getByText("New Chat").first().click();
    await page.waitForTimeout(1200);
  }
  await expect(textarea).not.toBeDisabled({ timeout: 15000 });
}

async function sendAndWaitAssistant(page: Page, message: string, timeout = 90_000) {
  const textarea = page.locator("textarea").first();
  await textarea.click();
  await textarea.fill(message);
  const before = await page.locator("[data-role='assistant']").count();
  await page.keyboard.press("Enter");
  await expect(page.locator("[data-role='assistant']")).toHaveCount(before + 1, {
    timeout,
  });
  const last = page.locator("[data-role='assistant']").last();
  let prev = "";
  for (let i = 0; i < 40; i++) {
    await page.waitForTimeout(500);
    const text = (await last.textContent()) || "";
    if (text.length > 10 && text === prev) break;
    prev = text;
  }
  return ((await last.textContent()) || "").trim();
}

function assertDomain101(reply: string) {
  const lower = reply.toLowerCase();
  for (const m of FALLBACK_MARKERS) {
    expect(lower).not.toContain(m.toLowerCase());
  }
  const hasDomain =
    reply.includes("散户") || reply.includes("接盘") || reply.includes("边际");
  expect(hasDomain, `Expected investment jargon sense:\n${reply.slice(0, 400)}`).toBeTruthy();

  // Must not be encyclopedia-only
  const onlyEncyclopedia =
    ENCYCLOPEDIA_ONLY.some((p) => lower.includes(p)) && !hasDomain;
  expect(onlyEncyclopedia).toBeFalsy();
}

test.describe("Memory jargon ZH (TC-ZH)", () => {
  test("TC-ZH-01 API: 什么是101 hits jargon", async ({ request }) => {
    const res = await request.get(`${API}/memory`, {
      params: { search: "什么是101", limit: "5" },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.total).toBeGreaterThanOrEqual(1);
    const blob = JSON.stringify(body.memories || []);
    expect(blob).toMatch(/101|散户|接盘/);
  });

  test("TC-ZH-02 API: 你知道哪些黑话 hits inventory", async ({ request }) => {
    const res = await request.get(`${API}/memory`, {
      params: { search: "你知道哪些黑话", limit: "5" },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.total).toBeGreaterThanOrEqual(1);
    const blob = JSON.stringify(body.memories || []);
    expect(blob).toMatch(/黑话|Jargon|jargon|懂王|101/);
  });

  test("TC-ZH-05 panel shows ingested jargon", async ({ page }) => {
    await waitForApp(page);
    await ensureSession(page);
    await page.getByTitle("Memory").click();
    await page.waitForTimeout(600);
    const panel = page.getByTestId("memory-panel");
    await expect(panel).toBeVisible({ timeout: 10000 });
    // Active layer may have overflowed; search in panel
    const search = panel.locator('input[placeholder*="Search"]');
    if (await search.isVisible().catch(() => false)) {
      await search.fill("101");
      await panel.getByRole("button", { name: /Search/i }).click();
      await page.waitForTimeout(500);
    }
    await expect(panel.getByText(/101|Investment Jargon|散户/i).first()).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText("Porsche Macan")).toHaveCount(0);
  });

  test("TC-ZH-03 UI: 什么是101 domain answer (DeepSeek gated)", async ({
    page,
    request,
  }) => {
    test.skip(!(await deepseekReady(request)), "DeepSeek API key not configured");
    await request.put(`${API}/settings/model`, { data: { model: MODEL } });

    await waitForApp(page);
    await ensureSession(page);
    const reply = await sendAndWaitAssistant(page, "什么是101");
    assertDomain101(reply);
    await page.screenshot({
      path: "test-results/memory-jargon-zh-101.png",
      fullPage: true,
    });
  });

  test("TC-ZH-04 UI: list jargon from memory (DeepSeek gated)", async ({
    page,
    request,
  }) => {
    test.skip(!(await deepseekReady(request)), "DeepSeek API key not configured");
    await request.put(`${API}/settings/model`, { data: { model: MODEL } });

    await waitForApp(page);
    await ensureSession(page);
    const reply = await sendAndWaitAssistant(
      page,
      "你知道哪些黑话？请列举记忆里的投资黑话，至少说出两个词条名。"
    );
    for (const m of FALLBACK_MARKERS) {
      expect(reply.toLowerCase()).not.toContain(m.toLowerCase());
    }
    const names = ["懂王", "TACO", "皮夹克", "101", "老钱", "三王", "FAANG", "新循环", "央妈"];
    const hitCount = names.filter((n) => reply.toUpperCase().includes(n.toUpperCase())).length;
    expect(hitCount, `Expected >=2 jargon names in:\n${reply.slice(0, 500)}`).toBeGreaterThanOrEqual(
      2
    );
  });
});
