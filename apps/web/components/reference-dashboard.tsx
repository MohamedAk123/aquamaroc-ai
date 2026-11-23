"use client";
import Link from "next/link";
import { useState } from "react";
import {
  Bell,
  BrainCircuit,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronRight,
  Droplet,
  Expand,
  ShieldCheck,
  SlidersHorizontal,
  TrendingUp,
} from "lucide-react";
import { Shell } from "./shell";
import { Filters } from "./filters";
import { ErrorState, LoadingState, EmptyState, Provenance } from "./status";
import { HistoryPanel } from "./history-panel";
import { MapCanvas, coordinates } from "./reservoir-map";
import { Button } from "./ui/button";
import { dateLabel, numberLabel, reasons } from "../lib/format";
import type {
  Basin,
  Filters as FilterValues,
  Measurement,
  Mode,
  Overview,
  Page,
  Quality,
  Source,
  Snapshot,
} from "../lib/types";

type Remote<T> = { loading: boolean; data?: T; error?: Error };
export interface ReferenceDashboardProps {
  mode?: Mode;
  imported?: string;
  boot: Remote<{
    basins: Page<Basin>;
    sources: Page<Source>;
    quality: Quality;
  }>;
  overview: Remote<Overview>;
  history: Remote<Page<Measurement>>;
  filters: FilterValues;
  draft: FilterValues;
  setDraft: (value: FilterValues) => void;
  apply: (value: FilterValues) => void;
  reset: () => void;
  retry: () => void;
  chartId: string;
  setChartId: (value: string) => void;
}

function DamIcon({ size = 25 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <path
        d="M6 7h20M3 27h26M8 8 5 26m19-18 3 18M13 9l-2 16m8-16 2 16M4 7h24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.7"
        strokeLinecap="round"
      />
      <path
        d="M8 3v3m16-3v3"
        stroke="currentColor"
        strokeWidth="2.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ReferenceDashboard(props: ReferenceDashboardProps) {
  const {
    mode,
    imported,
    boot,
    overview,
    history,
    filters,
    draft,
    setDraft,
    apply,
    reset,
    retry,
    chartId,
    setChartId,
  } = props;
  const [advanced, setAdvanced] = useState(false);
  const [period, setPeriod] = useState("all");
  const data = overview.data;
  const rows = data?.reservoirs ?? [];
  const sources = boot.data?.sources.items ?? [];
  const quality = boot.data?.quality;
  const chartReservoir = rows.find(
    (row) => row.reservoir.id === chartId,
  )?.reservoir;
  const loading = boot.loading || overview.loading;
  const error = boot.error || overview.error;
  const accepted =
    quality && quality.rows_read > 0
      ? (Math.max(0, quality.rows_read - quality.rejected_rows) /
          quality.rows_read) *
        100
      : null;
  function choosePeriod(value: string) {
    setPeriod(value);
    const last = sources
      .map((source) => source.latest_observation_date)
      .filter((date): date is string => date !== null)
      .sort()
      .at(-1);
    let start = "",
      end = "";
    if (value !== "all" && last) {
      const date = new Date(`${last}T00:00:00Z`);
      date.setUTCMonth(date.getUTCMonth() - Number(value));
      start = date.toISOString().slice(0, 10);
      end = last;
    }
    const next = { ...filters, start_date: start, end_date: end };
    setDraft(next);
    apply(next);
  }
  return (
    <Shell
      mode={mode}
      importedAt={imported}
      search={filters.search}
      issueCount={quality?.unresolved_issues}
      onSearch={(search) => {
        const next = { ...filters, search };
        setDraft(next);
        apply(next);
      }}
    >
      <div className="reference-dashboard">
        <div className="dashboard-heading">
          <div>
            <h1>Tableau de bord</h1>
            <p>Vue d’ensemble des ressources hydriques suivies au Maroc</p>
          </div>
          <div className="dashboard-period">
            <label htmlFor="dashboard-period">Période</label>
            <div>
              <CalendarDays size={19} />
              <select
                id="dashboard-period"
                value={period}
                onChange={(event) => choosePeriod(event.target.value)}
              >
                <option value="all">Tout l’historique</option>
                <option value="12">12 derniers mois de relevés</option>
                <option value="6">6 derniers mois de relevés</option>
                <option value="1">Dernier mois de relevés</option>
              </select>
            </div>
            <Button
              variant="outline"
              onClick={() => setAdvanced(!advanced)}
              aria-label="Filtres"
              aria-expanded={advanced}
            >
              <SlidersHorizontal size={16} />
              <span>Filtres</span>
            </Button>
          </div>
        </div>
        {advanced && boot.data && (
          <Filters
            values={draft}
            onChange={setDraft}
            onApply={() => {
              setPeriod("all");
              apply({ ...draft });
            }}
            onReset={() => {
              setPeriod("all");
              reset();
            }}
            basins={boot.data.basins.items}
            sources={sources}
            mode={mode ?? "demo"}
          />
        )}
        {filters.search && (
          <p className="dashboard-selection">
            Recherche : « {filters.search} »{" "}
            <button onClick={reset}>Effacer</button>
          </p>
        )}
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error.message} retry={retry} />
        ) : !rows.length ? (
          <EmptyState reset={reset} />
        ) : (
          data && (
            <>
              <div className="dashboard-kpis">
                <Kpi
                  icon={<DamIcon size={38} />}
                  title="Barrages surveillés"
                  value={String(data.reservoir_count)}
                  note={
                    boot.data?.basins.items.find(
                      (basin) => basin.id === filters.basin_id,
                    )?.name ?? "dans la sélection courante"
                  }
                />
                <Kpi
                  icon={<Droplet size={37} />}
                  title="Réserves totales"
                  value={numberLabel(data.storage_mm3, 1)}
                  unit={data.storage_mm3 !== null ? "Mm³" : undefined}
                  note={
                    data.storage_status === "available"
                      ? `${data.comparable_count} barrages · relevés comparables`
                      : reasons[data.storage_status]
                  }
                />
                <Kpi
                  icon={
                    <span
                      className="kpi-donut"
                      style={
                        {
                          "--ring-value": `${Number(data.weighted_filling_rate_pct ?? 0)}%`,
                        } as React.CSSProperties
                      }
                    />
                  }
                  title="Taux de remplissage pondéré"
                  value={numberLabel(data.weighted_filling_rate_pct, 1)}
                  unit={
                    data.weighted_filling_rate_pct !== null ? "%" : undefined
                  }
                  note={
                    data.filling_status === "available"
                      ? "pondéré par capacités sourcées"
                      : data.filling_status === "unverified_capacities"
                        ? "Capacités à vérifier"
                        : (reasons[data.filling_status] ??
                          "Taux non calculable")
                  }
                />
                <Kpi
                  icon={<CalendarDays size={36} />}
                  title="Dernière mise à jour"
                  value={dateLabel(imported)}
                  note={`Dernier relevé : ${dateLabel(data.latest_observation_date)}`}
                />
              </div>
              <div className="dashboard-main-grid">
                <MapPreview rows={rows} />
                <div className="dashboard-chart">
                  {history.loading ? (
                    <LoadingState />
                  ) : history.error ? (
                    <ErrorState message={history.error.message} retry={retry} />
                  ) : (
                    chartReservoir && (
                      <HistoryPanel
                        rows={history.data?.items ?? []}
                        name={chartReservoir.name}
                        sources={sources}
                        compact
                        selector={
                          <>
                            <label
                              className="sr-only"
                              htmlFor="history-reservoir"
                            >
                              Barrage du graphique
                            </label>
                            <select
                              id="history-reservoir"
                              value={chartId}
                              onChange={(event) =>
                                setChartId(event.target.value)
                              }
                            >
                              {rows.map((row) => (
                                <option
                                  value={row.reservoir.id}
                                  key={row.reservoir.id}
                                >
                                  {row.reservoir.name}
                                </option>
                              ))}
                            </select>
                          </>
                        }
                      />
                    )
                  )}
                </div>
              </div>
              <div className="dashboard-bottom-grid">
                <section className="panel dashboard-reservoirs">
                  <div className="reference-panel-title">
                    <DamIcon />
                    <h2>Situation par barrage</h2>
                  </div>
                  <div
                    className="table-scroll"
                    role="region"
                    aria-label="Situation des barrages, tableau défilant"
                    tabIndex={0}
                  >
                    <table>
                      <caption className="sr-only">
                        Derniers relevés des barrages de votre sélection
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Barrage</th>
                          <th scope="col">Réserve (Mm³)</th>
                          <th scope="col">Taux de remplissage</th>
                          <th scope="col">Date du relevé</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.slice(0, 5).map((row) => (
                          <tr key={row.reservoir.id}>
                            <th scope="row">
                              <Link href={`/barrages/${row.reservoir.id}`}>
                                {row.reservoir.name}
                              </Link>
                              <small>
                                <Provenance
                                  kind={row.latest?.data_kind ?? "UNVERIFIED"}
                                />
                              </small>
                            </th>
                            <td>{numberLabel(row.latest?.storage_mm3, 1)}</td>
                            <td>
                              {row.latest?.filling_rate_pct != null ? (
                                <>
                                  <strong>
                                    {numberLabel(
                                      row.latest.filling_rate_pct,
                                      1,
                                    )}{" "}
                                    %
                                  </strong>
                                  <span className="reference-progress">
                                    <span
                                      style={{
                                        width: `${Number(row.latest.filling_rate_pct)}%`,
                                        background:
                                          Number(row.latest.filling_rate_pct) >=
                                          50
                                            ? "#00bd98"
                                            : Number(
                                                  row.latest.filling_rate_pct,
                                                ) >= 20
                                              ? "#e2ad00"
                                              : "#e8494f",
                                      }}
                                    />
                                  </span>
                                </>
                              ) : (
                                "Non disponible"
                              )}
                            </td>
                            <td>{dateLabel(row.latest_date)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <Link className="all-reservoirs-link" href="/barrages">
                    Voir tous les barrages <span aria-hidden="true">→</span>
                  </Link>
                </section>
                <section className="panel reference-quality">
                  <div className="reference-panel-title">
                    <ShieldCheck />
                    <h2>Qualité des données</h2>
                  </div>
                  <div className="reference-quality-body">
                    <div
                      className="quality-ring"
                      style={
                        {
                          "--ring-value": `${accepted ?? 0}%`,
                        } as React.CSSProperties
                      }
                    >
                      <div>
                        <strong>
                          {accepted === null
                            ? "—"
                            : `${numberLabel(accepted, 1)} %`}
                        </strong>
                        <span>Lignes acceptées</span>
                      </div>
                    </div>
                    <dl>
                      <div>
                        <dt>
                          <CheckCircle2 />
                          Lignes acceptées
                        </dt>
                        <dd>
                          {accepted === null
                            ? "Non disponible"
                            : `${numberLabel(accepted, 1)} %`}
                        </dd>
                      </div>
                      <div>
                        <dt>
                          <CheckCircle2 />
                          Champs manquants
                        </dt>
                        <dd>
                          {quality
                            ? `${quality.missing_storage + quality.missing_filling_rate} / ${quality.observations * 2}`
                            : "—"}
                        </dd>
                      </div>
                      <div>
                        <dt>
                          <CheckCircle2 />
                          Signalements ouverts
                        </dt>
                        <dd>{quality?.unresolved_issues ?? "—"}</dd>
                      </div>
                    </dl>
                  </div>
                  <div className="quality-callout">
                    <Check size={21} />
                    <div>
                      <strong>
                        {quality?.rejected_rows === 0
                          ? "Aucun rejet à l’import"
                          : "Des lignes restent à vérifier"}
                      </strong>
                      <p>
                        {quality?.rows_read ?? 0} lignes contrôlées ·{" "}
                        {quality?.rejected_rows ?? 0} rejetées
                      </p>
                    </div>
                  </div>
                  <p className="quality-footnote">
                    Contrôles d’import du mode actif, hors filtres. Ils ne
                    certifient pas la fiabilité hydrologique.
                  </p>
                </section>
                <section className="panel reference-ai">
                  <div className="reference-panel-title">
                    <BrainCircuit />
                    <h2>Analyses IA</h2>
                  </div>
                  <AiRow
                    href="/analyses-ia#previsions"
                    icon={<TrendingUp />}
                    title="Prévision des réserves"
                    description="Historique officiel insuffisant pour valider un modèle"
                  />
                  <AiRow
                    href="/analyses-ia"
                    icon={<Bell />}
                    title="Variations inhabituelles"
                    description="Analyse des relevés par Isolation Forest"
                  />
                  <AiRow
                    href="/analyses"
                    icon={<TrendingUp />}
                    title="Analyse des tendances"
                    description="Évolution historique et comparaison"
                  />
                </section>
              </div>
            </>
          )
        )}
      </div>
    </Shell>
  );
}

function Kpi({
  icon,
  title,
  value,
  unit,
  note,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  unit?: string;
  note?: string;
}) {
  return (
    <section className="dashboard-kpi">
      <span className="dashboard-kpi-icon">{icon}</span>
      <div>
        <h2>{title}</h2>
        <div
          className={`dashboard-kpi-value ${value === "Non disponible" ? "unavailable" : ""}`}
        >
          {value}
          {unit && <span>{unit}</span>}
        </div>
        <p>{note}</p>
      </div>
    </section>
  );
}
function AiRow({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link href={href} className="ai-feature-row">
      <span>{icon}</span>
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
      <ChevronRight size={18} />
    </Link>
  );
}
function MapPreview({ rows }: { rows: Snapshot[] }) {
  const [expanded, setExpanded] = useState(false);
  const located = rows.filter((row) => coordinates(row)).length;
  return (
    <section
      id="carte"
      className={`panel reference-map ${expanded ? "map-expanded" : ""}`}
    >
      <div className="reference-panel-title">
        <DamIcon />
        <div>
          <h2>Carte des barrages</h2>
          <p>Localisation et état de remplissage</p>
        </div>
        <button
          className="map-expand icon-button"
          onClick={() => setExpanded(!expanded)}
          aria-label={expanded ? "Réduire la carte" : "Agrandir la carte"}
          aria-expanded={expanded}
        >
          <Expand size={18} />
        </button>
      </div>
      <div className="map-preview-frame">
        <MapCanvas rows={rows} />
        {!located && (
          <div className="map-data-notice">
            <span className="map-notice-dot" />
            <div>
              <strong>Coordonnées vérifiées non disponibles</strong>
              <p>{rows.length} barrages suivis</p>
            </div>
          </div>
        )}
      </div>
      <p className="map-attribution">
        <Link href="/carte">Ouvrir la carte et ses filtres</Link>
      </p>
    </section>
  );
}
