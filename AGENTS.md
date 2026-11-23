# AquaMaroc AI

- Référence : `AquaMaroc_AI_Codex_Specification_v2.1.md` (révision CatBoost).
- Périmètre actif autorisé : exploitation et analyse IA rétrospective des relevés officiels, sur demande de l’utilisateur.
- Conditionner l’entraînement avancé à l’éligibilité documentée des données officielles par horizon.
- Ne jamais inventer de mesures officielles, coordonnées, URL de ressources ou scores ML.
- Garder les modes demo/official séparés et préserver la provenance.
- Les imports sont des commandes locales ; aucun endpoint d'administration public.
- Aucune modification silencieuse d'une mesure publiée : journaliser les conflits.
- Exécuter `python -m pytest` et `python -m ruff check .` après une modification Python.
- Les tests PostgreSQL nécessitent une base isolée via `TEST_DATABASE_URL`.
- Ne lancer aucun entraînement avancé avant l'audit des données officielles.
