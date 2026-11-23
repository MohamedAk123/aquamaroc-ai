import type { Measurement, Mode, QualityIssue, Source } from "./types";

function cell(value: unknown): string {
  let text = value === null || value === undefined ? "" : String(value);
  if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

export function measurementCsv(
  rows: Measurement[],
  name: string,
  sources: Source[],
): string {
  const headers = [
    "barrage",
    "date_observation",
    "reserve_Mm3",
    "remplissage_pct",
    "provenance",
    "source_id",
    "source",
    "licence",
    "date_publication",
    "date_ingestion",
    "qualite",
  ];
  const values = rows.map((row) => {
    const source = sources.find((s) => s.source_id === row.source_id);
    return [
      name,
      row.observation_date,
      row.storage_mm3,
      row.filling_rate_pct,
      row.data_kind,
      row.source_id,
      source?.title,
      source?.license,
      row.published_at,
      row.ingested_at,
      row.quality_status,
    ];
  });
  return (
    "\ufeff" +
    [headers, ...values].map((row) => row.map(cell).join(";")).join("\r\n")
  );
}

export function downloadCsv(content: string, filename: string) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function qualityCsv(rows: QualityIssue[], mode: Mode) {
  return (
    "\ufeff" +
    [
      [
        "mode",
        "id",
        "import_id",
        "fichier",
        "ligne",
        "type",
        "gravite",
        "motif",
        "resolu_le",
      ],
      ...rows.map((r) => [
        mode,
        r.id,
        r.ingestion_run_id,
        r.filename,
        r.row,
        r.issue_type,
        r.severity,
        r.reason,
        r.resolved_at,
      ]),
    ]
      .map((row) => row.map(cell).join(";"))
      .join("\r\n")
  );
}
