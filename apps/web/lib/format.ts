export const dateLabel = (value: string | null | undefined) =>
  value
    ? new Intl.DateTimeFormat("fr-MA", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }).format(new Date(value.length === 10 ? `${value}T00:00:00Z` : value))
    : "Non disponible";
export const numberLabel = (
  value: string | number | null | undefined,
  digits = 2,
) =>
  value === null || value === undefined
    ? "Non disponible"
    : new Intl.NumberFormat("fr-MA", { maximumFractionDigits: digits }).format(
        Number(value),
      );
export const reasons: Record<string, string> = {
  no_data: "Aucune observation dans cette sélection.",
  multiple_sources:
    "Plusieurs sources au même relevé : sélectionnez une source.",
  different_dates: "Les derniers relevés ne sont pas datés du même jour.",
  mixed_provenance: "Les statuts de provenance diffèrent : affinez le filtre.",
  missing_storage: "Certaines réserves ne sont pas renseignées.",
  unverified_capacities:
    "Les capacités vérifiées ne sont pas disponibles pour tous les barrages.",
};
