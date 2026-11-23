# API — jalons 1 et 2

OpenAPI : `http://127.0.0.1:8000/docs` ; schéma JSON : `/openapi.json`.

| GET | Comportement |
|---|---|
| `/health` | 200 sans dépendance DB, mode actif |
| `/ready` | 200 si connexion et migration présentes, sinon 503 |
| `/api/v1/basins` | Bassins ayant des observations visibles dans le mode |
| `/api/v1/reservoirs` | Barrages visibles ; `basin_id`, `search`, `limit`, `offset` |
| `/api/v1/reservoirs/{id}/measurements` | Historique croissant ; `start_date`, `end_date`, `data_kind`, pagination |
| `/api/v1/data/freshness` | Dernières dates et statut d'import, avec source et licence |
| `/api/v1/overview` | Derniers relevés filtrés et agrégats uniquement comparables ; filtres bassin/recherche/dates/source/provenance |
| `/api/v1/reservoirs/{id}` | Détail du barrage visible, capacité et référence de capacité |
| `/api/v1/sources` | Inventaire paginé, statuts, licences, dates et URL connues |
| `/api/v1/data/quality` | Statistiques de qualité globales du mode actif, avec dénominateurs |

Les listes renvoient `items,total,limit,offset,mode,is_real_time` (toujours false).
Les dates de mesure utilisent ISO 8601 ; les timestamps d'ingestion sont UTC ; les
décimaux sont des chaînes JSON pour préserver leur précision. Les valeurs inconnues
sont null, sans zéro inventé. Les mesures exposent source, run, qualité et provenance.
Les erreurs utilisent `{"error":{"code":"...","message":"..."}}` et éventuellement
une liste `details`. UUID, pagination, formats et ordre des dates sont validés.

Le mode `demo` exclut les observations `OFFICIAL`/`UNVERIFIED` ; `official` exclut
`DEMO`. Le statut `UNVERIFIED` reste explicite et filtrable, sans assimilation aux
mesures officielles. L'inventaire sans observation n'est pas exposé au J1.

Exemples après initialisation locale DEMO (PowerShell, `curl.exe`) :

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8000/ready
curl.exe "http://127.0.0.1:8000/api/v1/reservoirs?search=Alpha&limit=10"
curl.exe "http://127.0.0.1:8000/api/v1/reservoirs/00000000-0000-0000-0000-000000000101/measurements?start_date=2026-01-01&end_date=2026-01-02"
curl.exe http://127.0.0.1:8000/api/v1/data/freshness
```

Aucune route d'import, d'administration ou de prédiction. L'historique accepte
aussi `source_id`. La synthèse indique la raison de chaque agrégat indisponible et
ne choisit pas arbitrairement une source lorsque plusieurs relevés concurrents existent.
Les autres endpoints de la spécification attendent les jalons suivants ; une route
absente renvoie 404. Voir [les contrats J2](jalon-2.md) pour les règles de calcul.
