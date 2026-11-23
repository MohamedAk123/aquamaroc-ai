import { expect, test } from "@playwright/test";

test.use({ launchOptions: { args: ["--enable-unsafe-swiftshader"] } });

test("seules les coordonnées sourcées deviennent des marqueurs", async ({
  page,
}) => {
  // Fixture cartographique synthétique injectée dans cette page de test uniquement.
  await page.route(/\/api\/v1\/overview(?:\?|$)/, async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    const first = json.reservoirs[0];
    const second = json.reservoirs[1];
    first.reservoir = {
      ...first.reservoir,
      name: "Point synthétique sourcé",
      latitude: "31",
      longitude: "-8",
      coordinates_source: "Fixture de test",
    };
    second.reservoir = {
      ...second.reservoir,
      name: "Point synthétique non sourcé",
      latitude: "31.1",
      longitude: "-8.1",
      coordinates_source: null,
    };
    json.reservoirs = [first, second];
    await route.fulfill({ response, json });
  });
  await page.goto("/carte");
  await expect(page.getByText("1 sur 2 barrage(s) localisé(s)")).toBeVisible();
  const marker = page.locator(".dam-marker");
  await expect(marker).toHaveCount(1);
  await expect(marker).toHaveAttribute(
    "aria-label",
    "Point synthétique sourcé",
  );
  await marker.click();
  await expect(
    page.getByText("Source géographique : Fixture de test"),
  ).toBeVisible();
});
