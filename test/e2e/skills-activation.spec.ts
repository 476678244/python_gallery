/**
 * Skills Activation — headed gold paths S1–S3
 * Spec: docs/features/skills-activation/e2e.md
 *
 * Requires: API :8000 + UI :3000
 * Run: HEADED=1 npx playwright test skills-activation.spec.ts --retries=0
 */

import { test, expect, Page, APIRequestContext } from "@playwright/test";

const API = process.env.SAFECLAW_API_URL || "http://127.0.0.1:8000";
const SCREENSHOTS = "screenshots";

async function apiJson(request: APIRequestContext, path: string, init?: Parameters<APIRequestContext["fetch"]>[1]) {
  const res = await request.fetch(`${API}${path}`, init);
  const body = await res.json().catch(() => ({}));
  return { res, body };
}

async function enableOnlySkills(request: APIRequestContext, skillNames: string[]) {
  const { res, body } = await apiJson(request, "/skills");
  expect(res.ok(), `GET /skills ${res.status()}`).toBeTruthy();
  const tree = body.tree || [];
  for (const n of tree) {
    if (n.is_folder) {
      const off = await request.fetch(`${API}/skills`, {
        method: "POST",
        data: { folder_id: n.id, enabled: false },
      });
      expect(off.ok()).toBeTruthy();
    }
  }
  for (const name of skillNames) {
    const on = await request.fetch(`${API}/skills`, {
      method: "POST",
      data: { skill_id: name, enabled: true },
    });
    expect(on.ok(), `enable ${name}`).toBeTruthy();
  }
}

async function restoreAllFolders(request: APIRequestContext) {
  const { body } = await apiJson(request, "/skills");
  for (const n of body.tree || []) {
    if (n.is_folder) {
      await request.fetch(`${API}/skills`, {
        method: "POST",
        data: { folder_id: n.id, enabled: true },
      });
    }
  }
}

async function gotoFresh(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => localStorage.removeItem("safeclaw-ui-store"));
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(800);
}

async function ensureSession(page: Page) {
  const textarea = page.locator("textarea").first();
  if (await textarea.isDisabled().catch(() => true)) {
    const newChat = page.getByText("New Chat").first();
    if (await newChat.isVisible().catch(() => false)) {
      await newChat.click();
      await page.waitForTimeout(500);
    }
  }
  await expect(page.locator("textarea").first()).toBeEnabled({ timeout: 15000 });
}

/** Capture skills_loaded from the next /chat/stream response. */
async function captureSkillsLoaded(
  page: Page,
  sendText: string,
): Promise<string[]> {
  const loadedPromise = page.waitForResponse(
    (r) => r.url().includes("/chat/stream") && r.request().method() === "POST",
    { timeout: 120_000 },
  );
  const textarea = page.locator("textarea").first();
  await textarea.fill(sendText);
  await textarea.press("Enter");
  const resp = await loadedPromise;
  const text = await resp.text();
  const names: string[] = [];
  for (const line of text.split("\n")) {
    if (!line.startsWith("data:")) continue;
    try {
      const data = JSON.parse(line.slice(5).trim());
      if (Array.isArray(data.skills_loaded) && data.skills_loaded.length) {
        names.splice(0, names.length, ...data.skills_loaded);
      }
    } catch {
      /* skip */
    }
  }
  return names;
}

test.describe.configure({ mode: "serial" });

test.describe("Skills Activation S1–S3", () => {
  test.afterAll(async ({ request }) => {
    await restoreAllFolders(request).catch(() => undefined);
  });

  test("S1: persist / reload / skills_loaded matches enabled", async ({
    page,
    request,
  }) => {
    const keep = ["flow_coding_testing"];
    // Prefer a second private skill if present
    const { body } = await apiJson(request, "/skills");
    const privateFolder = (body.tree || []).find((n: { id: string }) => n.id === "private");
    const privateNames = (privateFolder?.children || []).map((c: { name: string }) => c.name);
    if (!privateNames.includes("flow_coding_testing")) {
      test.skip(true, "flow_coding_testing not in private skills");
    }
    if (privateNames.length > 1) {
      const other = privateNames.find((n: string) => n !== "flow_coding_testing");
      if (other) keep.push(other);
    }

    await enableOnlySkills(request, keep);

    // Persist check via agent_config is server-side; tree must match after reload
    await gotoFresh(page);
    await ensureSession(page);

    const after = await apiJson(request, "/skills");
    const enabledLeaf = new Set<string>();
    for (const folder of after.body.tree || []) {
      for (const c of folder.children || []) {
        if (c.enabled) enabledLeaf.add(c.name);
      }
    }
    expect([...enabledLeaf].sort()).toEqual([...keep].sort());

    const loaded = await captureSkillsLoaded(
      page,
      "List the skills currently loaded into the agent. Reply with names only.",
    );
    await page.screenshot({
      path: `${SCREENSHOTS}/skills-activation-s1.png`,
      fullPage: true,
    });

    expect(loaded.length, "SSE must include skills_loaded").toBeGreaterThan(0);
    expect([...loaded].sort()).toEqual([...keep].sort());
    for (const name of loaded) {
      expect(name.startsWith("ljg-")).toBeFalsy();
    }
  });

  test("S2: disable Ljg → skills_loaded and tools have no ljg-*", async ({
    page,
    request,
  }) => {
    const { body } = await apiJson(request, "/skills");
    const privateFolder = (body.tree || []).find((n: { id: string }) => n.id === "private");
    const one =
      (privateFolder?.children || []).find((c: { name: string }) => c.name === "flow_coding_testing")
        ?.name || privateFolder?.children?.[0]?.name;
    if (!one) test.skip(true, "need a private skill");

    // Enable private only + ensure Ljg off
    await enableOnlySkills(request, [one]);
    const ljgOff = await request.fetch(`${API}/skills`, {
      method: "POST",
      data: { folder_id: "linked/ljg-skills", enabled: false },
    });
    // folder may already be off from enableOnlySkills
    expect([200, 404].includes(ljgOff.status())).toBeTruthy();

    await gotoFresh(page);
    await ensureSession(page);

    const loaded = await captureSkillsLoaded(
      page,
      "Does the agent have ljg-roundtable loaded? Answer yes or no, then list loaded skill names.",
    );
    await page.screenshot({
      path: `${SCREENSHOTS}/skills-activation-s2.png`,
      fullPage: true,
    });

    expect(loaded.length).toBeGreaterThan(0);
    expect(loaded.every((n) => !n.startsWith("ljg-"))).toBeTruthy();
    expect(loaded).toContain(one);
  });

  test("S3: slash skill autocomplete respects enabled allowlist", async ({
    page,
    request,
  }) => {
    const skill = "flow_coding_testing";
    const { body } = await apiJson(request, "/skills");
    const names = new Set<string>();
    for (const f of body.tree || []) {
      for (const c of f.children || []) names.add(c.name);
    }
    if (!names.has(skill)) test.skip(true, `${skill} missing`);

    await enableOnlySkills(request, [skill]);
    await gotoFresh(page);
    await ensureSession(page);

    const textarea = page.locator("textarea").first();
    await textarea.fill("/skill");
    await page.waitForTimeout(600);

    // Autocomplete should show the enabled skill; ljg should be absent when disabled
    const menu = page.locator('[role="listbox"], [cmdk-list], .skill-autocomplete, div').filter({
      hasText: skill,
    }).first();
    await expect(menu).toBeVisible({ timeout: 8000 });

    // Disable skill → should disappear from suggestions
    await request.fetch(`${API}/skills`, {
      method: "POST",
      data: { skill_id: skill, enabled: false },
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    await ensureSession(page);
    await page.locator("textarea").first().fill("/skill");
    await page.waitForTimeout(800);
    const still = page.getByText(skill, { exact: false }).first();
    // May still appear in Skill Tree label; prefer that autocomplete popup is empty/gone
    const popupItems = page.locator("[cmdk-item], [role='option']");
    const count = await popupItems.count();
    if (count > 0) {
      const texts = await popupItems.allTextContents();
      expect(texts.some((t) => t.includes(skill))).toBeFalsy();
    } else {
      // no popup is acceptable when nothing enabled
      expect(count).toBe(0);
    }

    await page.screenshot({
      path: `${SCREENSHOTS}/skills-activation-s3.png`,
      fullPage: true,
    });
  });
});
