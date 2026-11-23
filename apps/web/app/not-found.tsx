import Link from "next/link";
export default function NotFound() {
  return (
    <main className="not-found">
      <h1>Page introuvable</h1>
      <p>Cette page n’est pas disponible.</p>
      <Link href="/">Retour au tableau de bord</Link>
    </main>
  );
}
