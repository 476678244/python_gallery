import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testIgnore: ["**/jupyterhub*"],
  timeout: 150_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 1,  // Phase 4: Self-healing - retry once on failure
  reporter: [["list"], ["html", { open: "never" }]],
  // globalTeardown: "./global-teardown.ts",
  use: {
    baseURL: process.env.FRONTEND_URL || "http://localhost:3000",
    trace: "on-first-retry",
    video: "on-first-retry",
    screenshot: "on",
    // HEADED=1 for Flow Coding visual confirmation; default headless for CI/agent
    headless: process.env.HEADED !== "1",
    launchOptions: {
      slowMo: process.env.HEADED === "1" ? 500 : 0,
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
  ],
});
