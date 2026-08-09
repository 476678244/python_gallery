/**
 * @readonly-boss-hire — shared readonly utilities for Boss 直聘 browsing.
 * CONSTRAINT: READONLY ONLY — zero write to zhipin.com
 */

import fs from "fs";
import path from "path";
import type { Page, Route } from "@playwright/test";

export const BOSS_HIRE_WORKDIR =
  process.env.BOSS_HIRE_WORKDIR ??
  "/Users/nicole/Downloads/nicole/boss直聘_工作目录";

export const CDP_URL = process.env.CDP_URL ?? "http://127.0.0.1:9222";

export const ZHIPIN_READONLY_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

export function ensureWorkdirs(): void {
  for (const sub of ["screenshots", "extracts", "reports", "tmp", "logs"]) {
    fs.mkdirSync(path.join(BOSS_HIRE_WORKDIR, sub), { recursive: true });
  }
}

export function sessionStamp(): string {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

/** Block mutating requests to Boss 直聘 domains. */
export async function installZhipinReadonlyGuard(page: Page): Promise<void> {
  await page.route("**/*", (route: Route) => {
    const req = route.request();
    const { method, url } = req;
    const isZhipin = /zhipin\.com|bosszhipin\.com/i.test(url);
    if (isZhipin && !ZHIPIN_READONLY_METHODS.has(method)) {
      route.abort("blockedbyclient");
      return;
    }
    route.continue();
  });
}

export interface DomNodeSummary {
  tag: string;
  id?: string;
  class?: string;
  role?: string;
  name?: string;
  text?: string;
  childCount: number;
  children?: DomNodeSummary[];
}

/** Walk DOM tree in browser; returns compact structure (depth-limited). */
export async function extractDomSummary(
  page: Page,
  maxDepth = 10,
  maxChildren = 40,
): Promise<DomNodeSummary> {
  return page.evaluate(
    ({ maxDepth, maxChildren }) => {
      type NodeOut = {
        tag: string;
        id?: string;
        class?: string;
        role?: string;
        name?: string;
        text?: string;
        childCount: number;
        children?: NodeOut[];
      };

      function summarize(el: Element, depth: number): NodeOut | null {
        if (depth > maxDepth) return null;

        const tag = el.tagName.toLowerCase();
        if (tag === "script" || tag === "style" || tag === "noscript") {
          return null;
        }

        const id = el.id || undefined;
        const cls =
          el.classList.length > 0
            ? Array.from(el.classList).slice(0, 8).join(" ")
            : undefined;
        const role = el.getAttribute("role") ?? undefined;
        const name =
          el.getAttribute("aria-label") ??
          el.getAttribute("title") ??
          undefined;

        const directText = Array.from(el.childNodes)
          .filter((n) => n.nodeType === Node.TEXT_NODE)
          .map((n) => (n.textContent ?? "").trim())
          .filter(Boolean)
          .join(" ")
          .slice(0, 120);

        const childEls = Array.from(el.children).slice(0, maxChildren);
        const children = childEls
          .map((c) => summarize(c, depth + 1))
          .filter((c): c is NodeOut => c !== null);

        const out: NodeOut = {
          tag,
          childCount: el.children.length,
        };
        if (id) out.id = id;
        if (cls) out.class = cls;
        if (role) out.role = role;
        if (name) out.name = name;
        if (directText) out.text = directText;
        if (children.length > 0) out.children = children;
        return out;
      }

      const root = document.documentElement;
      const tree = summarize(root, 0);
      if (!tree) {
        return { tag: "html", childCount: 0 };
      }
      return tree;
    },
    { maxDepth, maxChildren },
  );
}

/** Collect visible text blocks from page. */
export async function extractVisibleText(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const blocks: string[] = [];
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_ELEMENT,
    );
    let node = walker.currentNode as Element | null;
    while (node) {
      const el = node as HTMLElement;
      const style = window.getComputedStyle(el);
      if (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        el.offsetParent !== null
      ) {
        const t = (el.innerText ?? "").trim();
        if (t && t.length >= 2 && t.length <= 500) {
          const lines = t.split("\n").map((l) => l.trim()).filter(Boolean);
          if (lines.length === 1) {
            blocks.push(lines[0]);
          } else if (lines.length <= 6) {
            blocks.push(lines.join(" | "));
          }
        }
      }
      node = walker.nextNode() as Element | null;
    }
    return [...new Set(blocks)].slice(0, 200);
  });
}

export function writeJson(filePath: string, data: unknown): void {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
}

export function writeText(filePath: string, text: string): void {
  fs.writeFileSync(filePath, text, "utf-8");
}

export interface HeadedBrowserSession {
  browser: import("@playwright/test").Browser;
  context: import("@playwright/test").BrowserContext;
  page: import("@playwright/test").Page;
  mode: "cdp" | "launch";
}

/** Fetch CDP ws endpoint bypassing HTTP proxy (avoids 503 on localhost). */
async function resolveCdpEndpoint(): Promise<string> {
  const http = await import("http");
  const versionUrl = `${CDP_URL.replace(/\/$/, "")}/json/version`;

  return new Promise((resolve, reject) => {
    const req = http.get(versionUrl, (res) => {
      let body = "";
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        if (res.statusCode !== 200) {
          reject(
            new Error(
              `[readonly-boss-hire] CDP /json/version returned ${res.statusCode}\n` +
                `  URL: ${versionUrl}\n` +
                `  Hint: start Chrome CDP first:\n` +
                `    ./flow_coding/scripts/start_chrome_cdp.sh --restart`,
            ),
          );
          return;
        }
        try {
          const data = JSON.parse(body) as { webSocketDebuggerUrl?: string };
          if (!data.webSocketDebuggerUrl) {
            reject(new Error("CDP response missing webSocketDebuggerUrl"));
            return;
          }
          resolve(data.webSocketDebuggerUrl);
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on("error", reject);
    req.setTimeout(5000, () => {
      req.destroy(new Error(`CDP timeout: ${versionUrl}`));
    });
  });
}

/** Same page path (ignore query/hash) — avoid redundant goto → refresh. */
export function samePagePath(current: string, target: string): boolean {
  try {
    const a = new URL(current);
    const b = new URL(target);
    return a.origin === b.origin && a.pathname === b.pathname;
  } catch {
    return current === target;
  }
}

/**
 * Navigate only if not already on target path. Single load, no reload loop.
 */
export async function gotoOnce(
  page: import("@playwright/test").Page,
  url: string,
): Promise<boolean> {
  const current = page.url();
  if (samePagePath(current, url)) {
    console.log(`[readonly-boss-hire] already on ${url} — skip goto (no refresh)`);
    await page.bringToFront();
    return false;
  }
  console.log(`[readonly-boss-hire] goto: ${url}`);
  await page.goto(url, { waitUntil: "commit", timeout: 60_000 });
  await page.bringToFront();
  return true;
}

/**
 * Attach to user's Chrome via CDP. Reuses existing zhipin tab when possible
 * (avoids opening yet another tab / navigation).
 */
export async function connectCdpBrowser(options?: {
  exportLogs?: boolean;
}): Promise<HeadedBrowserSession> {
  const { chromium } = await import("@playwright/test");
  const wsEndpoint = await resolveCdpEndpoint();
  const browser = await chromium.connectOverCDP(wsEndpoint);
  const context = browser.contexts()[0] ?? (await browser.newContext());

  const existing = context.pages().find((p) => {
    const u = p.url();
    return /zhipin\.com/i.test(u) && u !== "about:blank";
  });

  const page = existing ?? (await context.newPage());
  if (!existing) {
    await page.setViewportSize({ width: 1920, height: 1080 });
  }

  if (options?.exportLogs !== false) {
    const { installBrowserLogExport } = await import("./browser-log-export");
    installBrowserLogExport(page);
  }

  return { browser, context, page, mode: "cdp" };
}

/**
 * Prefer CDP; optional fallback to Playwright Chromium (requires `npx playwright install`).
 */
export async function connectHeadedBrowser(): Promise<HeadedBrowserSession> {
  try {
    return await connectCdpBrowser();
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.warn(`[readonly-boss-hire] CDP attach failed: ${message}`);
    console.warn("[readonly-boss-hire] Falling back to headed Chromium launch");
  }

  const { chromium } = await import("@playwright/test");
  const browser = await chromium.launch({
    headless: false,
    slowMo: 300,
    args: ["--window-size=1920,1080"],
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();
  return { browser, context, page, mode: "launch" };
}

/** Read zhipin.com cookies from current CDP context (session reuse signal). */
export async function getZhipinCookies(
  context: import("@playwright/test").BrowserContext,
): Promise<{ count: number; names: string[] }> {
  const cookies = await context.cookies("https://www.zhipin.com");
  return {
    count: cookies.length,
    names: cookies.map((c) => c.name).sort(),
  };
}
