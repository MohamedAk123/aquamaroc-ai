"use client";

import { useSyncExternalStore } from "react";

const storageKey = "aquamaroc.preferences";
const changeEvent = "aquamaroc:preferences";
export const pageSizes = [3, 5, 10, 20];
export type HistoryMetric = "storage_mm3" | "filling_rate_pct";
export type Preferences = {
  historyMetric: HistoryMetric;
  reservoirPageSize: number;
};
export const defaultPreferences: Preferences = {
  historyMetric: "storage_mm3",
  reservoirPageSize: 10,
};

export function parsePreferences(raw: string | null): Preferences {
  try {
    const parsed = JSON.parse(raw ?? "null");
    return {
      historyMetric:
        parsed?.historyMetric === "filling_rate_pct" ? "filling_rate_pct" : "storage_mm3",
      reservoirPageSize: pageSizes.includes(parsed?.reservoirPageSize)
        ? parsed.reservoirPageSize
        : defaultPreferences.reservoirPageSize,
    };
  } catch {
    return defaultPreferences;
  }
}

function readSnapshot() {
  try {
    return window.localStorage.getItem(storageKey);
  } catch {
    return null;
  }
}

function subscribe(change: () => void) {
  function storageChange(event: StorageEvent) {
    if (event.key === storageKey || event.key === null) change();
  }
  window.addEventListener("storage", storageChange);
  window.addEventListener(changeEvent, change);
  return () => {
    window.removeEventListener("storage", storageChange);
    window.removeEventListener(changeEvent, change);
  };
}

export function usePreferences(): Preferences {
  return parsePreferences(useSyncExternalStore(subscribe, readSnapshot, () => null));
}

export function savePreferences(preferences: Preferences) {
  window.localStorage.setItem(storageKey, JSON.stringify(preferences));
  window.dispatchEvent(new Event(changeEvent));
}
