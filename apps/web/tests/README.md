# Tests Web J2

`unit/csv.test.ts` vérifie provenance, valeurs nulles et neutralisation des formules.
`e2e/dashboard.spec.ts` couvre les parcours de consultation, recherche, filtres,
détail, export, chargement, erreurs/reprise, navigation, WCAG et largeur 360 px.
Un historique synthétique intercepté de 501 relevés vérifie la pagination complète
avant export ; les autres parcours consultent la véritable API DEMO.

Lancer le build, préparer une base DEMO dédiée et suivre les commandes du
[rapport J2](../../../docs/jalon-2.md). Les traces et captures sont des artefacts locaux
ignorés par Git. Le test d'accessibilité conserve une capture desktop et mobile.
