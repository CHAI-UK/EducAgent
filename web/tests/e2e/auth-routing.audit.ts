import { test, expect } from "@playwright/test";

// Auth cookie name — must match AUTH_TOKEN_KEY in web/lib/auth-constants.ts
const AUTH_COOKIE = "educagent_access_token";

// Resolve hostname dynamically so tests work on localhost and staging alike
const BASE_HOSTNAME = new URL(
  process.env.WEB_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE ||
    "http://localhost:3000",
).hostname;

test.describe("Auth :: Middleware routing (Story 1.4)", () => {
  // ── AC1 ──────────────────────────────────────────────────────────────────
  // Unauthenticated user hitting a protected route is redirected to
  // /login?redirect={originalPath} with no cookie present.
  test("AC1: unauthenticated access to / redirects to /login?redirect=/", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/login\?redirect=%2F/);
  });

  test("AC1: unauthenticated access to /study redirects to /login?redirect=/study", async ({
    page,
  }) => {
    await page.goto("/study");

    await expect(page).toHaveURL(/\/login\?redirect=%2Fstudy/);
  });

  test("AC1: unauthenticated access to /settings redirects to /login?redirect=/settings", async ({
    page,
  }) => {
    await page.goto("/settings");

    await expect(page).toHaveURL(/\/login\?redirect=%2Fsettings/);
  });

  // ── AC2 ──────────────────────────────────────────────────────────────────
  // After login from /login?redirect=/study the user lands on /study.
  // We mock the backend login endpoint and set the cookie manually to
  // simulate what the login page does, then verify the redirect param is used.
  test("AC2: login page redirects to ?redirect= target after successful login", async ({
    page,
  }) => {
    // Mock the FastAPI-Users login endpoint
    await page.route("**/auth/jwt/login", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          access_token: "fake-test-token",
          token_type: "bearer",
        }),
      }),
    );

    await page.goto("/login?redirect=/study");

    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    // After login the page sets localStorage + cookie then router.push('/study').
    // Middleware will then see the cookie and allow /study through.
    await expect(page).toHaveURL(/\/study/);
  });

  // ── AC3 (server-side — no FOUC) ──────────────────────────────────────────
  // Middleware fires before HTML is served, so protected routes return a
  // redirect response (HTTP 3xx) rather than rendering the page first.
  // Playwright follows redirects by default; we verify we land on /login
  // without any intermediate page flash.
  test("AC3: redirect response comes from server (no intermediate page render)", async ({
    page,
  }) => {
    let redirectedFromServer = false;

    page.on("response", (response) => {
      if (
        response.url().includes("/settings") &&
        response.status() >= 300 &&
        response.status() < 400
      ) {
        redirectedFromServer = true;
      }
    });

    await page.goto("/settings");

    expect(redirectedFromServer).toBe(true);
    await expect(page).toHaveURL(/\/login/);
  });

  // ── AC4 ──────────────────────────────────────────────────────────────────
  // /login and /signup are always accessible without auth.
  test("AC4: /login is accessible without authentication", async ({ page }) => {
    await page.goto("/login");

    // Should NOT be redirected elsewhere — the login form is visible
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("AC4: /signup is accessible without authentication", async ({
    page,
  }) => {
    await page.goto("/signup");

    await expect(page).toHaveURL(/\/signup/);
    await expect(
      page.getByRole("button", { name: "Create account" }),
    ).toBeVisible();
  });

  // AC4: authenticated users are redirected away from /login and /signup.
  // The cookie is set so middleware fires the redirect server-side.
  test("AC4: authenticated user visiting /login is redirected home by middleware", async ({
    context,
    page,
  }) => {
    await context.addCookies([
      {
        name: AUTH_COOKIE,
        value: "fake-test-token",
        domain: BASE_HOSTNAME,
        path: "/",
        sameSite: "Lax",
      },
    ]);

    await page.goto("/login");

    await expect(page).toHaveURL(/^[^?]*\/$/);
  });

  test("AC4: authenticated user visiting /signup is redirected home by middleware", async ({
    context,
    page,
  }) => {
    await context.addCookies([
      {
        name: AUTH_COOKIE,
        value: "fake-test-token",
        domain: BASE_HOSTNAME,
        path: "/",
        sameSite: "Lax",
      },
    ]);

    await page.goto("/signup");

    await expect(page).toHaveURL(/^[^?]*\/$/);
  });
});
