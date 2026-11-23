"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bell,
  CircleHelp,
  Code2,
  ChevronRight,
  FileText,
  LayoutDashboard,
  MapPin,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Waves,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { dateLabel } from "../lib/format";
import type { Mode } from "../lib/types";

const links = [
  { href: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/barrages", label: "Barrages", icon: Waves },
  { href: "/carte", label: "Carte des barrages", icon: MapPin },
  { href: "/analyses", label: "Analyses & tendances", icon: BarChart3 },
  { href: "/analyses-ia", label: "Analyses IA", icon: Sparkles },
  { href: "/qualite", label: "Qualité des données", icon: ShieldCheck },
  { href: "/rapports", label: "Rapports", icon: FileText },
  { href: "/sources", label: "API & données", icon: Code2 },
  { href: "/parametres", label: "Paramètres", icon: Settings },
];

export function Shell({
  children,
  mode,
  importedAt,
  search,
  onSearch,
  issueCount,
}: {
  children: ReactNode;
  mode?: Mode;
  importedAt?: string | null;
  search?: string;
  onSearch?: (value: string) => void;
  issueCount?: number;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState(false);
  return (
    <div className="app-shell reference-shell">
      <a className="skip-link" href="#main-content">
        Aller au contenu
      </a>
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <Link href="/" className="brand" onClick={() => setOpen(false)}>
          <svg
            className="water-logo"
            width="48"
            height="61"
            viewBox="0 0 48 64"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="drop-blue" x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="#84e6ff" />
                <stop offset="1" stopColor="#008de8" />
              </linearGradient>
            </defs>
            <path
              d="M24 1C19 13 4 31 4 43a20 20 0 0040 0C44 31 29 13 24 1Z"
              fill="url(#drop-blue)"
            />
            <path
              d="M29 17C31 31 11 40 13 52c8 9 24 2 25-10 1-7-4-16-9-25Z"
              fill="#007ac5"
              opacity=".65"
            />
            <path
              d="M8 43c0 9 7 16 16 16"
              fill="none"
              stroke="#a7eeff"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
          <span>
            AquaMaroc AI
            <small>
              Observatoire des ressources
              <br />
              hydriques du Maroc
            </small>
          </span>
        </Link>
        <nav aria-label="Navigation principale">
          {links.map(({ href, label, icon: Icon }) => (
            <div key={href}>
              {href === "/parametres" && <div className="settings-divider" />}
              <Link
                href={href}
                className={`nav-link ${(href === pathname && !href.includes("#")) || (href === "/barrages" && pathname.startsWith("/barrages/")) ? "active" : ""}`}
                aria-label={
                  href === "/sources"
                    ? "API & données — Sources et méthode"
                    : undefined
                }
                aria-current={href === pathname ? "page" : undefined}
                onClick={() => setOpen(false)}
              >
                <Icon size={22} />
                <span>{label}</span>
              </Link>
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="sidebar-avatar">AM</span>
          <div>
            <strong>
              {mode === "demo"
                ? "Espace de démonstration"
                : "Observatoire AquaMaroc"}
            </strong>
            <small>
              {mode === "demo"
                ? "Données synthétiques"
                : "Consultation publique"}
            </small>
          </div>
          <ChevronRight size={18} />
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            aria-label={open ? "Fermer la navigation" : "Ouvrir la navigation"}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
          {onSearch ? (
            <form
              className="global-search"
              onSubmit={(event) => {
                event.preventDefault();
                onSearch(
                  String(new FormData(event.currentTarget).get("search") ?? ""),
                );
              }}
            >
              <Search size={21} />
              <label className="sr-only" htmlFor="global-search">
                Recherche rapide de barrage
              </label>
              <input
                id="global-search"
                type="search"
                placeholder="Rechercher un barrage…"
                key={search ?? ""}
                name="search"
                defaultValue={search ?? ""}
              />
              <button type="submit" className="sr-only">
                Lancer la recherche
              </button>
            </form>
          ) : (
            <Link href="/barrages" className="global-search search-shortcut">
              <Search size={21} />
              <span>Rechercher un barrage…</span>
            </Link>
          )}
          <div className="topbar-actions">
            <div className="notification-wrapper">
              <button
                className="icon-button notification-button"
                aria-label="Consulter les signalements"
                aria-expanded={notifications}
                onClick={() => setNotifications(!notifications)}
              >
                <Bell size={23} />
                {issueCount !== undefined && issueCount > 0 && (
                  <span className="notification-dot" />
                )}
              </button>
              {notifications && (
                <div className="notification-popover" role="status">
                  <strong>Qualité des données</strong>
                  <p>
                    {issueCount === undefined
                      ? "Consultez les contrôles et les sources disponibles."
                      : issueCount === 0
                        ? "Aucun signalement ouvert dans le mode actif."
                        : `${issueCount} signalement(s) ouvert(s) dans le mode actif.`}
                  </p>
                  <Link href="/qualite" onClick={() => setNotifications(false)}>
                    Voir les contrôles
                  </Link>
                </div>
              )}
            </div>
            <Link
              className="icon-button"
              href="/sources"
              aria-label="Aide et méthodologie"
            >
              <CircleHelp size={24} />
            </Link>
            <span className="morocco-flag" role="img" aria-label="Maroc">
              <svg viewBox="0 0 30 24" aria-hidden="true">
                <path
                  d="m15 5 4 12-10-7h12l-10 7Z"
                  fill="none"
                  stroke="#007a43"
                  strokeWidth="1.4"
                />
              </svg>
            </span>
          </div>
        </header>
        {mode === "demo" && (
          <div className="demo-banner">
            <span className="demo-tag">DEMO</span>
            <strong>Données de démonstration</strong>
            <span>Mesures synthétiques · Aucun barrage réel</span>
          </div>
        )}
        <main id="main-content" tabIndex={-1}>
          {children}
        </main>
        <footer className="app-footer">
          <span>
            AquaMaroc AI · Projet indépendant, sans communication officielle.
          </span>
          <span>
            Dernier import : {dateLabel(importedAt)} ·{" "}
            <Link href="/sources">Sources et méthodologie</Link>
          </span>
        </footer>
      </div>
    </div>
  );
}
