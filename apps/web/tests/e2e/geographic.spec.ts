import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("la carte filtre et ouvre la fiche d’un barrage non localisé", async ({
  page,
}) => {
  await page.route("**/api/v1/overview?*", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    for (const row of payload.reservoirs) {
      row.reservoir.latitude = null;
      row.reservoir.longitude = null;
      row.reservoir.coordinates_source = null;
    }
    await route.fulfill({ response, json: payload });
  });
  await page.goto("/carte");
  await expect(
    page.getByRole("heading", { name: "Carte des barrages", level: 1 }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Fond cartographique interactif" }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Coordonnées vérifiées non disponibles pour cette sélection.",
    ),
  ).toBeVisible();
  const details = page.getByRole("complementary", {
    name: "Résultats et détail",
  });
  await details.getByRole("button").first().click();
  await expect(
    details.getByRole("link", { name: "Voir l’historique du barrage" }),
  ).toBeVisible();
  await expect(page.locator(".dam-marker")).toHaveCount(0);
  await page
    .getByLabel("Taux du dernier relevé dans la période")
    .selectOption("-1");
  await expect(
    page.getByText("Aucun barrage ne correspond à ce taux."),
  ).toBeVisible();
});

test("le journal relie une anomalie à son import et exporte un CSV sûr", async ({
  page,
}) => {
  const filename = "fixture-de-test.xlsx";
  await page.route("**/api/v1/data/quality/issues?*", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    const openOnly = new URL(route.request().url()).searchParams.get(
      "open_only",
    );
    const items =
      openOnly === "true"
        ? []
        : [
            {
              id: "fixture",
              ingestion_run_id: "test-svg",
              filename,
              issue_type: "rejected_row",
              severity: "warning",
              row: 12,
              reason: "=FORMULE_TEST",
              resolved_at: "2026-01-02T00:00:00Z",
            },
          ];
    await route.fulfill({
      response,
      json: { ...payload, total: items.length, items },
    });
  });
  await page.goto("/qualite");
  await expect(
    page.getByRole("heading", { name: "Journal des imports" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Couverture des relevés" }),
  ).toBeVisible();
  await expect(
    page.getByRole("row", { name: /fixture-de-test.xlsx.*12.*Ligne rejetée/ }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Exporter les anomalies (CSV)" })
    .click();
  const file = await (await download).path();
  expect(await readFile(file!, "utf8")).toContain('"\'=FORMULE_TEST"');
  await page.getByRole("checkbox", { name: "Signalements ouverts" }).check();
  await expect(
    page.getByText("Aucune anomalie enregistrée pour cette sélection."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Exporter les anomalies (CSV)" }),
  ).toBeDisabled();
});
