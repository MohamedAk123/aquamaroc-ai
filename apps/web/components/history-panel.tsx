"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { Download, TrendingUp } from "lucide-react";
import type { Measurement, Source } from "../lib/types";
import { dateLabel, numberLabel } from "../lib/format";
import { downloadCsv, measurementCsv } from "../lib/csv";
import { type HistoryMetric, usePreferences } from "../lib/preferences";
import { Provenance } from "./status";
import { Button } from "./ui/button";

const Chart = dynamic(() => import("./history-chart"), {
  ssr: false,
  loading: () => (
    <div className="chart-placeholder" role="status">
      Préparation du graphique…
    </div>
  ),
});
export function HistoryPanel({
  rows,
  name,
  sources,
  selector,
  compact = false,
}: {
  rows: Measurement[];
  name: string;
  sources: Source[];
  selector?: React.ReactNode;
  compact?: boolean;
}) {
  const { historyMetric } = usePreferences();
  const [metricOverride, setMetric] = useState<HistoryMetric | null>(null);
  const metric = metricOverride ?? historyMetric;
  return (
    <section
      className={`panel history-panel ${compact ? "history-panel-compact" : ""}`}
    >
      <div className="panel-heading">
        <div>
          {!compact && (
            <p className="eyebrow">
              <TrendingUp size={14} />
              OBSERVATIONS HISTORIQUES
            </p>
          )}
          <h2>
            {compact && <TrendingUp size={23} />}{" "}
            {metric === "filling_rate_pct"
              ? "Évolution du taux de remplissage"
              : compact
                ? "Évolution des réserves en eau"
                : "Évolution des réserves"}
          </h2>
          <p>{name}</p>
        </div>
        <div className="chart-controls">
          {!compact && selector}
          {compact ? (
            <div
              className="metric-tabs"
              role="group"
              aria-label="Unité du graphique"
            >
              <button
                aria-pressed={metric === "storage_mm3"}
                onClick={() => setMetric("storage_mm3")}
              >
                Réserves (Mm³)
              </button>
              <button
                aria-pressed={metric === "filling_rate_pct"}
                onClick={() => setMetric("filling_rate_pct")}
              >
                Taux de remplissage (%)
              </button>
            </div>
          ) : (
            <>
              <label className="sr-only" htmlFor="chart-unit">
                Unité du graphique
              </label>
              <select
                id="chart-unit"
                value={metric}
                onChange={(event) =>
                  setMetric(event.target.value as typeof metric)
                }
              >
                <option value="storage_mm3">Réserve · Mm³</option>
                <option value="filling_rate_pct">Remplissage · %</option>
              </select>
            </>
          )}
        </div>
      </div>
      {rows.length ? (
        <>
          <Chart
            rows={rows}
            metric={metric}
            name={name}
            sources={sources}
            compact={compact}
          />
          <details
            className={`history-extra ${compact ? "compact" : "expanded"}`}
            open={compact ? undefined : true}
          >
            <summary>Options, données et export CSV</summary>
            {compact && (
              <div className="compact-chart-selector">{selector}</div>
            )}
            <p className="chart-note">
              {rows.length} relevé{rows.length > 1 ? "s" : ""} · Les lignes
              relient les relevés, sans constituer des mesures intermédiaires.
              Chaque source et provenance forme une série distincte.
            </p>
            <details className="chart-data">
              <summary>Consulter les données du graphique</summary>
              <div
                className="table-scroll"
                role="region"
                aria-label="Données du graphique"
                tabIndex={0}
              >
                <table>
                  <caption className="sr-only">Observations de {name}</caption>
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Réserve (Mm³)</th>
                      <th scope="col">Remplissage (%)</th>
                      <th scope="col">Provenance</th>
                      <th scope="col">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <th scope="row">{dateLabel(row.observation_date)}</th>
                        <td>{numberLabel(row.storage_mm3)}</td>
                        <td>{numberLabel(row.filling_rate_pct)}</td>
                        <td>
                          <Provenance kind={row.data_kind} />
                        </td>
                        <td>
                          {sources.find((s) => s.source_id === row.source_id)
                            ?.title ?? row.source_id}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
            <div className="export-line">
              <span>
                Export de tous les relevés de cette sélection, avec source et
                licence.
              </span>
              <Button
                variant="outline"
                onClick={() =>
                  downloadCsv(
                    measurementCsv(rows, name, sources),
                    "aquamaroc-observations.csv",
                  )
                }
              >
                <Download size={15} />
                Exporter les relevés CSV
              </Button>
            </div>
          </details>
        </>
      ) : (
        <div className="state">
          <h3>Aucun relevé dans cette période</h3>
          <p>Modifiez les dates ou la source pour consulter l’historique.</p>
        </div>
      )}
    </section>
  );
}
