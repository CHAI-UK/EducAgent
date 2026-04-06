import { test, expect } from "@playwright/test";
import { AUTH_TOKEN_KEY } from "../../lib/api";

// baseURL is configured centrally in playwright.config.ts (WEB_BASE_URL env var,
// defaulting to http://localhost:3782). All page.goto() calls use relative paths.
const BASE_HOSTNAME = new URL(
  process.env.WEB_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE ||
    "http://localhost:3782",
).hostname;

test.describe("Auth :: Login UX and session behavior", () => {
  test("AC1: successful login with ?redirect= param redirects to target", async ({
    page,
  }) => {
    await page.route("**/auth/jwt/login", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          access_token: "fake-token-ac1",
          token_type: "bearer",
        }),
      }),
    );
    await page.route("**/api/v1/profile", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "user@example.com",
          username: "user",
          first_name: "Test",
          last_name: "User",
          institution: null,
          avatar_url: null,
          is_active: true,
          is_superuser: false,
          is_verified: true,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          learner_profile: {
            id: "00000000-0000-0000-0000-000000000002",
            background: "Scientist",
            role: "Researcher",
            prior_knowledge: ["machine_learning"],
            expertise_level: "knows_correlation_confounding",
            learning_goal: "Learn causality",
            is_skipped: false,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        }),
      }),
    );

    await page.goto("/login?redirect=%2F");

    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    // Should redirect to "/" (the decoded redirect target)
    await expect(page).toHaveURL(/\/$/, { timeout: 5000 });
  });

  test("AC1b: successful login without ?redirect= param redirects to home", async ({
    page,
  }) => {
    await page.route("**/auth/jwt/login", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          access_token: "fake-token-ac1b",
          token_type: "bearer",
        }),
      }),
    );
    await page.route("**/api/v1/profile", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "user@example.com",
          username: "user",
          first_name: "Test",
          last_name: "User",
          institution: null,
          avatar_url: null,
          is_active: true,
          is_superuser: false,
          is_verified: true,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          learner_profile: {
            id: "00000000-0000-0000-0000-000000000002",
            background: "Scientist",
            role: "Researcher",
            prior_knowledge: ["machine_learning"],
            expertise_level: "knows_correlation_confounding",
            learning_goal: "Learn causality",
            is_skipped: false,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        }),
      }),
    );

    await page.goto("/login");

    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/$/, { timeout: 5000 });
  });

  test("first-time login redirects to learner onboarding", async ({ page }) => {
    await page.route("**/auth/jwt/login", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          access_token: "fake-token-new-user",
          token_type: "bearer",
        }),
      }),
    );
    await page.route("**/api/v1/profile", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "new@example.com",
          username: "new-user",
          first_name: null,
          last_name: null,
          institution: null,
          avatar_url: null,
          is_active: true,
          is_superuser: false,
          is_verified: true,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          learner_profile: null,
        }),
      }),
    );

    await page.goto("/login?redirect=/study");

    await page.getByLabel("Email").fill("new@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/onboarding\/learner$/, { timeout: 5000 });
  });

  test("AC3: authenticated user navigating to /login is redirected home", async ({
    context,
    page,
  }) => {
    await context.addCookies([
      {
        name: AUTH_TOKEN_KEY,
        value: "fake-token",
        domain: BASE_HOSTNAME,
        path: "/",
        sameSite: "Lax",
      },
    ]);

    await page.goto("/login");

    await expect(page).toHaveURL(/^[^?]*\/$/);
  });

  test("AC3b: stale localStorage token without auth cookie does not loop away from /login", async ({
    page,
  }) => {
    await page.addInitScript((tokenKey: string) => {
      window.localStorage.setItem(tokenKey, "stale-token");
    }, AUTH_TOKEN_KEY);

    await page.goto("/login?redirect=%2F");

    await expect(page).toHaveURL(/\/login\?redirect=%2F/);
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("AC4: /login?session_expired=1 shows session-expired banner", async ({
    page,
  }) => {
    await page.goto("/login?session_expired=1");

    await expect(
      page.getByText("Session expired, please log in again."),
    ).toBeVisible();
  });

  test("AC2: invalid credentials show generic error message", async ({
    page,
  }) => {
    await page.route("**/auth/jwt/login", (route) =>
      route.fulfill({
        status: 400,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ detail: "LOGIN_BAD_CREDENTIALS" }),
      }),
    );

    await page.goto("/login");

    await page.getByLabel("Email").fill("someone@example.com");
    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByRole("alert")).toContainText(
      "Invalid email or password",
    );
  });
});
