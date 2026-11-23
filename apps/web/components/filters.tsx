import type { Basin, Filters as FilterValues, Source } from "../lib/types";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button } from "./ui/button";

export function Filters({
  values,
  onChange,
  onReset,
  onApply,
  basins,
  sources,
  detail = false,
  mode,
}: {
  values: FilterValues;
  onChange: (next: FilterValues) => void;
  onReset: () => void;
  onApply: () => void;
  basins: Basin[];
  sources: Source[];
  detail?: boolean;
  mode: string;
}) {
  function update(key: keyof FilterValues, value: string) {
    onChange({ ...values, [key]: value });
  }
  const invalid = Boolean(
    values.start_date && values.end_date && values.start_date > values.end_date,
  );
  return (
    <section className="filter-panel" aria-label="Filtres des observations">
      <div className="filter-title">
        <SlidersHorizontal size={16} />
        <span>Votre sélection</span>
        <Button variant="ghost" onClick={onReset}>
          Réinitialiser
        </Button>
      </div>
      <form
        className="filter-grid"
        onSubmit={(e) => {
          e.preventDefault();
          if (!invalid) onApply();
        }}
      >
        {!detail && (
          <label>
            Bassin
            <select
              value={values.basin_id}
              onChange={(e) => update("basin_id", e.target.value)}
            >
              <option value="">Tous les bassins</option>
              {basins.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Du
          <input
            type="date"
            value={values.start_date}
            max={values.end_date || undefined}
            onChange={(e) => update("start_date", e.target.value)}
            aria-invalid={invalid}
            aria-describedby={invalid ? "date-error" : undefined}
          />
        </label>
        <label>
          Au
          <input
            type="date"
            value={values.end_date}
            min={values.start_date || undefined}
            onChange={(e) => update("end_date", e.target.value)}
            aria-invalid={invalid}
          />
        </label>
        {!detail && (
          <label className="search-field">
            Rechercher un barrage
            <span>
              <Search size={16} />
              <input
                type="search"
                placeholder="Nom du barrage…"
                value={values.search}
                onChange={(e) => update("search", e.target.value)}
              />
            </span>
          </label>
        )}
        <label>
          Source
          <select
            value={values.source_id}
            onChange={(e) => update("source_id", e.target.value)}
          >
            <option value="">Toutes les sources</option>
            {sources.map((s) => (
              <option key={s.source_id} value={s.source_id}>
                {s.title}
              </option>
            ))}
          </select>
        </label>
        {mode === "official" && (
          <label>
            Provenance
            <select
              value={values.data_kind}
              onChange={(e) => update("data_kind", e.target.value)}
            >
              <option value="">Tous les statuts</option>
              <option value="OFFICIAL">Officielle</option>
              <option value="UNVERIFIED">Non vérifiée</option>
            </select>
          </label>
        )}
        <Button type="submit" disabled={invalid}>
          Appliquer
        </Button>
      </form>
      {invalid && (
        <p id="date-error" className="field-error" role="alert">
          La date de début doit précéder la date de fin.
        </p>
      )}
    </section>
  );
}
