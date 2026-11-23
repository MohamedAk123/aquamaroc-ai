import { readFile } from "node:fs/promises";

function object(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error("Valeur numérique absente du résultat DEMO.");
  }
  return value;
}

function day(value: unknown): string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new Error("Date absente du résultat DEMO.");
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  if (!Number.isFinite(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new Error("Date invalide dans le résultat DEMO.");
  }
  return value;
}

function reservoir(input: unknown, fallbackName?: string) {
  const row = object(input);
  const name = fallbackName ?? row.name;
  if (typeof name !== "string" || !name.startsWith("Barrage DEMO")) {
    throw new Error("Barrage fictif absent du résultat DEMO.");
  }
  const capacity = number(row.capacity_mm3_demo);
  const storage = number(row.predicted_storage_mm3_demo);
  const initial = number(row.initial_filling_pct_demo);
  const filling = number(row.predicted_filling_pct_demo);
  const candidate = number(row.h2o_filling_pct_demo);
  if (
    capacity <= 0 || storage < 0 || storage > capacity ||
    [initial, filling, candidate].some((rate) => rate < 0 || rate > 100)
  ) {
    throw new Error("Remplissage hors des limites du scénario.");
  }
  return { name, capacity, storage, initial, filling, candidate };
}

export function parseDemoForecast(input: unknown) {
  const report = object(input);
  const conditions = object(report.conditions);
  const weather = object(report.weather);
  const metrics = object(report.metrics_synthetic_only);
  if (
    report.data_kind !== "DEMO" ||
    report.status !== "experimental_synthetic_training" ||
    report.horizon_days !== 7 ||
    weather.provider !== "Open-Meteo" ||
    weather.kind !== "weather_model_forecast" ||
    typeof weather.mountain_point !== "string" ||
    typeof report.h2o_candidate !== "string" ||
    typeof report.mlflow_run_id !== "string" ||
    !/^[0-9a-f]{32}$/.test(report.mlflow_run_id) ||
    (report.selected_on_synthetic_validation !== "h2o_automl" &&
      report.selected_on_synthetic_validation !== "persistence")
  ) {
    throw new Error("Rapport expérimental incompatible.");
  }
  const directFilling = report.target_kind === "filling_rate_pct";
  let reservoirs;
  if (directFilling) {
    if (!Array.isArray(report.reservoirs) || !report.reservoirs.length) {
      throw new Error("Le rapport ne contient aucun barrage fictif.");
    }
    reservoirs = report.reservoirs.map((item) => reservoir(item));
    if (new Set(reservoirs.map((item) => item.name)).size !== reservoirs.length) {
      throw new Error("Barrage dupliqué dans le rapport DEMO.");
    }
  } else {
    if (report.target_kind !== undefined || report.reservoirs !== undefined) {
      throw new Error("Cible du modèle inconnue.");
    }
    const capacity = number(report.capacity_mm3_demo);
    reservoirs = [reservoir({
      ...report,
      initial_filling_pct_demo: 100 * number(conditions.storage_mm3) / capacity,
      h2o_filling_pct_demo: report.predicted_filling_pct_demo,
    }, "Barrage DEMO")];
  }
  const metricKey = directFilling ? "mae_pp" : "mae_mm3";
  return {
    issued: day(weather.issue_date),
    target: day(report.target_date),
    mountainPoint: weather.mountain_point,
    directFilling,
    reservoirs,
    initialSnow: number(conditions.snow_water_mm),
    rain: number(conditions.forecast_rain_mm),
    snow: number(conditions.forecast_snow_water_mm),
    temperature: number(conditions.forecast_temperature_c),
    estimatedMelt: number(conditions.forecast_melt_mm),
    selected: report.selected_on_synthetic_validation,
    h2oCandidate: report.h2o_candidate,
    runId: report.mlflow_run_id,
    modelMae: number(object(metrics.test_selected)[metricKey]),
    persistenceMae: number(object(metrics.test_persistence)[metricKey]),
  };
}

export async function readDemoForecast(path = process.env.DEMO_FORECAST_PATH) {
  if (!path) return null;
  try {
    return parseDemoForecast(JSON.parse(await readFile(path, "utf8")));
  } catch {
    return null;
  }
}
