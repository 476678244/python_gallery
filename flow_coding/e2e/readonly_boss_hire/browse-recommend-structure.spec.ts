// @readonly-boss-hire
// WORKFLOW SCRIPT — 可复用工作脚本，非回归测试
// CONSTRAINT: Boss 直聘 READONLY ONLY — 零 write
// Browse https://www.zhipin.com/web/chat/recommend — screenshot, text, DOM summary
// 成功标准：产物落盘 BOSS_HIRE_WORKDIR

import { test, expect } from "@playwright/test";
import path from "path";
import {
  BOSS_HIRE_WORKDIR,
  ensureWorkdirs,
  extractDomSummary,
  extractVisibleText,
  installZhipinReadonlyGuard,
  connectCdpBrowser,
  gotoOnce,
  sessionStamp,
  writeJson,
  writeText,
} from "./helpers/readonly-guard";

const TARGET_URL = "https://www.zhipin.com/web/chat/recommend";

test.use({ headless: false });

test.describe.configure({ mode: "serial", retries: 0 });

test.describe("readonly: recommend page structure", () => {
  test.beforeAll(() => {
    ensureWorkdirs();
  });

  test("browse recommend — screenshot, text, dom", async () => {
    const stamp = sessionStamp();
    const outBase = `recommend-${stamp}`;
    const screenshotPath = path.join(
      BOSS_HIRE_WORKDIR,
      "screenshots",
      `${outBase}.png`,
    );
    const screenshotFullPath = path.join(
      BOSS_HIRE_WORKDIR,
      "screenshots",
      `${outBase}-full.png`,
    );
    const textPath = path.join(
      BOSS_HIRE_WORKDIR,
      "extracts",
      `${outBase}-text.txt`,
    );
    const domPath = path.join(
      BOSS_HIRE_WORKDIR,
      "extracts",
      `${outBase}-dom.json`,
    );
    const htmlPath = path.join(
      BOSS_HIRE_WORKDIR,
      "extracts",
      `${outBase}-dom.html`,
    );
    const reportPath = path.join(
      BOSS_HIRE_WORKDIR,
      "reports",
      `${outBase}-structure.md`,
    );

    // Headed browser: CDP Chrome (preferred) or launch headless: false
    const { page, mode } = await connectCdpBrowser();
    console.log(`[readonly-boss-hire] Browser mode: ${mode} (headed)`);

    await installZhipinReadonlyGuard(page);
    await gotoOnce(page, TARGET_URL);

    // Single short settle — no networkidle (SPA polling looks like refresh)
    await page.waitForTimeout(5000);

    const title = await page.title();
    const url = page.url();

    // Screenshots (readonly)
    await page.screenshot({ path: screenshotPath, fullPage: false });
    await page.screenshot({ path: screenshotFullPath, fullPage: true });

    // Visible text blocks
    const textBlocks = await extractVisibleText(page);
    const bodyText = ((await page.locator("body").innerText()) ?? "").trim();
    writeText(
      textPath,
      [
        `URL: ${url}`,
        `Title: ${title}`,
        `Captured: ${new Date().toISOString()}`,
        "",
        "=== body.innerText ===",
        bodyText.slice(0, 50_000),
        "",
        "=== visible text blocks ===",
        ...textBlocks.map((b, i) => `${i + 1}. ${b}`),
      ].join("\n"),
    );

    // DOM summary (compact JSON tree)
    const domSummary = await extractDomSummary(page);
    writeJson(domPath, {
      url,
      title,
      capturedAt: new Date().toISOString(),
      viewport: { width: 1920, height: 1080 },
      root: domSummary,
    });

    // Raw HTML snapshot (truncated if huge)
    const html = await page.content();
    const htmlOut =
      html.length > 500_000
        ? html.slice(0, 500_000) + "\n<!-- truncated -->"
        : html;
    writeText(htmlPath, htmlOut);

    // Markdown report
    const topTags = countTags(domSummary);
    writeText(
      reportPath,
      [
        `# Boss 直聘 Recommend 页面结构探查`,
        "",
        `- **URL**: ${url}`,
        `- **Title**: ${title}`,
        `- **Captured**: ${new Date().toISOString()}`,
        `- **Mode**: READONLY ONLY | headed (${mode})`,
        "",
        "## 输出文件",
        "",
        `| 类型 | 路径 |`,
        `|------|------|`,
        `| 截图 (viewport) | \`${screenshotPath}\` |`,
        `| 截图 (full) | \`${screenshotFullPath}\` |`,
        `| 文本 | \`${textPath}\` |`,
        `| DOM 树 (JSON) | \`${domPath}\` |`,
        `| DOM HTML | \`${htmlPath}\` |`,
        "",
        "## 页面文本预览（前 30 条）",
        "",
        ...textBlocks.slice(0, 30).map((b) => `- ${b}`),
        "",
        "## DOM 标签统计（摘要树）",
        "",
        ...Object.entries(topTags)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 20)
          .map(([tag, n]) => `- \`${tag}\`: ${n}`),
        "",
        "## 根节点摘要",
        "",
        "```json",
        JSON.stringify(domSummary, null, 2).slice(0, 4000),
        "```",
      ].join("\n"),
    );

    // Basic sanity — page loaded something
    await expect(page.locator("body")).toBeVisible();

    console.log(`[readonly-boss-hire] Report: ${reportPath}`);
    console.log(`[readonly-boss-hire] Screenshot: ${screenshotPath}`);

    // Do not close browser — CDP session is user's Chrome
  });
});

function countTags(
  node: { tag: string; children?: { tag: string; children?: unknown[] }[] },
  acc: Record<string, number> = {},
): Record<string, number> {
  acc[node.tag] = (acc[node.tag] ?? 0) + 1;
  for (const child of node.children ?? []) {
    countTags(child as typeof node, acc);
  }
  return acc;
}
