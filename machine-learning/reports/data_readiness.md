# Audit des données

Statut : `insufficient_history`.

460 observations OFFICIAL · 5 barrages.
Période : 2026-08-01 à 2026-10-31.

460 dates de publication manquantes. Consulter les effectifs par horizon et par bloc avant toute comparaison. Aucune approbation d’entraînement avancé n’est émise par cet audit.

## J+7

- Décision : `insufficient_history`.
- Frontières de validation et test : 2026-09-20 / 2026-10-13.
- Étendue : 92 jours. Minimum calendaire pour trois blocs non vides : 24 jours, avant les lags et les retards de publication.

| Bloc | Couples après purge | Avec les quatre lags | Publications vérifiées |
|---|---:|---:|---:|
| Train | 215 | 65 | 0 |
| Validation | 80 | 80 | 0 |
| Test final | 60 | 60 | 0 |

## J+30

- Décision : `insufficient_history`.
- Frontières de validation et test : 2026-09-20 / 2026-10-13.
- Étendue : 92 jours. Minimum calendaire pour trois blocs non vides : 93 jours, avant les lags et les retards de publication.

| Bloc | Couples après purge | Avec les quatre lags | Publications vérifiées |
|---|---:|---:|---:|
| Train | 100 | 0 | 0 |
| Validation | 0 | 0 | 0 |
| Test final | 0 | 0 | 0 |

Les éditions épinglées du Tensift comportent une ligne d’en-tête supplémentaire en octobre. L’import vérifié préserve les deux unités.

Le JSON détaille les distributions, les variations quotidiennes, les capacités et les empreintes des fichiers. Aucune météo horodatée ne figure dans ce jeu.

Aucun entraînement n'a été exécuté.
