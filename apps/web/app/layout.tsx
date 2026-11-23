import type { Metadata } from "next";
import type { ReactNode } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import "./theme.css";
import "./reference.css";
import "./geographic.css";

export const metadata: Metadata = {
  title: "AquaMaroc AI — Observatoire hydrique",
  description:
    "Historiques, réserves et provenance des observations hydriques suivies au Maroc.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
