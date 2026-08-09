// @readonly-boss-hire
// WORKFLOW SCRIPT — 打开 URL 驻留，非回归测试
// 打开一次 → 等待 → browser logs 落盘 BOSS_HIRE_WORKDIR/logs/

import { test } from "@playwright/test";
import { connectCdpBrowser, gotoOnce } from "./helpers/readonly-guard";

// Stable URL (no _security_check — that token expires and triggers refresh loops)
const TARGET_URL =
  process.env.BOSS_TARGET_URL ?? "https://www.zhipin.com/web/geek/jobs";

const WAIT_MS = 30 * 60 * 1000;

test.use({ headless: false });
test.describe.configure({ retries: 0, mode: "serial" });
test.setTimeout(WAIT_MS + 60_000);

test("idle: open geek/jobs once and wait", async () => {
  const { page, mode } = await connectCdpBrowser();

  console.log(`[idle-wait] browser: ${mode}`);
  console.log(`[idle-wait] target: ${TARGET_URL}`);

  await gotoOnce(page, TARGET_URL);

  console.log(`[idle-wait] settled — waiting ${WAIT_MS / 60_000} min, no further navigation`);
  console.log("[idle-wait] Ctrl+C to stop");

  await page.waitForTimeout(WAIT_MS);
});
