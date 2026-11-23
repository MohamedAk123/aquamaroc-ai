# Jalon 2 — Dashboard Web historique

## Périmètre

Cette livraison prolonge J1 dans le dépôt local. Les données officielles restent à
auditer ; aucun entraînement avancé, application mobile ou déploiement public.
La cartographie et le suivi détaillé des anomalies attendent J4.

Routes Web : `/`, `/barrages`, `/barrages/{id}`, `/analyses`, `/sources`, `/qualite`,
`/rapports`. Le dashboard présente les derniers relevés filtrés, des KPI conditionnels,
un historique ECharts et un tableau triable/paginé. Le détail ajoute des capacités
sourcées, une comparaison de deux dates et un export de tous les relevés sélectionnés.

Les contrôles de dates, bassin, recherche, source et provenance se valident avec
« Appliquer ». Une modification en cours ne remplace pas silencieusement la sélection
appliquée. Les filtres sont locaux à chaque écran ; ils ne sont pas encore partagés
dans l'URL. Les écrans indiquent la portée des statistiques de qualité, qui concernent
tous les imports du mode actif et ne suivent pas le filtre historique.

## Provenance et calculs

- Mode DEMO clairement signalé après lecture du mode réel de l'API. Aucun fallback
  synthétique en cas d'échec réseau. OFFICIAL et UNVERIFIED restent explicitement identifiés.
- Réserves agrégées seulement pour des derniers relevés du même jour, de même
  statut, avec une valeur par barrage. En cas de sources multiples, le total est
  indisponible jusqu'à sélection d'une source, sans choix arbitraire.
- Taux pondéré : somme des réserves / somme des capacités sourcées × 100. Une
  capacité sans référence ne suffit pas. La migration `0002_capacity_provenance`
  ajoute `reservoirs.capacity_source`, nullable ; aucune valeur existante n'est inventée.
- Le graphique sépare chaque couple source/provenance en une série. Les dates sans
  relevé ne sont pas interpolées comme des observations. Les lignes ne sont qu'une
  liaison visuelle des relevés.
- Les séries complètes sont récupérées par pagination, sans s'arrêter à la première
  page. Les décimaux API restent des chaînes ; la conversion en nombres intervient
  uniquement pour l'affichage graphique et la comparaison descriptive.
- Le CSV UTF-8 contient unités, provenance, source, licence et horodatages. Les
  cellules pouvant être interprétées comme formules sont neutralisées et les guillemets
  échappés. Les dates de publication absentes restent vides.

## Structure Web

`components/workspace.tsx` orchestre les vues ; composants séparés pour shell,
filtres, états, tableaux et historique. `components/ui` contient des primitives
locales selon les conventions shadcn (CVA, clsx, tailwind-merge) et un manifeste
`components.json` ; elles sont volontairement simples, sans registry distante.
Tailwind 4 est intégré via PostCSS. ECharts est chargé côté navigateur, en module
séparé. Les icônes viennent de Lucide.

Le client `lib/api.ts` fournit les types, la pagination, l'annulation des requêtes
obsolètes et un délai maximal de 15 secondes par requête. Les réponses anciennes
ne peuvent pas remplacer une sélection plus récente.

## API complémentaire

- `GET /api/v1/overview` : synthèse filtrée et derniers relevés. Filtres : `basin_id`,
  `search`, `start_date`, `end_date`, `source_id`, `data_kind`.
- `GET /api/v1/reservoirs/{id}` : métadonnées d'un barrage visible dans le mode actif.
- `GET /api/v1/sources` : inventaire sourcé, licence, statut et fraîcheur, paginé.
- `GET /api/v1/data/quality` : compteurs globaux du mode actif et dénominateurs.
- L'historique J1 accepte aussi `source_id`.

Aucune route d'import ou de prédiction n'est ajoutée. Les endpoints existants restent
compatibles. La migration initiale demeure figée.

## Exécution et tests

Docker : mêmes commandes que le README (`up --build -d` applique aussi la migration).
Pour le Web local : API sur le port 8000, puis depuis `apps/web` :

```powershell
npm.cmd ci
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test:unit
npm.cmd run build
npm.cmd run start
```

URL : http://127.0.0.1:3000. Le script `start` prépare les assets du build standalone
puis lance le serveur sur loopback. `npm run dev` reste disponible pour développer.

Tests navigateur, après préparation DEMO et build :

```powershell
# Depuis la racine, sur une base locale réservée aux tests :
$env:DATABASE_URL='sqlite:///./e2e.db'
$env:APP_MODE='demo'
.\.venv-verify\Scripts\python -m scripts.prepare_e2e

# Depuis apps/web, garder les mêmes variables DATABASE_URL / APP_MODE :
$env:E2E_PYTHON=(Resolve-Path ../../.venv-verify/Scripts/python.exe).Path
$env:PLAYWRIGHT_BROWSERS_PATH='.cache/playwright'
npx.cmd playwright install chromium
npm.cmd run test -- --workers=2
```

Playwright lance l'API depuis la racine si elle n'est pas déjà disponible, et le Web
si le port 3000 n'est pas utilisé. En CI, les serveurs doivent être créés pour les tests.
Le paramètre `E2E_EXTERNAL_SERVER=1` permet de tester une composition déjà démarrée.
Le backend ne doit utiliser qu'une base DEMO pour ces parcours. Les tests couvrent
recherche, filtres, détail, export, erreur/reprise, chargement, navigation, WCAG et largeur
360 px. Les captures et traces sont dans `apps/web/test-results/` et restent ignorées.

La CI configure aussi ces contrôles ; son exécution distante n'est pas revendiquée.

### Résultats réellement exécutés

| Contrôle | Résultat |
|---|---|
| Pytest, avec PostgreSQL/PostGIS isolé | **42 tests réussis**, aucun ignoré |
| Parcours Playwright desktop et mobile 360 px | **16 tests réussis** |
| Test CSV (échappement, formules, nulls, provenance) | **1 test réussi** |
| Axe WCAG A/AA et 2.1 AA, dashboard desktop/mobile | Aucune violation détectée sur les pages auditées |
| Largeur mobile | Viewport, largeur de document et largeur intérieure : 360 px, sans débordement global |
| Reprise réseau, état vide et chargement | Vérifiés sur les deux tailles |
| Export d'un historique paginé de 501 relevés DEMO | 501 lignes de données exportées, sans troncature |
| Ruff lint/format, ESLint, TypeScript | Réussis |
| Build Next.js local et image Docker Linux | Réussis |
| Préparation et démarrage autonomes des serveurs E2E | Vérifiés avec SQLite DEMO |
| Recette E2E contre la composition Docker complète | 16 tests réussis avec Web Linux et API PostgreSQL/PostGIS |
| Services DB/API/Web et endpoints de synthèse | Trois services sains, réponses HTTP 200 |
| Readiness sur schéma ancien | HTTP 503 explicite jusqu'à application de la migration |

L'intégration navigateur a aussi été exécutée contre l'API PostgreSQL/PostGIS. Les
contrôles visuels sont conservés dans [la capture desktop](screenshots/j2-dashboard-desktop.png)
et [la capture mobile](screenshots/j2-dashboard-mobile.png). La recette ne valide
aucune performance hydrologique ni prédictive. Les avertissements tiers déjà connus
(TestClient Starlette/HTTPX, ESLint 9 en fin de maintenance) restent documentés.

Les services locaux sont laissés démarrés après la refonte visuelle, documentée
dans [le rapport d’interface](interface-reference.md), avec 18 tests navigateur
réussis. Après un arrêt, relancer `docker compose --env-file .env.example up --build -d`
pour ouvrir le dashboard sur le port 3000. Dans cette session, utiliser le préfixe
`docker --config .docker-local` si l'accès à la configuration utilisateur est restreint.

## Limites

L'audit Axe est automatisé et ne remplace pas une validation humaine complète avec
lecteur d'écran. Le navigateur intégré de la session n'était pas disponible ; les
captures de rendu proviennent des tests Chromium du projet. Les gros historiques sont
chargés en mémoire après pagination ; mesurer avant d'ajouter un downsampling ou un
export serveur. Les filtres, préférences et comparaisons ne sont pas persistés.

ESLint 9 reste requis par les peer dependencies de certains plugins Next.js ; sa fin
de maintenance demeure une dette documentée de J1, sans résolution forcée des peers.
Les données officielles, licences, capacités et coordonnées doivent toujours être
auditées avant de remplacer le mode de démonstration.
