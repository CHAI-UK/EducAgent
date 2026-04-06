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

function buildProfileResponse(overrides: Record<string, unknown> = {}) {
  return {
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
    updated_at: "2026-01-01T00:00:00Z",
    learner_profile: null,
    ...overrides,
  };
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
          body: JSON.stringify(buildProfileResponse()),
        });
        return;
      }

      if (request.method() === "PATCH") {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify(
            buildProfileResponse({
              username: body.username,
              first_name: body.first_name,
              last_name: body.last_name,
              institution: body.institution,
            }),
          ),
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
        body: JSON.stringify(buildProfileResponse()),
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
        body: JSON.stringify(buildProfileResponse()),
      });
    });

    await page.route("**/api/v1/profile/avatar", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(
          buildProfileResponse({
            avatar_url: "/api/outputs/profile/avatars/test-avatar.png",
          }),
        ),
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

  test("loads learner profile section and saves learner details", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.route("**/api/v1/profile", async (route, request) => {
      if (request.method() === "GET") {
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify(
            buildProfileResponse({
              learner_profile: {
                id: "00000000-0000-0000-0000-000000000002",
                background: null,
                role: null,
                prior_knowledge: [],
                expertise_level: null,
                learning_goal: null,
                is_skipped: true,
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
              },
            }),
          ),
        });
        return;
      }

      if (request.method() === "PATCH") {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify(
            buildProfileResponse({
              learner_profile: {
                id: "00000000-0000-0000-0000-000000000002",
                background: body.background,
                role: body.role,
                prior_knowledge: body.prior_knowledge,
                expertise_level: body.expertise_level,
                learning_goal: body.learning_goal,
                is_skipped: false,
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-02T00:00:00Z",
              },
            }),
          ),
        });
      }
    });

    await page.goto("/profile");

    await expect(
      page.getByText(
        "You skipped setup earlier. Add your learner profile now any time.",
      ),
    ).toBeVisible();
    await page.getByLabel("Background").fill("Computer scientist");
    await page.getByText("Machine Learning").click();
    await page.getByText("Moderate").click();
    await page.getByRole("button", { name: /save learner profile/i }).click();

    await expect(page.getByText("Learner profile saved.")).toBeVisible();
  });
});
