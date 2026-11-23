"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Map as LibreMap, Marker } from "maplibre-gl";
import type { Snapshot } from "../lib/types";
import { dateLabel, numberLabel } from "../lib/format";
import { Provenance } from "./status";

export const bands = [
  { label: "Moins de 20 %", min: 0, max: 20, color: "#be123c" },
  { label: "20 à moins de 50 %", min: 20, max: 50, color: "#a55c08" },
  { label: "50 à moins de 80 %", min: 50, max: 80, color: "#1d61b4" },
  { label: "80 % et plus", min: 80, max: 101, color: "#087655" },
];

function bandOf(row: Snapshot) {
  const rate = row.latest?.filling_rate_pct;
  return rate == null
    ? -1
    : bands.findIndex((b) => Number(rate) >= b.min && Number(rate) < b.max);
}

export function coordinates(row: Snapshot): [number, number] | null {
  const { latitude, longitude, coordinates_source: source } = row.reservoir;
  if (
    !source?.trim() ||
    latitude == null ||
    longitude == null ||
    !String(latitude).trim() ||
    !String(longitude).trim()
  )
    return null;
  const lat = Number(latitude),
    lng = Number(longitude);
  return Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    Math.abs(lat) <= 90 &&
    Math.abs(lng) <= 180
    ? [lng, lat]
    : null;
}

export function MapCanvas({
  rows,
  onPick,
}: {
  rows: Snapshot[];
  onPick?: (id: string) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LibreMap | null>(null);
  const moduleRef = useRef<typeof import("maplibre-gl") | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let disposed = false;
    let map: LibreMap | undefined;
    let resize: ResizeObserver | undefined;
    void import("maplibre-gl")
      .then((lib) => {
        if (disposed || !container.current) return;
        moduleRef.current = lib;
        map = new lib.Map({
          container: container.current,
          center: [-8.4, 31.55],
          zoom: 6,
          maxZoom: 17,
          scrollZoom: false,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
              },
            },
            layers: [{ id: "fond", type: "raster", source: "osm" }],
          },
        });
        mapRef.current = map;
        map.addControl(
          new lib.NavigationControl({ showCompass: false }),
          "top-right",
        );
        map.on("error", () => {
          if (!disposed)
            setError("Certaines tuiles du fond sont indisponibles.");
        });
        resize = new ResizeObserver(() => map?.resize());
        resize.observe(container.current);
        setReady(true);
      })
      .catch(() => {
        if (!disposed)
          setError("La carte nécessite un navigateur compatible WebGL.");
      });
    return () => {
      disposed = true;
      resize?.disconnect();
      map?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current,
      lib = moduleRef.current;
    if (!ready || !map || !lib) return;
    const markers: Marker[] = [];
    const bounds = new lib.LngLatBounds();
    for (const row of rows) {
      const point = coordinates(row);
      if (!point) continue;
      const key = row.reservoir.id;
      const label = row.reservoir.name;
      const marker = document.createElement(onPick ? "button" : "a");
      marker.className = "dam-marker";
      marker.setAttribute("aria-label", label);
      marker.title = label;
      marker.style.backgroundColor = bands[bandOf(row)]?.color ?? "#475569";
      if (onPick) {
        marker.setAttribute("type", "button");
        marker.onclick = () => onPick(key);
      } else
        marker.setAttribute("href", `/barrages/${encodeURIComponent(key)}`);
      markers.push(
        new lib.Marker({ element: marker }).setLngLat(point).addTo(map),
      );
      bounds.extend(point);
    }
    if (markers.length)
      map.fitBounds(bounds, { padding: 50, maxZoom: 11, duration: 0 });
    return () => {
      markers.forEach((marker) => marker.remove());
    };
  }, [ready, rows, onPick]);

  return (
    <>
      <div
        className="libre-map"
        ref={container}
        role="region"
        aria-label="Fond cartographique interactif"
      />
      {error && (
        <p className="libre-map-error" role="status">
          {error}
        </p>
      )}
      <a
        className="libre-attribution"
        href="https://www.openstreetmap.org/copyright"
      >
        © OpenStreetMap
      </a>
    </>
  );
}

export function ReservoirMap({ rows }: { rows: Snapshot[] }) {
  const [band, setBand] = useState("all");
  const [id, setId] = useState("");
  const selectedRows = useMemo(
    () => rows.filter((row) => band === "all" || bandOf(row) === Number(band)),
    [rows, band],
  );
  const located = selectedRows.filter((row) => coordinates(row)).length;
  const selected = selectedRows.find((row) => row.reservoir.id === id);
  return (
    <section className="panel geographic-panel" aria-labelledby="map-title">
      <h2 id="map-title">Localisation des barrages</h2>
      <label className="geo-filter">
        Taux du dernier relevé dans la période
        <select value={band} onChange={(e) => setBand(e.target.value)}>
          <option value="all">Tous les taux</option>
          {bands.map((b, i) => (
            <option value={i} key={b.label}>
              {b.label}
            </option>
          ))}
          <option value="-1">Taux indisponible</option>
        </select>
      </label>
      <ul className="map-legend" aria-label="Légende du remplissage">
        {[...bands, { label: "Indisponible", color: "#475569" }].map((b) => (
          <li key={b.label}>
            <span style={{ backgroundColor: b.color }} aria-hidden="true" />
            {b.label}
          </li>
        ))}
      </ul>
      <div className="geographic-grid">
        <div className="geographic-map">
          <MapCanvas rows={selectedRows} onPick={setId} />
        </div>
        <aside className="geographic-detail" aria-label="Résultats et détail">
          <p role="status">
            {located} sur {selectedRows.length} barrage(s) localisé(s)
          </p>
          {located === 0 && (
            <p>Coordonnées vérifiées non disponibles pour cette sélection.</p>
          )}
          {selectedRows.length === 0 && (
            <p>Aucun barrage ne correspond à ce taux.</p>
          )}
          <ul>
            {selectedRows.map((row) => (
              <li key={row.reservoir.id}>
                <button
                  type="button"
                  aria-pressed={row.reservoir.id === id}
                  onClick={() => setId(row.reservoir.id)}
                >
                  {row.reservoir.name}
                </button>
              </li>
            ))}
          </ul>
          {selected && (
            <div className="geographic-selection">
              <h3>{selected.reservoir.name}</h3>
              <p>
                {selected.basin_name} · {dateLabel(selected.latest_date)}
              </p>
              <p>Réserve : {numberLabel(selected.latest?.storage_mm3)} Mm³</p>
              <p>
                Remplissage :{" "}
                {numberLabel(selected.latest?.filling_rate_pct, 1)} %
              </p>
              {selected.latest && (
                <Provenance kind={selected.latest.data_kind} />
              )}
              <p>
                {coordinates(selected)
                  ? `Source géographique : ${selected.reservoir.coordinates_source}`
                  : "Coordonnées non disponibles."}
              </p>
              <Link href={`/barrages/${selected.reservoir.id}`}>
                Voir l’historique du barrage
              </Link>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
