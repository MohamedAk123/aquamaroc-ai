# Import XLSX J1

Le fichier `config/column_mapping.yaml` concerne exclusivement le classeur DEMO.
Il fixe le mode, le nom de feuille, la ligne d'en-tête, les noms des quatre colonnes,
les unités `Mm3` et `%`, et l'association exacte de chaque nom à un UUID existant.
Les en-têtes manquants ou ambigus et les unités inconnues sont refusés. Aucun fichier
officiel ne peut être importé avec ce mapping sans en changer explicitement le mode.

Dates acceptées : cellules Excel de date, `YYYY-MM-DD`, `JJ/MM/AAAA`. Les nombres
acceptent virgule décimale et espaces de milliers ; nombres non finis, formules,
précision au-delà de quatre décimales et valeurs hors bornes sont rejetés.
Au moins une réserve ou un taux est requis. La taille compressée et décompressée
est bornée. Ne pas fournir de documents XLSX non maîtrisés.

Les lignes totalement vides sont ignorées. `rows_read` compte les lignes non vides
après l'en-tête ; `rows_valid` compte les mesures écrites ; `rows_rejected` compte
les lignes refusées. L'invariant est `read = valid + rejected`. Lors d'un rollback,
`valid=0` et toutes les lignes lues sont comptées rejetées ; aucun succès partiel
n'est annoncé. Une erreur de structure sans lignes lues donne zéro aux trois compteurs.

Statuts : `success` (toutes acceptées), `partial` (acceptées et rejetées), `failed`
(aucune acceptée ou erreur du classeur), `pending` (transaction non terminée).
La CLI renvoie respectivement les codes 0, 2 et 1 pour succès, partiel et échec.
Les erreurs de préconditions (chemin, taille, source, mapping) surviennent avant
création d'un journal ; les erreurs de classeur après préconditions sont journalisées.

`--dry-run` lit la base et valide, sans journal, archive ou mesure écrits. Il exige
une base migrée et le référentiel existant. Il ne crée pas le référentiel.

Les octets d'origine sont conservés dans `data/archive/<sha256>.xlsx` ou le volume
Docker correspondant. Le journal conserve nom, hash, chemin, licence et URL connues,
statut de la source et hash du mapping. Le fichier d'origine n'est jamais modifié.
La sauvegarde et la rétention des archives restent à définir avant production.

L'unicité source/hash/mode rend un réimport identique idempotent. Un import déjà
terminé est retourné tel quel ; un mapping changé provoque une erreur explicite.
Les journaux échoués ou `pending` ne sont pas automatiquement réexécutés.
Sur un nouveau fichier, une mesure déjà présente est rejetée comme doublon ou
conflit ; l'original reste intact. Toute révision officielle devra suivre une future
procédure de versionnement approuvée, avec références et audit, avant modification.

En `official`, une source `VERIFIED` donne `OFFICIAL`, sinon `UNVERIFIED`. Une source
`DEMO` est refusée. La création des référentiels officiels reste manuelle et documentée
après vérification des noms, producteurs, licences et unités ; aucun import public.
`published_at` reste null dans ce parseur démonstratif ; son mapping officiel attend
l'audit. `ingested_at` est UTC et distinct de la date d'observation.

## Import officiel du Tensift

Le lecteur `pipelines.ingestion.import_tensift` est dédié aux trois éditions
auditées. Il vérifie les empreintes, les dimensions, les capacités et les jours
de chaque feuille. Il lit les valeurs enregistrées par le producteur (y compris
les résultats de formules mis en cache) et contrôle les taux à 0,01 point près
par rapport à la réserve et à la capacité déclarées. Le taux publié est conservé
avec un arrondi à quatre décimales. Les dates de publication par relevé et les
coordonnées restent inconnues. Le journal conserve l’URL précise et l’onglet,
et l’archive conserve les octets d’origine. Le même fichier peut être réimporté
sans créer de doublons. Une édition corrigée exige un audit de révision.

Depuis la racine, avec PostgreSQL déjà migré et les fichiers en place :

```powershell
$env:APP_MODE='official'
docker --config .docker-local compose --env-file .env.example build api
docker --config .docker-local compose --env-file .env.example run --rm --no-deps api python -m pipelines.ingestion.import_tensift
docker --config .docker-local compose --env-file .env.example up -d api web
```

Le client Flutter doit être compilé avec `--dart-define=APP_MODE=official`.
Le mode DEMO conserve ses propres mesures et reste disponible via la configuration
DEMO. Cette procédure ne lance aucun entraînement.
