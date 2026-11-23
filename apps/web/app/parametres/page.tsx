"use client";

import { useState } from "react";
import { Shell } from "../../components/shell";
import { Button } from "../../components/ui/button";
import {
  defaultPreferences,
  pageSizes,
  savePreferences,
  type HistoryMetric,
  type Preferences,
  usePreferences,
} from "../../lib/preferences";

export default function Parametres() {
  const saved = usePreferences();
  const [draft, setDraft] = useState<Preferences | null>(null);
  const [status, setStatus] = useState<"saved" | "reset" | "error" | null>(null);
  const values = draft ?? saved;

  function update(next: Preferences) {
    setDraft(next);
    setStatus(null);
  }

  function persist(preferences: Preferences, success: "saved" | "reset") {
    try {
      savePreferences(preferences);
      setDraft(null);
      setStatus(success);
    } catch {
      setStatus("error");
    }
  }

  return (
    <Shell>
      <div className="page-heading">
        <div>
          <h1>Paramètres</h1>
          <p>Préférences d’affichage enregistrées dans ce navigateur.</p>
        </div>
      </div>
      <form
        className="panel quality-journal preferences-form"
        onSubmit={(event) => {
          event.preventDefault();
          persist(values, "saved");
        }}
      >
        <div className="preferences-fields">
          <label>
            Unité par défaut des graphiques
            <select
              value={values.historyMetric}
              onChange={(event) =>
                update({
                  ...values,
                  historyMetric: event.target.value as HistoryMetric,
                })
              }
            >
              <option value="storage_mm3">Réserve (Mm³)</option>
              <option value="filling_rate_pct">Taux de remplissage (%)</option>
            </select>
          </label>
          <label>
            Barrages par page dans le tableau
            <select
              value={values.reservoirPageSize}
              onChange={(event) =>
                update({
                  ...values,
                  reservoirPageSize: Number(event.target.value),
                })
              }
            >
              {pageSizes.map((size) => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="preferences-actions">
          <Button type="submit">Enregistrer</Button>
          <Button
            variant="outline"
            onClick={() => persist(defaultPreferences, "reset")}
          >
            Rétablir les valeurs par défaut
          </Button>
        </div>
        {status === "error" && (
          <p role="alert">Le navigateur bloque l’enregistrement des préférences.</p>
        )}
        {(status === "saved" || status === "reset") && (
          <p role="status">
            {status === "saved"
              ? "Préférences enregistrées."
              : "Valeurs par défaut rétablies."}
          </p>
        )}
      </form>
    </Shell>
  );
}
