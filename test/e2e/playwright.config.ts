import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 150_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 1,  // Phase 4: Self-healing - retry once on failure
  reporter: [["list"], ["html", { open: "never" }]],
  // globalTeardown: "./global-teardown.ts",
  use: {
    baseURL: process.env.FRONTEND_URL || "http://localhost:3000",
    trace: "on-first-retry",
    video: "on-first-retry",
    screenshot: "on",
    headless: false,  // Show browser window for visual confirmation
    launchOptions: {
      slowMo: 500,  // Slow down operations for better visibility
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
