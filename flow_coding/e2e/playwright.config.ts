import { defineConfig, devices } from "@playwright/test";

/**
 * Flow Coding standard Playwright config.
 * Copy this scaffold to <project>/test/e2e/ and adjust baseURL.
 *
 * Conventions:
 * - TS only (*.spec.ts), no Python test scripts
 * - viewport 1920×1080 for reproducible screenshot baselines
 * - headless: false + slowMo for visual confirmation
 * - retries: 1 for Phase 4 self-healing
 */
export default defineConfig({
  testDir: ".",
  timeout: 150_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.FRONTEND_URL || "http://localhost:3000",
    trace: "on-first-retry",
    video: "on-first-retry",
    screenshot: "on",
    headless: false,
    launchOptions: {
      slowMo: 500,
    },
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1920, height: 1080 },
      },
    },
    // readonly-boss-hire: 可复用工作脚本（非回归测试）
    // - retries: 0 — 一次执行，产物落盘 BOSS_HIRE_WORKDIR
    // - 成功标准：screenshots/extracts/reports/logs，非 runner 全绿
    {
      name: "readonly-boss-hire",
      testMatch: /readonly_boss_hire\/.*\.spec\.ts/,
      retries: 0,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1920, height: 1080 },
        headless: false,
        screenshot: "off",
        launchOptions: {
          slowMo: 0,
        },
      },
    },
  ],
});
