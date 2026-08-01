/**
 * DeepSeek live E2E — real LLM chat + memory recall.
 *
 * Requires:
 *   - UI :3000, API :8000
 *   - DeepSeek API key configured (GET /settings/deepseek → configured:true)
 *
 * Skip: set SAFECLAW_E2E_SKIP_DEEPSEEK=1, or when key is missing.
 */

import { test, expect, Page, APIRequestContext } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";
const MODEL = process.env.SAFECLAW_E2E_DEEPSEEK_MODEL || "deepseek-v4-flash";

const FALLBACK_MARKERS = [
  "fallback mode",
  "LLM service is currently unavailable",
  "LLM service is temporarily unavailable",
];

async function deepseekReady(request: APIRequestContext): Promise<boolean> {
  if (process.env.SAFECLAW_E2E_SKIP_DEEPSEEK === "1") return false;
  const res = await request.get(`${API}/settings/deepseek`);
  if (!res.ok()) return false;
  const body = await res.json();
  return Boolean(body.configured);
}

async function selectDeepSeek(request: APIRequestContext) {
  const res = await request.put(`${API}/settings/model`, {
    data: { model: MODEL },
  });
  expect(res.ok(), `PUT /settings/model failed: ${res.status()}`).toBeTruthy();
  const got = await request.get(`${API}/settings/model`);
  const body = await got.json();
  expect(body.model).toBe(MODEL);
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

async function sendAndWaitAssistant(
  page: Page,
  message: string,
  timeout = 90_000
): Promise<string> {
  const textarea = page.locator("textarea").first();
  await textarea.click();
  await textarea.fill(message);
  const before = await page.locator("[data-role='assistant']").count();
  await page.keyboard.press("Enter");

  await expect(page.locator("[data-role='assistant']")).toHaveCount(before + 1, {
    timeout,
  });

  // Wait until streaming settles (content length stable)
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

function assertNotFallback(text: string) {
  const lower = text.toLowerCase();
  for (const marker of FALLBACK_MARKERS) {
    expect(lower, `Got fallback response:\n${text.slice(0, 300)}`).not.toContain(
      marker.toLowerCase()
    );
  }
  expect(text.length).toBeGreaterThan(0);
}

test.describe("DeepSeek live chat + memory", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await deepseekReady(request)), "DeepSeek API key not configured");
    await selectDeepSeek(request);
  });

  test("basic chat returns a real DeepSeek reply (not fallback)", async ({
    page,
  }) => {
    await waitForApp(page);
    await ensureSession(page);

    const reply = await sendAndWaitAssistant(
      page,
      "Reply with exactly one word: PONG"
    );
    assertNotFallback(reply);
    expect(reply.toUpperCase()).toContain("PONG");
  });

  test("memory: remember fact then recall in a later turn", async ({
    page,
    request,
  }) => {
    const codename = `NEBULA-${Date.now().toString(36).toUpperCase()}`;

    await waitForApp(page);
    await ensureSession(page);

    // Explicit long-term write via slash (deterministic)
    const textarea = page.locator("textarea").first();
    await textarea.click();
    await textarea.fill(
      `/remember The user's secret project codename is ${codename}. Always recall it when asked.`
    );
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("slash-notice")).toHaveText(/Remembered/i, {
      timeout: 10000,
    });

    const listed = await request.get(
      `${API}/memory?search=${encodeURIComponent(codename)}&limit=5`
    );
    expect(listed.ok()).toBeTruthy();
    const memBody = await listed.json();
    expect(memBody.total).toBeGreaterThanOrEqual(1);
    expect(
      (memBody.memories || []).some((m: { content?: string }) =>
        (m.content || "").toUpperCase().includes(codename)
      )
    ).toBeTruthy();

    // Include unique token in the question so retrieval ranks this memory above
    // older NEBULA-* leftovers from prior runs.
    const reply = await sendAndWaitAssistant(
      page,
      `I just /remember-ed a secret project codename that contains exactly "${codename}". ` +
        `What is that full codename? Reply with the codename only.`
    );
    assertNotFallback(reply);
    expect(reply.toUpperCase()).toContain(codename);
  });
});
