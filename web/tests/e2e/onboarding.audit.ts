import { expect, test } from "@playwright/test";
import { AUTH_TOKEN_KEY } from "../../lib/api";

async function setAuthToken(page: import("@playwright/test").Page) {
  await page.addInitScript((tokenKey: string) => {
    window.localStorage.setItem(tokenKey, "fake-jwt-token");
  }, AUTH_TOKEN_KEY);

  await page.context().addCookies([
    {
      name: AUTH_TOKEN_KEY,
      value: "fake-jwt-token",
      domain: "localhost",
      path: "/",
      sameSite: "Lax",
    },
  ]);
}

test.describe("Learner onboarding", () => {
  test("selecting None clears other prior knowledge options", async ({
    page,
  }) => {
    await setAuthToken(page);

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

    await page.goto("/onboarding/learner");
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByRole("button", { name: "Next" }).click();

    await page.getByText("Confounding and controls").click();
    await expect(page.getByText("Confounding and controls")).toBeVisible();
    await page.getByText("None yet").click();

    await expect(page.getByLabel("Confounding and controls")).not.toBeChecked();
    await expect(page.getByLabel("None yet")).toBeChecked();
  });

  test("finish saves learner profile and returns home", async ({ page }) => {
    await setAuthToken(page);

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
    await page.route("**/api/v1/profile/learner", (route) =>
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
          learner_profile: {
            id: "00000000-0000-0000-0000-000000000002",
            background: "Computer scientist",
            role: "Researcher",
            prior_knowledge: ["confounding_controls"],
            expertise_level: "knows_correlation_confounding",
            learning_goal: "Learn causality",
            is_skipped: false,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        }),
      }),
    );

    await page.goto("/onboarding/learner");
    await page.getByLabel("Background").fill("Computer scientist");
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByLabel("Role").fill("Researcher");
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByText("Confounding and controls").click();
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByText("I know correlation and confounding").click();
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByLabel("Learning goal").fill("Learn causality");
    await page.getByRole("button", { name: "Finish" }).click();

    await expect(page).toHaveURL(/\/$/, { timeout: 5000 });
  });
});
