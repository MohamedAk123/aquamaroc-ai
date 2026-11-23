# Compte rendu du jalon 1 — 17 novembre 2026

## 1. Fichiers créés et périmètre

Le dépôt initial contenait seulement la spécification v2.1, révision CatBoost.
Le nom v2 demandé n'était pas présent ; la v2 originale a été consultée dans Downloads
et la révision v2.1 conserve les décisions ML demandées précédemment.

- Racine : AGENTS, configuration, packaging, verrous runtime/dev, Compose et Makefile.
- `services/api/` : FastAPI, modèles SQLAlchemy, schémas de sortie, repositories,
  routes, configuration, logs JSON, migration initiale figée, Dockerfile et tests.
- `pipelines/` : parsing XLSX, mapping, normalisation, validation, import transactionnel,
  génération/référencement DEMO et tests de rejets/réimports/rollback.
- `config/` et `data/demo/` : mapping explicite et classeur synthétique de quatre lignes.
- `machine-learning/` : structure section 11, extras séparés, configurations, audit
  descriptif, utilitaires temporels/baselines et contrats des futurs modules.
- `apps/web/` : squelette Next.js App Router/TypeScript, une page DEMO, Dockerfile,
  lint, typage et verrou npm. Aucun écran métier du J2.
- `docs/`, `scripts/` et `.github/workflows/` : architecture, sources, API, ingestion,
  audit, garde-fou de fichiers sensibles et CI Python/PostgreSQL/Web.

## 2. Architecture et dépendances

PostgreSQL/PostGIS est la cible, SQLite le support rapide de test/local. Les six
tables J1 sont migrées explicitement. UUID, contraintes, index, NUMERIC et JSONB
préservent l'intégrité et la provenance ; geometry reste nulle sans coordonnées vérifiées.
Le journal est durable avant la transaction de mesures et conserve les rejets.
L'API ne fournit que de la lecture et filtre le mode actif.

Python propre validé : 3.12.13 ; image API : 3.12.12 ; hôte initial : Python 3.14.0.
FastAPI 0.136.0, SQLAlchemy 2.0.48, Pydantic 2.12.5, Alembic 1.20.1, openpyxl 3.1.5.
Node 24.18.0, Next.js 16.4.6, React 19.3.1 et TypeScript 5.9.3.
Les dépendances Python runtime/dev et npm sont verrouillées. Images de base Docker
épinglées par digest. Pandas et les dépendances ML lourdes restent hors du runtime API.

Voir [ADR 0001](decisions/0001-architecture.md) pour les arbitrages.

## 3. Commandes exactes de lancement

Voir [README](../README.md) pour les parcours Docker et Python. Dans cet environnement,
les commandes Docker utilisent `--config .docker-local` pour contourner l'accès restreint
à la configuration Docker utilisateur ; aucun identifiant utilisateur n'y est copié.

```powershell
docker --config .docker-local compose --env-file .env.example up --build -d
docker --config .docker-local compose --env-file .env.example exec -T api python -m pipelines.ingestion.demo
docker --config .docker-local compose --env-file .env.example exec -T api python -m pipelines.ingestion.import_xlsx --file data/demo/reservoirs_demo.xlsx --source-id 00000000-0000-0000-0000-000000000001 --dry-run
docker --config .docker-local compose --env-file .env.example exec -T api python -m pipelines.ingestion.import_xlsx --file data/demo/reservoirs_demo.xlsx --source-id 00000000-0000-0000-0000-000000000001
```

La configuration de démonstration ne contient aucun secret réel. Personnaliser `.env`
avant une utilisation différente de la démonstration locale.

## 4. Résultats de validation

| Vérification exécutée | Résultat |
|---|---|
| Suite Python isolée 3.12, avec PostgreSQL/PostGIS réel | **36 tests réussis**, aucun ignoré |
| Migration SQLite upgrade/downgrade/upgrade | Réussie |
| Migration PostgreSQL, PostGIS, JSONB, contraintes et lecture API | Réussies dans un schéma de test isolé |
| Génération SQL PostgreSQL sans connexion | Réussie, `schema-postgresql.sql` |
| Ruff lint et format | Réussis |
| Installation editable du monorepo | Réussie |
| Import XLSX CLI local SQLite | 4 lues, 4 valides, 0 rejet |
| Import XLSX CLI Docker/PostgreSQL | 4 lues, 4 valides, 0 rejet |
| Dry-run et réimport identique | Pas d'écriture en dry-run ; même run et `reused=true` au réimport |
| Build image API et service de migration Compose | Réussis |
| Endpoints HTTP réels API et OpenAPI | Tous les endpoints J1 répondent 200 après initialisation |
| Squelette Web : ESLint, TypeScript, build | Réussis en local |
| Image Web Linux avec installation npm propre | Build réussi, sans conflit de peer dependencies |
| Composition finale DB/API/Web | Trois services sains, migration terminée avec succès |
| Web en HTTP réel | 200, bannière DEMO présente |
| Origine CORS du Web local | Autorisée ; origine tierce refusée par les tests |
| CI GitHub Actions | Configurée, non exécutée sur GitHub dans cette session |

La suite couvre les erreurs d'import, doublons, révisions préservées, dates/nombres,
rollback, absence de coordonnées, isolation de mode, pagination et erreurs API.
Les tests ML portent uniquement sur audit/baselines/utilitaires et refus d'entraînement.
Un avertissement tiers Starlette indique la future migration de son TestClient HTTPX ;
les tests actuels passent. ESLint 9 est retenu pour satisfaire les peer dependencies
des plugins Next ; sa fin de maintenance est à traiter lors d'une mise à jour compatible.

Les conteneurs de vérification ont été arrêtés après ces contrôles ; les volumes et
les quatre mesures synthétiques sont conservés. Les commandes du README permettent
de les relancer. Aucun service n'a été déployé publiquement.

## 5. Endpoints disponibles

`/health`, `/ready`, `/api/v1/basins`, `/api/v1/reservoirs`,
`/api/v1/reservoirs/{id}/measurements`, `/api/v1/data/freshness`, `/docs`, `/openapi.json`.

Voir [contrats et exemples curl](api.md). Aucune route de prédiction ni import public.

## 6. Sources officielles

La fiche Tensift a renvoyé HTTP 403 lors de la consultation Web. Aucun fichier
officiel, schéma, licence, capacité, coordonnée ou historique n'a été validé.
Les points à auditer et l'inventaire sont dans [data-sources.md](data-sources.md).
Le rapport ML décrit zéro observation officielle chargée, pas l'absence de données
chez le producteur ; il reste `insufficient_history`, `ready_for_experiments=false`.

## 7. Limites et dette technique

- Le parseur est démonstratif : mapping officiel, publications, unités et révisions
  doivent être audités avant l'ingestion réelle.
- Les journaux `failed`/`pending` nécessitent une reprise explicite ultérieure.
  Une concurrence sur le même fichier peut produire une erreur de contrainte unique,
  sans duplication ; il faudra améliorer ce retour si l'ingestion devient concurrente.
- Aucun entraînement CatBoost/XGBoost/LightGBM, benchmark H2O/FLAML, SHAP ou registre
  MLflow n'est exécuté. Les extras ML ne sont pas encore résolus ni verrouillés.
- Le découpage ML préparatoire suppose une disponibilité à la date cible ; intégrer
  les délais de publication réels avant toute expérience.
- Aucun test navigateur d'accessibilité ni test d'interaction Web complet au J1.
- Aucun déploiement public, compte utilisateur ou système de surveillance opérationnel.

## 8. Proposition de jalon 2, sans exécution

Créer `apps/web/lib/api.ts`, composants de provenance/états, pages tableau de bord et
liste/détail, filtres datés, ECharts et tests d'accessibilité. Maintenir attribution,
unités et dates visibles, bannière DEMO, absence de prévision et coordonnées nulles
tant que les données officielles ne sont pas auditées. Le jalon 2 n'est pas commencé.
