import { strict as assert } from "node:assert";
import { test } from "node:test";
import { measurementCsv } from "../../lib/csv.ts";
import type { Measurement } from "../../lib/types.ts";

test("CSV keeps provenance, nulls and escapes spreadsheet formulas", () => {
  const row = {
    id: "DEMO",
    reservoir_id: "DEMO",
    source_id: "source",
    ingestion_run_id: "run",
    observation_date: "2026-01-01",
    storage_mm3: "1.2500",
    filling_rate_pct: null,
    published_at: null,
    ingested_at: "2026-01-02T00:00:00Z",
    data_kind: "DEMO",
    quality_status: "VALID",
  } as Measurement;
  const csv = measurementCsv([row], '=HYPERLINK("test")', []);
  assert.ok(csv.startsWith("\ufeff"));
  assert.ok(csv.includes('"DEMO"'));
  assert.ok(csv.includes('"\'=HYPERLINK(""test"")"'));
  assert.ok(csv.includes('"1.2500";""'));
  assert.ok(csv.includes("date_observation"));
});
