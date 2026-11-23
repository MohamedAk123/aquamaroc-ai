# AquaMaroc AI — Cahier des charges technique et plan d'exécution pour Codex

> **Statut :** spécification de démarrage, version 2.1 — 17 novembre 2026 (révision CatBoost)  
> **Langue produit :** français (prévoir internationalisation arabe ultérieurement)  
> **Mission :** construire un produit Web + Mobile d'observation des ressources hydriques du Maroc, avec pipeline de données reproductible, API, visualisations et MLOps.  
> **Important :** les valeurs des maquettes sont **fictives**. Ne jamais les présenter comme des mesures officielles.

## 0. Instructions impératives à Codex

Tu es un ingénieur full-stack senior, Data Engineer et MLOps Engineer. Travaille de façon incrémentale dans le dépôt courant. Avant de coder, inspecte le dépôt et les versions installées. N'écrase aucun fichier existant sans nécessité. Crée un plan de travail court, puis réalise **uniquement le jalon 1** (socle monorepo, base de données, backend, ingestion démonstrative, tests et documentation), sauf instruction contraire explicite. Après chaque étape, lance les tests disponibles, corrige les erreurs et fournis les commandes exactes de démarrage. N'invente ni données réelles, ni endpoints de téléchargement, ni coordonnées de barrages, ni métriques de modèles.

**Critères non négociables :** code lisible et typé, architecture modulaire, secrets dans `.env` non versionné, fichiers `.env.example`, migrations, tests automatisés, logs structurés, données de démonstration clairement signalées, documentation reproductible, pas de Power BI, pas de scraping agressif. Prévoir des modes `demo` et `official`; ne pas mélanger les deux dans une même série sans provenance explicite.

## 1. Contexte, vision et limites

Le produit répond à une question simple : « Que disent les données officielles sur les réserves et le remplissage des barrages suivis, comment ces valeurs évoluent-elles, et quelle est la fiabilité de cette information ? »

**Publics cibles :** citoyens, chercheurs, étudiants, acteurs territoriaux et professionnels intéressés par les ressources hydriques. **Périmètre MVP :** bassin du Tensift, puis extension à d'autres bassins uniquement après identification et validation des sources correspondantes. **Ne pas promettre :** temps réel, couverture nationale complète, alertes hydrologiques officielles, recommandations de sécurité ou prévisions fiables sans données suffisantes.

### Objectifs métier

1. Centraliser les relevés publiés par les sources ouvertes autorisées.
2. Afficher une carte et une liste des barrages avec historique vérifiable.
3. Rendre visibles les dates de mesure, de publication et d'ingestion.
4. Exposer les données via une API documentée.
5. Détecter doublons, valeurs manquantes et anomalies à examiner.
6. Préparer des expériences ML reproductibles et traçables avec MLflow, sans activer une fonction prédictive non validée.
7. Fournir un dashboard Web et une application mobile partageant le même backend.

### Indicateurs de réussite MVP

- Installation locale documentée avec Docker Compose.
- Import idempotent d'au moins un fichier local représentatif.
- API accessible avec OpenAPI et tests réussis.
- Historique filtrable par barrage et dates.
- Dashboard lisible sur desktop et mobile.
- Distinction claire `OFFICIAL`, `DEMO`, `UNVERIFIED`.
- Zéro secret commité.

## 2. Sources et politique de données

**Portail officiel :** https://www.data.gov.ma/  
**Fiche candidate identifiée :** https://data.gov.ma/data/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift

La fiche a été repérée comme source potentielle de fichiers XLSX sur les réserves (Mm³) et les taux de remplissage (%). **Avant d'écrire le parseur définitif**, télécharger manuellement ou par accès autorisé un échantillon, examiner les feuilles, en-têtes, unités, formats de dates, noms de barrages, lignes de total et cellules fusionnées. Les détails de schéma, l'historique, la fréquence de mise à disposition et les conditions de réutilisation doivent être revérifiés. Documenter la licence et l'attribution de chaque source dans `docs/data-sources.md`.

**Règles :**
- Utiliser l'API ou les fichiers téléchargeables officiellement disponibles ; ne pas deviner les URL directes.
- Si le téléchargement échoue, accepter un fichier placé dans `data/raw/` ; ne pas bloquer le développement.
- Conserver les fichiers bruts sans modification, avec SHA-256, nom, URL source si connue, horodatage, licence et statut.
- Séparer `observation_date` (date du relevé), `published_at` (date de publication si connue) et `ingested_at` (date d'import).
- Ne pas afficher « aujourd'hui » ou « en temps réel » pour des données publiées mensuellement.
- Ne pas fabriquer de coordonnées géographiques. Laisser `geometry` vide si aucune source géographique vérifiée.
- Ne pas faire passer une maquette, un échantillon synthétique ou une prédiction pour une donnée officielle.

### Inventaire des sources à produire

Créer `docs/data-inventory.csv` avec : `dataset_name,producer,dataset_page,resource_url,format,license,coverage_start,coverage_end,granularity,geographic_scope,last_checked,validation_status,notes`. Toute information inconnue doit être vide ou marquée `TO_VERIFY`.

## 3. Stack technologique retenue

| Couche | Technologie | Rôle |
|---|---|---|
| Frontend Web | Next.js (App Router), TypeScript | Application Web |
| UI | Tailwind CSS, shadcn/ui, Lucide | Composants et accessibilité |
| Graphiques | Apache ECharts | Séries temporelles, comparaisons |
| Cartographie | MapLibre GL JS | Cartes interactives |
| Mobile | Flutter, Dart | Android, iOS si environnement adapté |
| API | FastAPI, Python, Pydantic | API REST, validation |
| ORM et migrations | SQLAlchemy 2, Alembic | Persistance et évolution de schéma |
| Stockage | PostgreSQL + PostGIS | Mesures et géométries vérifiées |
| ETL | Python, Pandas, openpyxl | Import et normalisation XLSX |
| Tests | Pytest, httpx, Ruff, ESLint | Qualité logicielle |
| ML | scikit-learn, CatBoost, XGBoost, LightGBM | Baselines et régression expérimentale |
| Explicabilité | SHAP et contributions natives CatBoost | Explications globales et locales |
| AutoML | H2O AutoML, FLAML | Comparaison hors chemin critique |
| Tracking ML | MLflow | Paramètres, métriques, artefacts |
| Infra | Docker Compose, GitHub Actions | Reproductibilité, CI |
| Observabilité | Prometheus, Grafana | Étape ultérieure, technique uniquement |
| Orchestration | Scripts planifiés, Airflow ultérieurement | Ingestion selon complexité réelle |

**Dépendances ML :** définir dans `machine-learning/pyproject.toml` un groupe ML avec `numpy`, `pandas`, `scikit-learn`, `catboost`, `xgboost`, `lightgbm`, `shap` et `mlflow`. Prévoir les groupes optionnels `automl-h2o` (`h2o`, environnement Java compatible documenté) et `automl-flaml` (`flaml[automl]`, avec `catboost`, `xgboost` et `lightgbm` explicitement installés). Conserver scikit-learn pour les métriques, transformations et Isolation Forest. Vérifier ensemble les compatibilités Python/OS/bibliothèques puis figer les versions résolues dans un fichier de verrouillage, sans inventer de versions non testées. Documenter les commandes d'installation et tester les imports. Garder ces dépendances hors de l'installation API minimale.

**Principes :** pas de Power BI ; ne pas introduire Spark, Kafka, Kubernetes ou Airflow dans le MVP sans besoin démontré. Prévoir des interfaces permettant de les ajouter plus tard.

## 4. Architecture logique

```text
[data.gov.ma / fichiers XLSX autorisés]
                |
                v
      [Ingestion Python]
       | validation + hash
       v
     [raw files] ---> [journal d'ingestion]
                |
                v
       [normalisation ETL]
                |
                v
    [PostgreSQL + PostGIS]
        |             |
        v             v
    [FastAPI]    [pipeline ML offline]
      |  |             |
      |  |          [MLflow]
      |  |
      v  v
 [Next.js] [Flutter]

 [Prometheus/Grafana] = phase observabilité, séparée du dashboard métier
```

**Ne pas forcer les requêtes Power BI ni faire transiter l'ingestion par le frontend.** L'API doit être l'unique point d'accès métier des clients Web/Mobile.

## 5. Structure de dépôt cible

```text
aquamaroc-ai/
├── README.md
├── AGENTS.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
├── apps/
│   ├── web/                      # Next.js
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── tests/
│   └── mobile/                   # Flutter (jalon 3)
├── services/
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/v1/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── repositories/
│       │   └── services/
│       ├── alembic/
│       ├── tests/
│       ├── pyproject.toml
│       └── Dockerfile
├── pipelines/
│   ├── ingestion/
│   ├── normalization/
│   ├── validation/
│   └── tests/
├── ml/
│   ├── baselines/
│   ├── experiments/
│   ├── evaluation/
│   └── README.md
├── infrastructure/
│   ├── monitoring/
│   └── ci/
├── data/
│   ├── raw/.gitkeep
│   └── demo/
├── docs/
│   ├── architecture.md
│   ├── data-sources.md
│   ├── data-inventory.csv
│   ├── api.md
│   ├── decisions/
│   └── screenshots/
└── .github/workflows/ci.yml
```

## 6. Modèle de données relationnel

Créer les migrations suivantes, en conservant des contraintes strictes et des index utiles :

### `basins`
- `id` UUID ou BIGINT PK ; `name` unique non nul ; `code` nullable ; `created_at`.

### `reservoirs`
- `id` UUID ou BIGINT PK ; `basin_id` FK ; `name` non nul ; `normalized_name` ; `capacity_mm3` nullable ; `latitude`, `longitude` nullable ; `coordinates_source` nullable ; `created_at`, `updated_at`.
- Unicité raisonnée sur `(basin_id, normalized_name)` ; ne pas dédupliquer sur une simple ressemblance de nom sans validation.

### `data_sources`
- `id` PK ; `title` ; `producer` ; `dataset_url` ; `license` nullable ; `source_type` ; `checked_at` ; `verification_status`.

### `ingestion_runs`
- `id` PK ; `source_id` FK ; `filename` ; `sha256` ; `started_at`, `completed_at` ; `status` (`pending`, `success`, `partial`, `failed`) ; `rows_read`, `rows_valid`, `rows_rejected` ; `error_summary` ; `is_demo` bool.
- Index sur `sha256` et `source_id` ; répétition du même fichier = résultat idempotent.

### `reservoir_measurements`
- `id` PK ; `reservoir_id` FK ; `source_id` FK ; `ingestion_run_id` FK ; `observation_date` DATE ; `storage_mm3` NUMERIC nullable ; `filling_rate_pct` NUMERIC nullable ; `published_at` nullable ; `ingested_at` timestamp ; `quality_status` ; `data_kind` (`OFFICIAL`, `DEMO`, `UNVERIFIED`).
- Contrainte : `storage_mm3 >= 0` si présent ; `0 <= filling_rate_pct <= 100` si présent.
- Unique `(reservoir_id, observation_date, source_id, data_kind)` pour le MVP ; documenter la politique de correction des données publiées (versions/révisions) avant d'écraser une observation.
- Index `(reservoir_id, observation_date DESC)`.

### `quality_issues`
- `id` PK ; `ingestion_run_id` FK ; `measurement_id` nullable ; `issue_type` ; `severity` ; `details` JSONB ; `resolved_at` nullable.

### `model_runs` (phase ML)
- `id` PK ; `mlflow_run_id` ; `model_name` ; `target` ; `horizon_days` ; `trained_at` ; `metrics` JSONB ; `dataset_version` ; `approved_for_display` bool default false.

Ne pas créer de comptes utilisateurs ni collecter de données personnelles dans le premier jalon. Les favoris pourront être stockés localement sur le client avant une éventuelle authentification.

## 7. Pipeline d'ingestion : contrat fonctionnel

### Commande CLI

Proposer une commande de type :

```bash
python -m pipelines.ingestion.import_xlsx --file data/raw/exemple.xlsx --source-id SOURCE_ID --dry-run
python -m pipelines.ingestion.import_xlsx --file data/raw/exemple.xlsx --source-id SOURCE_ID
```

Adapter les imports et le packaging pour que ces commandes fonctionnent réellement depuis la racine du dépôt.

### Étapes du pipeline

1. Vérifier le fichier, sa taille, son extension et son empreinte SHA-256.
2. Lire les feuilles XLSX sans supposer les en-têtes ; permettre un mapping configurable `config/column_mapping.yaml` après audit réel.
3. Normaliser les dates, nombres et unités ; conserver les valeurs originales en cas de rejet.
4. Associer les noms de barrages à des identifiants de référence, sans rapprochement automatique risqué.
5. Valider : date, unités, taux entre 0 et 100, réserve non négative, valeurs obligatoires.
6. Détecter doublons et anomalies ; journaliser les lignes rejetées avec raison.
7. Écrire en transaction ; assurer l'idempotence ; produire un bilan d'import.
8. Permettre `--dry-run` sans écriture en base.
9. En cas d'échec partiel, conserver un statut explicite et ne pas déclarer « succès » silencieusement.

**Tests à couvrir :** fichier valide, fichier vide, feuille inconnue, date invalide, taux > 100, réserve négative, doublon intra-fichier, réimport identique, format décimal français, absence de coordonnées, rollback en cas d'erreur.

## 8. Contrat API REST v1

Base `/api/v1` ; réponses JSON cohérentes ; dates ISO 8601 ; pagination ; erreurs normalisées ; CORS limité aux origines configurées.

| Méthode | Route | Usage |
|---|---|---|
| GET | `/health` | Liveness sans dépendance externe |
| GET | `/ready` | Readiness incluant base de données |
| GET | `/api/v1/basins` | Bassins disponibles |
| GET | `/api/v1/reservoirs` | Liste, recherche, filtre `basin_id`, pagination |
| GET | `/api/v1/reservoirs/{id}` | Détail, coordonnées uniquement si vérifiées |
| GET | `/api/v1/reservoirs/{id}/measurements` | Historique, `start_date`, `end_date`, `limit` |
| GET | `/api/v1/reservoirs/{id}/summary` | Dernière observation, tendances calculables |
| GET | `/api/v1/overview` | Indicateurs agrégés pour la sélection courante |
| GET | `/api/v1/data/freshness` | Dates des sources, statuts d'import |
| GET | `/api/v1/data/quality` | Indicateurs de qualité et anomalies |
| GET | `/api/v1/sources` | Sources, producteurs, licences |
| GET | `/api/v1/models/metrics` | Expériences validées, vide si aucune |
| POST | `/api/v1/predictions` | **Désactivé** jusqu'à validation ML |

### Exemples de réponses

```json
{
  "reservoir_id": "demo-reservoir-1",
  "name": "Barrage de démonstration",
  "latest": {
    "observation_date": "2026-10-01",
    "storage_mm3": 42.5,
    "filling_rate_pct": 35.0
  },
  "source": {
    "title": "Jeu synthétique de démonstration",
    "dataset_url": null,
    "data_kind": "DEMO"
  },
  "is_real_time": false,
  "updated_at": "2026-10-02T09:00:00Z"
}
```

Cet exemple est **synthétique**. Ne pas utiliser ses chiffres dans les données officielles.

**Agrégation :** ne pas calculer le « taux national » comme simple moyenne non pondérée des taux de barrages. Pour un groupe de barrages dont les capacités sont vérifiées et compatibles, calculer un taux pondéré `sum(storage_mm3)/sum(capacity_mm3)*100`, avec couverture explicitée ; sinon afficher `non disponible`. Ne pas additionner des observations prises à des dates différentes sans avertissement.

## 9. Design Web — spécifications détaillées

**Style :** produit SaaS institutionnel moderne, sobre, fond blanc/gris clair, bleu profond `#123A68`, bleu eau `#087FB4`, turquoise `#14B8A6`, orange d'attention `#F59E0B`, texte `#172033`. Contrastes WCAG AA, états focus visibles, composants accessibles, mobile-first. Ne pas copier une maquette pixel par pixel si cela dégrade l'ergonomie.

### Navigation latérale

1. Tableau de bord
2. Barrages
3. Carte interactive
4. Analyses et tendances
5. Prévisions IA (badge « expérimental » ou désactivé)
6. Qualité des données
7. Sources et méthodologie
8. Rapports (export CSV d'abord)
9. Paramètres (langue et thème ultérieurement)

### Écran A — Tableau de bord

- En-tête : logo AquaMaroc AI, titre, filtre de bassin, plage de dates, recherche, dernière actualisation.
- Cartes KPI : nombre de barrages avec données, réserves agrégées si comparables, taux pondéré si calculable, dernière date d'observation.
- Bloc carte MapLibre : points uniquement si coordonnées vérifiées ; sinon état vide « coordonnées non disponibles ».
- Bloc ECharts : historique des réserves et taux, choix des unités, tooltips incluant date et source.
- Tableau des barrages : nom, bassin, dernière réserve, taux, date du relevé, statut de qualité ; tri et recherche.
- Bloc « Qualité des données » : nombre de fichiers ingérés, observations valides, erreurs, données manquantes.
- Bloc « Analyses IA » : présentation des expériences seulement si validées ; sinon message « modèle non encore évalué ».
- Pied de page : attribution, licence, méthodologie et avertissement sur la fréquence des publications.

### Écran B — Détail barrage

- Nom, bassin, date du dernier relevé, source et statut.
- Cartes réserve, remplissage, capacité si connue.
- Historique ECharts avec zoom et sélecteur de période.
- Comparaison de deux périodes, uniquement si dates disponibles.
- Liste des dernières mesures et export CSV.
- Encadré « Comment lire ces données ? ».

### Écran C — Carte

- Fond cartographique sous licence appropriée, légende accessible, recherche.
- Marqueurs par barrage avec géométrie vérifiée.
- Filtres bassin, date, taux de remplissage.
- Panneau latéral de détail ; pas de géocodage approximatif caché.

### Écran D — Qualité des données

- Source, date de vérification, dernier import, état.
- Tableau des anomalies : doublon, valeur hors plage, date manquante, format inconnu.
- Pourcentages calculés avec dénominateurs affichés.
- Export des anomalies et traçabilité par fichier.

### Écrans de service

- Chargement, absence de données, erreur réseau, source indisponible, absence de coordonnées.
- Tous les graphiques et tableaux doivent fonctionner avec clavier et lecteurs d'écran dans la mesure du possible ; fournir alternatives textuelles.

## 10. Application mobile Flutter — spécifications

**Écrans :** Accueil, Barrages, Détail barrage, Carte, Favoris, À propos des données.

**Accueil :** dernière date de relevé, résumé du bassin, accès rapides, favoris locaux. **Barrages :** recherche, filtres, cartes compactes. **Détail :** graphique historique, dernières valeurs, provenance. **Carte :** points vérifiés seulement. **Favoris :** stockage local sans compte. **Notifications :** reportées après définition d'un service de synchronisation fiable ; ne pas annoncer une alerte de risque officiel.

**Architecture Flutter :** séparation `features`, `data`, `domain`, `presentation` ; client HTTP avec timeout, gestion d'erreurs et modèles typés ; stratégie de cache et indicateur « dernière synchronisation » ; tests widgets et tests de parsing JSON.

## 11. Spécification détaillée Machine Learning et MLOps

> **Règle principale :** ne pas présenter un modèle comme fiable sans évaluation chronologique sur des données officielles suffisamment longues. Avec seulement quelques mois de relevés, implémenter le pipeline et les baselines, puis signaler `insufficient_history` si nécessaire.

### 11.1 Cas d'usage et cibles

**UC-ML-01 — Prévision des réserves :** prédire `storage_mm3` pour un barrage donné aux horizons **J+7 et J+30**, évalués séparément. Prévoir J+1 comme baseline technique si utile. Le taux de remplissage peut être déduit de la réserve et de la capacité officielle vérifiée, mais ne jamais inventer cette capacité.

**UC-ML-02 — Détection d'anomalies :** identifier des observations suspectes (doublons, valeurs hors bornes, ruptures inhabituelles). Distinguer les erreurs de données des événements hydrologiques réels ; ne jamais qualifier automatiquement une anomalie de danger.

**UC-ML-03 — Explicabilité :** produire des explications SHAP pour les modèles tabulaires compatibles, sans les présenter comme des relations causales.

**UC-ML-04 — Suivi expérimental :** comparer les modèles avec MLflow et enregistrer les jeux de données, versions, métriques et artefacts reproductibles.

### 11.2 Audit préalable et critère d'éligibilité

Avant tout entraînement, créer `machine-learning/reports/data_readiness.json` et un rapport Markdown comprenant :

- nombre de barrages, nombre d'observations par barrage, première et dernière dates ;
- fréquence réelle, jours manquants, doublons, valeurs nulles et changements de schéma ;
- distribution des réserves et variations quotidiennes ;
- disponibilité d'une capacité vérifiée, de la pluie et des variables météo ;
- présence d'assez de périodes distinctes pour un test chronologique et, si nécessaire, une analyse saisonnière ;
- décision explicite `ready_for_experiments`, `baseline_only` ou `insufficient_history`, avec justification.

Ne fixer **aucun seuil arbitraire universel** de jours qui garantirait la fiabilité. Un historique couvrant moins d'un cycle saisonnier complet ne permet pas de valider correctement la saisonnalité annuelle. Les prédictions expérimentales ne deviennent pas automatiquement des prévisions opérationnelles.

### 11.3 Modèles retenus et ordre d'implémentation

| Identifiant | Modèle | Usage | Statut |
|---|---|---|---|
| `naive_last_value` | Persistence / dernière valeur | Baseline incontournable | MVP |
| `moving_average` | Moyenne mobile historique | Baseline secondaire | MVP |
| `catboost` | `CatBoostRegressor` | Candidat tabulaire de référence, catégories natives | Après audit |
| `xgboost` | `XGBRegressor` | Concurrent tabulaire | Après audit |
| `lightgbm` | `LGBMRegressor` | Concurrent tabulaire | Après audit |
| `sarima` | SARIMA | Modèle temporel univarié | Historique long |
| `sarimax` | SARIMAX | Modèle temporel avec variables externes connues | Historique + exogènes |
| `isolation_forest` | `IsolationForest` | Détection d'anomalies | Après règles métier |
| `lstm` | Réseau LSTM PyTorch | Recherche expérimentale | Optionnel, long historique |

**Important :** CatBoost, XGBoost et LightGBM sont des **candidats**, sans gagnant présumé. Sélectionner par horizon sur la validation chronologique, puis confirmer la performance sur un test final intact. Conserver la baseline si aucun candidat ne démontre un gain acceptable, avec une complexité et une latence maîtrisées. Ne pas entraîner LSTM sur un historique trop court pour justifier son coût.

### 11.4 Variables explicatives et prévention des fuites

Construire les caractéristiques **par barrage**, triées par date :

- `storage_lag_1`, `storage_lag_7`, `storage_lag_14`, `storage_lag_30` ;
- variations passées : `delta_1d`, `delta_7d` ;
- moyennes mobiles **décalées** : `rolling_mean_7`, `rolling_mean_30` ;
- volatilité passée : `rolling_std_7`, `rolling_std_30` ;
- mois et encodage cyclique du jour de l'année ;
- pluviométrie passée uniquement si elle provient d'une source légale et vérifiée ;
- identifiant du barrage et capacité officielle si disponible.

Pour prédire à l'horizon de `h` jours, associer chaque date `t` à la mesure du même barrage datée exactement de `t + h jours`. `storage_mm3.shift(-h)` par barrage convient uniquement sur une grille quotidienne régulière vérifiée ; sur des dates irrégulières, utiliser une jointure de dates et exclure les cibles absentes, sans interpolation depuis le futur. Vérifier aussi les lags exprimés en jours. Aucune feature ne doit utiliser une observation postérieure à la date de prévision. Ne pas mélanger les séries entre barrages. Les données météo futures ne peuvent être utilisées que si une prévision météorologique réellement disponible à la date de décision est archivée ; sinon les exclure.

Pour les prévisions multi-horizons, commencer par une stratégie **directe** : un modèle pour J+7 et un autre pour J+30. Ne pas alimenter J+30 avec les valeurs réelles des jours intermédiaires.

### 11.5 Pipeline d'entraînement, validation chronologique et sélection

1. Versionner un découpage `train → validation → test final` par dates calendaires communes à tous les barrages. Une même date ne doit pas être répartie aléatoirement entre ensembles ; interdire mélange aléatoire et validation croisée aléatoire. Réserver le bloc final le plus récent avant toute recherche.
2. Utiliser une validation à origine glissante (`rolling-origin`, fenêtres croissantes ou glissantes documentées) sur les périodes pré-test si l'historique le permet ; sinon justifier une validation chronologique fixe. Purger à chaque frontière les exemples dont la cible à `t + h` n'est pas encore disponible au début du bloc suivant. Tenir compte des dates réelles de publication lorsqu'elles sont connues. Documenter les bornes, exclusions et gaps par horizon ; un nombre de lignes ne remplace pas un écart calendaire sur une série irrégulière.
3. Ajuster imputations, encodages et transformations apprises uniquement sur le train de chaque fenêtre. Aucun encodage de cible ne doit apprendre de la validation ou du test. Les features de validation/test utilisent seulement les informations disponibles à leur date de prévision selon le protocole de réémission documenté.
4. Comparer les baselines, CatBoost, XGBoost, LightGBM et les candidats AutoML sur les mêmes dates, barrages et cibles éligibles, avec budgets explicites et seeds journalisées. Signaler exclusions et couverture ; ne pas favoriser un modèle par un sous-ensemble plus facile.
5. Pour CatBoost, utiliser `CatBoostRegressor` et des `Pool` conservant noms et ordre des features. Déclarer `cat_features` (notamment l'identifiant du barrage), convertir les catégories en chaînes et remplacer leurs valeurs manquantes par un marqueur constant. Trier par date puis barrage et fixer `has_time=True` pour préserver l'ordre fourni dans les traitements internes concernés ; ce paramètre ne remplace pas le découpage et la purge externes. Documenter NaN numériques et catégories inconnues à l'inférence.
6. Fixer et tracer `random_seed`, `loss_function`, `eval_metric`, `iterations`, `depth`, `learning_rate`, `l2_leaf_reg`, `thread_count` et `task_type` (CPU par défaut). Rechercher les hyperparamètres uniquement sur les fenêtres de validation. Utiliser leur `eval_set` pour l'early stopping et `use_best_model=True`, jamais le test final. Appliquer la même séparation aux concurrents.
7. Mesurer **MAE**, **RMSE** en Mm³, biais moyen et gain relatif face aux baselines ; sMAPE facultative avec précautions près de zéro. Produire les métriques globales, par barrage, horizon et période, ainsi que la dispersion entre fenêtres. Déclarer avant la recherche une métrique principale (MAE par défaut), son agrégation et le départage (stabilité, puis complexité et latence).
8. Sélectionner modèle et hyperparamètres sur la validation chronologique uniquement, séparément pour J+7 et J+30 ; consigner la décision et le gain minimal attendu face aux baselines. Aucun gagnant n'est imposé par famille.
9. Après gel du choix, réentraîner sur train + validation en respectant la disponibilité des cibles, avec un nombre d'itérations fixé depuis la validation et sans early stopping sur le test. Évaluer une seule fois le modèle retenu et les baselines sur le test final intact pour approuver ou refuser son utilisation. Un échec ne permet pas de choisir un autre candidat sur ce même test ; une nouvelle recherche exige une nouvelle période finale indépendante.
10. Générer graphique prédit/réel, résidus, erreurs extrêmes et rapport de sélection. Ne jamais présenter un score de train comme une mesure de généralisation ni fabriquer une métrique.

**Orchestration :** `train.py` enchaîne audit d'éligibilité, construction des cibles/features, fenêtres purgées, baselines, recherche des trois candidats et benchmarks optionnels, sélection sur validation, réentraînement et évaluation finale. Centraliser dans les configurations J+7/J+30 : dates, disponibilité des données, features, catégories, seeds, budgets, espaces d'hyperparamètres, métrique et critères d'approbation.

**Artefacts :** sauvegarder CatBoost au format natif `.cbm`, avec schéma d'entrée, catégories, politique de valeurs manquantes, versions et configuration. Vérifier les prédictions après rechargement, y compris sur une catégorie inconnue. `serving.py` recharge prétraitement et modèle approuvés sans nouvel ajustement sur les données d'inférence. Aucun entraînement ne rend automatiquement un modèle public.

### 11.6 H2O AutoML et FLAML

Les benchmarks utilisent les mêmes fenêtres chronologiques purgées et la même métrique principale que les candidats dédiés. Ils participent à la sélection sur validation ; le test final ne doit alimenter aucun leaderboard. Tracer versions, seeds, budgets, durée, latence et algorithmes réellement exécutés.

**H2O AutoML :** CatBoost n'est pas un algorithme natif H2O ; le comparer comme candidat entraîné séparément. Fixer `nfolds=0` et fournir explicitement `training_frame`, `validation_frame` et `leaderboard_frame` issus des blocs pré-test pour éviter les partitions automatiques aléatoires. Les deux derniers peuvent utiliser le même bloc de validation chronologique, avec cette réutilisation documentée. Exclure `DRF` et `StackedEnsemble` via `exclude_algos` pour ce benchmark. Fixer `seed`, `max_models` et/ou un budget de temps ; conserver leaderboard et configuration. Consigner la disponibilité de XGBoost dans l'environnement H2O ; maintenir dans tous les cas le concurrent XGBoost Python dédié.

**FLAML :** utiliser `task="regression"`, `estimator_list=["catboost", "xgboost", "lgbm"]`, une métrique cohérente avec la sélection et un `time_budget` fixé. Passer explicitement `X_train`, `y_train`, `X_val`, `y_val` des blocs externes avec `eval_method="holdout"` ; ne pas laisser créer de holdout aléatoire ou de validation croisée par défaut. Répéter sur les fenêtres préparées si le backtesting est retenu. Vérifier que les adaptateurs respectent le prétraitement et la disponibilité des données, ainsi que l'ordre temporel CatBoost ; adapter la configuration ou signaler explicitement l'exclusion d'un estimateur si la version installée ne peut garantir ce contrat. Ne pas déclarer évalués les candidats non exécutés faute de budget ou de compatibilité.

Recalculer les scores de validation avec l'évaluateur commun dans les unités originales. Le candidat AutoML retenu suit le même réentraînement et test final que tout autre gagnant. Déployer uniquement le modèle approuvé par horizon ; les moteurs AutoML servent à la comparaison hors production.

### 11.7 Détection d'anomalies

**Étape A — règles déterministes :** réserves négatives, taux hors bornes plausibles, dates dupliquées, capacités incohérentes, valeurs manquantes, variations importantes à examiner.

**Étape B — Isolation Forest :** utiliser uniquement les observations historiques validées et des features comme variation, moyenne mobile et volatilité. Fixer et documenter `contamination` en tant qu'hypothèse expérimentale, non comme fréquence réelle des anomalies.

Afficher `à vérifier`, `erreur de donnée confirmée` ou `variation inhabituelle` selon les preuves. Aucune notification de risque hydrologique automatique sans validation métier.

### 11.8 Explicabilité SHAP

Pour CatBoost, XGBoost et LightGBM, produire un résumé global et une explication locale sur un échantillon chronologique représentatif. Pendant la recherche, expliquer des observations de validation ; analyser le test final seulement après gel du choix, sans réajustement.

Pour CatBoost, privilégier `model.get_feature_importance(pool, type="ShapValues")` avec un `Pool` conservant le schéma et les `cat_features` de l'entraînement. Pour une régression à cible unique, séparer les contributions des features de la dernière colonne, qui contient la valeur de référence. Vérifier que référence + somme des contributions reconstitue la prédiction dans la sortie expliquée, avec une tolérance numérique documentée. `shap.TreeExplainer` peut être utilisé si sa compatibilité avec le modèle et les catégories est vérifiée. Appliquer le même contrat d'additivité aux explications XGBoost/LightGBM. Tout jeu de référence nécessaire provient exclusivement du train.

Afficher date, barrage, horizon, version du modèle, référence et unités (Mm³ pour la sortie de régression non transformée). Conserver l'alignement features/contributions, les paramètres d'explication et les figures dans MLflow. SHAP explique le comportement du modèle, **pas la cause physique** d'une variation.

### 11.9 MLflow : conventions et artefacts

Configurer un serveur MLflow local (stockage persistant, artefacts dans un volume dédié). Expériences recommandées :

- `aquamaroc-forecast-7d`
- `aquamaroc-forecast-30d`
- `aquamaroc-anomaly-detection`

Tags obligatoires : `data_source`, `dataset_version`, `git_commit`, `reservoir_scope`, `forecast_horizon`, `split_strategy`, `model_family`, `experiment_status`.

Logger : paramètres, seed, versions de bibliothèques, intervalles de dates, MAE/RMSE distinguant validation et test final, scores par barrage, courbes, configuration et signature d'entrée/sortie. Conserver fenêtres purgées, budgets, nombre d'itérations retenu, rapport de sélection, artefact `.cbm` pour CatBoost, schéma des catégories, contrôle de rechargement et artefacts SHAP. Enregistrer le modèle dans le registre seulement après validation et avec une décision explicite d'approbation. Ne pas mettre des données sensibles ou secrets dans les artefacts.

### 11.10 Contrat d'inférence API

Prévoir, **uniquement après validation des modèles**, les routes :

- `GET /api/v1/ml/models` : modèles disponibles, version, statut et métriques ;
- `GET /api/v1/reservoirs/{id}/forecasts?horizon_days=7` : prévision et métadonnées ;
- `GET /api/v1/reservoirs/{id}/anomalies` : observations signalées avec motifs ;
- `GET /api/v1/ml/health` : disponibilité du service ML.

Exemple **illustratif de schéma, sans chiffres de prédiction inventés** :

```json
{
  "reservoir_id": 1,
  "as_of_date": "2026-10-31",
  "horizon_days": 7,
  "predicted_storage_mm3": null,
  "prediction_interval_mm3": null,
  "model_name": null,
  "model_version": null,
  "status": "insufficient_history",
  "source": "official",
  "disclaimer": "Aucune prévision validée disponible"
}
```

Si le modèle est indisponible, répondre avec un statut métier clair, sans générer une fausse prédiction. Les intervalles d'incertitude ne doivent être fournis que s'ils ont été calibrés et évalués.

### 11.11 Monitoring et dérive

- **Prometheus + Grafana** : disponibilité API, erreurs, latences p50/p95, ressources système.
- **Qualité des données** : fraîcheur, anomalies, dates manquantes, évolution du schéma.
- **Performance ML** : suivi des MAE/RMSE lorsque les valeurs réelles deviennent disponibles, dérive des variables et dégradation face à la baseline.
- **MLflow** : historique des entraînements, paramètres et modèles.
- Grafana sert à l'observabilité technique ; **Next.js + ECharts** reste le dashboard métier.

### 11.12 Organisation du code ML

```text
machine-learning/
├── pyproject.toml                 # dépendances ML et groupes AutoML
├── configs/
│   ├── forecast_7d.yaml
│   ├── forecast_30d.yaml
│   └── anomaly_detection.yaml
├── src/aquamaroc_ml/
│   ├── data_readiness.py
│   ├── features.py
│   ├── splits.py
│   ├── baselines.py
│   ├── train.py
│   ├── selection.py
│   ├── catboost_model.py
│   ├── evaluate.py
│   ├── explain.py
│   ├── anomalies.py
│   ├── mlflow_tracking.py
│   └── serving.py
├── benchmarks/
│   ├── h2o_automl.py
│   └── flaml_automl.py
├── tests/
│   ├── test_no_future_leakage.py
│   ├── test_grouped_lags.py
│   ├── test_temporal_split.py
│   ├── test_naive_baseline.py
│   ├── test_catboost_training.py
│   ├── test_model_selection.py
│   ├── test_automl_temporal_contract.py
│   ├── test_shap_additivity.py
│   ├── test_model_roundtrip.py
│   └── test_forecast_schema.py
└── reports/
```

### 11.13 Critères d'acceptation ML

1. Un rapport d'éligibilité des données est généré sans entraînement obligatoire.
2. Les baselines s'exécutent sur un jeu **synthétique explicitement marqué**.
3. Les tests prouvent qu'aucune variable ne consulte le futur.
4. CatBoost, XGBoost et LightGBM sont comparés aux baselines sur les mêmes fenêtres chronologiques purgées ; la sélection par horizon utilise la validation uniquement, puis un test final indépendant confirme ou refuse l'approbation.
5. MLflow conserve les métriques et les artefacts d'une expérience locale.
6. Les modèles expérimentaux restent séparés du service public tant qu'ils ne sont pas validés.
7. L'API signale proprement `insufficient_history` lorsqu'aucune prévision fiable n'est disponible.
8. Un entraînement CatBoost synthétique, le rechargement `.cbm`, les catégories inconnues, l'additivité SHAP et les contrats temporels H2O/FLAML sont vérifiés.

## 12. Sécurité, fiabilité, conformité

- Aucune clé API, mot de passe ou URL secrète dans Git.
- Variables d'environnement validées au démarrage ; `.env.example` sans secrets réels.
- Conteneurs non-root si possible, images épinglées et mises à jour.
- Validation Pydantic de tous les paramètres ; requêtes SQL paramétrées via ORM.
- CORS configuré ; rate limiting pour endpoints publics lors du déploiement.
- Routes d'import et d'administration non publiques ; ne pas exposer d'endpoint d'upload sans authentification.
- Sauvegardes PostgreSQL et restauration testée avant mise en production.
- Respect des licences des données et fonds cartographiques, attribution affichée.
- Journalisation sans informations personnelles ; ne pas ajouter d'analytics intrusifs par défaut.
- Déclarer explicitement que les analyses ne constituent pas une communication officielle des autorités hydrauliques.

## 13. Environnements et exécution locale

### Prérequis

Docker Desktop/Engine + Compose, Git, Node.js LTS compatible avec la version Next.js retenue, Python compatible avec les dépendances, Flutter SDK uniquement pour le jalon mobile. Vérifier les versions stables au moment de l'implémentation et les figer dans le dépôt.

### Services Docker MVP

- `db` : PostgreSQL/PostGIS, volume persistant, healthcheck.
- `api` : FastAPI, dépendance sur DB saine, migrations documentées.
- `web` : Next.js, variable d'URL API adaptée au réseau Docker et au navigateur.
- `mlflow` : **profil optionnel** ; ne pas le lancer par défaut si non utilisé.

Prévoir des commandes de type :

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
docker compose logs -f api
# commandes exactes de migration et de tests à documenter dans README
```

Ne pas écrire dans README qu'une commande fonctionne avant de l'avoir vérifiée.

## 14. Tests et définition de terminé

### Backend

- `GET /health` = 200.
- `GET /ready` reflète correctement l'état DB.
- CRUD lecture via API avec pagination, filtres et validation.
- Sérialisation des dates, décimaux et statuts.
- Tests d'intégration PostgreSQL sur DB isolée.

### ETL

- Tests unitaires du parseur et du mapping.
- Import reproductible et idempotent.
- Comptage cohérent `rows_read = rows_valid + rows_rejected` selon la définition documentée.
- Rapport des anomalies sans perte silencieuse.

### Web

- Navigation clavier, contraste, responsive 360px à desktop.
- Gestion loading/error/empty.
- Aucun chiffre fictif présenté sans bandeau `Données de démonstration`.
- Graphiques et tableaux affichant unités, période et source.

### ML (jalon 5)

- Sur fixtures synthétiques marquées `DEMO`, tester cibles J+7/J+30 par date, lags par barrage, dates irrégulières, frontières communes entre barrages et purge des cibles indisponibles.
- Entraîner un petit `CatBoostRegressor` avec catégorie barrage et valeurs manquantes ; vérifier schéma, `cat_features`, ordre temporel, paramètres figés et early stopping limité à la validation.
- Vérifier que modifier valeurs ou labels du test final ne modifie ni hyperparamètres, ni modèle sélectionné, ni nombre d'itérations. Tester le choix sur scores de validation contrôlés, le départage et le maintien de la baseline si le gain est insuffisant ; ne pas imposer CatBoost comme gagnant.
- Vérifier les mêmes couples date/barrage et horizons pour tous les modèles, les métriques MAE/RMSE et leur agrégation documentée.
- Tester les adaptateurs AutoML : `nfolds=0`, frames explicites et exclusions H2O ; liste CatBoost/XGBoost/LightGBM et holdout explicite FLAML. Vérifier que ni sélection, ni leaderboard, ni early stopping n'accèdent au test final.
- Tester forme, valeurs finies, alignement des features et additivité SHAP, ainsi que la conservation des prédictions après sauvegarde/rechargement CatBoost, y compris sur une catégorie inconnue.
- Tester imports du groupe ML verrouillé et artefacts MLflow requis. Exécuter les intégrations AutoML dans des jobs optionnels avec les dépendances réelles ; signaler les tests ignorés et leurs raisons.

### CI

- Lint Python et TypeScript.
- Tests backend et pipeline. À J5, ajouter un job ML sur données synthétiques (CatBoost, concurrents, sélection chronologique, SHAP, sérialisation) et des jobs AutoML optionnels à budgets bornés.
- Build Web.
- Vérification des fichiers `.env` et secrets accidentels.

## 15. Roadmap en six jalons

| Jalon | Résultat attendu | Dépendances |
|---|---|---|
| J1 — Socle & données | Monorepo, Compose, DB, migrations, ingestion locale, API minimale, tests | Aucune |
| J2 — Dashboard Web | Pages principales Next.js, ECharts, filtres, états, sources | J1 |
| J3 — Mobile Flutter | Accueil, liste, détail, favoris, client API | J1 |
| J4 — Cartographie et qualité | MapLibre avec coordonnées vérifiées, contrôles de qualité | J1/J2 |
| J5 — ML expérimental | Audit d'éligibilité, baselines, CatBoost/XGBoost/LightGBM, H2O/FLAML, SHAP, Isolation Forest, MLflow, sélection sur validation chronologique et test final indépendant | Historique suffisant |
| J6 — Déploiement | CI/CD, sécurité, monitoring, sauvegardes, documentation | J1–J5 pertinents |

### Ordre de priorité si le temps est limité

**P0 :** pipeline, DB, API, dashboard historique, provenance.  
**P1 :** mobile, carte, qualité, export CSV.  
**P2 :** modèles ML, AutoML, MLflow, notifications, déploiement avancé.

## 16. Travail exact demandé à Codex maintenant — JALON 1

1. Examiner le dossier courant ; présenter les hypothèses techniques et les risques.
2. Créer le monorepo, `AGENTS.md`, README, `.gitignore`, `.env.example` et Docker Compose.
3. Initialiser PostgreSQL/PostGIS, FastAPI, SQLAlchemy et Alembic.
4. Créer les tables `basins`, `reservoirs`, `data_sources`, `ingestion_runs`, `reservoir_measurements`, `quality_issues`.
5. Implémenter `/health`, `/ready`, `/api/v1/basins`, `/api/v1/reservoirs`, `/api/v1/reservoirs/{id}/measurements`, `/api/v1/data/freshness`.
6. Créer un jeu **synthétique** minimal dans `data/demo/` avec une bannière de provenance `DEMO`, sans reprendre les valeurs des maquettes.
7. Implémenter un import CLI configurable, avec un mapping de colonnes documenté et un test sur fixture XLSX synthétique.
8. Écrire les tests ETL/API, configurer Ruff/Pytest et un workflow CI minimal.
9. Préparer un squelette Next.js simple uniquement si le socle backend est validé ; ne pas construire encore les écrans complets.
10. Produire `docs/decisions/0001-architecture.md`, `docs/data-sources.md` et une liste explicite des éléments à vérifier sur les fichiers officiels.
11. Exécuter les commandes, rapporter les résultats de tests et les limitations ; proposer les fichiers et tâches du jalon 2.

### Format attendu du compte rendu Codex

```text
1. Résumé des fichiers créés/modifiés
2. Choix d'architecture et justifications
3. Commandes exactes de lancement
4. Résultats des tests réellement exécutés
5. Endpoints disponibles et exemples curl
6. Sources officielles vérifiées / à vérifier
7. Limitations et dette technique
8. Prochaines étapes (J2)
```

## 17. Questions bloquantes à résoudre avant la vraie ingestion

- Les fichiers XLSX officiels sont-ils effectivement téléchargeables dans l'environnement Codex ?
- Quelles sont les colonnes et feuilles exactes ?
- Quelle est la profondeur historique réellement disponible ?
- Quelles sont les conventions de noms des barrages ?
- Les capacités maximales et coordonnées sont-elles disponibles et sourcées ?
- Quelles conditions de licence et d'attribution s'appliquent aux ressources réutilisées ?
- Y a-t-il des corrections rétroactives de mesures publiées ?

**Si ces réponses manquent, avancer avec des fixtures synthétiques et marquer les tâches de vérification ; ne pas inventer les réponses.**

## 18. Prompt de lancement à copier dans Codex

> Lis entièrement `AquaMaroc_AI_Codex_Specification.md` et considère-le comme le cahier des charges de référence. Inspecte le dépôt existant, puis réalise uniquement le **jalon 1** de la section 16. Applique toutes les contraintes de provenance et de sécurité. Commence par proposer un plan bref, puis code, exécute les tests et documente précisément les résultats. N'invente aucune donnée officielle et ne mets pas en place Power BI. Si l'accès aux fichiers officiels est indisponible, utilise uniquement des fixtures synthétiques clairement étiquetées `DEMO`. Termine par un compte rendu structuré et les commandes exactes pour lancer le projet localement.

---

**Note de cadrage :** cette spécification est un plan d'implémentation, pas la preuve que les données ou les fonctions avancées sont déjà disponibles. Les éléments non vérifiés doivent rester explicitement identifiés jusqu'à l'audit des sources.

## 19. Références techniques de la révision CatBoost

Contrats à revérifier avec les versions verrouillées lors de l'implémentation :

- [CatBoostRegressor et catégories](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor).
- [Paramètres CatBoost, dont has_time](https://catboost.ai/docs/en/references/training-parameters/common).
- [Contributions SHAP CatBoost](https://catboost.ai/docs/en/concepts/shap-values).
- [H2O AutoML : algorithmes, frames et validation](https://docs.h2o.ai/h2o/latest-stable/h2o-docs/automl.html).
- [Interface AutoML FLAML : estimateurs et validation externe](https://github.com/microsoft/FLAML/blob/main/flaml/automl/automl.py).
