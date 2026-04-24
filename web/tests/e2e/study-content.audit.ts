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

test.describe("Study content routing", () => {
  test("serves the requested profile folder when that concept profile exists", async ({
    page,
  }) => {
    await setAuthToken(page);

    const profileAsset = await page.request.get(
      "/study-assets/pc-algorithm/biologist/img_00.png",
    );
    expect(profileAsset.status()).toBe(200);
    expect(profileAsset.headers()["content-type"]).toContain("image/png");
  });

  test("falls back to computer science content for allowed concepts when profile content is missing", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.goto("/study?concept=interventions");

    const firstImage = page.locator("section img").first();
    await expect(firstImage).toHaveAttribute(
      "src",
      /\/study-assets\/interventions\/computer_science_ml\/img_00\.png$/,
    );

    await page.goto("/knowledge-graph?concept=interventions");
    await expect(
      page.getByText("Why Interventions Matter in ML Systems").first(),
    ).toBeVisible();

    const profileFallbackAsset = await page.request.get(
      "/study-assets/interventions/material/img_00.png",
    );
    const computerScienceAsset = await page.request.get(
      "/study-assets/interventions/computer_science_ml/img_00.png",
    );
    expect(profileFallbackAsset.status()).toBe(200);
    expect(await profileFallbackAsset.body()).toEqual(
      await computerScienceAsset.body(),
    );
  });

  test("falls back to the first configured computer science concept for unsupported profile/concept combinations", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.goto("/study?concept=pc-algorithm");

    await expect(
      page
        .getByRole("heading", {
          name: "Graphs as Causal Blueprints",
        })
        .first(),
    ).toBeVisible();
  });

  test("shows a concept switcher for multi-concept profiles", async ({
    page,
  }) => {
    await setAuthToken(page);

    await page.goto("/study");

    await page.getByRole("button", { name: "Interventions" }).click();
    await expect(page).toHaveURL(/concept=interventions/);
    await expect(
      page
        .getByRole("heading", {
          name: "Why Interventions Matter in ML Systems",
        })
        .first(),
    ).toBeVisible();
  });

  test("serves requested assets, falls back to computer science assets, and rejects unsafe paths", async ({
    page,
  }) => {
    await setAuthToken(page);

    const profileAsset = await page.request.get(
      "/study-assets/pc-algorithm/biologist/img_00.png",
    );
    expect(profileAsset.status()).toBe(200);
    expect(profileAsset.headers()["content-type"]).toContain("image/png");

    const fallbackAsset = await page.request.get(
      "/study-assets/interventions/history/img_00.png",
    );
    expect(fallbackAsset.status()).toBe(200);

    const defaultAsset = await page.request.get(
      "/study-assets/interventions/computer_science_ml/img_00.png",
    );
    expect(defaultAsset.status()).toBe(200);
    expect(await fallbackAsset.body()).toEqual(await defaultAsset.body());

    const missingEverywhere = await page.request.get(
      "/study-assets/interventions/history/img_99.png",
    );
    expect(missingEverywhere.status()).toBe(404);

    const unsafeProfile = await page.request.get(
      "/study-assets/pc-algorithm/%2E%2E/img_00.png",
    );
    expect(unsafeProfile.status()).toBe(404);

    const unsafeImagePath = await page.request.get(
      "/study-assets/pc-algorithm/computer_science_ml/%2E%2E/content.md",
    );
    expect(unsafeImagePath.status()).toBe(404);
  });
});
