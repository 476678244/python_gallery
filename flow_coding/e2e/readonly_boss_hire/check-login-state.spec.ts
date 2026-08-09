// @readonly-boss-hire
// WORKFLOW SCRIPT — 登录态探查，非回归测试
// Verify: CDP Chrome 是否复用日常 Chrome 的 Boss 登录态
// 产出：reports/login-check-*-{OK,STOP}.* — STOP 是有效输出，非测试失败

import { test, expect } from "@playwright/test";
import path from "path";
import {
  BOSS_HIRE_WORKDIR,
  CDP_URL,
  connectCdpBrowser,
  gotoOnce,
  ensureWorkdirs,
  getZhipinCookies,
  sessionStamp,
  writeJson,
  writeText,
} from "./helpers/readonly-guard";

const TARGET_URL = "https://www.zhipin.com/web/chat/recommend";

test.use({ headless: false });
test.describe.configure({ retries: 0 });

async function detectLoggedIn(page: import("@playwright/test").Page) {
  const bodyText = (await page.locator("body").innerText()) ?? "";
  const url = page.url();
  const greetCount = await page.getByText("打招呼").count();

  return {
    bodyText,
    url,
    greetCount,
    stillLoading: /^加载中/.test(bodyText.trim()),
    onRecommendUrl: /zhipin\.com\/web\/chat\/recommend/.test(url),
    hasRecommendNav: bodyText.includes("推荐牛人"),
    hasGreetButton: greetCount > 0,
    hasUserBar: /VIP|招聘规范|我的客服/.test(bodyText),
    redirectedToLogin:
      /login|signin|passport/.test(url) ||
      /扫码登录|请登录|登录\/注册/.test(bodyText),
  };
}

test("open /web/chat/recommend — stop if no login, screenshot if yes", async () => {
  ensureWorkdirs();
  const stamp = sessionStamp();

  // ── Step 0: CDP must be available ──
  const { page, context, mode } = await connectCdpBrowser();
  if (mode !== "cdp") {
    writeText(
      path.join(BOSS_HIRE_WORKDIR, "reports", `login-check-${stamp}-STOP.md`),
      `# STOP\n\nCDP Chrome not available. Start with:\n\`./flow_coding/scripts/start_chrome_cdp.sh --restart\`\n`,
    );
    expect(mode, "Must use CDP Chrome to reuse login profile").toBe("cdp");
    return;
  }

  const cookiesBefore = await getZhipinCookies(context);
  if (cookiesBefore.count === 0) {
    writeText(
      path.join(BOSS_HIRE_WORKDIR, "reports", `login-check-${stamp}-STOP.md`),
      [
        `# STOP — 无登录 Cookie`,
        "",
        "CDP Chrome 已连接，但 zhipin.com 无 cookie。",
        "请先在 CDP Chrome 中手动登录 Boss 直聘，或执行：",
        "`./flow_coding/scripts/start_chrome_cdp.sh --restart` 同步最新 profile。",
      ].join("\n"),
    );
    expect(
      cookiesBefore.count,
      "zhipin.com cookies required for login reuse",
    ).toBeGreaterThan(0);
    return;
  }

  // NOTE: no route guard — SPA needs API; login test only checks session reuse
  await gotoOnce(page, TARGET_URL);

  // ── Step 2: Wait for logged-in UI (max 60s) ──
  let state = await detectLoggedIn(page);
  for (let i = 0; i < 24 && !state.hasGreetButton && !state.hasRecommendNav; i++) {
    if (state.redirectedToLogin) break;
    await page.waitForTimeout(2500);
    state = await detectLoggedIn(page);
  }

  const cookiesAfter = await getZhipinCookies(context);
  const loggedIn =
    !state.redirectedToLogin &&
    state.onRecommendUrl &&
    (state.hasGreetButton || state.hasRecommendNav || state.hasUserBar);

  // ── Step 3: STOP if cannot reuse login ──
  if (!loggedIn) {
    const stopReport = path.join(
      BOSS_HIRE_WORKDIR,
      "reports",
      `login-check-${stamp}-STOP.md`,
    );
    writeText(
      stopReport,
      [
        `# STOP — 无法重用登录态`,
        "",
        `- **Target**: ${TARGET_URL}`,
        `- **CDP**: ${CDP_URL}`,
        `- **zhipin cookies**: ${cookiesAfter.count}`,
        `- **final URL**: ${state.url}`,
        `- **stillLoading**: ${state.stillLoading}`,
        `- **redirectedToLogin**: ${state.redirectedToLogin}`,
        "",
        "## Body",
        "",
        "```",
        state.bodyText.slice(0, 2000),
        "```",
        "",
        "## 建议",
        "",
        "1. 在 CDP Chrome 中手动打开 Boss 直聘确认已登录",
        "2. 重新同步 profile：`./flow_coding/scripts/start_chrome_cdp.sh --restart`",
        "3. 确认 Chrome-CDP 与日常 Chrome 登录态一致",
      ].join("\n"),
    );
    writeJson(path.join(BOSS_HIRE_WORKDIR, "reports", `login-check-${stamp}-STOP.json`), {
      loggedIn: false,
      stopped: true,
      mode,
      cookiesAfter,
      state: {
        url: state.url,
        stillLoading: state.stillLoading,
        redirectedToLogin: state.redirectedToLogin,
        hasRecommendNav: state.hasRecommendNav,
        hasGreetButton: state.hasGreetButton,
        hasUserBar: state.hasUserBar,
      },
    });
    console.log(`[login-check] STOP — cannot reuse login. Report: ${stopReport}`);
    test.skip(true, `Login NOT reusable — see ${stopReport}`);
    return;
  }

  // ── Step 4: Logged in — screenshot as proof ──
  const proofPath = path.join(
    BOSS_HIRE_WORKDIR,
    "screenshots",
    `login-proof-${stamp}.png`,
  );
  await page.screenshot({ path: proofPath, fullPage: false });

  const okReport = path.join(
    BOSS_HIRE_WORKDIR,
    "reports",
    `login-check-${stamp}-OK.md`,
  );
  writeText(
    okReport,
    [
      `# ✅ 登录态可重用`,
      "",
      `- **Target**: ${TARGET_URL}`,
      `- **URL**: ${state.url}`,
      `- **zhipin cookies**: ${cookiesAfter.count}`,
      `- **推荐牛人**: ${state.hasRecommendNav}`,
      `- **打招呼按钮数**: ${state.greetCount}`,
      "",
      `**截图证明**: \`${proofPath}\``,
    ].join("\n"),
  );

  console.log(`[login-check] OK — login reused. Proof: ${proofPath}`);
  expect(loggedIn).toBe(true);
});
