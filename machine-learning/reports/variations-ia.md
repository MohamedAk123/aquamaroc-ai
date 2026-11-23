# Variations inhabituelles des réserves

AquaMaroc analyse les relevés passés avec Isolation Forest. Le modèle a été
ajusté séparément pour chaque barrage et source sur août et septembre 2026,
puis appliqué aux observations d’octobre. L’étude exploite les 460 relevés du
Tensift provenant des trois classeurs audités. Les différences de réserve sont
calculées à 1 et 7 jours, uniquement si les huit dates consécutives sont présentes.
[Source officielle](https://data.gov.ma/data/fr/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift)

Les cinq modèles utilisent 128 arbres et la graine 42. Le seuil de tri est
le 5e percentile empirique arrondi à l’indice inférieur des scores sur la
période de référence, sans recalibrage sur octobre. Les scores les plus bas
indiquent les variations les plus atypiques par rapport à cette référence.
[Documentation Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)

Les 270 exemples de référence et les 155 observations analysées ont produit
24 signalements à examiner. La proportion affichée n’est pas une mesure de
précision ou de fréquence réelle des anomalies. Le jeu n’a pas d’étiquettes
d’incidents. Un signalement décrit un écart inhabituel et appelle une
vérification des relevés et de leur contexte. Il ne déclenche aucune alerte.

Depuis la racine avec Python 3.12 et la base officielle configurée, installer
les dépendances de l’étude dans un environnement hors ligne de l’API, puis
générer le résultat :

```powershell
uv pip install -r machine-learning/requirements-variations.lock
python -m scripts.study_variations
```

Le générateur contrôle les trois empreintes du rapport d’audit et le nombre
de mesures. Il écrit `services/api/app/resources/variation_review.json`.
L’API sert uniquement ce JSON dérivé. Elle n’exécute aucun modèle et
ne charge aucun fichier de modèle. L’empreinte de l’instantané doit correspondre
à la base officielle active. Si le lot change ou si le mode est DEMO, le
résultat devient indisponible. Les fiches des barrages et les données
sources restent accessibles dans l’application.

La page Web est `/analyses-ia`. Sur l’accueil Flutter, ouvrir **Analyse IA**.
Les prévisions J+7, J+30 et la variante mensuelle restent soumises à leur
propre audit. CatBoost, XGBoost et LightGBM restent les candidats de prévision.
