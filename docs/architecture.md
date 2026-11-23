# Architecture J1

Le flux est : fichier local → archive SHA-256 → parsing configurable → validation
par ligne → transaction SQL → API REST en lecture. Le journal garde l'origine,
les compteurs, le statut et les rejets. Web et mobile utiliseront la même API.

`services/api/app/core` : configuration validée et logs JSON.
`db` : base déclarative et sessions ; `models` : contraintes métier.
`repositories` : requêtes ; `schemas` : contrats de sortie ; `api/v1` : routes.
`pipelines/normalization` et `validation` sont indépendants du transport HTTP.

Compose démarre PostgreSQL/PostGIS, applique Alembic puis lance l'API non-root.
La DB et les archives utilisent des volumes persistants. Aucun secret réel dans Git.
La configuration locale charge `.env` ; les origines CORS doivent être explicites.
Les services restent liés à l'interface loopback, sans exposition publique par défaut.

Le Web J2 utilise un client API typé, des requêtes annulables, Tailwind/PostCSS et
des composants de présentation séparés. Les graphiques ECharts sont chargés côté
navigateur. Aucun fallback synthétique ne remplace une requête en échec. La migration
0002 ajoute une référence de capacité avant de permettre le calcul pondéré.

La structure ML reste hors du service API : audit, baselines et utilitaires temporels
testables ; contrats d'entraînement, SHAP, MLflow et benchmarks réservés à J5.
Les extras ML ne sont ni installés ni verrouillés avant l'audit de compatibilité.

Voir [ADR 0001](decisions/0001-architecture.md) et [contrat d'import](ingestion.md).

## Client mobile J3

Flutter partage les endpoints de lecture FastAPI existants, sans accès direct à
la base. Le domaine conserve types, unités et provenance. Le repository sépare
transport HTTP, préférences locales et validation du cache ; les features et la
présentation consomment ces contrats. Un ChangeNotifier porte les états de
synchronisation et favoris ; les dépendances sont injectables pour les tests.

Les caches et favoris sont isolés par URL serveur, mode et version de format.
Une perte de connexion affiche les données précédentes avec avertissement et
horodatage inchangé. Une incompatibilité de mode masque les anciennes données.
Les séries graphiques restent distinctes par source et catégorie ; les nulls
interrompent les lignes. L’écran géographique expose uniquement la disponibilité
des coordonnées sourcées ; la carte interactive reste au J4.

L’aperçu navigateur Flutter utilise un serveur local de fichiers et un proxy GET
sur le port 3100, sans changement du CORS ni des services du Web Next.js. Voir
[le guide mobile](../apps/mobile/README.md) et [le rapport J3](jalon-3.md).
