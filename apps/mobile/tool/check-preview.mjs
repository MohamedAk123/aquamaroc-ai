// Requires the existing apps/web Playwright installation and local preview :3100.
import { chromium } from '../../web/node_modules/playwright/index.mjs';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const output = fileURLToPath(new URL('../../../docs/screenshots/', import.meta.url));
const screenshots = process.argv.includes('--screenshots');
if (screenshots) await mkdir(output, { recursive: true });
const mode = process.env.EXPECTED_APP_MODE ?? 'official';
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const capture = (name) => screenshots && page.screenshot({ path: `${output}/j3-flutter-${name}.png` });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const overview = page.waitForResponse((r) => r.url().includes('/api/v1/overview'));
  await page.goto('http://127.0.0.1:3100/');
  const overviewResponse = await overview;
  assert.equal(overviewResponse.status(), 200);
  const catalog = await overviewResponse.json();
  assert.equal(catalog.mode, mode);
  assert.ok(catalog.reservoirs.length > 0, 'Importer les relevés avant cette recette.');
  const first = catalog.reservoirs[0].reservoir;
  await page.locator('flt-semantics-placeholder').evaluate((element) => element.click());
  await page.getByText(/Bonjour !/).first().waitFor();
  await capture('home');
  await page.getByRole('tab', { name: 'Barrages', exact: true }).click();
  await page.getByRole('button', { name: 'Ajouter aux favoris' }).first().waitFor();
  await capture('list');
  await page.getByRole('button', { name: 'Ajouter aux favoris' }).first().click();
  await page.getByRole('tab', { name: 'Favoris', exact: true }).click();
  await page.getByRole('button', { name: 'Retirer des favoris' }).first().waitFor();
  await capture('favorites');
  await page.reload();
  await page.locator('flt-semantics-placeholder').waitFor({ state: 'attached' });
  await page.locator('flt-semantics-placeholder').evaluate((element) => element.click());
  await page.getByRole('tab', { name: 'Favoris', exact: true }).click();
  await page.getByRole('button', { name: 'Retirer des favoris' }).first().waitFor();
  const reservoir = page.getByRole('button', { name: first.name });
  const [history] = await Promise.all([
    page.waitForResponse((r) => r.url().includes(`/${first.id}/measurements`), { timeout: 10000 }),
    reservoir.click({ timeout: 8000 }).catch(async (error) => {
      console.error(await page.locator('body').ariaSnapshot());
      throw error;
    }),
  ]);
  assert.equal(history.status(), 200);
  const measurements = await history.json();
  assert.equal(measurements.mode, mode);
  assert.ok(measurements.items.length > 0);
  assert.ok(measurements.items.every(row => row.data_kind === (mode === 'official' ? 'OFFICIAL' : 'DEMO')));
  await page.getByText('Détail barrage', { exact: true }).waitFor();
  await capture('detail');
  await context.route('**/api/v1/**', (route) => route.abort('failed'));
  await page.reload();
  await page.locator('flt-semantics-placeholder').waitFor({ state: 'attached' });
  await page.locator('flt-semantics-placeholder').evaluate((element) => element.click());
  await page.getByText(/Cache local · actualisation indisponible/).waitFor();
  await capture('offline');
  console.log('Preview Flutter : API, navigation, détail, favoris après rechargement et cache hors connexion validés.');
  assert.deepEqual(errors, []);
} finally { await browser.close(); }
