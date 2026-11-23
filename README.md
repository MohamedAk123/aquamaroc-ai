# AquaMaroc AI — jalons 1 à 4

Socle d'observation des ressources hydriques : API FastAPI, PostgreSQL/PostGIS,
migrations Alembic, import XLSX traçable et dashboard Next.js.
La référence est `AquaMaroc_AI_Codex_Specification_v2.1.md` (révision CatBoost).

Le Web et le mobile démarrent en mode officiel et utilisent les relevés du
bassin du Tensift d’août à octobre 2026. Une instance officielle sans relevés
affiche une sélection vide. Les fixtures synthétiques servent aux tests avec
`APP_MODE=demo` explicitement sélectionné. Les coordonnées des barrages restent
non renseignées et l’entraînement avancé est désactivé.
Voir [les sources](docs/data-sources.md) et [la procédure d’import](docs/ingestion.md).

## Démarrage Docker local

Pour relancer l’instance officielle après l’import, utiliser `.env` avec
`APP_MODE=official` : `docker compose --env-file .env up -d`.

Prérequis : Docker Desktop démarré, ports 5432/8000/3000 disponibles.
Depuis la racine, démarrer les services officiels sur `127.0.0.1`, puis importer
les trois classeurs s’ils sont présents dans `data/raw/tensift/`.

```powershell
docker compose --env-file .env.example up --build -d
docker compose --env-file .env.example ps
docker compose --env-file .env.example exec -T api python -m pipelines.ingestion.import_tensift
```

Le service `migrate` applique les migrations avant le démarrage de l’API.
Répéter l’import réutilise les journaux existants et laisse les relevés intacts.

- Web : http://127.0.0.1:3000
- API/OpenAPI : http://127.0.0.1:8000/docs
- Liveness : http://127.0.0.1:8000/health
- Readiness : http://127.0.0.1:8000/ready

Dans l'environnement Codex de cette livraison, le dossier de configuration Docker
utilisateur est restreint : les commandes ont été exécutées avec
`docker --config .docker-local compose ...`. Ce dossier local est ignoré par Git.

Pour une configuration personnalisée, copier `.env.example` vers `.env` sans écraser
un fichier existant, puis configurer les paramètres avant d'utiliser `docker compose`
sans `--env-file`. Encoder les caractères réservés du mot de passe dans `DATABASE_URL`.
L'URL DB du service Compose utilise le nom interne `db`, celle d'un Python local
utilise `localhost`.

```powershell
docker compose --env-file .env.example logs -f api
docker compose --env-file .env.example run --rm migrate
docker compose --env-file .env.example stop
```

`stop` conserve les volumes de base et d'archives. Aucun import officiel n'est
automatique. Le répertoire `data/raw/` est monté en lecture seule pour les imports locaux.

## Exécution Python locale

Python 3.12 recommandé (validé : 3.12.13 ; image API : 3.12.12). Les dépendances
runtime sont figées dans `requirements.lock`, les outils dans `requirements-dev.lock`.
Le packaging editable du monorepo a également été vérifié.

Installation dans un environnement neuf, avec le Python compatible sélectionné :

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.lock
.\.venv\Scripts\python -m pip install --no-deps -e .
```

L’environnement Python préparé est `.venv-verify`. Cette procédure est réservée
aux tests locaux et utilise une base SQLite dédiée :

```powershell
$env:DATABASE_URL='sqlite:///./aquamaroc-demo.db'
$env:APP_MODE='demo'
.\.venv-verify\Scripts\python -m alembic upgrade head
.\.venv-verify\Scripts\python -m pipelines.ingestion.demo
.\.venv-verify\Scripts\python -m pipelines.ingestion.import_xlsx --file data/demo/reservoirs_demo.xlsx --source-id 00000000-0000-0000-0000-000000000001 --dry-run
.\.venv-verify\Scripts\python -m pipelines.ingestion.import_xlsx --file data/demo/reservoirs_demo.xlsx --source-id 00000000-0000-0000-0000-000000000001
.\.venv-verify\Scripts\python -m scripts.audit_data --output machine-learning/reports
```

Pour lancer l'API depuis Python :

```powershell
.\.venv-verify\Scripts\python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8011
```

L’instance de test écoute sur le port 8011, séparé du serveur officiel Docker.

## Vérifications

```powershell
.\.venv-verify\Scripts\python -m ruff check .
.\.venv-verify\Scripts\python -m ruff format --check .
.\.venv-verify\Scripts\python -m pytest -q
```

Pour inclure PostgreSQL, créer une seule fois la base isolée `aquamaroc_test`
dans le conteneur de base de données :

```powershell
docker compose --env-file .env.example exec -T db createdb -U aquamaroc aquamaroc_test
$env:TEST_DATABASE_URL='postgresql+psycopg2://aquamaroc:CHANGE_ME@127.0.0.1:5432/aquamaroc_test'
.\.venv-verify\Scripts\python -m pytest -q -p no:cacheprovider --basetemp .pytest-local-run
```

La base doit être joignable ; le test crée puis supprime uniquement son schéma
aléatoire. Sans `TEST_DATABASE_URL`, ce test est explicitement ignoré. La CI prévoit
PostgreSQL/PostGIS et les contrôles Web ; son exécution GitHub n'est pas revendiquée.
La suite vérifie aussi le rollback, les réimports, la provenance, les erreurs API,
le découpage chronologique préparatoire et le verrouillage de l'entraînement.

## Web et ML

Le Web J2 fournit dashboard, liste/détail des barrages, historique ECharts, filtres,
comparaison de deux relevés, sources, synthèse de qualité et exports CSV traçables.
Les données officielles et non vérifiées restent séparées par statut ; le mode DEMO
porte une bannière visible. Les totaux et taux pondérés sont indisponibles lorsque
dates, sources, réserves ou capacités sourcées ne permettent pas leur calcul.
Depuis `apps/web` : `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test:unit`,
`npm run build`, puis `npm run start` (sur Windows, `npm.cmd` si nécessaire).
Le démarrage utilise le build standalone avec ses assets. Voir les tests navigateur
desktop/mobile et les commandes de préparation dans [le rapport J2](docs/jalon-2.md).

`machine-learning/` contient les configurations J+7/J+30/anomalies, les baselines,
les utilitaires temporels et [l’audit officiel du jalon 5](machine-learning/reports/data_readiness.md).
Les deux horizons sont classés `insufficient_history`.
Les dépendances CatBoost/XGBoost/LightGBM, SHAP, MLflow, H2O et FLAML sont déclarées
dans des extras distincts, sans installation ni entraînement avancé au J1. Leur
verrouillage attend la validation de compatibilité lors de J5.

## Documentation et suite

- [Compte rendu et résultats réels](docs/jalon-1-report.md)
- [Dashboard, architecture Web et validation J2](docs/jalon-2.md)
- [Interface issue de la maquette et validation visuelle](docs/interface-reference.md)
- [Application Flutter : lancement, architecture et tests](apps/mobile/README.md)
- [Compte rendu mobile J3](docs/jalon-3.md)
- [Architecture](docs/architecture.md) et [ADR 0001](docs/decisions/0001-architecture.md)
- [Contrat d'import et politique de révision](docs/ingestion.md)
- [Endpoints et exemples curl](docs/api.md)
- [Sources officielles à auditer](docs/data-sources.md) et [inventaire](docs/data-inventory.csv)
- [Préparation ML](machine-learning/README.md)

J1 et J2 sont livrés localement. Le client Flutter J3 est implémenté avec ses tests
et son aperçu local sur le port 3100 ; la validation native est détaillée dans son
rapport. Le [J4](docs/jalon-4.md) ajoute la carte et le journal de qualité.
Le jalon 5 a produit l’audit officiel. Le [jalon 6](docs/jalon-6.md) fournit
la configuration de déploiement, le monitoring et la procédure de restauration.
