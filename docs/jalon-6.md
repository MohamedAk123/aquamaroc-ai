# Jalon 6 — Déploiement et exploitation

Le déploiement utilise le mode officiel. La passerelle Nginx sert le Web et
l’API de lecture sur la même origine, sans port hôte pour PostgreSQL, FastAPI
ou Prometheus. Elle réserve un budget global initial de 30 requêtes par seconde
et une rafale de 60 requêtes API. Le dépassement renvoie HTTP 429. Ce budget est
partagé entre les visiteurs. Ajuster après mesure sur l’infrastructure retenue.
La documentation interactive, la readiness interne et les métriques ne sont
pas routées par la passerelle. Les imports s’exécutent en CLI locale.

## Préparer et lancer

Depuis la racine, copier `.env.prod.example` vers un nouveau `.env.prod`.
Renseigner un mot de passe PostgreSQL aléatoire de 32 caractères ou plus en
hexadécimal, et un mot de passe Grafana indépendant d’au moins 16 caractères
si le profil monitoring est utilisé. Restreindre les permissions du fichier.
Le projet Compose `aquamaroc-prod` dispose de volumes séparés du développement.

```sh
docker compose -f docker-compose.prod.yml --env-file .env.prod config --quiet
docker compose -f docker-compose.prod.yml --env-file .env.prod --profile monitoring up -d --build --wait
curl --fail http://127.0.0.1:8080/health
```

Pour une première installation vide, placer les trois classeurs officiels
audités dans `data/raw/tensift/`, puis exécuter
`docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T api python -m pipelines.ingestion.import_tensift`.
Contrôler ensuite `/api/v1/data/quality` sur la passerelle. Cette commande est
inutile si l’installation a été restaurée depuis une sauvegarde complète.

Pour publier sur Internet, installer Caddy sur l’hôte, faire pointer le DNS
vers cet hôte et autoriser uniquement les ports publics 80/443 au pare-feu.
Utiliser `infrastructure/deploy/Caddyfile` comme configuration du service Caddy.
Définir `PUBLIC_HOST` avec le domaine réel et laisser Nginx sur
`127.0.0.1:8080`. Si le port local diffère, adapter `GATEWAY_UPSTREAM`.
Conserver les données ACME de Caddy entre redémarrages. Vérifier ensuite le
certificat public, la redirection HTTP, `/health` et les relevés visibles.
[Configuration HTTPS de Caddy](https://caddyserver.com/docs/quick-starts/reverse-proxy)

La compilation Next.js utilise une origine d’API relative. Les clients Flutter
sur appareil doivent être reconstruits avec `API_URL` égal à l’origine HTTPS
publique et `APP_MODE=official`. Les étapes de signature et distribution
native dépendent des comptes et certificats du propriétaire.

## Livraison et retour arrière

La CI contrôle Python/PostGIS, Next.js, Flutter et la configuration de
production. Le workflow manuel **Livraison d’images** réexécute ces contrôles
sur la branche principale, puis publie les images API et Web dans GHCR au
tag du commit. Le résumé fournit les références par digest.

Sur l’hôte, renseigner `API_IMAGE` et `WEB_IMAGE` dans `.env.prod` avec les
digests, puis exécuter `docker compose -f docker-compose.prod.yml --env-file .env.prod pull api migrate web`
et `docker compose -f docker-compose.prod.yml --env-file .env.prod --profile monitoring up -d --no-build --wait`.
Conserver les digests et une sauvegarde cohérente de la version précédente.
Si le schéma est compatible, revenir aux anciens digests et relancer. Si une
migration bloque ce retour, restaurer le couple base/archives dans un projet
isolé et remettre l’ancienne version en service après vérification.

## Sauvegarde et restauration

Exécuter avec Python 3.12+, depuis la racine, en dehors d’une fenêtre d’import.
Les fichiers produits incluent un dump PostgreSQL, une archive des classeurs
originaux et un manifeste SHA-256. Si un import est concurrent, la commande
peut refuser de finaliser le manifeste. Une sauvegarde sans manifeste n’est
pas utilisable. Les chemins `backups/` sont exclus de Git et du build Docker.

```sh
python -m scripts.backup_db backup backups/avant-livraison
python -m scripts.backup_db rehearse backups/avant-livraison
```

Planifier la commande de sauvegarde sur l’hôte après chaque import ou au
minimum quotidiennement. Copier les sauvegardes validées vers un stockage
hors hôte, chiffré et à accès restreint. Transporter le manifeste par un canal
de confiance. Le manifeste contrôle l’intégrité, tandis que l’authenticité
dépend de la chaîne de stockage. Définir la rétention avec l’exploitant.

`rehearse` restaure le dump dans une base temporaire et vérifie les relevés
et les liens vers les archives. Pour une récupération complète, créer un
projet distinct avec un fichier d’environnement propre, un port de passerelle
libre et un mot de passe adapté. Démarrer seulement `db` en premier :

```sh
docker compose -p aquamaroc-recovery -f docker-compose.prod.yml --env-file .env.prod.recovery up -d --wait db
python -m scripts.backup_db recover backups/avant-livraison --project aquamaroc-recovery --env-file .env.prod.recovery --database aquamaroc_recovered
```

`recover` exige un nom de base jamais utilisé et un volume d’archives vide.
Après succès, fixer `POSTGRES_DB=aquamaroc_recovered` dans le fichier de
récupération et lancer la composition sur ce même projet. Vérifier la qualité
et les mesures via la passerelle avant de basculer l’accès vers cette instance.
N’utiliser qu’une sauvegarde issue de l’installation de confiance elle-même.

## Recette locale

Le projet de répétition `aquamaroc-j6` a été démarré sur
http://127.0.0.1:8086/. Les trois classeurs officiels ont produit 460 relevés.
Le test Chromium a chargé le tableau de bord sur la même origine que l’API.
Les routes internes ont renvoyé 404, les écritures 403 et la rafale de lecture
a déclenché la limite 429. Le chemin Caddy a été testé sur `localhost`
avec une autorité locale, un certificat vérifié et l’en-tête HSTS.

Prometheus a confirmé la cible API disponible et ses deux règles valides.
Grafana a chargé les quatre panneaux. La sauvegarde a été restaurée en base
temporaire, puis dans un projet isolé avec ses trois archives. Les 460 relevés
restaurés correspondent à la sauvegarde et aucun relevé DEMO ne figure dans
cette installation.

Il reste à raccorder un domaine et un hôte réels. La CI distante, GHCR,
le certificat public, l’ordonnancement des sauvegardes et leur stockage hors
hôte dépendent de l’environnement de déploiement.
