import { defineConfig, devices } from "@playwright/test";

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
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
