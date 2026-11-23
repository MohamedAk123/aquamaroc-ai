"use client";

import { useCallback, useState } from "react";
import { api } from "../lib/api";
import { dateLabel } from "../lib/format";
import { downloadCsv, qualityCsv } from "../lib/csv";
import { useRemote } from "../lib/use-remote";
import type { Mode } from "../lib/types";
import { ErrorState, LoadingState } from "./status";
import { Card } from "./ui/card";
import { Button } from "./ui/button";

const runStatuses: Record<string, string> = {
  success: "Réussi",
  partial: "Partiel",
  failed: "Échec",
  pending: "En cours",
};
const issueTypes: Record<string, string> = {
  rejected_row: "Ligne rejetée",
  invalid_workbook: "Classeur invalide",
};

export function QualityJournal({ mode }: { mode: Mode }) {
  const [revision, setRevision] = useState(0);
  const [run, setRun] = useState("");
  const [openOnly, setOpenOnly] = useState(false);
  const [visible, setVisible] = useState(20);
  const [visibleImports, setVisibleImports] = useState(20);
  const [visibleSeries, setVisibleSeries] = useState(20);
  const loadImports = useCallback(
    (signal: AbortSignal) => api.imports(signal),
    [],
  );
  const loadIssues = useCallback(
    (signal: AbortSignal) =>
      api.issues({ run_id: run, open_only: String(openOnly) }, signal),
    [run, openOnly],
  );
  const imports = useRemote(`imports:${mode}:${revision}`, loadImports);
  const coverage = useRemote(`coverage:${mode}:${revision}`, api.coverage);
  const issues = useRemote(
    `issues:${mode}:${revision}:${run}:${openOnly}`,
    loadIssues,
  );
  const retry = () => setRevision((n) => n + 1);
  const error = imports.error ?? issues.error ?? coverage.error;
  if (error) return <ErrorState message={error.message} retry={retry} />;
  if (imports.loading || coverage.loading) return <LoadingState />;
  if (
    imports.data?.mode !== mode ||
    coverage.data?.mode !== mode ||
    (issues.data && issues.data.mode !== mode)
  ) {
    return <ErrorState message="Le mode des données a changé." retry={retry} />;
  }
  const items = issues.data?.items ?? [];
  return (
    <>
      <Card className="quality-journal">
        <h2>Journal des imports</h2>
        {imports.data.items.length === 0 ? (
          <p>Aucun fichier importé dans ce mode.</p>
        ) : (
          <div
            className="journal-table"
            role="region"
            aria-label="Fichiers importés"
            tabIndex={0}
          >
            <table>
              <thead>
                <tr>
                  <th>Fichier</th>
                  <th>Source et vérification</th>
                  <th>Import</th>
                  <th>État</th>
                  <th>Lignes acceptées</th>
                </tr>
              </thead>
              <tbody>
                {imports.data.items.slice(0, visibleImports).map((i) => (
                  <tr key={i.id}>
                    <th scope="row">
                      {i.filename}
                      <details>
                        <summary>Empreinte SHA-256</summary>
                        <code>{i.sha256}</code>
                      </details>
                    </th>
                    <td>
                      {i.source_title}
                      <br />
                      Vérifiée le {dateLabel(i.source_checked_at)}
                    </td>
                    <td>{dateLabel(i.completed_at ?? i.started_at)}</td>
                    <td>{runStatuses[i.status] ?? i.status}</td>
                    <td>
                      {i.rows_valid} / {i.rows_read}
                      {i.rows_read
                        ? ` · ${((100 * i.rows_valid) / i.rows_read).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`
                        : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {visibleImports < imports.data.items.length && (
          <Button
            variant="outline"
            onClick={() => setVisibleImports((n) => n + 20)}
          >
            Afficher plus d’imports
          </Button>
        )}
      </Card>
      <Card className="quality-journal">
        <h2>Couverture des relevés</h2>
        <p>
          Les écarts sont les jours sans relevé entre la première et la dernière
          date de chaque série. Ils ne prouvent pas qu’une publication était
          attendue.
        </p>
        {!coverage.data.items.length ? (
          <p>Aucune série observée dans ce mode.</p>
        ) : (
          <div
            className="journal-table"
            role="region"
            aria-label="Couverture par série"
            tabIndex={0}
          >
            <table>
              <thead>
                <tr>
                  <th>Barrage et source</th>
                  <th>Période observée</th>
                  <th>Jours avec relevé</th>
                  <th>Jours sans relevé</th>
                </tr>
              </thead>
              <tbody>
                {coverage.data.items.slice(0, visibleSeries).map((s) => (
                  <tr key={`${s.reservoir_id}:${s.source_id}:${s.data_kind}`}>
                    <th scope="row">
                      {s.reservoir_name}
                      <br />
                      {s.source_title} · {s.data_kind}
                    </th>
                    <td>
                      {dateLabel(s.first_date)} – {dateLabel(s.last_date)}
                    </td>
                    <td>
                      {s.observed_days} / {s.span_days}
                    </td>
                    <td>{s.gap_days}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {visibleSeries < coverage.data.items.length && (
          <Button
            variant="outline"
            onClick={() => setVisibleSeries((n) => n + 20)}
          >
            Afficher plus de séries
          </Button>
        )}
      </Card>
      <Card className="quality-journal">
        <h2>Anomalies d’import</h2>
        <div className="journal-actions">
          <label>
            Fichier importé
            <select
              value={run}
              onChange={(e) => {
                setRun(e.target.value);
                setVisible(20);
              }}
            >
              <option value="">Tous les fichiers</option>
              {imports.data.items.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.filename} · {dateLabel(i.started_at)}
                </option>
              ))}
            </select>
          </label>
          <label className="journal-checkbox">
            <input
              type="checkbox"
              checked={openOnly}
              onChange={(e) => {
                setOpenOnly(e.target.checked);
                setVisible(20);
              }}
            />{" "}
            Signalements ouverts
          </label>
          <Button
            variant="outline"
            disabled={issues.loading || !items.length}
            onClick={() =>
              downloadCsv(qualityCsv(items, mode), `anomalies-${mode}.csv`)
            }
          >
            Exporter les anomalies (CSV)
          </Button>
        </div>
        {issues.loading ? (
          <LoadingState />
        ) : !items.length ? (
          <p role="status">Aucune anomalie enregistrée pour cette sélection.</p>
        ) : (
          <>
            <p role="status">{items.length} signalement(s)</p>
            <div
              className="journal-table"
              role="region"
              aria-label="Signalements"
              tabIndex={0}
            >
              <table>
                <thead>
                  <tr>
                    <th>Fichier</th>
                    <th>Ligne</th>
                    <th>Type</th>
                    <th>Motif</th>
                    <th>État</th>
                  </tr>
                </thead>
                <tbody>
                  {items.slice(0, visible).map((i) => (
                    <tr key={i.id}>
                      <th scope="row">{i.filename}</th>
                      <td>{i.row ?? "—"}</td>
                      <td>
                        {issueTypes[i.issue_type] ?? i.issue_type} ·{" "}
                        {i.severity}
                      </td>
                      <td>{i.reason ?? "—"}</td>
                      <td>
                        {i.resolved_at
                          ? `Résolu le ${dateLabel(i.resolved_at)}`
                          : "Ouvert"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {visible < items.length && (
              <Button
                variant="outline"
                onClick={() => setVisible((n) => n + 20)}
              >
                Afficher plus de signalements
              </Button>
            )}
          </>
        )}
      </Card>
    </>
  );
}
