import { defineConfig, devices } from "@playwright/test"

const isCI = !!process.env.CI
const baseURL = process.env.BASE_URL ?? "http://localhost:5175"

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  reporter: isCI ? "github" : "html",

  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },

  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
    actionTimeout: 5_000,
    navigationTimeout: isCI ? 30_000 : 10_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    command: "pnpm dev",
    url: baseURL,
    reuseExistingServer: !isCI,
    timeout: 60_000,
  },
})
