"use client";

import Link from "next/link";
import { useState } from "react";
import { Shell } from "../../components/shell";
import { LoadingState, ErrorState } from "../../components/status";
import { api } from "../../lib/api";
import { dateLabel, numberLabel } from "../../lib/format";
import { useRemote } from "../../lib/use-remote";

export default function AnalysesIA() {
  const [attempt, setAttempt] = useState(0);
  const state = useRemote(`variations:${attempt}`, api.variationReview);
  const result = state.data?.report;
  return (
    <Shell mode={state.data?.mode}>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ANALYSE DES RELEVÉS OFFICIELS</p>
          <h1>Variations inhabituelles · IA</h1>
          <p>Points de l’historique à examiner en priorité.</p>
        </div>
      </div>
      <section id="previsions" className="panel quality-journal">
        <h2>Prévisions officielles de réserves et de remplissage</h2>
        <p>
          Les horizons à 7 et 30 jours restent indisponibles. Les bulletins
          datés disponibles ne permettent pas encore une validation
          chronologique des prévisions sur les barrages suivis.
        </p>
        <Link href="/analyses-ia/prevision-demo" className="button button-outline">
          Voir les prévisions de remplissage DEMO à J+7
        </Link>
      </section>
      {state.loading ? (
        <LoadingState />
      ) : state.error ? (
        <ErrorState
          message={state.error.message}
          retry={() => setAttempt((a) => a + 1)}
        />
      ) : !result ? (
        <section className="panel quality-journal">
          <h2>Analyse indisponible</h2>
          <p>Aucun rapport IA ne correspond aux relevés du jeu actif.</p>
        </section>
      ) : (
        <>
          <section className="panel quality-journal">
            <h2>Étude rétrospective avec {result.model}</h2>
            <p>
              {result.findings.length} variations à examiner sur{" "}
              {result.analysed_samples} relevés analysés.
            </p>
            <p>
              Analyse du {dateLabel(result.analysed_start)} au{" "}
              {dateLabel(result.analysed_end)}. Référence :{" "}
              {dateLabel(result.reference_start)} au{" "}
              {dateLabel(result.reference_end)}.
            </p>
            <p>
              Le modèle compare les écarts de réserve sur 1 et 7 jours au
              comportement antérieur du même barrage. Un signalement appelle une
              vérification des relevés et du contexte hydrologique.
            </p>
          </section>
          <section className="panel quality-journal">
            <h2>Relevés à vérifier</h2>
            {result.findings.length === 0 ? (
              <p>Aucun relevé au-delà du seuil de tri.</p>
            ) : (
              <div
                className="journal-table"
                role="region"
                aria-label="Variations inhabituelles"
                tabIndex={0}
              >
                <table>
                  <thead>
                    <tr>
                      <th>Barrage</th>
                      <th>Relevé</th>
                      <th>Réserve (Mm³)</th>
                      <th>Écart sur 1 j (Mm³)</th>
                      <th>Écart sur 7 j (Mm³)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.findings.map((row) => (
                      <tr key={`${row.reservoir_id}:${row.observation_date}`}>
                        <th scope="row">
                          <Link href={`/barrages/${row.reservoir_id}`}>
                            {row.reservoir_name}
                          </Link>
                        </th>
                        <td>{dateLabel(row.observation_date)}</td>
                        <td>{numberLabel(row.storage_mm3, 3)}</td>
                        <td>{numberLabel(row.delta_1d_mm3, 3)}</td>
                        <td>{numberLabel(row.delta_7d_mm3, 3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <Link href="/sources">Consulter les sources officielles</Link>
          </section>
        </>
      )}
    </Shell>
  );
}
