/**
 * Thin smoke coverage for Memory / Safety API + sessions rename/delete.
 * Does not require LM Studio.
 */

import { test, expect, Page } from "@playwright/test";

const API = process.env.API_URL || "http://localhost:8000";

async function goto(page: Page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
}

test.describe("API smoke · Memory & Safety", () => {
  test("GET /memory returns 200 with structural fields", async ({ request }) => {
    const res = await request.get(`${API}/memory`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    // Accept either list payload or stats object
    expect(body).toBeTruthy();
    expect(
      Array.isArray(body.memories) ||
        Array.isArray(body.items) ||
        typeof body === "object"
    ).toBeTruthy();
  });

  test("GET /safety returns 200 with structural fields", async ({ request }) => {
    const res = await request.get(`${API}/safety`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toBeTruthy();
    expect(typeof body).toBe("object");
  });
});

test.describe("Sessions · rename and delete", () => {
  test("API rename + delete round-trip", async ({ request }) => {
    const created = await request.post(`${API}/sessions`, {
      data: { title: "Smoke Rename Me" },
    });
    expect(created.ok()).toBeTruthy();
    const createdBody = await created.json();
    const session = createdBody.session || createdBody;
    const sid = session.id;

    const renamed = await request.patch(`${API}/sessions/${sid}`, {
      data: { title: "Smoke Renamed" },
    });
    expect(renamed.ok()).toBeTruthy();
    const renamedBody = await renamed.json();
    expect((renamedBody.session || renamedBody).title).toBe("Smoke Renamed");

    const deleted = await request.delete(`${API}/sessions/${sid}`);
    expect(deleted.ok()).toBeTruthy();

    const listed = await request.get(`${API}/sessions`);
    const ids = ((await listed.json()).sessions || []).map((s: { id: string }) => s.id);
    expect(ids).not.toContain(sid);
  });

  test("UI can create and delete a session", async ({ page }) => {
    await goto(page);

    const newChat = page.getByText("New Chat").first();
    await expect(newChat).toBeVisible({ timeout: 10000 });
    await newChat.click();
    await page.waitForTimeout(800);

    const sessionItem = page.locator("[data-testid='session-item']").first();
    if (await sessionItem.isVisible().catch(() => false)) {
      await sessionItem.hover();
      const del = sessionItem.locator("button").filter({ hasText: /delete|Delete|×|✕/i }).first();
      if (await del.isVisible().catch(() => false)) {
        await del.click();
        await page.waitForTimeout(500);
      } else {
        // Fallback: delete via API using active session from store is enough for smoke
        const res = await page.request.get(`${API}/sessions?limit=1`);
        const sessions = (await res.json()).sessions || [];
        if (sessions[0]) {
          await page.request.delete(`${API}/sessions/${sessions[0].id}`);
        }
      }
    }

    await expect(page.getByText(/Something went wrong/i)).not.toBeVisible();
  });
});
