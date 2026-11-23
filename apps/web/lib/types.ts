export type Mode = "demo" | "official";
export interface VariationReview {
  status: "available" | "unavailable";
  mode: Mode;
  report: {
    model: "Isolation Forest";
    reference_start: string;
    reference_end: string;
    analysed_start: string;
    analysed_end: string;
    input_observations: number;
    reference_samples: number;
    analysed_samples: number;
    findings: {
      reservoir_id: string;
      reservoir_name: string;
      observation_date: string;
      storage_mm3: string;
      delta_1d_mm3: string;
      delta_7d_mm3: string;
    }[];
  } | null;
}
export type DataKind = "DEMO" | "OFFICIAL" | "UNVERIFIED";
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  mode: Mode;
  is_real_time: false;
}
export interface Basin {
  id: string;
  name: string;
  code: string | null;
}
export interface Reservoir {
  id: string;
  basin_id: string;
  name: string;
  capacity_mm3: string | null;
  capacity_source: string | null;
  latitude: string | null;
  longitude: string | null;
  coordinates_source: string | null;
}
export interface Measurement {
  id: string;
  reservoir_id: string;
  source_id: string;
  ingestion_run_id: string;
  observation_date: string;
  storage_mm3: string | null;
  filling_rate_pct: string | null;
  published_at: string | null;
  ingested_at: string;
  quality_status: string;
  data_kind: DataKind;
}
export interface Source {
  source_id: string;
  title: string;
  producer: string | null;
  dataset_url: string | null;
  license: string | null;
  verification_status: "DEMO" | "VERIFIED" | "TO_VERIFY";
  checked_at: string | null;
  latest_observation_date: string | null;
  latest_published_at: string | null;
  latest_ingested_at: string | null;
  latest_run_status: string | null;
  latest_run_completed_at: string | null;
}
export interface Snapshot {
  reservoir: Reservoir;
  basin_name: string;
  latest_date: string;
  latest: Measurement | null;
  source_count: number;
}
export interface Overview {
  mode: Mode;
  is_real_time: false;
  reservoirs: Snapshot[];
  reservoir_count: number;
  latest_observation_date: string | null;
  storage_mm3: string | null;
  weighted_filling_rate_pct: string | null;
  comparable_count: number;
  storage_status: string;
  filling_status: string;
}
export interface Quality {
  mode: Mode;
  files_ingested: number;
  observations: number;
  rejected_rows: number;
  rows_read: number;
  missing_storage: number;
  missing_filling_rate: number;
  unresolved_issues: number;
}
export interface ImportEntry {
  id: string;
  filename: string;
  sha256: string;
  source_title: string;
  source_checked_at: string | null;
  started_at: string;
  completed_at: string | null;
  status: string;
  rows_read: number;
  rows_valid: number;
  rows_rejected: number;
}
export interface QualityIssue {
  id: string;
  ingestion_run_id: string;
  filename: string;
  issue_type: string;
  severity: string;
  resolved_at: string | null;
  row: number | null;
  reason: string | null;
}
export interface ObservationCoverage {
  reservoir_id: string;
  reservoir_name: string;
  source_id: string;
  source_title: string;
  data_kind: DataKind;
  first_date: string;
  last_date: string;
  observed_days: number;
  span_days: number;
  gap_days: number;
}
export interface Filters {
  basin_id: string;
  search: string;
  start_date: string;
  end_date: string;
  data_kind: string;
  source_id: string;
}
export const emptyFilters: Filters = {
  basin_id: "",
  search: "",
  start_date: "",
  end_date: "",
  data_kind: "",
  source_id: "",
};
