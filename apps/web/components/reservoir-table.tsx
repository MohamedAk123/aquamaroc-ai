"use client";
import Link from "next/link";
import { ArrowDown, ArrowUp, ArrowUpRight } from "lucide-react";
import { useState } from "react";
import { dateLabel, numberLabel } from "../lib/format";
import { usePreferences } from "../lib/preferences";
import type { Snapshot } from "../lib/types";
import { Provenance } from "./status";
import { Button } from "./ui/button";

type Sort = "name" | "date" | "storage" | "filling";
export function ReservoirTable({ rows }: { rows: Snapshot[] }) {
  const [sort, setSort] = useState<Sort>("name");
  const [ascending, setAscending] = useState(true);
  const [page, setPage] = useState(0);
  const { reservoirPageSize } = usePreferences();
  const count = Math.ceil(rows.length / reservoirPageSize);
  const currentPage = Math.min(page, Math.max(0, count - 1));
  function value(row: Snapshot) {
    return sort === "name"
      ? row.reservoir.name
      : sort === "date"
        ? row.latest_date
        : sort === "storage"
          ? row.latest?.storage_mm3
          : row.latest?.filling_rate_pct;
  }
  const sorted = [...rows].sort((a, b) => {
    const left = value(a),
      right = value(b);
    if (left == null) return right == null ? 0 : 1;
    if (right == null) return -1;
    const compared =
      sort === "storage" || sort === "filling"
        ? Number(left) - Number(right)
        : left.localeCompare(right, "fr");
    return compared * (ascending ? 1 : -1);
  });
  function header(label: string, key: Sort) {
    return (
      <th
        scope="col"
        aria-sort={
          sort === key ? (ascending ? "ascending" : "descending") : "none"
        }
      >
        <button
          className="sort-button"
          onClick={() => {
            setSort(key);
            setAscending(sort === key ? !ascending : true);
          }}
        >
          {label}
          {sort === key ? (
            ascending ? (
              <ArrowUp size={13} />
            ) : (
              <ArrowDown size={13} />
            )
          ) : null}
        </button>
      </th>
    );
  }
  return (
    <>
      <div
        className="table-scroll"
        role="region"
        aria-label="Tableau des barrages, défilement horizontal possible"
        tabIndex={0}
      >
        <table>
          <caption className="sr-only">
            Dernière observation de chaque barrage dans la période sélectionnée,
            sans mélange de sources.
          </caption>
          <thead>
            <tr>
              {header("Barrage", "name")}
              <th scope="col">Bassin</th>
              {header("Réserve (Mm³)", "storage")}
              {header("Remplissage (%)", "filling")}
              {header("Date du relevé", "date")}
              <th scope="col">Provenance / qualité</th>
              <th scope="col">
                <span className="sr-only">Détail</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted
              .slice(currentPage * reservoirPageSize, (currentPage + 1) * reservoirPageSize)
              .map((row) => (
                <tr key={row.reservoir.id}>
                  <th scope="row">
                    <Link
                      className="reservoir-link"
                      href={`/barrages/${row.reservoir.id}`}
                    >
                      {row.reservoir.name}
                    </Link>
                  </th>
                  <td>{row.basin_name}</td>
                  <td className="numeric">
                    {numberLabel(row.latest?.storage_mm3)}
                  </td>
                  <td>
                    {row.latest?.filling_rate_pct != null ? (
                      <div className="filling-cell">
                        <span>
                          {numberLabel(row.latest.filling_rate_pct, 1)} %
                        </span>
                        <span className="progress-track" aria-hidden="true">
                          <span
                            style={{
                              width: `${Number(row.latest.filling_rate_pct)}%`,
                            }}
                          />
                        </span>
                      </div>
                    ) : (
                      "Non disponible"
                    )}
                  </td>
                  <td>{dateLabel(row.latest_date)}</td>
                  <td>
                    {row.latest ? (
                      <>
                        <Provenance kind={row.latest.data_kind} />
                        <small className="quality-label">
                          {row.latest.quality_status === "VALID"
                            ? "Contrôles de format valides"
                            : row.latest.quality_status}
                        </small>
                      </>
                    ) : (
                      <span className="provenance kind-unverified">
                        Sources multiples · à comparer
                      </span>
                    )}
                  </td>
                  <td>
                    <Link
                      href={`/barrages/${row.reservoir.id}`}
                      className="icon-link"
                      aria-label={`Voir ${row.reservoir.name}`}
                    >
                      <ArrowUpRight size={18} />
                    </Link>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">
        <span>
          {rows.length} barrage{rows.length > 1 ? "s" : ""} dans cette sélection
        </span>
        {count > 1 && (
          <div className="pagination">
            <Button
              variant="outline"
              disabled={currentPage === 0}
              onClick={() => setPage(currentPage - 1)}
            >
              Précédent
            </Button>
            <span>
              Page {currentPage + 1} / {count}
            </span>
            <Button
              variant="outline"
              disabled={currentPage >= count - 1}
              onClick={() => setPage(currentPage + 1)}
            >
              Suivant
            </Button>
          </div>
        )}
      </div>
    </>
  );
}
