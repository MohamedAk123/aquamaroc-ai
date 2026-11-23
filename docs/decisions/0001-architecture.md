# ADR 0001 — Socle modulaire, ingestion locale et ML hors ligne

Date : 17 novembre 2026. Statut : adopté pour J1.

La spécification v2.1 (révision CatBoost demandée précédemment) est la référence du
dépôt. La v2 originale a été consultée depuis Downloads ; elle n'existe pas sous le
nom `AquaMaroc_AI_Codex_Specification_v2.md` dans le dossier courant.

## Décisions

- Monorepo Python : `services/api/app` contient configuration, modèles, schémas,
  accès aux données et routes ; `pipelines` contient mapping, normalisation,
  validation et import. Packaging/dépendances centralisés à la racine.
- FastAPI/Pydantic 2, SQLAlchemy 2 synchrone et Alembic. Aucun `create_all` au
  démarrage : les migrations sont explicites et le service `migrate` précède l'API.
- PostgreSQL 16/PostGIS est la cible. UUID, NUMERIC, JSONB et geometry POINT/4326.
  SQLite est uniquement un mode local/test rapide, avec clés étrangères activées ;
  il ne prouve ni la compatibilité PostGIS ni les propriétés de concurrence PostgreSQL.
- Six tables métier au J1 ; `model_runs` et les routes prédictives attendent J5.
- Les coordonnées et capacités restent nulles sans preuve officielle. Aucun géocodage.
- Lecture XLSX en flux avec openpyxl : pas de dépendance Pandas dans le chemin J1,
  puisque le schéma officiel n'est pas audité. Pandas appartient au futur groupe ML.
- Référentiel explicite noms/UUID ; aucun rapprochement flou. Le mapping contient
  son mode, sa feuille, la ligne d'en-tête et les unités acceptées.
- Archivage brut par SHA-256, snapshot de provenance et empreinte du mapping.
  Un journal `pending` est commité avant la transaction de mesures pour conserver
  la trace d'un échec ; les mesures sont atomiques et les rejets sont journalisés.
- Le mode `demo` expose uniquement `DEMO` ; `official` expose `OFFICIAL` et
  `UNVERIFIED`, avec statut sur chaque observation. Les séries vérifiées et non
  vérifiées peuvent être séparées via `data_kind` ; aucune provenance n'est cachée.
- Pas de compte utilisateur, upload HTTP, Power BI ou infrastructure distribuée.
- L'organisation ML de la section 11 (`machine-learning/`) prime sur le chemin
  générique `ml/` de la section 5. Entraînement avancé volontairement inactif.
- Après validation PostgreSQL/PostGIS, un squelette Next.js minimal est ajouté ;
  les écrans métier restent réservés à J2.

## Limites et suites

L'API synchrone et le calcul de fraîcheur par source conviennent au petit MVP.
Mesurer avant d'optimiser. Le parsing officiel, les révisions de données, la
reprise explicite des imports échoués et les règles saisonnières exigent un audit.
Un import concurrent identique est protégé par une contrainte unique ; l'un des
appelants peut recevoir une erreur DB, sans duplication, et doit consulter le journal.
Un crash peut laisser `pending` : aucune reprise automatique n'est simulée au J1.

Références consultées : [sessions FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/),
[migrations Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html),
[modèles SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html).
