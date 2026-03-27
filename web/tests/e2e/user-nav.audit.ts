import { test, expect } from "@playwright/test";
import { AUTH_TOKEN_KEY } from "../../lib/api";

// Helper: inject a fake auth token into localStorage + cookie so middleware
// allows the request through and UserNav can fetch /api/v1/profile.
async function setAuthToken(page: import("@playwright/test").Page) {
  const fakeToken = "fake-jwt-token";

  // Mock GET /api/v1/profile to return a test user
  await page.route("**/api/v1/profile", (route) =>
    route.fulfill({
      status: 200,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        id: "00000000-0000-0000-0000-000000000001",
        email: "test@example.com",
        username: "testuser",
        first_name: null,
        last_name: null,
        institution: null,
        avatar_url: null,
        is_active: true,
        is_superuser: false,
        is_verified: true,
        created_at: "2026-01-01T00:00:00Z",
      }),
    }),
  );

  // Inject token into localStorage before page scripts run
  // Single-string arg pattern matches Playwright's PageFunction<string, any> signature
  await page.addInitScript((tokenKey: string) => {
    window.localStorage.setItem(tokenKey, "fake-jwt-token");
  }, AUTH_TOKEN_KEY);

  // Also set the auth cookie so Next.js middleware allows the route
  await page.context().addCookies([
    {
      name: AUTH_TOKEN_KEY,
      value: fakeToken,
      domain: "localhost",
      path: "/",
      sameSite: "Lax",
    },
  ]);
}

test.describe("UserNav :: Avatar and username in nav bar (Story 1.5)", () => {
  // ── AC1 ────────────────────────────────────────────────────────────────────
  // Authenticated user sees circular avatar + username in top-right corner.
  test("AC1: shows avatar initial and username for authenticated user", async ({
    page,
  }) => {
    await setAuthToken(page);
    await page.goto("/");

    // Avatar button should be visible
    const avatarBtn = page.getByRole("button", { name: /user menu/i });
    await expect(avatarBtn).toBeVisible();

    // Avatar initial (first letter of "testuser" = "T")
    await expect(avatarBtn).toContainText("T");

    // Username text
    await expect(avatarBtn).toContainText("testuser");
  });

  // ── AC2 ────────────────────────────────────────────────────────────────────
  // Clicking avatar opens dropdown with "View Profile" and "Logout".
  test("AC2: clicking avatar opens dropdown with View Profile and Logout", async ({
    page,
  }) => {
    await setAuthToken(page);
    await page.goto("/");

    await page.getByRole("button", { name: /user menu/i }).click();

    await expect(
      page.getByRole("menuitem", { name: /view profile/i }),
    ).toBeVisible();
    await expect(page.getByRole("menuitem", { name: /logout/i })).toBeVisible();
  });

  // ── AC3 ────────────────────────────────────────────────────────────────────
  // Clicking Logout POSTs to /auth/jwt/logout, clears cookie, redirects to /login.
  test("AC3: logout calls /auth/jwt/logout, clears token, redirects to /login", async ({
    page,
  }) => {
    await setAuthToken(page);

    // Mock logout endpoint
    let logoutCalled = false;
    await page.route("**/auth/jwt/logout", (route) => {
      logoutCalled = true;
      route.fulfill({ status: 204 });
    });

    await page.goto("/");
    await page.getByRole("button", { name: /user menu/i }).click();
    await page.getByRole("menuitem", { name: /logout/i }).click();

    // Logout endpoint was called
    expect(logoutCalled).toBe(true);

    // Redirected to /login
    await expect(page).toHaveURL(/\/login/);

    // Auth cookie cleared
    const cookies = await page.context().cookies();
    const authCookie = cookies.find((c) => c.name === AUTH_TOKEN_KEY);
    expect(authCookie?.value ?? "").toBe("");
  });

  // ── AC4 ────────────────────────────────────────────────────────────────────
  // Avatar remains visible at mobile viewport (≤ 768px).
  test("AC4: avatar visible at 375px mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await setAuthToken(page);
    await page.goto("/");

    const avatarBtn = page.getByRole("button", { name: /user menu/i });
    await expect(avatarBtn).toBeVisible();

    // Dropdown still works via tap (click)
    await avatarBtn.click();
    await expect(page.getByRole("menuitem", { name: /logout/i })).toBeVisible();
  });
});
