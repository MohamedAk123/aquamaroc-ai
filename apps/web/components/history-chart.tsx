"use client";
import { useEffect, useRef } from "react";
import { graphic, init, use as registerECharts } from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { Measurement, Source } from "../lib/types";

registerECharts([
  LineChart,
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  SVGRenderer,
]);
export default function HistoryChart({
  rows,
  metric,
  name,
  sources,
  compact = false,
}: {
  rows: Measurement[];
  metric: "storage_mm3" | "filling_rate_pct";
  name: string;
  sources: Source[];
  compact?: boolean;
}) {
  const element = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!element.current) return;
    const chart = init(element.current, undefined, { renderer: "svg" });
    const groups = new Map<string, Measurement[]>();
    rows.forEach((row) => {
      const key = `${row.source_id}/${row.data_kind}`;
      groups.set(key, [...(groups.get(key) ?? []), row]);
    });
    const unit = metric === "storage_mm3" ? "Mm³" : "%";
    chart.setOption({
      animation: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      color: ["#007bff", "#0f766e", "#96550a", "#6d28d9"],
      aria: {
        enabled: true,
        label: {
          description: `Historique de ${name}, en ${unit}. Les valeurs, dates et sources sont disponibles dans le tableau accessible sous le graphique.`,
        },
      },
      grid: {
        left: 48,
        right: 18,
        top: compact ? 22 : 50,
        bottom: compact ? 50 : 72,
      },
      legend: {
        show: !compact,
        type: "scroll",
        top: 0,
        textStyle: { color: "#475569", fontSize: 11 },
      },
      tooltip: {
        trigger: "axis",
        renderMode: "richText",
        confine: true,
        valueFormatter: (value: number) =>
          value == null
            ? "Non disponible"
            : `${value.toLocaleString("fr-MA")} ${unit}`,
      },
      xAxis: {
        type: "time",
        minInterval: 86400000,
        axisLabel: {
          color: "#56657a",
          hideOverlap: true,
          formatter: (value: number) =>
            new Intl.DateTimeFormat("fr-MA", {
              day: "2-digit",
              month: "short",
              timeZone: "UTC",
            }).format(value),
        },
        axisLine: { lineStyle: { color: "#dce5ee" } },
        splitLine: { show: false },
      },
      yAxis: {
        scale: metric === "storage_mm3",
        type: "value",
        name: unit,
        min: metric === "filling_rate_pct" ? 0 : undefined,
        max: metric === "filling_rate_pct" ? 100 : undefined,
        axisLabel: { color: "#56657a" },
        splitLine: { lineStyle: { color: "#edf1f5", type: "dashed" } },
      },
      dataZoom: [
        { type: "inside", filterMode: "none" },
        {
          type: "slider",
          bottom: 8,
          height: 20,
          borderColor: "#dce5ee",
          fillerColor: "#087fb41a",
          showDetail: false,
        },
      ],
      series: [...groups.entries()].map(([key, data]) => ({
        name: `${sources.find((source) => source.source_id === data[0].source_id)?.title ?? data[0].source_id} · ${data[0].data_kind}`,
        id: key,
        type: "line",
        showSymbol: true,
        symbolSize: 8,
        connectNulls: false,
        lineStyle: { width: 3 },
        smooth: 0.25,
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#168fff66" },
            { offset: 1, color: "#168fff08" },
          ]),
        },
        data: [...data]
          .sort((a, b) => a.observation_date.localeCompare(b.observation_date))
          .map((row) => [
            `${row.observation_date}T00:00:00Z`,
            row[metric] === null ? null : Number(row[metric]),
          ]),
      })),
    });
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(element.current);
    return () => {
      observer.disconnect();
      chart.dispose();
    };
  }, [rows, metric, name, sources, compact]);
  return (
    <div
      ref={element}
      className="history-chart"
      role="img"
      aria-label={`Historique de ${name}, ${metric === "storage_mm3" ? "réserve en Mm³" : "remplissage en pourcentage"}`}
    />
  );
}
