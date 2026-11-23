# Jalon 3 — client mobile Flutter

## Refonte selon la maquette du 18 novembre 2026

L’accueil reprend le bandeau paysager, les raccourcis et la synthèse. La liste
présente la recherche, les filtres de bassin, les étoiles de favoris et les
barres de remplissage. Le détail propose les onglets Aperçu, Historique et
Prévisions IA. Le dernier indique le statut du service prédictif.

Le paysage embarqué est une illustration générée d’un barrage fictif. Les
vignettes reprennent ce même visuel générique. Les mesures, les dates et la
provenance viennent de l’API. Les taux indisponibles sont signalés.

Le jalon 3 a été ouvert sur demande explicite de l’utilisateur après livraison
du Web J2. `AGENTS.md` reflète ce périmètre. Les jalons 4 à 6 et les entraînements
avancés restent désactivés ; aucun fichier officiel supplémentaire n’a été importé.

## Fonctionnalités implémentées

- Accueil : synthèse API, dates de relevé et synchronisation, bassins et favoris.
- Barrages : recherche locale et filtre de bassin, états vide/chargement/erreur.
- Détail : dernières valeurs, capacité seulement si sourcée, historique filtrable
  par dates/source/provenance, réserves ou remplissage, relevés textuels et traçabilité.
- Favoris persistants, sans compte, isolés par serveur et mode.
- Écran géographique : disponibilité des coordonnées vérifiées, sans points inventés.
- Sources : producteur, licence, URL lorsqu’elle est fournie, dates et méthode.
- Cache local explicitement signalé hors connexion, avec horodatage conservé.

L’API existante reste l’unique accès métier. Aucun endpoint d’administration ni
service prédictif n’est ajouté. La carte interactive reste au J4. Les dates de
mesure, publication, import et synchronisation ne sont pas confondues.

## Structure et dépendances

`apps/mobile/lib/domain`, `data`, `features` et `presentation` séparent contrats,
transport/stockage, écrans et état. Le transport HTTP est injectable pour les tests,
avec timeout de 15 secondes et pagination intégrale. Le cache est versionné,
validé et cloisonné par URL/mode. La persistance utilise SharedPreferencesAsync.

Versions réellement résolues : Flutter 3.50.0, Dart 3.14.0, material_ui 1.11.1,
http 1.6.0, shared_preferences 2.5.6. Le verrouillage est dans `pubspec.lock`.
Le SDK est épinglé au tag stable, révision
`ab2912035e160d9cad6306df307576da6128ebdb`. Il a été installé dans `.cache/flutter`,
sans changement permanent du PATH. La CI ajoute analyse, formatage, tests, build
Flutter Web et APK debug ; son exécution GitHub n’est pas revendiquée.

## Résultats locaux après la refonte

| Contrôle | Résultat |
|---|---|
| Tests de modèles et séries | 5 réussis |
| Tests du client API | 8 réussis |
| Tests repository, cache et favoris | 6 réussis |
| Tests widgets | 9 réussis |
| Lecture de l’API DEMO Docker réelle | 1 réussie, aucune écriture |
| Total avec `LIVE_API_URL` | **29 tests**, dont 1 contre l’API DEMO |
| `flutter analyze` | Aucune anomalie |
| Formatage Dart | Vérifié |
| Build Flutter Web release, moteur embarqué | Réussi |
| Recette Chromium de l’aperçu | API, navigation, détail, favoris persistants après rechargement, cache en coupure API validés |

Les widgets sont testés à 360 × 780, ainsi qu’avec un texte agrandi à 180 %.
Les contrôles Flutter de contraste, cibles tactiles Android et libellés passent
sur l’accueil et la liste. Ils ne remplacent pas une recette TalkBack/VoiceOver.
Les tests HTTP couvrent notamment une pagination de 501 éléments, les timeouts,
les erreurs, les modes incompatibles et les provenances incohérentes. Les tests
de stockage vérifient aussi qu’un échec d’écriture de favori n’annonce pas un succès.

Les captures Chromium à 390 × 844 ont été inspectées :
[accueil](screenshots/j3-flutter-home.png),
[liste](screenshots/j3-flutter-list.png),
[favoris](screenshots/j3-flutter-favorites.png),
[détail](screenshots/j3-flutter-detail.png),
[hors connexion](screenshots/j3-flutter-offline.png).
Les valeurs affichées proviennent du serveur DEMO et ne sont pas des mesures officielles.

Le code Python et le client Next.js ne sont pas modifiés par ce jalon. Les suites
de ces composants n’ont pas été relancées pour cette implémentation Flutter.

## Lancement et validation native

Les commandes reproductibles et paramètres sont dans
[le guide mobile](../apps/mobile/README.md). L’aperçu est laissé démarré sur
http://127.0.0.1:3100/ ; Next.js reste sur http://127.0.0.1:3000/ et l’API sur le
port 8000. Le proxy d’aperçu n’élargit pas le CORS du backend.

Les projets Android et iOS sont générés. La compilation Android debug a produit
`apps/mobile/build/app/outputs/flutter-apk/app-debug.apk`. La recette sur un
téléphone reste à effectuer. La compilation iOS nécessite macOS et Xcode.

## Limites

L’historique complet est chargé après pagination, puis conservé en mémoire et dans
les préférences. Mesurer avant une montée en volume ; une base locale avec rétention
pourra remplacer ce cache. La synchronisation est manuelle ou au démarrage, sans
service de fond. Les notifications, signatures de distribution et déploiement ne
sont pas activés. Les icônes de lanceur natives générées restent à personnaliser
avant distribution.

La carte affiche seulement la disponibilité et les coordonnées sourcées. Aucun
fond ou marqueur hydrologique n’est inventé. Aucun entraînement avancé, prévision
ou score ML n’a été produit. L’audit des données officielles reste nécessaire.
