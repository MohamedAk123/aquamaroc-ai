# Dashboard Web — jalon 2

Next.js App Router/TypeScript, Tailwind 4, primitives UI locales selon les conventions
shadcn et graphiques ECharts. Les données viennent exclusivement de l'API FastAPI.
Routes : `/`, `/barrages`, `/barrages/{id}`, `/analyses`, `/sources`, `/qualite`, `/rapports`.
Les capacités non sourcées et les prévisions non validées restent indisponibles.

Depuis ce dossier : `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`,
puis `npm run start`. En développement : `npm run dev`. URL locale : http://127.0.0.1:3000.
Sur Windows, utiliser `npm.cmd` si la politique PowerShell bloque `npm.ps1`.
Les versions résolues sont dans `package-lock.json`. Aucun hébergement n'est créé.

ESLint 9.39.5 est figé car les plugins de `eslint-config-next` ne déclarent pas encore
la compatibilité ESLint 10. npm signale la fin de maintenance de la branche 9 ;
réévaluer ce couple lors de la mise à jour Next.js, sans forcer les peer dependencies.

Tests : `npm run test:unit`, puis Playwright selon les instructions du
[rapport J2](../../docs/jalon-2.md). Le serveur API doit être accessible sur le port 8000
(ou via `NEXT_PUBLIC_API_URL` fixé avant le build). Les tests E2E utilisent les
fixtures synthétiques DEMO et peuvent lancer leurs propres serveurs.
