import { test, expect } from "@playwright/test";
import { AUTH_TOKEN_KEY } from "../../lib/api";

async function setAuthToken(page: import("@playwright/test").Page) {
  const fakeToken = "fake-jwt-token";

  await page.addInitScript((tokenKey: string) => {
    window.localStorage.setItem(tokenKey, "fake-jwt-token");
  }, AUTH_TOKEN_KEY);

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

test.describe("Profile page", () => {
  test("loads hero state and saves edited profile details", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.route("**/api/v1/profile", async (route, request) => {
      if (request.method() === "GET") {
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            id: "00000000-0000-0000-0000-000000000001",
            email: "test@example.com",
            username: "testuser",
            first_name: "Test",
            last_name: "User",
            institution: "EducAgent",
            avatar_url: null,
            is_active: true,
            is_superuser: false,
            is_verified: true,
            created_at: "2026-01-01T00:00:00Z",
          }),
        });
        return;
      }

      if (request.method() === "PATCH") {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            id: "00000000-0000-0000-0000-000000000001",
            email: "test@example.com",
            username: body.username,
            first_name: body.first_name,
            last_name: body.last_name,
            institution: body.institution,
            avatar_url: null,
            is_active: true,
            is_superuser: false,
            is_verified: true,
            created_at: "2026-01-01T00:00:00Z",
          }),
        });
      }
    });

    await page.goto("/profile");

    await expect(
      page.getByRole("heading", { name: "Test User" }),
    ).toBeVisible();
    await expect(page.getByText("Verified")).toBeVisible();
    await expect(page.getByText("Active")).toBeVisible();

    await page.getByLabel("Institution").fill("New Institution");
    await expect(
      page.getByRole("button", { name: /save changes/i }),
    ).toBeEnabled();
    await page.getByRole("button", { name: /save changes/i }).click();

    await expect(page.getByText("Profile details saved.")).toBeVisible();
    await expect(page.getByText("New Institution")).toBeVisible();
  });

  test("blocks mismatched password confirmation and handles success", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.route("**/api/v1/profile", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "test@example.com",
          username: "testuser",
          first_name: "Test",
          last_name: "User",
          institution: "EducAgent",
          avatar_url: null,
          is_active: true,
          is_superuser: false,
          is_verified: true,
          created_at: "2026-01-01T00:00:00Z",
        }),
      });
    });

    await page.route("**/api/v1/profile/password", async (route) => {
      await route.fulfill({ status: 204 });
    });

    await page.goto("/profile");

    await page.getByLabel("Current password").fill("current-pass-123");
    await page.getByLabel("New password").fill("next-pass-123");
    await page.getByLabel("Confirm new password").fill("mismatch");

    await expect(
      page.getByText("Password confirmation does not match."),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /update password/i }),
    ).toBeDisabled();

    await page.getByLabel("Confirm new password").fill("next-pass-123");
    await page.getByRole("button", { name: /update password/i }).click();

    await expect(page.getByText("Password updated.")).toBeVisible();
  });

  test("uploads avatar and updates nav avatar immediately", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.route("**/api/v1/profile", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "test@example.com",
          username: "testuser",
          first_name: "Test",
          last_name: "User",
          institution: "EducAgent",
          avatar_url: null,
          is_active: true,
          is_superuser: false,
          is_verified: true,
          created_at: "2026-01-01T00:00:00Z",
        }),
      });
    });

    await page.route("**/api/v1/profile/avatar", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "test@example.com",
          username: "testuser",
          first_name: "Test",
          last_name: "User",
          institution: "EducAgent",
          avatar_url: "/api/outputs/profile/avatars/test-avatar.png",
          is_active: true,
          is_superuser: false,
          is_verified: true,
          created_at: "2026-01-01T00:00:00Z",
        }),
      });
    });

    await page.goto("/profile");
    await page.setInputFiles('input[type="file"]', {
      name: "avatar.png",
      mimeType: "image/png",
      buffer: Buffer.from("fakepng"),
    });

    await expect(page.getByText("Avatar updated.")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /user menu/i }).locator("img"),
    ).toBeVisible();
  });
});
