import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";

const apiPattern = "**/api/v1/**";
test("reference dashboard controls use the API and remain accessible", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Situation par barrage" }),
  ).toBeVisible();
  await page.getByLabel("Recherche rapide de barrage").fill("Beta");
  await page.getByLabel("Recherche rapide de barrage").press("Enter");
  await expect(
    page.getByRole("link", {
      name: "Réservoir synthétique Alpha",
      exact: true,
    }),
  ).toHaveCount(0);
  await page.getByLabel("Recherche rapide de barrage").fill("");
  await page.getByLabel("Recherche rapide de barrage").press("Enter");
  await expect(
    page.getByRole("link", {
      name: "Réservoir synthétique Alpha",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Taux de remplissage (%)", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Taux de remplissage (%)", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page
    .getByRole("button", { name: "Consulter les signalements" })
    .click();
  await expect(
    page.getByText("Aucun signalement ouvert dans le mode actif.", {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Consulter les signalements" })
    .click();
  await page.getByRole("button", { name: "Agrandir la carte" }).click();
  await expect(
    page.getByRole("button", { name: "Réduire la carte" }),
  ).toHaveAttribute("aria-expanded", "true");
  await page.getByRole("button", { name: "Réduire la carte" }).click();
  await expect(
    page.getByText("Coordonnées vérifiées non disponibles", { exact: true }),
  ).toBeVisible();
});
test("dashboard reads real DEMO API, filters and opens details", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByText("Données de démonstration", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Situation par barrage" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", {
      name: "Réservoir synthétique Alpha",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Filtres", exact: true }).click();
  await page.getByLabel("Rechercher un barrage").fill("Beta");
  await page.getByRole("button", { name: "Appliquer", exact: true }).click();
  await expect(
    page.getByRole("link", {
      name: "Réservoir synthétique Alpha",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Réservoir synthétique Beta", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Réservoir synthétique Beta", exact: true })
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Réservoir synthétique Beta",
  );
  await page
    .getByText("Consulter les données du graphique", { exact: true })
    .click();
  await expect(page.getByRole("table")).toBeVisible();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exporter les relevés CSV" }).click();
  expect((await downloaded).suggestedFilename()).toBe(
    "aquamaroc-observations.csv",
  );
  expect(errors).toEqual([]);
});

test("empty date range and reset", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Filtres", exact: true }).click();
  await expect(page.getByLabel("Du", { exact: true })).toBeVisible();
  await page.getByLabel("Du", { exact: true }).fill("2030-01-01");
  await page.getByRole("button", { name: "Appliquer", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Aucune observation pour cette sélection",
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Réinitialiser les filtres", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Situation par barrage" }),
  ).toBeVisible();
});

test("network error offers retry without fabricated data", async ({ page }) => {
  await page.route(apiPattern, (route) => route.abort("failed"));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Les données ne sont pas accessibles" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Réessayer" })).toBeVisible();
  await page.unroute(apiPattern);
  await page.getByRole("button", { name: "Réessayer" }).click();
  await expect(
    page.getByRole("heading", { name: "Situation par barrage" }),
  ).toBeVisible();
});

test("loading is announced before API responds", async ({ page }) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(apiPattern, async (route) => {
    await gate;
    await route.continue();
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Chargement des observations" }),
  ).toBeVisible();
  release();
  await expect(
    page.getByRole("heading", { name: "Situation par barrage" }),
  ).toBeVisible();
});

test("accessible dashboard at desktop and mobile widths", async ({
  page,
}, testInfo) => {
  if (testInfo.project.name === "desktop")
    await page.setViewportSize({ width: 1673, height: 941 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Situation par barrage" }),
  ).toBeVisible();
  await page.getByRole("img", { name: /Historique de/ }).waitFor();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  await page.screenshot({
    path: testInfo.outputPath("dashboard.png"),
    fullPage: true,
  });
  expect(
    results.violations.map((violation) => ({
      id: violation.id,
      nodes: violation.nodes.map((node) => ({
        target: node.target,
        summary: node.failureSummary,
      })),
    })),
  ).toEqual([]);
  const layout = await page.evaluate(() => ({
    inner: window.innerWidth,
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
    overflowing: [...document.querySelectorAll("body *")]
      .filter(
        (node) =>
          node.getBoundingClientRect().right >
          document.documentElement.clientWidth + 1,
      )
      .slice(0, 12)
      .map((node) => ({
        tag: node.tagName,
        class: node.className,
        right: node.getBoundingClientRect().right,
      })),
  }));
  const regions = await page
    .locator(".panel,.table-scroll,details,.workspace,body")
    .evaluateAll((nodes) =>
      nodes.map((node) => ({
        class: node.className,
        width: node.clientWidth,
        scroll: node.scrollWidth,
        right: node.getBoundingClientRect().right,
        overflow: getComputedStyle(node).overflowX,
      })),
    );
  expect(layout, JSON.stringify({ layout, regions })).toMatchObject({
    inner: page.viewportSize()!.width,
    client: page.viewportSize()!.width,
    scroll: page.viewportSize()!.width,
  });
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Aller au contenu" }),
  ).toBeFocused();
});

test("sources, analyses, quality and reports are functional routes", async ({
  page,
}) => {
  for (const [path, title] of [
    ["/sources", "Sources et méthodologie"],
    ["/analyses", "Analyses et tendances"],
    ["/qualite", "Qualité des données"],
    ["/rapports", "Rapports et exports"],
  ]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    await expect(
      page.getByText("Données de démonstration", { exact: true }),
    ).toBeVisible();
  }
});

test("navigation is usable with the mobile menu and keyboard", async ({
  page,
}) => {
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Ouvrir la navigation" });
  if (await menu.isVisible()) await menu.click();
  await page
    .getByRole("navigation", { name: "Navigation principale" })
    .getByRole("link", { name: "Sources et méthode" })
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Sources et méthodologie",
  );
});

test("export includes history beyond the first 500 rows", async ({ page }) => {
  const rows = Array.from({ length: 501 }, (_, index) => ({
    id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`,
    reservoir_id: "00000000-0000-0000-0000-000000000101",
    source_id: "00000000-0000-0000-0000-000000000001",
    ingestion_run_id: "00000000-0000-4000-8000-999999999999",
    observation_date: new Date(Date.UTC(2020, 0, 1 + index))
      .toISOString()
      .slice(0, 10),
    storage_mm3: `${index}.0000`,
    filling_rate_pct: null,
    published_at: null,
    ingested_at: "2026-01-01T00:00:00Z",
    data_kind: "DEMO",
    quality_status: "VALID",
  }));
  await page.route("**/reservoirs/*/measurements?*", (route) => {
    const query = new URL(route.request().url()).searchParams;
    const offset = Number(query.get("offset") ?? 0),
      limit = Number(query.get("limit") ?? 500);
    return route.fulfill({
      json: {
        items: rows.slice(offset, offset + limit),
        total: rows.length,
        offset,
        limit,
        mode: "demo",
        is_real_time: false,
      },
    });
  });
  await page.goto("/barrages/00000000-0000-0000-0000-000000000101");
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exporter les relevés CSV" }).click();
  const file = await (await downloadEvent).path();
  const csv = await readFile(file!, "utf8");
  expect(csv.split("\r\n")).toHaveLength(502);
  expect(csv).toContain('"500.0000"');
  expect(csv).toContain('"DEMO"');
});
