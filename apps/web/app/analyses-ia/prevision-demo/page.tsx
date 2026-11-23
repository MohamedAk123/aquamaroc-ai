import Link from "next/link";
import { Shell } from "../../../components/shell";
import { readDemoForecast } from "../../../lib/demo-forecast";
import { dateLabel, numberLabel } from "../../../lib/format";

export const dynamic = "force-dynamic";

export default async function PrevisionDemo() {
  const report = await readDemoForecast();
  return (
    <Shell mode="demo">
      <div className="page-heading">
        <div>
          <h1>Prévisions de remplissage à J+7</h1>
          <p>Simulation hydrologique sur des barrages fictifs.</p>
        </div>
      </div>
      <Link href="/analyses-ia#previsions">Retour aux analyses IA</Link>
      {report ? (
        <>
          <section className="panel quality-journal">
            <h2>Résultats pour le {dateLabel(report.target)}</h2>
            <p>Prévision archivée, émise le {dateLabel(report.issued)}.</p>
            <div className="journal-table" role="region" aria-label="Taux par barrage fictif" tabIndex={0}>
              <table>
                <thead>
                  <tr>
                    <th scope="col">Barrage fictif</th>
                    <th scope="col">Taux initial</th>
                    <th scope="col">Taux prévu à J+7</th>
                    {report.directFilling && report.selected === "persistence" && (
                      <th scope="col">Candidat H2O</th>
                    )}
                    <th scope="col">Réserve prévue</th>
                    <th scope="col">Capacité fictive</th>
                  </tr>
                </thead>
                <tbody>
                  {report.reservoirs.map((row) => (
                    <tr key={row.name}>
                      <th scope="row">{row.name}</th>
                      <td>{numberLabel(row.initial)} %</td>
                      <td><strong>{numberLabel(row.filling)} %</strong></td>
                      {report.directFilling && report.selected === "persistence" && (
                        <td>{numberLabel(row.candidate)} %</td>
                      )}
                      <td>{numberLabel(row.storage)} Mm³</td>
                      <td>{numberLabel(row.capacity)} Mm³</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p>
              {report.directFilling
                ? "La cible du modèle est le taux de remplissage. La réserve est calculée à partir de la capacité fictive."
                : "Ce rapport archivé déduit le taux de la réserve estimée."}
            </p>
          </section>
          <section className="panel quality-journal">
            <h2>Météo utilisée</h2>
            <p>Prévisions Open-Meteo pour le point {report.mountainPoint}.</p>
            <ul>
              <li>Pluie cumulée sur sept jours — {numberLabel(report.rain)} mm</li>
              <li>
                Neige cumulée sur sept jours — {numberLabel(report.snow)} mm
                d’équivalent eau selon la conversion du scénario
              </li>
              <li>Température moyenne — {numberLabel(report.temperature)} °C</li>
            </ul>
            <p><a href="https://open-meteo.com/en/docs">Source Open-Meteo</a></p>
          </section>
          <section className="panel quality-journal">
            <h2>Hypothèses du scénario</h2>
            <p>
              Les taux initiaux du tableau sont des hypothèses.{" "}
              Stock initial de neige supposé de {numberLabel(report.initialSnow)} mm
              d’équivalent eau. Le simulateur en déduit une fonte de{" "}
              {numberLabel(report.estimatedMelt)} mm d’équivalent eau sur sept jours.
            </p>
          </section>
          <section className="panel quality-journal">
            <h2>Évaluation sur données synthétiques</h2>
            <p>
              Modèle retenu sur validation —{" "}
              {report.selected === "h2o_automl" ? "H2O AutoML" : "Persistance"}.
              Candidat H2O — {report.h2oCandidate}.
            </p>
            <p>
              Erreur absolue moyenne sur le test — {numberLabel(report.modelMae)}{" "}
              {report.directFilling ? "points de pourcentage" : "Mm³"} pour le modèle
              retenu, {numberLabel(report.persistenceMae)}{" "}
              {report.directFilling ? "points" : "Mm³"} pour
              la référence qui conserve la dernière réserve.
            </p>
            <details>
              <summary>Identifiant du run MLflow</summary>
              <code>{report.runId}</code>
            </details>
          </section>
        </>
      ) : (
        <section className="panel quality-journal">
          <h2>Résultat DEMO indisponible</h2>
          <p>Le rapport de simulation à J+7 est absent ou illisible.</p>
        </section>
      )}
    </Shell>
  );
}
