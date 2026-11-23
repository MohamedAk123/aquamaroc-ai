# Audit technique complet d’AquaMaroc AI

Audit du 18 novembre 2026. Le référentiel est [la spécification v2.1 révisée pour CatBoost](../AquaMaroc_AI_Codex_Specification_v2.1.md), présente dans l’espace de travail. La grille suit la numérotation de la demande d’audit. J2 évalue l’ingestion, J3 évalue le Web ainsi que la carte et la qualité, et J4 évalue Flutter. La roadmap du cahier des charges place ces sujets différemment. La phase couvre la lecture du code et les recettes locales. Les seuls ajouts au projet sont les livrables d’audit et les captures.

## A. Résumé exécutif

**Verdict. Le projet est démontrable localement comme observatoire officiel du Tensift avec analyse IA rétrospective. La mise en production publique et les prévisions de réserves ne sont pas approuvées.**

- Les trois fichiers téléchargés depuis les URL consignées sur data.gov.ma correspondent octet pour octet aux empreintes locales. Leur import de recette alimente 460 relevés officiels quotidiens pour cinq barrages entre le 1er août et le 31 octobre 2026. La recette utilise une composition et des volumes propres à l’audit.
- Le client Web, l’API, PostgreSQL/PostGIS et l’import local sont intégrés. Les suites Python, les essais navigateur et la recette Flutter sont détaillés ci-dessous. Les marqueurs officiels dépendent d’un référentiel géographique encore absent.
- Isolation Forest sert un rapport rétrospectif sur l’instantané officiel. Il signale 24 variations à examiner sur 155 relevés d’octobre. Ce nombre ne mesure ni exactitude ni fiabilité prédictive.
- Les horizons J+7 et J+30 sont `insufficient_history` dans le rapport de données. Les trois publications contiennent des séries quotidiennes, avec 460 dates de mise à disposition individuelles inconnues. CatBoost, XGBoost et LightGBM n’ont aucun score de validation ou modèle approuvé. Le statut métier n’est pas exposé via une route de prévision.
- Le dossier ouvert n’a pas de métadonnées Git exploitables. Les workflows sont présents, mais la CI distante, les images publiées, l’état des fichiers suivis, le domaine HTTPS et l’exploitation sur l’hôte cible restent à vérifier.

Le flux applicatif repose sur une CLI Python indépendante. Le parseur XLSX et SQLAlchemy alimentent PostgreSQL, tandis que les migrations Alembic installent le schéma et PostGIS. FastAPI expose les lectures et la provenance. Next.js et Flutter interrogent cette API. La présérie Compose place Nginx devant le Web et l’API sur la même origine, avec PostgreSQL sur un réseau interne. Le traitement IA rétrospectif publie un artefact JSON avec empreinte de l’instantané, que l’API vérifie avant de le servir. Le serveur d’inférence prédictive et le registre ML ne font pas partie du déploiement actuel.

## B. Grille de conformité

Chaque ligne compte pour un critère. **VALIDÉ** exige une preuve d’exécution ou une vérification directe de la propriété. **PARTIELLEMENT VALIDÉ** couvre un résultat établi avec un manque concret. **NON FONCTIONNEL** désigne un échec observé dans l’environnement indiqué. **NON IMPLÉMENTÉ** désigne une capacité absente ou seulement déclarée. **NON VÉRIFIÉ** indique une preuve insuffisante. Les fonctions facultatives sont signalées hors score.

| Jalon | Fonctionnalité | Statut | Preuve | Problème |
|---|---|---|---|---|
| J1 | Structure et installation locale | VALIDÉ | README, dossiers applicatifs, démarrage de la composition d’audit | — |
| J1 | Compose de développement et de production | VALIDÉ | `compose config --quiet`, composition production démarrée | Démarrage isolé du profil production |
| J1 | PostgreSQL, PostGIS et migrations | VALIDÉ | 50 Pytest avec base isolée, migration de production, contrôle SQL | — |
| J1 | FastAPI, configuration et santé | VALIDÉ | `/health` public, `/ready` interne, Pydantic et tests API | — |
| J1 | Contrat de lecture API v1 | PARTIELLEMENT VALIDÉ | Routes bassins, barrages, historique, synthèse agrégée, qualité et sources en service | La route individuelle `/reservoirs/{id}/summary` renvoie 404 |
| J1 | Dépendances et reproductibilité du checkout propre | PARTIELLEMENT VALIDÉ | `requirements*.lock`, verrou npm, Flutter lock, images construites avec cache | Checkout et CI distante indisponibles |
| J2 | Source officielle et téléchargement | VALIDÉ | GET des trois URL, taille et SHA-256 identiques aux fichiers archivés | Couverture limitée à trois classeurs |
| J2 | Contrat XLSX, décimales, unités, dates et valeurs invalides | VALIDÉ | Suites `test_import.py` et `test_tensift.py`, import officiel | Parseur spécialisé sur éditions auditées |
| J2 | PostgreSQL, historique et séparation OFFICIAL/DEMO | VALIDÉ | Décompte SQL, API et intégration PostGIS | — |
| J2 | Idempotence séquentielle et journal des conflits | VALIDÉ | Réimport des classeurs et tests de conflits/rejets | Charge concurrente hors recette |
| J2 | Provenance, conservation et disponibilité temporelle | PARTIELLEMENT VALIDÉ | URL, producteur, ODbL, empreintes et archives. 460 dates de publication manquantes | Dates de mise à disposition par version à établir |
| J2 | Découverte et automatisation des nouvelles éditions | NON IMPLÉMENTÉ | `EDITIONS` contient trois versions figées. CLI locale d’import fournie | Traitement de chaque nouvelle édition à intégrer et planifier |
| J3 | Next.js, navigation, recherche, filtres et KPI | VALIDÉ | App Router, suite Playwright, tableau officiel | — |
| J3 | ECharts, historique, cohérence et export | VALIDÉ | Code ECharts, export CSV testé, dernière observation comparée à l’API officielle sur deux largeurs | Vérification ponctuelle de la correspondance de valeurs |
| J3 | Responsive, clavier, chargement et état d’erreur | VALIDÉ | Playwright desktop/mobile, contrôle axe, clavier, erreurs et reprise | Portée des contrôles automatisés, essai lecteur d’écran hors recette |
| J3 | MapLibre et points sourcés | PARTIELLEMENT VALIDÉ | Tests `map-markers.spec.ts` et `geographic.spec.ts`, coordonnées officielles absentes | Tester des points réels après validation d’une source |
| J3 | Qualité, sources et provenance visibles | PARTIELLEMENT VALIDÉ | Routes et interface de qualité, journal d’import et export | Journal des anomalies navigateur testé avec fixture |
| J3 | Tailwind et composants UI | VALIDÉ | Tailwind dans PostCSS, `components.json`, composants locaux et Lucide | Les composants spécifiques au produit sont maintenus localement |
| J3 | Build Next.js par défaut sous Windows | NON FONCTIONNEL | `npm run build` échoue deux fois. `npm run build -- --webpack` réussit | Échec du traitement CSS par Turbopack, cause racine non isolée |
| J4 | Architecture, parsing, provenance et séparation des modes | VALIDÉ | Analyse Flutter, modèles, tests HTTP et repository | — |
| J4 | Accueil, liste, détail, graphique et favoris | VALIDÉ | Tests Flutter, aperçu avec API officielle et rechargement des favoris | Recette exécutée dans Chromium |
| J4 | Cache, reprise sur erreur réseau et synchronisation | VALIDÉ | Tests repository et aperçu avec interruption API | Recette exécutée dans Chromium |
| J4 | Carte interactive sur mobile | NON IMPLÉMENTÉ | Écran de disponibilité des coordonnées dans `apps/mobile/lib/features` | Pas de carte à marqueurs dans le client Flutter |
| J4 | Compilation Android et installation sur appareil | PARTIELLEMENT VALIDÉ | `flutter build apk --debug` réussi, APK produit | Recette appareil et signature de distribution non établies |
| J5 | Audit d’éligibilité séparé J+7 et J+30 | VALIDÉ | Rapport d’audit et tests fenêtre/purge, décision `insufficient_history` | Données défavorables à la prévision |
| J5 | Persistence et moyenne mobile | PARTIELLEMENT VALIDÉ | Fonctions et tests unitaires `test_ml_contracts.py` | Aucune comparaison d’erreur sur l’historique officiel |
| J5 | Features, découpage temporel et prévention des fuites | PARTIELLEMENT VALIDÉ | Lags par barrage, fenêtres purgées, contrôles de publication | Chaîne de prétraitement et backtesting incomplets. Disponibilité individuelle des lags à contrôler |
| J5 | CatBoost, XGBoost et LightGBM | NON IMPLÉMENTÉ | Dépendances optionnelles, module CatBoost descriptif et `train.py` qui refuse l’exécution | Aucun pipeline d’entraînement et de comparaison |
| J5 | SARIMA/SARIMAX | NON IMPLÉMENTÉ | Modèles cités dans la spécification | Historique insuffisant pour la saisonnalité annuelle, exogènes absentes |
| J5 | Isolation Forest rétrospectif | VALIDÉ | Rapport lié à son instantané officiel, API et 24 signalements sur 155 | Détection exploratoire sans vérité terrain ni qualification hydrologique |
| J5 | Backtesting, MAE/RMSE, gain et sélection | NON IMPLÉMENTÉ | `evaluate.py` et `selection.py` descriptifs | Aucune métrique de généralisation, aucun gagnant |
| J5 | H2O AutoML, FLAML et SHAP | NON IMPLÉMENTÉ | Modules descriptifs et groupes de dépendances | Aucun benchmark exécuté, aucune explication vérifiée |
| J5 | MLflow, artefacts, versionnement et suivi ML | NON IMPLÉMENTÉ | `mlflow_tracking.py` descriptif. Aucun suivi opérationnel des prédictions | Verrou ML, registre, dérive et métriques réelles manquants |
| J5 | API de prévision et gestion d’indisponibilité | PARTIELLEMENT VALIDÉ | Requêtes de contrôle 403/404, page Web informative, helper `unavailable_forecast` | Helper non exposé. Pas de réponse structurée `insufficient_history` |
| J6 | Suites automatisées backend, ETL, Web, mobile et contrats ML | PARTIELLEMENT VALIDÉ | Rapport d’exécution en C | Pas d’intégration avancée ML ni de recette Android sur appareil |
| J6 | Build et démarrage Docker de recette | VALIDÉ | Résolution des images/build avec cache, migration terminée, services sains | Qualifier aussi la construction en CI sur checkout neuf |
| J6 | Restrictions HTTP, CORS et isolation des services | VALIDÉ | Contrôles locaux de méthodes, origines, routes internes et ports. Tests de validation des entrées | Contrôle fonctionnel de configuration |
| J6 | GitHub Actions, GHCR et contrôle des secrets suivis | NON VÉRIFIÉ | `ci.yml`, `release.yml`, `check_tracked_secrets.py`. Git sort 128 | Checkout réel, statut CI et images par digest indisponibles |
| J6 | Journaux, Prometheus et Grafana | PARTIELLEMENT VALIDÉ | Configuration Prometheus valide, deux règles, cible API `up=1`, Grafana HTTP 200 | Routage d’alertes et exploitation cible non vérifiés |
| J6 | Sauvegarde et restauration | PARTIELLEMENT VALIDÉ | Dump, archives, manifeste de recette et contrôles détaillés en C | Copie hors hôte et planification non vérifiées |
| J6 | HTTPS public, cible de déploiement et retour arrière | NON VÉRIFIÉ | Caddyfile et runbook présents | Aucun domaine, certificat public ou environnement cible qualifié dans cette recette |

Hors score. LSTM est optionnel et absent. Les notifications sont reportées dans la spécification. iOS exige macOS et Xcode. Les trois sujets restent en dehors de la conclusion sur Android.

## C. Tests et parcours de bout en bout

### Commandes et preuves

Les commandes sont données depuis la racine, sauf les commandes npm exécutées dans `apps/web` et les commandes Flutter dans `apps/mobile`. L’environnement est Windows PowerShell, Python 3.12.13 dans `.venv-verify`, Node 24.18.0, Next.js 16.4.6, Flutter 3.50.0 et Dart 3.14.0. Docker Desktop utilise des conteneurs Linux incluant PostgreSQL 16/PostGIS.

| Commande ou contrôle | Environnement | Résultat | Preuve ou trace |
|---|---|---|---|
| `git status --short` et `python scripts/check_tracked_secrets.py` | Windows, dossier ouvert | Échec Git 128, dossier hors dépôt Git. Audit de l’index NON VÉRIFIÉ | `.gitignore` et script lisibles. Le script inspecte des noms de fichiers, pas leur contenu |
| `python -m ruff check .` et `python -m ruff format --check .` | Python local | Lint OK. 94 fichiers déjà formatés | `pyproject.toml` |
| `python -m pytest -o cache_dir=.cache/audit-pg-pytest --basetemp=.cache/audit-pg-tmp -q` | `TEST_DATABASE_URL` vers PostGIS temporaire, port 15439, schéma de test isolé | **50 réussis**, aucun ignoré, 1 avertissement Starlette/httpx, 40,66 s | [Tests PostGIS](../services/api/tests/test_postgres.py) et sortie de l’exécution |
| `docker compose --env-file .env.example config --quiet` et `docker compose -f docker-compose.prod.yml --env-file .env.prod-rehearsal config --quiet` | Docker Compose | Configurations valides | [Dev](../docker-compose.yml), [production](../docker-compose.prod.yml) |
| `docker compose -p aquamaroc-audit -f docker-compose.prod.yml --env-file .env.prod-rehearsal --profile monitoring up -d --build --wait --wait-timeout 120` | Projet isolé sur 18086, noms d’images d’audit | Build avec cache, migration code 0, API/Web/DB/passerelle sains | Sortie Compose et `ps -a` |
| `curl.exe -fLsS --max-time 45 -o <fichier> <url>` et `Get-FileHash -Algorithm SHA256` | Source officielle, cache local | Fiche HTTP 200 via curl, trois téléchargements comparés, tailles 14 178 / 1 984 212 / 1 982 632 octets pour août / septembre / octobre | [Manifeste de provenance](../data/raw/tensift/provenance.json), `.cache/audit-tensift-download/`. L’accès depuis l’outil Web a renvoyé 403 |
| `docker compose … exec -T api python -m pipelines.ingestion.import_tensift` et SQL `COUNT` / `PostGIS_Version()` | Base de recette | Premier passage 155 / 150 / 155 lignes valides, 0 rejet. Réimport `reused: true` pour les trois exécutions avec les mêmes identifiants. 460 lignes OFFICIAL, cinq barrages, 0 date de publication. PostGIS 3.4 et révision Alembic `0002_capacity_provenance` | [CLI](../pipelines/ingestion/import_tensift.py), journal et manifeste de sauvegarde |
| `npm run lint`, `npm run typecheck`, `npm run test:unit` | Next.js sous Windows | Lint et contrôle de types OK, 1 test CSV réussi, avertissement de module ES implicite sous Node | [Suite CSV](../apps/web/tests/unit/csv.test.ts) |
| `npm run build` puis `npm run build -- --webpack` | Next.js sous Windows | Avec Turbopack, échec reproduit hors bac à sable lors du traitement CSS, sous-processus Node quitté. Avec Webpack, compilation et génération des 10 pages réussies | Sortie du build, `apps/web/.next/BUILD_ID` |
| `python -m scripts.prepare_e2e`, `python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 18000`, `playwright test --workers=2 --output=../../.cache/audit-playwright` | Base SQLite DEMO isolée, `E2E_EXTERNAL_SERVER=1`. Relais local sur 13000 pour servir le bundle Docker et l’API de test | **24 réussis** en 43,5 s, 12 par profil desktop et mobile. Recherche, filtres, navigation, export, erreurs, accessibilité et carte. Certaines réponses sont injectées par Playwright pour éprouver les cas limites | [Rapport HTML](../.cache/audit-playwright-html/index.html), `.cache/audit-playwright/.last-run.json` |
| Contrôle Chromium officiel via Playwright | Passerelle 18086, viewport 1280 px puis 360 px | Cinq séries OFFICIAL de 92 observations, graphique sans débordement, dernière réserve API 18,3550 Mm³ et UI 18,36 Mm³ suivant l’arrondi, taux 82,05 %, rapport IA consultable. La première assertion, qui attendait trois décimales, a été corrigée dans la commande de recette | [Capture desktop](screenshots/audit-web-1280.png) · [Capture mobile](screenshots/audit-web-360.png) |
| `curl.exe` HTTP sur la passerelle, `promtool check config`, requête `up` | Docker Compose de recette | `/health` et overview 200. Routes internes 404. POST et OPTIONS non autorisés 403. En-têtes de sécurité présents. Deux règles valides et `up=1`. Grafana 200 | [Nginx](../infrastructure/deploy/nginx.conf), [règles](../infrastructure/monitoring/alerts.yml) |
| `python -m scripts.backup_db backup backups/audit-20261118 --project aquamaroc-audit --env-file .env.prod-rehearsal`, puis mêmes arguments avec `rehearse` | Projet Compose d’audit | Dump, archive et manifeste créés. `restored_and_verified` pour 460 OFFICIAL, 0 DEMO et 0 UNVERIFIED. Trois archives source, empreinte logique identique `386390ac0662f2e9a14775a468579d89` | `backups/audit-20261118/manifest.json` et sortie de restauration |
| `python -m scripts.audit_data --kind OFFICIAL --validation-start 2026-09-20 --test-start 2026-10-13 --output /tmp/audit-readiness` | Script et modules d’audit copiés sous `/tmp` dans le conteneur. Exécution du script par son chemin, `PYTHONPATH=/tmp/audit_ml:/app` | `insufficient_history` sur 460 observations. Aucun entraînement | [Rapport reproduit](../.cache/audit-readiness/data_readiness.md) et [JSON](../.cache/audit-readiness/data_readiness.json) |
| `flutter --version` et `flutter analyze --no-pub` | SDK local, Windows | Flutter 3.50.0, Dart 3.14.0. Aucun problème signalé par l’analyse | [Dossier Flutter](../apps/mobile/README.md) |
| `flutter test --no-pub --reporter expanded --dart-define=LIVE_API_URL=http://127.0.0.1:18000` | Windows, API DEMO dédiée et base SQLite isolée | **29 réussis**, dont l’intégration HTTP DEMO, aucun ignoré au dernier passage | [Journal Flutter](../.cache/audit-flutter-test.log) |
| `flutter build apk --debug --no-pub --dart-define=APP_MODE=official --dart-define=API_URL=http://127.0.0.1:18086` | Windows, Java 17, SDK Android local | Compilation réussie en 122,7 s, APK debug de 190 719 537 octets. Installation physique NON VÉRIFIÉE | `apps/mobile/build/app/outputs/flutter-apk/app-debug.apk` |
| `adb devices -l` | SDK Android local | Aucun appareil ou émulateur connecté | Liste des appareils vide |
| `node tool/preview.mjs` et `node tool/check-preview.mjs` | Chromium 390 px, aperçu Flutter précompilé sur 3100, relais de lecture vers la passerelle officielle | Réponse 200 du catalogue et du détail, observations OFFICIAL, navigation, favoris après rechargement, cache après interruption simulée | [Scénario de recette](../apps/mobile/tool/check-preview.mjs) |

### Parcours A — Portail → données → API → Web

La fiche et ses trois ressources consignées ont répondu via curl. Les octets téléchargés et archivés coïncident. Le parseur et la CLI importent les trois éditions approuvées en PostgreSQL. Le manifeste documente le producteur et la licence ODbL. Cinq séries de 92 observations sont disponibles via l’API officielle. Le Web affiche le graphique historique et sa table. La recette de réimport confirme l’idempotence pour ces trois fichiers. Le cycle de découverte et mise à jour d’une nouvelle édition manque. [Fiche officielle du Tensift](https://www.data.gov.ma/data/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift)

### Parcours B — Flutter → FastAPI → PostgreSQL

La suite Flutter valide les modèles, widgets, cache et transport, ainsi que le test HTTP sur l’API DEMO. La recette officielle utilise l’aperçu Flutter avec un relais de lecture vers la passerelle et PostgreSQL d’audit. Elle confirme catalogue, navigation, détail et provenance des relevés, favoris après rechargement et mode cache après une coupure. L’APK debug compile. L’essai natif Android reste NON VÉRIFIÉ faute d’appareil ou d’émulateur connecté.

### Parcours C — Historique → MLflow → prévision

Décision documentée `insufficient_history` aux deux horizons. J+7 a 215/80/60 couples calendaires après purge en train/validation/test, dont 65/80/60 avec les quatre lags examinés. J+30 a 100/0/0 couples, avec une étendue de 92 jours alors que trois blocs calendaires disjoints exigent au moins 93 jours dans ce protocole. Aucun couple ne satisfait les vérifications de publication dans les deux découpages. Trois bulletins donnent au plus deux transitions mensuelles adjacentes avant même les contrôles de disponibilité. Répliquer la transition sur cinq barrages laisse inchangé le nombre de dates.

Aucun entraînement avancé déclenché. Les tests unitaires portent sur des contrats et des exemples de test. Aucun leaderboard, MAE/RMSE officiel, artefact SHAP ou run MLflow de prévision. Les routes GET de prévision J+7/J+30, modèles et santé ML renvoient 404. POST predictions est refusé par la passerelle (403). La page Analyses IA explique l’état des prévisions en texte. Le rapport Isolation Forest est disponible via `GET /api/v1/data/variation-review`. La preuve concerne un artefact préexistant lié à l’instantané actuel. [Audit d’éligibilité](../machine-learning/reports/data_readiness.md) · [Protocole mensuel](../machine-learning/reports/previsions-mensuelles.md) · [Étude rétrospective](../machine-learning/reports/variations-ia.md)

### Parcours D — Tests → Docker → services

La composition locale applique les migrations avant le démarrage de FastAPI. La recette vérifie la santé interne, les requêtes métier et l’exposition réseau. Prometheus atteint le service API et Grafana répond. La chaîne publique de livraison jusqu’à GHCR, le TLS du domaine cible, le basculement et le retour arrière réel restent NON VÉRIFIÉS. Les tests de restauration portent sur un projet de recette.

## D. Anomalies et fonctionnalités manquantes

P0 désigne un blocage total du service de lecture ou un risque établi pour l’intégrité des données. Aucun P0 n’a été démontré sur la recette locale. P1 bloque la livraison de l’usage concerné. P2 concerne une exigence importante. P3 concerne l’outillage ou la documentation.

| ID | Priorité | Emplacement | Constat et cause | Correction recommandée |
|---|---|---|---|---|
| A1 | P1 | `.github/workflows/`, `scripts/check_tracked_secrets.py` | Absence de contexte Git. Contrôle limité aux noms de fichiers suivis | Recetter le commit candidat en CI et scanner les contenus |
| A2 | P1 | `pipelines/ingestion/import_tensift.py`, `data/raw/tensift/provenance.json` | Éditions figées et disponibilité temporelle des versions lacunaire | Catalogue versionné et revue avant import, planification avec trace de révision |
| A3 | P1 | `services/api/app/api/v1/routes.py`, `aquamaroc_ml/serving.py` | Aucune route de prévision ne relie l’audit à une réponse métier | Retourner `insufficient_history` et métadonnées d’audit par horizon |
| A4 | P1 | `apps/mobile/android/app/build.gradle.kts` | La configuration `release` utilise la clé debug | Préparer une signature de distribution, une URL HTTPS et une recette appareil |
| A5 | P1 | `infrastructure/deploy/`, `docs/jalon-6.md` | Preuves de recette locale uniquement | Vérifier TLS public, versions immuables, restauration hors hôte et alertes sur la cible |
| A6 | P2 | `apps/mobile/lib/features`, référentiel `reservoirs` | Pas de carte Flutter ni de coordonnées officielles disponibles | Valider une source géographique puis compléter la carte |
| A7 | P2 | `machine-learning/src/aquamaroc_ml/`, `machine-learning/benchmarks/` | Fonctions isolées et modules descriptifs. Comparaison, backtesting, SHAP, AutoML, MLflow absents | Développer après éligibilité et qualifier l’ensemble avec mêmes cibles, fenêtres, métriques et test indépendant |
| A8 | P2 | `services/api/app/services/variation_review.py`, `scripts/study_variations.py` | La correspondance d’instantané protège l’affichage. Une nouvelle ingestion rend le rapport indisponible jusqu’à régénération | Intégrer une régénération explicite et un contrôle de fraîcheur au processus d’exploitation |
| A9 | P2 | `apps/web/app/geographic.css`, script `build` | Turbopack/Windows échoue dans le sous-processus CSS. Cause racine non isolée | Reproduire sur un checkout Windows propre, documenter le chemin de build qualifié |
| A10 | P3 | `README.md`, spécification v2.1, `docs/jalon-*.md` | Numérotation différente du mandat d’audit. Avertissements Starlette/httpx et Node ESM | Fixer un découpage de référence, traiter les avertissements dans des mises à niveau testées |
| A11 | P2 | `services/api/app/api/v1/routes.py` | Résumé individuel prévu dans le contrat absent des routes | Exposer la synthèse individuelle selon le contrat API ou documenter le changement de contrat |

## E. Ordre de correction

Le [plan de correction](PLAN_CORRECTION_AQUAMAROC.md) décrit les dépendances, critères d’acceptation et tests de chaque action. Priorité à une recette publique reproductible de l’observatoire, à la mise à jour traçable des données, au statut de prévision par horizon et à la qualification Android. La comparaison avancée dépend du résultat d’un nouvel audit officiel.

## F. Score de conformité

Pour chaque jalon, le **taux validé** vaut `100 × VALIDÉ / critères`, et le **taux non vérifié** vaut `100 × NON VÉRIFIÉ / critères`. Une validation partielle est comptée séparément et ne rapporte aucun point de validation complète. Les critères facultatifs sont exclus. Un critère validé ne prouve que le périmètre couvert. Le score ne remplace pas les critères de livraison.

| Jalon | Critères | Validés | Partiels | Non fonctionnels | Non implémentés | Non vérifiés | Taux validé | Taux non vérifié |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| J1 — Infrastructure | 6 | 4 | 2 | 0 | 0 | 0 | 66,7 % | 0 % |
| J2 — Data Engineering | 6 | 4 | 1 | 0 | 1 | 0 | 66,7 % | 0 % |
| J3 — Dashboard Web | 7 | 4 | 2 | 1 | 0 | 0 | 57,1 % | 0 % |
| J4 — Flutter | 5 | 3 | 1 | 0 | 1 | 0 | 60,0 % | 0 % |
| J5 — ML et MLOps | 10 | 2 | 3 | 0 | 5 | 0 | 20,0 % | 0 % |
| J6 — Déploiement | 7 | 2 | 3 | 0 | 0 | 2 | 28,6 % | 28,6 % |
| Total | 41 | 19 | 12 | 1 | 7 | 2 | 46,3 % | 4,9 % |

## Conclusion

Le socle local, l’import officiel et la revue IA rétrospective justifient une démonstration du Tensift. La livraison sur Internet reste conditionnée à une recette d’exploitation et de sécurité sur le commit et l’hôte cibles. La livraison native exige une signature de distribution et un essai sur appareil. Toute promesse de prévision exige des archives suffisantes et vérifiables pour l’horizon retenu, une comparaison chronologique et une évaluation finale indépendante.
