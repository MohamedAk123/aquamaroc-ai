# Interface issue de la maquette AquaMaroc AI

Le dashboard du jalon 2 reprend la composition de l’image fournie : navigation
latérale bleue, recherche, quatre indicateurs, carte et historique côte à côte,
puis situation des barrages, qualité des imports et accès aux analyses. La mise
en page s’adapte aux écrans mobiles, avec un menu repliable.

Les composants `reference-dashboard.tsx` et `shell.tsx` consomment les données API
existantes. `reference.css` porte les styles de cette présentation ; le graphique
réutilise ECharts et les exports existants. Recherche, filtres, période, choix de
mesure, agrandissement de carte et navigation sont fonctionnels.

## Données et limites

- La bannière DEMO et la provenance sont conservées. Les chiffres illustratifs
  de la maquette ne sont pas utilisés comme mesures.
- Les indicateurs indisponibles restent explicitement indisponibles, notamment
  le taux pondéré en l’absence de capacités vérifiées.
- Le fond OpenStreetMap est une iframe publique avec attribution, dépendante du
  réseau. Il sert au repérage : aucun marqueur ou contour de bassin inventé
  n’est ajouté. La couche cartographique détaillée reste hors du jalon 2.
- La qualité indique les contrôles d’import, sans certifier la fiabilité
  hydrologique. Aucun compte administrateur fictif n’est affiché.
- Les prévisions restent désactivées ; les liens des cartes IA conduisent aux
  sources, aux contrôles de qualité et aux analyses historiques disponibles.

## Validation locale du 17 novembre 2026

Après reconstruction de l’image Docker Web :

| Contrôle | Résultat |
|---|---|
| Playwright contre Web et API Docker | 18 tests réussis |
| Export CSV | 1 test unitaire réussi |
| ESLint et TypeScript | Réussis |
| Build Next.js dans Docker | Réussi |
| Axe sur dashboard desktop et mobile | Aucune violation détectée |
| Largeur mobile 360 px | Aucun débordement global |

Les captures ont été inspectées : [ordinateur](screenshots/interface-reference-desktop.png)
et [mobile](screenshots/interface-reference-mobile.png). L’audit automatisé
d’accessibilité ne remplace pas une recette humaine complète avec lecteur d’écran.
Le code Python n’a pas été modifié par cette refonte.

L’interface reste accessible sur http://127.0.0.1:3000/ ; les services locaux
DB, API et Web sont laissés démarrés. Aucun jalon suivant ni entraînement avancé
n’a été lancé.
