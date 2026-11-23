import type {
  Basin,
  Filters,
  ImportEntry,
  ObservationCoverage,
  Measurement,
  Overview,
  Page,
  Quality,
  QualityIssue,
  Reservoir,
  Source,
  VariationReview,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const base = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export function queryString(
  values: Record<string, string | number | undefined>,
) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  return params.toString();
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  signal?.addEventListener("abort", abort, { once: true });
  if (signal?.aborted) controller.abort();
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, 15000);
  try {
    const response = await fetch(`${base}/api/v1${path}`, {
      signal: controller.signal,
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new ApiError(
        response.status,
        error?.error?.message ?? "La source est momentanément indisponible.",
      );
    }
    return response.json() as Promise<T>;
  } catch (error) {
    if (timedOut)
      throw new ApiError(
        504,
        "Le délai de réponse de la source est dépassé. Réessayez.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", abort);
  }
}

async function all<T>(
  path: string,
  params: Record<string, string | number> = {},
  signal?: AbortSignal,
): Promise<Page<T>> {
  const items: T[] = [];
  let offset = 0;
  let last: Page<T>;
  do {
    last = await get<Page<T>>(
      `${path}?${queryString({ ...params, limit: 500, offset })}`,
      signal,
    );
    if (
      last.offset !== offset ||
      (last.items.length === 0 && offset < last.total)
    )
      throw new ApiError(502, "Pagination incohérente : réessayez.");
    items.push(...last.items);
    offset += last.items.length;
  } while (offset < last.total);
  return { ...last!, items, offset: 0, limit: items.length };
}

export const api = {
  variationReview: (signal?: AbortSignal) =>
    get<VariationReview>("/data/variation-review", signal),
  basins: (signal?: AbortSignal) => all<Basin>("/basins", {}, signal),
  sources: (signal?: AbortSignal) => all<Source>("/sources", {}, signal),
  quality: (signal?: AbortSignal) => get<Quality>("/data/quality", signal),
  imports: (signal?: AbortSignal) =>
    all<ImportEntry>("/data/quality/imports", {}, signal),
  coverage: (signal?: AbortSignal) =>
    all<ObservationCoverage>("/data/quality/coverage", {}, signal),
  issues: (params: Record<string, string>, signal?: AbortSignal) =>
    all<QualityIssue>("/data/quality/issues", params, signal),
  overview: (filters: Filters, signal?: AbortSignal) =>
    get<Overview>(`/overview?${queryString({ ...filters })}`, signal),
  reservoir: (id: string, signal?: AbortSignal) =>
    get<Reservoir>(`/reservoirs/${encodeURIComponent(id)}`, signal),
  history: (id: string, filters: Filters, signal?: AbortSignal) =>
    all<Measurement>(
      `/reservoirs/${encodeURIComponent(id)}/measurements`,
      {
        start_date: filters.start_date,
        end_date: filters.end_date,
        source_id: filters.source_id,
        data_kind: filters.data_kind,
      },
      signal,
    ),
};
