import { defineConfig, devices } from "@playwright/test";

const FRONTEND_PORT = 5274;
const BACKEND_PORT = 8100;
const FRONTEND_URL = `http://127.0.0.1:${FRONTEND_PORT}`;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

// Os testes usam uma API e um banco próprios. O comando do backend recria o
// SQLite descartável em data/e2e/ antes de subir, então nada toca no banco de
// desenvolvimento.
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: FRONTEND_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: ".\\.venv\\Scripts\\python.exe backend\\scripts\\serve_e2e.py",
      cwd: "..",
      url: `${BACKEND_URL}/api/health`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort`,
      url: FRONTEND_URL,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        VITE_API_PROXY_TARGET: BACKEND_URL,
      },
    },
  ],
});
