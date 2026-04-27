import { expect, test } from "@playwright/test";
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

test.describe("Knowledge Graph course map", () => {
  test("renders course graph with unavailable courses disabled for the default profile", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.goto("/knowledge-graph");

    await expect(page.getByRole("link", { name: "DAG" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Intervention" }),
    ).toBeVisible();

    const causalDiscovery = page.getByRole("button", {
      name: "Causal Discovery",
    });
    const pcAlgorithm = page.getByRole("button", { name: "PC algorithm" });
    await expect(causalDiscovery).toBeDisabled();
    await expect(pcAlgorithm).toBeDisabled();

    await expect(page.locator("svg line")).toHaveCount(3);
  });

  test("navigates enabled course nodes to Study Mode", async ({ page }) => {
    await setAuthToken(page);

    await page.goto("/knowledge-graph");
    await page.getByRole("link", { name: "Intervention" }).click();

    await expect(page).toHaveURL(/\/study\?concept=interventions/);
    await expect(
      page
        .getByRole("heading", {
          name: "Why Interventions Matter in ML Systems",
        })
        .first(),
    ).toBeVisible();
  });
});
