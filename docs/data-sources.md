# Sources et audit à réaliser

La [fiche Tensift](https://www.data.gov.ma/data/dataset/situation-journaliere-des-barrages-dans-le-bassin-du-tensift)
identifie l’Agence du bassin hydraulique de Tensift comme producteur et indique
la licence ODbL. Les trois classeurs XLSX proposés (août, septembre et octobre 2026)
ont été téléchargés dans `data/raw/tensift/` depuis les liens de la fiche.
Le manifeste local `data/raw/tensift/provenance.json` conserve les URLs, tailles,
empreintes SHA-256 et l’horodatage. Les feuilles couvrent le 1er août au 31 octobre
2026, avec 92 jours consécutifs et cinq barrages suivis chaque jour. L’inspection
des en-têtes et des tableaux a confirmé les unités Mm³ et %, les capacités
normales et 460 couples réserve/taux complets. Les contrôles météo et
l’éligibilité à un entraînement avancé restent hors de cet audit d’import.

La fixture locale `data/demo/reservoirs_demo.xlsx` est entièrement synthétique.
Ses noms ne correspondent à aucun barrage réel ; les coordonnées et capacités sont
absentes. Elle n'a pas de producteur officiel ni d'URL de ressource officielle.

Pour toute nouvelle édition, vérifier :

- Accès autorisé à la fiche et à ses ressources ; licence, attribution et producteur.
- Feuilles, lignes de titre et total, en-têtes, cellules fusionnées et formules.
- Unités, formats de nombres, dates de mesure et dates de publication.
- Noms et identifiants des barrages, capacités et coordonnées sourcées.
- Fréquence réelle, trous, doublons, nulls, historique, changements de schéma et révisions.
- Disponibilité de données météo archivées et leurs délais de publication.
- Possibilité de fenêtres chronologiques indépendantes J+7/J+30 et représentativité saisonnière.

Déposer le fichier reçu dans `data/raw/` (ignoré par Git), conserver sa provenance,
puis créer un mapping séparé, audité, avant l'import. Tenir à jour
`docs/data-inventory.csv` et le rapport d'éligibilité ML. Aucune communication de ce
projet ne constitue une communication officielle des autorités hydrauliques.
