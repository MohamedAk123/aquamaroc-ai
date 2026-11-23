# Prévision conditionnée par les bulletins mensuels du Tensift

La variante proposée estime la réserve de fin du mois suivant, par barrage,
en Mm³. La prévision est datée du jour où le bulletin utilisé est disponible.
Elle peut être comparée à la valeur observée en fin de mois lorsque le bulletin
suivant paraît. Cette cible mensuelle est distincte des horizons fixes J+7 et J+30.

| Mois des relevés | Métadonnée de la ressource actuellement référencée |
|---|---|
| Août 2026 | Téléversement documenté le 6 octobre. [Journal du portail](https://www.data.gov.ma/data/dataset/changes/6e5305be-b166-4012-94ac-0e0d9b2dc426) |
| Septembre 2026 | Création de la ressource et dernière mise à jour des données le 2 octobre. [Fiche de la ressource](https://data.gov.ma/data/fr/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift-aout-2026/resource/57580e59-8b9c-4bde-bf9f-2a25107bbf6e?view_id=27240bf2-7196-4215-aaca-02e912307930) |
| Octobre 2026 | Création de la ressource et dernière mise à jour des données le 4 novembre. [Fiche de la ressource](https://data.gov.ma/data/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift/resource/aae7d44c-6170-45cf-a21a-9a6fde498c3a?inner_span=True) |

Ces métadonnées concernent les ressources du portail. Elles ne sont pas
recopiées dans le champ de publication de chacun des 460 relevés. Notamment,
le téléversement de la ressource d’août référencée aujourd’hui est postérieur
à celui de septembre. Une ancienne version d’août peut avoir été accessible
plus tôt. Sa date et ses octets doivent être vérifiés avant de l’utiliser
pour reconstituer une prévision historique.

### Protocole lorsque les archives seront disponibles

1. Archiver chaque bulletin et chaque révision avec le mois couvert, l’URL
   d’origine, l’empreinte du fichier et la date à partir de laquelle cette
   version est attestée accessible. Pour les bulletins futurs, enregistrer
   aussi la première réception observée par le projet.
2. Pour chaque date d’émission, reconstruire l’information disponible ce
   jour-là. Prendre la réserve mesurée le dernier jour du mois suivant comme
   cible. Exclure les cas où cette date est déjà passée au moment de
   l’émission, où le relevé de fin de mois manque ou où la version exacte
   n’est pas reconstituable. Fixer la version de référence utilisée pour
   évaluer les cibles révisées.
3. Séparer entraînement, validation et test final sur des mois communs à
   tous les barrages. À chaque frontière, exclure les exemples dont le bulletin
   cible n’était pas encore disponible. Comparer CatBoost, XGBoost et LightGBM
   à la dernière réserve connue sur les mêmes cas et sélectionner sur la
   validation uniquement.

### Verdict actuel

Août, septembre et octobre fournissent au plus deux transitions calendaires
adjacentes avant les contrôles de disponibilité. Répéter chaque transition
sur cinq barrages n’ajoute aucune période indépendante. Il est impossible
de constituer trois blocs non vides pour une comparaison équitable.
La variante mensuelle reste donc `insufficient_history`. Aucun modèle
n’a été entraîné et le mode officiel de l’application est inchangé.
