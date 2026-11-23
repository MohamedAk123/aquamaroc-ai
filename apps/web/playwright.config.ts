import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], locale: "fr-FR" } },
    {
      name: "mobile",
      use: {
        ...devices["iPhone 13"],
        viewport: { width: 360, height: 780 },
        deviceScaleFactor: 1,
        defaultBrowserType: "chromium",
        locale: "fr-FR",
      },
    },
  ],
  webServer: process.env.E2E_EXTERNAL_SERVER
    ? undefined
    : [
        {
          command: `"${process.env.E2E_PYTHON ?? "python"}" -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000`,
          cwd: path.resolve(__dirname, "../.."),
          url: "http://127.0.0.1:8000/ready",
          reuseExistingServer: !process.env.CI,
        },
        {
          command: "npm run start",
          url: "http://127.0.0.1:3000",
          reuseExistingServer: !process.env.CI,
        },
      ],
});
