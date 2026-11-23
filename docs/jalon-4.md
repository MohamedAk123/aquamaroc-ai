# Jalon 4 — Cartographie et qualité

Sur le Web, la page [Carte](http://127.0.0.1:3000/carte) propose la recherche,
les filtres par bassin, période, source et tranche de remplissage. Le taux est
celui du dernier relevé disponible dans la période choisie. Un panneau textuel
donne accès aux relevés des barrages, y compris en l’absence de coordonnées.
Le même fond MapLibre GL JS est utilisé sur le tableau de bord.

Les marqueurs exigent une paire latitude/longitude valide et une référence
géographique explicite. Les classeurs du Tensift ne fournissent pas cette
paire. La [page des infrastructures de l’ABHT](https://abht.ma/bassin/infrastructures-hydrauliques/)
confirme l’identité d’ouvrages, mais ne fournit pas de paire réutilisable pour
ce catalogue. Les cinq ouvrages officiels restent non localisés dans l’API.
Le fond de repérage est fourni par [OpenStreetMap](https://www.openstreetmap.org/copyright).
Son chargement dépend du réseau et d’un navigateur compatible WebGL.

Sur la page [Qualité](http://127.0.0.1:3000/qualite), le journal affiche le
fichier, son empreinte, sa source, la date de vérification de celle-ci, la date
d’import, l’état et le ratio de lignes acceptées. Le tableau de couverture
compte les jours observés entre les deux dates extrêmes de chaque série
(barrage, source, statut), sans extrapoler au-delà de la période observée. Le
journal des anomalies affiche les motifs de rejet enregistrés, avec filtres
par import et par statut ouvert. L’export CSV porte sur la sélection entière.
Les valeurs brutes rejetées et les chemins d’archives restent internes.

Les trois points d’accès paginés sont `GET /api/v1/data/quality/imports`,
`GET /api/v1/data/quality/coverage` et `GET /api/v1/data/quality/issues`.
Ils respectent le mode configuré. Le mode officiel contient trois imports,
460 observations, cinq séries de 92 jours chacune et aucun rejet enregistré.
Ces contrôles portent sur les données et ne valent pas alerte hydrologique.

La compilation Docker, Ruff, ESLint et TypeScript ont réussi. Pytest a exécuté
44 tests avec une base PostgreSQL isolée et `APP_MODE=demo` pour les fixtures.
Les six parcours Playwright ont réussi sur le Web officiel, sur ordinateur et
mobile. Ils se lancent depuis `apps/web` avec le Web et l’API
démarrés, via `E2E_EXTERNAL_SERVER=1` et
`npm run test -- geographic.spec.ts map-markers.spec.ts`. Le marqueur et
l’anomalie utilisés par ces tests sont injectés uniquement dans le navigateur
de test. Le mode officiel reste actif sur les services locaux.
