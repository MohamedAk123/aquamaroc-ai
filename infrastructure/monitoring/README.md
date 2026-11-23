# Observabilité technique

Le profil `monitoring` de la composition de production lance Prometheus et
Grafana. Prometheus collecte l’endpoint interne `/metrics` de l’API. Les
étiquettes sont limitées aux modèles de routes et aux codes HTTP. La
rétention des séries est de quinze jours.

Grafana est accessible uniquement via son port local (3300 par défaut).
Sur un VPS, utiliser un tunnel SSH vers ce port pour accéder au tableau
technique. Les panneaux affichent la disponibilité, le débit et les erreurs
5xx, les latences p50/p95 et la mémoire résidente du processus API.
Les deux règles sont visibles dans Prometheus. La notification externe
nécessite une destination Alertmanager configurée par l’exploitant.
Voir [le guide de déploiement](../../docs/jalon-6.md).
