# AquaMaroc AI — Flutter (jalon 3)

Client de lecture de l’API : accueil, recherche/filtre de bassin, détail avec
historique et provenance, favoris locaux, disponibilité des coordonnées, sources
et méthodologie. Aucun import ni entraînement ML n’est ajouté.

## Installation et tests

Validés localement : Flutter **3.50.0**, Dart **3.14.0**, Material UI **1.11.1**,
HTTP **1.6.0**, shared_preferences **2.5.6**. `.flutter-version` indique le SDK
et `pubspec.lock` verrouille les dépendances. Material indépendant suit
[la migration officielle Flutter 3.50](https://docs.flutter.dev/release/breaking-changes/material-ui-and-cupertino-ui).

Le SDK de cette session est local, sans modification permanente du PATH. Depuis
la racine, uniquement si `.cache/flutter` n’existe pas :

```powershell
git clone --config core.longpaths=true --depth 1 --branch 3.50.0 https://github.com/flutter/flutter.git .cache/flutter
```

Puis, depuis `apps/mobile` :

```powershell
$env:PUB_CACHE=Join-Path (Resolve-Path '../..') '.cache/pub'
$flutter=Join-Path (Resolve-Path '../..') '.cache/flutter/bin/flutter.bat'
$dart=Join-Path (Resolve-Path '../..') '.cache/flutter/bin/dart.bat'
& $flutter --version
& $flutter pub get --enforce-lockfile
& $flutter analyze
& $dart format --output=none --set-exit-if-changed lib test
& $flutter test
& $flutter test --dart-define=LIVE_API_URL=http://127.0.0.1:8000
```

Le dernier test lit uniquement le serveur **DEMO** existant. Sans `LIVE_API_URL`,
il est explicitement ignoré. Sur un autre poste, utiliser directement `flutter`
et `dart` depuis le PATH. Le clonage du tag stable explique le canal `[user-branch]`
dans `flutter doctor` ; la révision correspond au manifeste officiel 3.50.0.

## Aperçu navigateur

Les services Docker du dépôt fournissent l’API sur `127.0.0.1:8000`. Après
[l’import officiel du Tensift](../../docs/ingestion.md#import-officiel-du-tensift),
utiliser `APP_MODE=official` côté Flutter et côté serveur.
Le client Flutter est accessible sur **http://127.0.0.1:3100/** ; le dashboard
Next.js reste sur le port 3000. Depuis `apps/mobile` :

```powershell
& $flutter build web --release --no-web-resources-cdn --dart-define=APP_MODE=official --dart-define=API_URL=http://127.0.0.1:3100
node tool/preview.mjs
```

Le serveur d’aperçu, lié à `127.0.0.1`, sert les fichiers compilés et relaie
uniquement des lectures `/api/v1/` vers l’API locale, sans élargir son CORS.
Depuis **Accueil → Prévisions IA**, le client lit le scénario synthétique
via `GET /api/v1/demo/forecast`. La composition locale monte le rapport
hydrologique en lecture seule dans FastAPI. L’écran distingue les taux par
barrage fictif, les prévisions météo Open-Meteo et les hypothèses de la
simulation. Le signalement d’indisponibilité des prévisions officielles reste
visible. Sur un autre serveur, définir `DEMO_FORECAST_PATH` côté FastAPI pour
activer la lecture du rapport expérimental. [Générer le rapport](../../machine-learning/README.md#scénario-hydrologique-expérimental-j7)
Il ne sert pas au déploiement. Les ressources du moteur sont incluses dans le build.
Le cache hors connexion concerne les données ; l’aperçu Web exige que son serveur
reste disponible pour charger l’application elle-même.

Recette Chromium optionnelle, avec Playwright installé dans `apps/web` :

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=Join-Path (Resolve-Path '../web') '.cache/playwright'
node tool/check-preview.mjs
```

## Android et iOS

Les projets natifs sont générés. Pour Android, compléter les outils requis par
`flutter doctor -v` et connecter un appareil/émulateur. Pour joindre l’API locale
sur Android USB sans exposer le backend sur le réseau :

```powershell
adb reverse tcp:8000 tcp:8000
flutter run -d DEVICE_ID --dart-define=APP_MODE=official --dart-define=API_URL=http://127.0.0.1:8000
```

Remplacer `DEVICE_ID` par la valeur de `flutter devices`. Si nécessaire, `adb`
est dans `platform-tools` du SDK Android. L’exception HTTP est limitée au manifeste
Android **debug** ; une distribution exige une API HTTPS. La permission Internet
est déclarée dans le manifeste principal. Aucun APK de production signé n’est préparé.

iOS exige macOS/Xcode et une API accessible depuis l’appareil ; il n’est pas
compilé sous Windows. Aucune exception ATS générale n’est ajoutée.

`APP_MODE` accepte `demo` ou `official` et doit correspondre au serveur. Un mode
officiel ne transforme pas un serveur DEMO en source officielle. `API_URL` est
la base HTTP(S) sans `/api/v1`, identifiants, paramètres ni fragment. Ces variables
sont injectées à la compilation et ne doivent contenir aucun secret.

## Architecture et cache

- `lib/domain` : modèles typés, unités, provenance et séries chronologiques.
- `lib/data` : HTTP, timeout de 15 s, pagination, repository et stockage local.
- `lib/features` : accueil, liste/détail, disponibilité géographique et sources.
- `lib/presentation` : synchronisation, thème et composants communs.

Le catalogue est enregistré après validation de la synthèse, des bassins et des
sources. Les historiques sont mis en cache séparément. Les clés incluent serveur,
mode et version du format ; les favoris suivent la même séparation, sans compte.

Au démarrage, le cache valide peut être affiché pendant l’actualisation. Un échec
réseau conserve son horodatage et affiche « Cache local ». Il n’y a ni expiration
silencieuse ni actualisation en arrière-plan : bouton ou geste de rafraîchissement.
Un cache invalide est ignoré ; une incompatibilité de mode/contrat masque les
données précédentes. Une erreur de stockage est visible, et aucun favori n’est
annoncé enregistré avant écriture réussie.

Le graphique suit les écarts de dates, sépare sources et catégories de provenance,
et interrompt les lignes aux valeurs nulles. Les relevés textuels offrent une
alternative accessible avec dates de mesure/publication/import, source et ingestion.
L’onglet **Carte** affiche un fond OpenStreetMap centré sur le Tensift, même
si aucun barrage ne possède de coordonnées vérifiées. Les déplacements,
le zoom et le recentrage fonctionnent sur le fond. Seules les coordonnées
sourcées donnent un marqueur et la liste des barrages localisés donne
accès à leurs fiches. Le fond nécessite une connexion Internet. L’attribution
et le lien de licence restent visibles sur la carte. [Licence OpenStreetMap](https://www.openstreetmap.org/copyright)

## Validation et limites

Tests : parsing, pagination de 501 éléments, timeouts, erreurs, provenance,
séparation et persistance du cache/favoris, reprise et états d’écran. Les widgets
sont contrôlés à 360 px, avec texte agrandi, et avec les contrôles Flutter de
contraste, libellés et cibles tactiles. Voir [le rapport J3](../../docs/jalon-3.md)
pour les résultats réels et les limites de compilation native.

Les historiques complets résident en mémoire et dans les préférences : mesurer
avant une montée en volume, puis envisager SQLite et une rétention configurée.
Ce cache n’est ni une archive officielle ni un stockage de secrets. La CI mobile
est ajoutée mais son exécution distante n’est pas revendiquée. Notifications,
entraînements avancés et jalons 4 à 6 restent hors périmètre.
