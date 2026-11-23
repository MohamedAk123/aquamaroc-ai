"use client";
import { ErrorState } from "../components/status";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main>
      <ErrorState message="La page n’a pas pu être chargée." retry={reset} />
    </main>
  );
}
