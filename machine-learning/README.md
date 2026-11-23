# Jalon 5 — Audit des prévisions

L’audit des trois imports officiels du Tensift est disponible en
[Markdown](reports/data_readiness.md) et [JSON](reports/data_readiness.json).
Le [protocole de prévision mensuelle](reports/previsions-mensuelles.md) documente
la variante adaptée aux bulletins datés et les limites des trois éditions actuelles.

La [revue rétrospective des variations](reports/variations-ia.md) constitue une
fonction IA distincte. Isolation Forest a repéré 24 variations à examiner parmi
155 relevés d’octobre, après ajustement sur août et septembre.
Les deux horizons sont classés `insufficient_history`. Les effectifs du rapport
décrivent les couples d’observations, sans métrique de modèle.

Depuis la racine, avec `DATABASE_URL` pointant vers la base officielle, reproduire
le rapport avec le Python du projet.

```powershell
python -m scripts.audit_data --kind OFFICIAL --validation-start 2026-09-20 --test-start 2026-10-13 --output machine-learning/reports
```

Les bornes sont communes aux barrages. La mesure cible doit exister à
`t + h`, dans la même série, et rester avant la frontière suivante. Les bornes
choisies donnent à J+7 une portion de train avec les quatre lags et deux périodes
ultérieures distinctes. Les compteurs calendaires mesurent la faisabilité du
découpage. Pour mesurer la faisabilité de l’évaluation, le rapport exige en
plus que la réserve d’origine soit publiée le jour de l’origine (date UTC),
et que les cibles pré-test aient été publiées avant la frontière suivante.
La date d’import ne remplace pas la date de publication. Aucun fichier fourni
ne permet de vérifier la disponibilité à J+7. À J+30, trois blocs non vides
exigent déjà 93 jours calendaires, avant prise en compte des lags et de la
fraîcheur des données. Ce minimum découle du protocole et ne garantit aucune
performance.

La [fiche de la source](https://data.gov.ma/data/fr/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift)
liste les trois fichiers mensuels. Par exemple, la [ressource d’octobre](https://data.gov.ma/data/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift/resource/aae7d44c-6170-45cf-a21a-9a6fde498c3a?inner_span=True)
indique une création le 4 novembre. Cela ne renseigne pas la date de disponibilité
de chaque mesure ou de ses révisions. Les 92 jours ne permettent pas non plus
d’évaluer la saisonnalité annuelle. Les contrôles descriptifs du jalon 4
couvrent déjà les doublons, les rejets et la couverture des séries.

## Benchmarks FLAML et H2O AutoML

Installer les dépendances API du projet dans un environnement Python 3.12
isolé, puis les extras des moteurs souhaités. Le verrou
`requirements-automl.lock` correspond à l’environnement Python 3.12
vérifié sous Windows. Sous Windows, H2O démarre dans un conteneur temporaire
Linux amd64 avec Java 17. Docker Desktop doit fonctionner en mode conteneurs
Linux. Le conteneur réutilise en lecture seule le JAR de la dépendance Python
et expose son API sur un port dynamique limité à `127.0.0.1`.
Sur les autres systèmes, H2O utilise la JVM locale. Chaque exécution
arrête son serveur à la fin.

```powershell
python -m pip install -r requirements.lock
python -m pip install -c machine-learning/requirements-automl.lock -e "./machine-learning[automl-flaml,automl-h2o]"
python -m aquamaroc_ml.train --check-h2o
python -m aquamaroc_ml.train --engine flaml --horizon 7
python -m aquamaroc_ml.train --engine h2o --horizon 30
```

Le diagnostic `--check-h2o` vérifie le moteur XGBoost natif sans lire les
relevés ni ajuster de modèle. Les deux commandes de benchmark renvoient
actuellement `insufficient_history`. Elles consultent
`reports/data_readiness.json` avant tout accès PostgreSQL ou
chargement d’un moteur. `--audit` désigne un autre rapport officiel revu.
L’audit automatisé calcule la couverture et ne délivre aucune approbation
automatique. Une revue doit attester `ready_for_experiments` pour le rapport
et l’horizon concerné, avec trois blocs dont la disponibilité est vérifiée.
La configuration de l’horizon doit autoriser le benchmark et fixer le budget.
Le mode `APP_MODE=official`, l’empreinte de l’instantané et les mêmes
frontières calendaires sont exigés à l’exécution. Les deux configurations
livrées gardent `advanced_training_enabled: false`.

Les deux moteurs reçoivent les mêmes couples barrage/date, classés par
date puis barrage. Les variables numériques communes sont la réserve
disponible à l’émission, les quatre lags exacts dont la publication est
attestée à cette date et le mois. Une cible doit exister à J+7 ou J+30 et
être publiée avant la prochaine frontière. Le bloc final ne quitte pas
la garde d’éligibilité et n’est jamais transmis aux moteurs.

- FLAML compare CatBoost, XGBoost et LightGBM avec un holdout externe et un
  budget borné. Le contexte CatBoost fixe `has_time=True` et désactive
  l’early stopping interne du wrapper pour conserver le train entier en
  ordre chronologique. La sélection FLAML repose sur le bloc externe.
- H2O utilise `nfolds=0`, exclut DRF et StackedEnsemble, et réutilise
  le même bloc de validation pour le classement. Le benchmark exige
  XGBoost natif avant de transmettre les blocs au serveur H2O. Le rapport
  indique quel environnement H2O a exécuté le benchmark.

`--engine all` exécute les deux moteurs et `--output fichier.json`
écrit le rapport. Chaque moteur expose sa version, le candidat classé
premier et ses métriques recalculées sur la validation en Mm³. Le rapport
inclut la dernière réserve connue comme baseline, les dates de coupure,
l’empreinte du jeu officiel et les coûts d’exécution. Il reste marqué
`validation_only`. Le test final, l’approbation et la mise en service
relèvent d’étapes distinctes. Les tests automatisés de l’intégration
simulent les moteurs et n’ajustent aucun modèle.

## Scénario hydrologique expérimental J+7

Le scénario **DEMO** simule trois barrages fictifs de capacités différentes,
alimentés par des bassins de montagne fictifs. Il reproduit la saison humide, l’accumulation
de neige en altitude, la fonte par température positive, des apports
retardés et des pertes quotidiennes. Le générateur part d’hypothèses
explicites et ne calibre aucun barrage réel. Les hivers et printemps
du Haut Atlas motivent sa structure. [Étude sur la neige dans le Haut Atlas](https://pmc.ncbi.nlm.nih.gov/articles/PMC12277445/)

Installer l’extra dans l’environnement dédié et exécuter depuis la racine.

```powershell
python -m pip install -c machine-learning/requirements-automl.lock -e "./machine-learning[hydrology-demo]"
python -m aquamaroc_ml.hydrology_demo --filling-pct 50 --snow-water-mm 20
python -m mlflow ui --backend-store-uri sqlite:///./.cache/hydrology-demo/mlflow.db --host 127.0.0.1 --port 5055
```

La commande récupère la prévision des sept jours suivant l’émission
au point météo de l’observatoire d’Oukaïmeden, avec dates et unités
vérifiées. Ce point est un exemple de montagne et ne représente pas
un bassin versant réel à lui seul. Les valeurs prévues par Open-Meteo
sont archivées avec leur empreinte. Le même forçage météo est utilisé
pour les trois scénarios. Les taux de remplissage initiaux et le stock
de neige sont des hypothèses ajustables via `--filling-pct` et
`--snow-water-mm` (équivalent eau). La conversion DEMO de neige
fraîche est de 1 mm d’eau par cm de neige, hypothèse de densité
100 kg/m³. [Coordonnées de l’observatoire](https://www.trappist.uliege.be/cms/c_5285930/en/site) · [Documentation Open-Meteo](https://open-meteo.com/en/docs)

H2O AutoML apprend directement le taux à J+7 en pourcentage. Les
frontières chronologiques sont communes aux trois barrages et les
cibles qui les franchissent sont exclues. La météo synthétique future utilisée
comme entrée comporte un bruit croissant avec l’avance. Le MAE sur
validation choisit entre le leader AutoML et le dernier taux connu.
Le bloc final sert à évaluer ce choix et la référence en points de
pourcentage. La réserve prévue est calculée à partir du taux et de
la capacité fictive de chaque barrage.
MLflow enregistre les paramètres, les métriques sur le synthétique,
le classement H2O, le modèle binaire H2O, les CSV DEMO et la météo brute.
Le binaire se recharge avec la même version H2O.
La sortie `.cache/hydrology-demo/forecast_demo.json` est datée et
étiquetée `experimental_synthetic_training`. Le tableau de bord local
la lit en lecture seule via **Analyses IA → Voir les prévisions de
remplissage DEMO à J+7**. Avec Next.js lancé hors Docker, définir `DEMO_FORECAST_PATH` sur le
chemin absolu du rapport pour afficher le résultat. Aucun de ces scores
n’établit la qualité d’une prévision sur un barrage officiel. Les
horizons officiels conservent leur garde d’éligibilité.

Pour recalculer les trois taux avec une nouvelle prévision Open-Meteo et
le modèle H2O déjà entraîné, exécuter la commande suivante depuis la racine.
Elle crée un run d’inférence lié au run d’entraînement dans MLflow et
publie le résultat lu par le Web et Flutter après succès.

```powershell
python -m aquamaroc_ml.hydrology_demo --predict-only --filling-pct 50 --snow-water-mm 20
```
