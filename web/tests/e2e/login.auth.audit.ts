import { test, expect } from "@playwright/test";
import { AUTH_TOKEN_KEY } from "../../lib/api";

// baseURL is configured centrally in playwright.config.ts (WEB_BASE_URL env var,
// defaulting to http://localhost:3782). All page.goto() calls use relative paths.

test.describe("Auth :: Login UX and session behavior", () => {
  test("AC1: successful login with ?redirect= param redirects to target", async ({
    page,
  }) => {
    await page.route("**/auth/jwt/login", (route) =>
      route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ access_token: "fake-token-ac1", token_type: "bearer" }),
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
        body: JSON.stringify({ access_token: "fake-token-ac1b", token_type: "bearer" }),
      }),
    );

    await page.goto("/login");

    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/$/, { timeout: 5000 });
  });

  test("AC3: authenticated user navigating to /login is redirected home", async ({
    page,
  }) => {
    await page.addInitScript((tokenKey: string) => {
      window.localStorage.setItem(tokenKey, "fake-token");
    }, AUTH_TOKEN_KEY);

    await page.goto("/login");

    await expect(page).toHaveURL(/^[^?]*\/$/);
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
