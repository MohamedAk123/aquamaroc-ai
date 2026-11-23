import { AlertCircle, Database, LoaderCircle } from "lucide-react";
import { Button } from "./ui/button";

export function LoadingState() {
  return (
    <div className="state" role="status" aria-live="polite">
      <LoaderCircle size={28} className="spin" />
      <h2>Chargement des observations</h2>
      <p>Récupération des relevés et de leur provenance…</p>
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry: () => void;
}) {
  return (
    <div className="state error-state" role="alert">
      <AlertCircle size={30} />
      <h2>Les données ne sont pas accessibles</h2>
      <p>{message}</p>
      <p>Aucune mesure n’est remplacée par des données fictives.</p>
      <Button onClick={retry}>Réessayer</Button>
    </div>
  );
}
export function EmptyState({ reset }: { reset?: () => void }) {
  return (
    <div className="state">
      <Database size={30} />
      <h2>Aucune observation pour cette sélection</h2>
      <p>Essayez une autre période ou retirez un filtre.</p>
      {reset && (
        <Button variant="outline" onClick={reset}>
          Réinitialiser les filtres
        </Button>
      )}
    </div>
  );
}
export function Provenance({ kind }: { kind: string }) {
  return (
    <span className={`provenance kind-${kind.toLowerCase()}`}>
      {kind === "DEMO"
        ? "DEMO · Synthétique"
        : kind === "OFFICIAL"
          ? "Source officielle"
          : "Non vérifié"}
    </span>
  );
}
