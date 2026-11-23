"use client";
import Link from "next/link";
import { useCallback, useState, type ReactNode } from "react";
import {
  ArrowUpRight,
  CalendarDays,
  Database,
  Droplets,
  RefreshCw,
  ShieldCheck,
  Waves,
} from "lucide-react";
import { api } from "../lib/api";
import { useRemote } from "../lib/use-remote";
import { dateLabel, numberLabel } from "../lib/format";
import {
  emptyFilters,
  type Filters as FilterValues,
  type Measurement,
  type Quality,
  type Source,
} from "../lib/types";
import { Shell } from "./shell";
import { Filters } from "./filters";
import { EmptyState, ErrorState, LoadingState } from "./status";
import { ReservoirTable } from "./reservoir-table";
import { HistoryPanel } from "./history-panel";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { ReferenceDashboard } from "./reference-dashboard";
import { ReservoirMap } from "./reservoir-map";
import { QualityJournal } from "./quality-journal";

type View =
  | "dashboard"
  | "reservoirs"
  | "detail"
  | "analyses"
  | "sources"
  | "quality"
  | "map"
  | "reports";
const titles: Record<View, [string, string]> = {
  dashboard: [
    "Tableau de bord",
    "Un regard clair sur les réserves en eau suivies.",
  ],
  reservoirs: [
    "Barrages",
    "Retrouvez les relevés, leur date et leur provenance.",
  ],
  detail: [
    "Détail du barrage",
    "Un historique lisible, une source pour chaque observation.",
  ],
  analyses: [
    "Analyses et tendances",
    "Explorez les observations passées, sans extrapolation.",
  ],
  sources: [
    "Sources et méthodologie",
    "Comprendre l’origine, la portée et les limites des données.",
  ],
  quality: [
    "Qualité des données",
    "Des contrôles documentés, sans confondre qualité et risque hydrologique.",
  ],
  map: [
    "Carte des barrages",
    "Localisations vérifiées et derniers relevés de la sélection.",
  ],
  reports: [
    "Rapports et exports",
    "Consultez puis exportez les relevés de votre sélection.",
  ],
};

export function Workspace({
  view = "dashboard",
  reservoirId = "",
}: {
  view?: View;
  reservoirId?: string;
}) {
  const [refresh, setRefresh] = useState(0);
  const [draft, setDraft] = useState<FilterValues>(emptyFilters);
  const [filters, setFilters] = useState<FilterValues>(emptyFilters);
  const [chartSelection, setChartSelection] = useState("");
  const loadBoot = useCallback(async (signal: AbortSignal) => {
    const [basins, sources, quality] = await Promise.all([
      api.basins(signal),
      api.sources(signal),
      api.quality(signal),
    ]);
    return { basins, sources, quality };
  }, []);
  const boot = useRemote(`boot:${refresh}`, loadBoot);
  const needsOverview = !["detail", "sources", "quality"].includes(view);
  const loadOverview = useCallback(
    (signal: AbortSignal) => api.overview(filters, signal),
    [filters],
  );
  const overview = useRemote(
    `overview:${refresh}:${JSON.stringify(filters)}`,
    loadOverview,
    needsOverview,
  );
  const loadDetail = useCallback(
    (signal: AbortSignal) => api.reservoir(reservoirId, signal),
    [reservoirId],
  );
  const detail = useRemote(
    `detail:${refresh}:${reservoirId}`,
    loadDetail,
    view === "detail",
  );
  const rows = overview.data?.reservoirs ?? [];
  const chartId =
    reservoirId ||
    (rows.some((row) => row.reservoir.id === chartSelection)
      ? chartSelection
      : (rows[0]?.reservoir.id ?? ""));
  const chartReservoir =
    view === "detail"
      ? detail.data
      : rows.find((row) => row.reservoir.id === chartId)?.reservoir;
  const wantsHistory = ["dashboard", "analyses", "detail", "reports"].includes(
    view,
  );
  const loadHistory = useCallback(
    (signal: AbortSignal) => api.history(chartId, filters, signal),
    [chartId, filters],
  );
  const history = useRemote(
    `history:${refresh}:${chartId}:${JSON.stringify(filters)}`,
    loadHistory,
    wantsHistory && Boolean(chartId),
  );
  const sources = boot.data?.sources.items ?? [];
  const mode = boot.data?.sources.mode;
  const imported = sources
    .map((s) => s.latest_ingested_at)
    .filter((x): x is string => x !== null)
    .sort()
    .at(-1);
  const error =
    boot.error ||
    (needsOverview
      ? overview.error
      : view === "detail"
        ? detail.error
        : undefined);
  const loading =
    boot.loading ||
    (needsOverview
      ? overview.loading
      : view === "detail"
        ? detail.loading
        : false);
  const retry = () => setRefresh((value) => value + 1);
  const reset = () => {
    setDraft(emptyFilters);
    setFilters(emptyFilters);
  };
  const hasFilters = Object.values(filters).some(Boolean);
  const selector =
    view !== "detail" ? (
      <>
        <label className="sr-only" htmlFor="history-reservoir">
          Barrage du graphique
        </label>
        <select
          id="history-reservoir"
          value={chartId}
          onChange={(event) => setChartSelection(event.target.value)}
        >
          {rows.map((row) => (
            <option key={row.reservoir.id} value={row.reservoir.id}>
              {row.reservoir.name}
            </option>
          ))}
        </select>
      </>
    ) : undefined;
  const latestDate = history.data?.items.at(-1)?.observation_date;
  const latestRows =
    history.data?.items.filter((row) => row.observation_date === latestDate) ??
    [];
  const latest = latestRows.length === 1 ? latestRows[0] : undefined;
  if (view === "dashboard")
    return (
      <ReferenceDashboard
        mode={mode}
        imported={imported}
        boot={boot}
        overview={overview}
        history={history}
        filters={filters}
        draft={draft}
        setDraft={setDraft}
        apply={setFilters}
        reset={reset}
        retry={retry}
        chartId={chartId}
        setChartId={setChartSelection}
      />
    );
  return (
    <Shell mode={mode} importedAt={imported}>
      <div className="page-heading">
        <div>
          <p className="eyebrow">OBSERVATOIRE DES RESSOURCES HYDRIQUES</p>
          <h1>
            {view === "detail"
              ? (detail.data?.name ?? titles[view][0])
              : titles[view][0]}
          </h1>
          <p>{titles[view][1]}</p>
        </div>
        <Button variant="outline" onClick={retry} disabled={loading}>
          <RefreshCw size={15} />
          Actualiser
        </Button>
      </div>
      {view === "detail" && (
        <Link className="back-link" href="/barrages">
          ← Retour aux barrages
        </Link>
      )}
      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error.message} retry={retry} />
      ) : (
        boot.data && (
          <>
            {!["sources", "quality"].includes(view) && (
              <Filters
                values={draft}
                onChange={setDraft}
                onApply={() => setFilters({ ...draft })}
                onReset={reset}
                basins={boot.data.basins.items}
                sources={sources}
                detail={view === "detail"}
                mode={mode ?? "demo"}
              />
            )}
            {hasFilters && (
              <p className="selection-note">
                Sélection appliquée :{" "}
                {filters.start_date
                  ? dateLabel(filters.start_date)
                  : "début de l’historique"}{" "}
                →{" "}
                {filters.end_date
                  ? dateLabel(filters.end_date)
                  : "fin de l’historique"}
                {filters.search ? ` · « ${filters.search} »` : ""}
              </p>
            )}
            {needsOverview && rows.length === 0 ? (
              <EmptyState reset={reset} />
            ) : (
              <>
                {view === "detail" && history.data && (
                  <div className="metrics-grid detail-metrics">
                    <Metric
                      title="Dernière réserve de la sélection"
                      value={numberLabel(latest?.storage_mm3)}
                      unit={latest?.storage_mm3 != null ? "Mm³" : undefined}
                      note={
                        latestRows.length > 1
                          ? "Sources multiples : affinez le filtre"
                          : "Valeur observée, sans extrapolation"
                      }
                      icon={<Waves size={20} />}
                    />
                    <Metric
                      title="Taux de remplissage observé"
                      value={numberLabel(latest?.filling_rate_pct, 1)}
                      unit={latest?.filling_rate_pct != null ? "%" : undefined}
                      note="Taux fourni par la source du relevé"
                      icon={<Droplets size={20} />}
                    />
                    <Metric
                      title="Dernier relevé de la sélection"
                      value={dateLabel(latestDate)}
                      note="Date de mesure ; pas une date de mise à jour"
                      icon={<CalendarDays size={20} />}
                    />
                  </div>
                )}
                {wantsHistory && chartReservoir && (
                  <div className={""}>
                    {history.loading ? (
                      <Card>
                        <LoadingState />
                      </Card>
                    ) : history.error ? (
                      <Card>
                        <ErrorState
                          message={history.error.message}
                          retry={retry}
                        />
                      </Card>
                    ) : (
                      <HistoryPanel
                        rows={history.data?.items ?? []}
                        name={chartReservoir.name}
                        sources={sources}
                        selector={selector}
                      />
                    )}
                  </div>
                )}
                {view === "detail" && chartReservoir && (
                  <>
                    <div className="detail-facts">
                      <Card>
                        <h2>Capacité de référence</h2>
                        <strong>
                          {chartReservoir.capacity_source
                            ? `${numberLabel(chartReservoir.capacity_mm3)} Mm³`
                            : "Non disponible"}
                        </strong>
                        <p>
                          {chartReservoir.capacity_source
                            ? `Source : ${chartReservoir.capacity_source}`
                            : "Aucune capacité sourcée enregistrée. Aucun taux n’est déduit."}
                        </p>
                      </Card>
                      <Card>
                        <h2>Coordonnées</h2>
                        <strong>
                          {chartReservoir.coordinates_source &&
                          chartReservoir.latitude != null &&
                          chartReservoir.longitude != null
                            ? `${numberLabel(chartReservoir.latitude, 5)}, ${numberLabel(chartReservoir.longitude, 5)}`
                            : "Non disponibles"}
                        </strong>
                        <p>
                          {chartReservoir.coordinates_source ??
                            "Aucune position géographique n’est inventée."}
                        </p>
                      </Card>
                    </div>
                    {history.data && <Comparison rows={history.data.items} />}
                    <Card className="reading-note">
                      <h2>Comment lire ces données ?</h2>
                      <p>
                        La réserve est exprimée en millions de mètres cubes
                        (Mm³). Le remplissage est un pourcentage publié,
                        distinct de la réserve. Un contrôle de format valide
                        n’atteste pas l’exactitude physique du relevé. Les dates
                        de publication manquantes restent inconnues.
                      </p>
                      <p>
                        Les relevés synthétiques, officiels et non vérifiés sont
                        identifiés séparément. Une variation passée ne constitue
                        ni une prévision ni une alerte hydrologique.
                      </p>
                    </Card>
                  </>
                )}
                {view === "reservoirs" && (
                  <Card className="reservoirs-panel">
                    <div className="panel-heading">
                      <div>
                        <p className="eyebrow">SUIVI DES OBSERVATIONS</p>
                        <h2>{"Derniers relevés par barrage"}</h2>
                        <p>
                          Dernier relevé disponible dans la période, avec sa
                          provenance.
                        </p>
                      </div>
                    </div>
                    <ReservoirTable rows={rows} />
                  </Card>
                )}

                {view === "quality" && (
                  <>
                    <QualityCard quality={boot.data.quality} />
                    <QualityJournal mode={boot.data.quality.mode} />
                    <Card className="reading-note">
                      <h2>Ce que mesurent ces indicateurs</h2>
                      <p>
                        Le périmètre couvre tous les imports du mode actif,
                        indépendamment des filtres des autres écrans. Les rejets
                        concernent les lignes d’import ; les valeurs manquantes
                        concernent les observations conservées.
                      </p>
                      <p>
                        Les règles vérifient notamment les dates, les bornes et
                        les doublons. Le journal relie chaque signalement à son
                        fichier. Aucun indicateur ne constitue une alerte de
                        sécurité hydrologique.
                      </p>
                    </Card>
                  </>
                )}
                {view === "map" && <ReservoirMap rows={rows} />}
                {view === "sources" && <Sources sources={sources} />}
                {["analyses", "reports"].includes(view) && (
                  <Card className="reading-note">
                    <h2>
                      {view === "reports"
                        ? "Un export traçable"
                        : "Une analyse descriptive"}
                    </h2>
                    <p>
                      {view === "reports"
                        ? "L’export CSV reprend tous les relevés de la sélection du barrage, avec unités, provenance, source, licence et horodatages."
                        : "Les graphiques présentent uniquement les relevés disponibles. Les dates sans observation ne sont pas comblées ; les sources et statuts restent des séries distinctes."}
                    </p>
                  </Card>
                )}
              </>
            )}
          </>
        )
      )}
    </Shell>
  );
}

function Metric({
  title,
  value,
  unit,
  note,
  icon,
}: {
  title: string;
  value: string;
  unit?: string;
  note?: string;
  icon: ReactNode;
}) {
  return (
    <section className="metric">
      <div className="metric-label">
        {title}
        <span className="metric-icon">{icon}</span>
      </div>
      <div
        className={`metric-value ${value === "Non disponible" ? "metric-unavailable" : ""}`}
      >
        {value}
        {unit && <span>{unit}</span>}
      </div>
      <p>{note}</p>
    </section>
  );
}

function QualityCard({ quality }: { quality: Quality }) {
  return (
    <Card className="quality-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">
            <ShieldCheck size={14} />
            TRAÇABILITÉ & CONTRÔLES
          </p>
          <h2>Qualité des données</h2>
          <p>Tous les imports du mode actif · hors filtres de période</p>
        </div>
        <Link href="/qualite" className="text-link">
          Détails <ArrowUpRight size={14} />
        </Link>
      </div>
      <div className="quality-stats">
        <div>
          <strong>{quality.files_ingested}</strong>
          <span>Fichiers importés</span>
        </div>
        <div>
          <strong>{quality.observations}</strong>
          <span>Observations conservées</span>
        </div>
        <div>
          <strong>
            {quality.rejected_rows} / {quality.rows_read}
          </strong>
          <span>Lignes rejetées / lues</span>
        </div>
        <div>
          <strong>{quality.unresolved_issues}</strong>
          <span>Signalements ouverts</span>
        </div>
      </div>
      <p className="muted">
        Réserves manquantes : {quality.missing_storage} / {quality.observations}{" "}
        observations · Taux manquants : {quality.missing_filling_rate} /{" "}
        {quality.observations}.
      </p>
    </Card>
  );
}

function Sources({ sources }: { sources: Source[] }) {
  return (
    <>
      <div className="source-grid">
        {sources.length ? (
          sources.map((source) => (
            <Card key={source.source_id}>
              <div className="panel-heading">
                <Database size={23} />
                <span className="neutral-tag">
                  {source.verification_status === "DEMO"
                    ? "Synthétique"
                    : source.verification_status === "VERIFIED"
                      ? "Vérifiée"
                      : "À vérifier"}
                </span>
              </div>
              <h2>{source.title}</h2>
              <dl className="source-facts">
                <div>
                  <dt>Producteur</dt>
                  <dd>{source.producer ?? "Non renseigné"}</dd>
                </div>
                <div>
                  <dt>Dernier relevé</dt>
                  <dd>{dateLabel(source.latest_observation_date)}</dd>
                </div>
                <div>
                  <dt>Dernière publication connue</dt>
                  <dd>{dateLabel(source.latest_published_at)}</dd>
                </div>
                <div>
                  <dt>Dernier import</dt>
                  <dd>{dateLabel(source.latest_ingested_at)}</dd>
                </div>
                <div>
                  <dt>Licence</dt>
                  <dd>{source.license ?? "À vérifier"}</dd>
                </div>
                <div>
                  <dt>Statut d’import</dt>
                  <dd>{source.latest_run_status ?? "Aucun import"}</dd>
                </div>
              </dl>
              {source.dataset_url && /^https?:\/\//.test(source.dataset_url) ? (
                <a
                  className="text-link"
                  href={source.dataset_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Consulter la source <ArrowUpRight size={15} />
                </a>
              ) : (
                <p className="muted">
                  Aucune URL de ressource officielle associée.
                </p>
              )}
            </Card>
          ))
        ) : (
          <EmptyState />
        )}
      </div>
      <Card className="reading-note">
        <h2>Une information sourcée, avec ses limites</h2>
        <p>
          Le périmètre officiel cible le bassin du Tensift, sous réserve de
          validation des fichiers et de leur licence. Aucun fichier officiel n’a
          encore été audité. La{" "}
          <a
            href="https://data.gov.ma/data/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift"
            target="_blank"
            rel="noopener noreferrer"
          >
            fiche candidate du portail data.gov.ma
          </a>{" "}
          reste à vérifier.
        </p>
        <p>
          La date du relevé, la date de publication et celle de l’import
          décrivent trois événements différents. Une date de publication absente
          n’est pas remplacée par celle de l’import. Les données ne sont pas
          présentées comme du temps réel.
        </p>
        <p>
          Les réserves ne sont additionnées que lorsque les dates et statuts
          sont comparables, sans ambiguïté de source. Le taux pondéré utilise
          les réserves divisées par les capacités sourcées ; aucune moyenne
          simple des taux n’est présentée comme un taux global.
        </p>
      </Card>
    </>
  );
}

function Comparison({ rows }: { rows: Measurement[] }) {
  const dates = [...new Set(rows.map((row) => row.observation_date))].sort();
  const [chosenA, setA] = useState("");
  const [chosenB, setB] = useState("");
  const a = dates.includes(chosenA) ? chosenA : (dates[0] ?? ""),
    b = dates.includes(chosenB) ? chosenB : (dates.at(-1) ?? "");
  const left = rows.filter((row) => row.observation_date === a),
    right = rows.filter((row) => row.observation_date === b);
  const comparable =
    left.length === 1 &&
    right.length === 1 &&
    left[0].source_id === right[0].source_id &&
    left[0].data_kind === right[0].data_kind &&
    a !== b;
  const delta =
    comparable && left[0].storage_mm3 !== null && right[0].storage_mm3 !== null
      ? Number(right[0].storage_mm3) - Number(left[0].storage_mm3)
      : null;
  return (
    <Card>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">COMPARAISON HISTORIQUE</p>
          <h2>Comparer deux relevés disponibles</h2>
        </div>
        <CalendarDays size={20} />
      </div>
      {dates.length >= 2 ? (
        <>
          <div className="comparison-controls">
            <label>
              Relevé de départ
              <select value={a} onChange={(event) => setA(event.target.value)}>
                {dates.map((value) => (
                  <option key={value} value={value}>
                    {dateLabel(value)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Relevé de comparaison
              <select value={b} onChange={(event) => setB(event.target.value)}>
                {dates.map((value) => (
                  <option key={value} value={value}>
                    {dateLabel(value)}
                  </option>
                ))}
              </select>
            </label>
            <div>
              <span>Variation de réserve (comparaison − départ)</span>
              <strong>
                {delta === null
                  ? "Non disponible"
                  : `${delta > 0 ? "+" : ""}${numberLabel(delta)} Mm³`}
              </strong>
            </div>
          </div>
          {!comparable && (
            <p className="muted">
              Choisissez deux dates distinctes et une source unique de même
              provenance.
            </p>
          )}
        </>
      ) : (
        <p className="muted">
          Deux dates de relevé sont nécessaires ; aucune comparaison n’est
          inventée.
        </p>
      )}
    </Card>
  );
}
