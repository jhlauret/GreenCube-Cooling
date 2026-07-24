# GreenCube Cooling — module Odoo Community 18

## Périmètre livré dans ce lot

- **Modèles** : `greencube.thermal.specification` (+ `greencube.thermal.facade`), `greencube.cooling.study`
  (avec statuts, révisions, snapshot, verrouillage après validation), `occupancy.profile`, `equipment.load`,
  `ventilation.profile`, `shading`, `climate.scenario`, `solver.version`, `result` (+ `result.component`,
  immuables), `equipment.selection`, `commercial.capacity`, et une extension de `product.template` pour le
  catalogue équipement (réutilisation d'Odoo, pas de nouveau catalogue produit).
- **Sécurité** : 4 groupes (`user`, `technician`, `manager`, `admin`), ACL par modèle, règles multi-société
  (`company_id in company_ids`) et règle "un utilisateur ne voit que ses études".
- **Vues** : liste/formulaire pour les études et les spécifications thermiques, menus.
- **Moteur MERCURE** : portage Python 1:1 de `frontend/src/mercure/engine.ts`, indépendant de l'ORM
  (`services/mercure/`), appelé de façon synchrone par `cooling_study.action_calculate()`.
- **Moteur de compatibilité équipement** : portage Python de `frontend/src/equipment/compatibility.ts`
  (`services/compatibility.py`).
- **API JSON** (`controllers/api.py`) : études (CRUD), révisions, validation, snapshot, calcul (MERCURE
  synchrone), résultats, catalogue équipement, recommandations et sélection d'équipement — endpoints alignés
  sur `README_GC-COOLING-MASTER.md`, avec le format d'erreur standard (`error.code/message/field/section/action/request_id`).
- **Snapshot de calcul immuable** (GC-COOLING-13, `greencube.cooling.calculation.snapshot`) : validation
  structurée (`greencube.cooling.study.get_validation()`, erreurs bloquantes/avertissements/informations
  avec codes), snapshot figé par empreinte SHA-256 (plus le hash Python non cryptographique d'origine),
  `action_calculate()` recalcule désormais à partir des données **figées** dans le snapshot plutôt que des
  données live de l'étude, et confirmation en masse des hypothèses non mesurées
  (`action_confirm_assumptions()`, audité dans le chatter de l'étude). Routes
  `GET /studies/<id>/validation` et `POST /studies/<id>/assumptions/confirm` ajoutées.

## Ce qui a été réellement vérifié

Ce lot a été vérifié sur une vraie instance Odoo 18 Community (`/opt/odoo/odoo18`, Python 3.13,
PostgreSQL 17), en plus des vérifications syntaxiques précédentes. Toutes les commandes ci-dessous ont
été exécutées réellement (pas de simulation) sur une base de test dédiée (`greencube_test`) :

- **Syntaxe** : `ast.parse(...)` sur tous les `.py` et `xml.etree.ElementTree.parse(...)` sur tous les
  `.xml` du module — aucune erreur.
- **Installation sur base vierge** :
  `odoo-bin -d greencube_test -i greencube_cooling --stop-after-init` → **code retour 0**, "28 modules
  loaded" incluant `greencube_cooling`. Deux bugs réels ont été trouvés et corrigés à cette étape (pas
  contournés) : les boutons statistiques (`oe_stat_button`) des vues `cooling_study_views.xml` et
  `thermal_specification_views.xml` référençaient un champ (`result_count`, `study_count`) au lieu d'une
  action `type="object"` — Odoo refusait de charger la vue ("`result_count` is not a valid action"). Ajout
  des méthodes `action_view_results()` et `action_view_studies()` sur les modèles correspondants.
- **Tests sous le vrai test runner Odoo** :
  `odoo-bin -d greencube_test -i greencube_cooling --test-enable --test-tags greencube_cooling --stop-after-init`
  → **30 tests, 0 échec, 0 erreur** (code retour 0). Ceci inclut :
  - les 18 tests purs Python déjà existants (`test_mercure_engine.py`, `test_compatibility.py`), qui ne
    sont montés en `odoo.tests.common.BaseCase` que lorsque le module `odoo` est réellement importable
    (fallback vers `unittest.TestCase` sinon) — nécessaire car sous le vrai test runner, les tests sans
    attribut `test_tags` sont silencieusement ignorés par le filtre `--test-tags` (bug de découverte
    diagnostiqué et corrigé : les classes héritaient de `unittest.TestCase` nu, jamais reconnu par
    `TagsSelector.check()`). Revérifié en standalone (`python3 tests/test_mercure_engine.py` /
    `test_compatibility.py`) : toujours 13 + 5 tests OK, donc le double mode est préservé.
  - **12 nouveaux tests `TransactionCase`** (`tests/test_cooling_study.py`), couvrant le §27 du prompt
    GC-COOLING-01 : cycle de statuts draft→incomplete→ready→calculated→validated, `action_validate()`
    refusé hors état `calculated`, verrouillage `write()` d'une étude validée (`UserError`) sauf champs
    autorisés, `action_create_revision()` (copie des sous-lignes, non-copie du résultat actif,
    `root_study_id` préservé), immutabilité de `greencube.cooling.result` et
    `greencube.cooling.result.component` (write/unlink → `UserError`), verrouillage d'une
    `thermal.specification` utilisée par une étude validée, et sécurité multi-société/ACL (un `user` ne
    voit que ses propres études, un `technician` voit toutes les études de sa société, un `user` d'une
    société A ne peut pas lire une étude de la société B — `AccessError`).
  - **Un vrai bug de sécurité a été trouvé et corrigé par ces tests**, pas seulement documenté : la règle
    `ir.rule` multi-société (`rule_cooling_study_company`) était scopée au groupe `group_greencube_cooling_user`,
    donc combinée en **OR** (et non en AND) avec la règle "l'utilisateur ne voit que ses propres études"
    (`rule_cooling_study_own_records_user`), puisque les deux règles s'appliquaient au même groupe. Un
    simple `user` voyait donc **toutes les études de sa société**, pas seulement les siennes — l'inverse de
    ce qu'exige le master prompt. Corrigé en rendant `rule_cooling_study_company` **globale** (`groups="[]"`,
    donc ANDée avec toute règle de groupe), et en donnant à la règle du technicien un domaine `[(1,'=',1)]`
    scopé à son seul groupe (pour qu'il OR-écrase la restriction "own records" qu'il hérite aussi via
    `group_user`). Revérifié : `test_user_sees_only_own_studies` et
    `test_user_of_company_a_cannot_read_company_b_study` passent désormais.
- **Mise à jour d'une base existante** : des données réelles (persistées, pas dans une transaction de
  test) ont été créées via `odoo-bin shell` — une spécification thermique, une étude complète avec
  occupation, un calcul MERCURE exécuté et son résultat — puis
  `odoo-bin -d greencube_test -u greencube_cooling --stop-after-init` a été lancé → **code retour 0**,
  aucune erreur de migration. Revérifié après coup via `odoo-bin shell` : l'étude, le résultat (avec ses
  17 composantes) et la spécification thermique sont toujours présents et inchangés, et la contrainte
  d'immutabilité du résultat (`write()` → `UserError`) fonctionne toujours après la mise à jour.
- **Routes API réelles avec client HTTP authentifié** : serveur Odoo lancé en HTTP (port dédié 8169,
  isolé du service de production sur 8069), authentification via `/web/session/authenticate` (login/mot
  de passe réels), puis appels HTTP réels (module `requests`) sur l'intégralité des routes du contrôleur :
  - `POST /studies` (201), `PATCH /studies/<id>` (200), `POST /studies/<id>/snapshots` (201),
    `POST /studies/<id>/calculations` (201, calcul MERCURE réellement exécuté, charge recommandée
    2550 W cohérente), `GET /results/<id>` (200, breakdown complet), `GET /equipment-catalog` (200).
  - `GET /studies` (200, liste, étude créée bien présente), `GET /calculations/<job_id>` (200),
    `GET /studies/<id>/results` (200), `POST /studies/<id>/equipment-recommendations` (200, calcul de
    compatibilité réel : statut `compatible` avec ratio de sur-dimensionnement 0.98 pour un split
    2.7 kW face à une charge recommandée de 2.55 kW), `GET`/`POST /studies/<id>/equipment-selections`
    (200/201, sélection créée puis relue), `POST /studies/<id>/validate` (200, état passé à `validated`),
    `POST /studies/<id>/revisions` (201, révision créée avec `parent_study_id`/`root_study_id`/
    `revision_number` corrects).
  - Chemins d'erreur : `GET /studies/999999` et `POST /studies/999999/revisions` (404,
    `COOLING_STUDY_NOT_FOUND`), `POST /studies/<draft_id>/validate` sur une étude encore en brouillon
    (403, `COOLING_VALIDATION_FORBIDDEN`), accès non authentifié sur `GET /studies` (303 redirection
    vers `/web/login`, confirmant `auth="user"`).
  Toutes les routes du contrôleur `controllers/api.py` sont donc désormais exercées en HTTP réel, pas
  seulement leur logique ORM sous-jacente.
- **GC-COOLING-13 (backend uniquement — voir "Ce qui reste en suspens" pour le périmètre non traité)** :
  - Réinstallation complète vérifiée (`-i greencube_cooling --stop-after-init` → code retour 0) avec le
    nouveau modèle `greencube.cooling.calculation.snapshot` et le champ `snapshot_id` ajouté sur
    `greencube.cooling.result`.
  - **39 tests, 0 échec, 0 erreur** sous le vrai test runner Odoo (18 purs Python + 3 round-trip de
    sérialisation MERCURE + 18 `TransactionCase`, dont 6 nouveaux pour ce lot). Un vrai bug a été trouvé et
    corrigé en cours de route : `self.occupancy_profile_ids | self.equipment_load_ids` levait
    `TypeError: inconsistent models in: ...` — Odoo interdit l'union `|` entre recordsets de modèles
    différents ; corrigé en itérant chaque recordset séparément dans `get_validation()` et
    `action_confirm_assumptions()`.
  - **Preuve d'immutabilité réelle du snapshot** : `write()`/`unlink()` sur un snapshot lèvent `UserError`
    (test + vérifié en HTTP) ; créer un second snapshot bascule le premier en `state="superseded"`.
  - **Preuve que le calcul utilise bien les données figées, pas les données live** : test dédié qui modifie
    la puissance d'un équipement *après* la création du snapshot, relance `action_calculate()`, et vérifie
    que le payload figé (donc le résultat) n'a pas changé — exactement la garantie d'immutabilité que
    GC-COOLING-13 exige ("le frontend ne doit jamais déclarer une étude prête... la validation définitive
    doit être réalisée côté backend").
  - **Vérifié en HTTP réel** : `GET /studies/<id>/validation` (issues structurées avec codes, sur une étude
    incomplète puis complète), `POST /studies/<id>/assumptions/confirm` (fait disparaître l'avertissement
    de provenance correspondant), empreinte SHA-256 réelle (64 caractères hex, vs l'ancien
    `str(abs(hash(...)))` non déterministe entre process Python), `active_snapshot_id` exposé sur
    `GET /studies/<id>`.
  - Round-trip pur Python (`services/mercure/serialization.py`, testé en standalone ET sous Odoo) :
    `MercureInput` → `dict` JSON-sérialisable → `MercureInput` reconstruit à l'identique, nécessaire pour
    figer puis relire le payload depuis `payload_json`.

## Lot suivant (2026-07-18) : climat/géo réels, câblage frontend, EnergyPlus honnête

Ce lot a été développé et vérifié dans un environnement **sans instance Odoo installée** (pas de binaire
`odoo-bin` disponible ici) : les vérifications ci-dessous se limitent donc à `ast.parse`/`ElementTree.parse`
sur tout le module, à la ré-exécution des suites pures Python (`test_mercure_engine.py`,
`test_mercure_serialization.py`, `test_compatibility.py` — toujours 21/21 OK), et à un test manuel en
direct des services HTTP externes (géocodage, climat). **Les 12 tests `TransactionCase`
(`test_cooling_study.py`) et l'installation réelle du module n'ont pas pu être rejoués ici** — à revalider
sur une vraie instance Odoo 18 avant mise en production, comme le lot précédent l'avait fait.

Changements :

- **GC-COOLING-03 (géolocalisation) — implémenté** : `services/geo.py` interroge l'API Open-Meteo
  (géocodage + altitude + fuseau horaire, gratuite, sans clé), avec un cache (`greencube.cooling.geo.cache`,
  TTL 30 j). Nouvelles routes `GET /geocode?query=...` et `GET /geo-context?latitude=..&longitude=..`.
  Le frontend (`LocationStep.tsx`) fait une vraie recherche d'adresse avec suggestions, utilise
  `navigator.geolocation`, et affiche l'altitude/fuseau horaire réels au lieu des coordonnées figées
  (46.2263/7.1231/1200 m).
- **GC-COOLING-04 (climat historique) — implémenté** : `services/climate.py` interroge l'API archive
  Open-Meteo (10 ans d'historique journalier réel, ERA5), dérive les 3 scénarios (`reference_summer` =
  P90, `hot_weather` = P98, `prolonged_heatwave` = max observé) à partir de vraies journées, avec
  cache 90 j (`greencube.cooling.climate.dataset`). `_build_climate_scenarios()` bascule sur ce service
  dès que lat/lon sont connus, avec repli sur l'ancienne heuristique altitude si le service est
  injoignable. Les scénarios utilisés sont désormais persistés sur `greencube.cooling.climate.scenario`
  (provenance `api` ou `estimated_reference`), qui était un modèle orphelin jusqu'ici.
- **Arrondi commercial (partie de GC-COOLING-16) — câblé** : `commercial_capacity.find_tier_for_load_w()`
  est maintenant appelé par `action_calculate()` ; `greencube.cooling.result.commercial_capacity_id` et le
  bloc `commercial_capacity` de `GET /results/<id>` exposent le palier retenu. Le modèle
  `commercial.capacity` n'est donc plus mort.
- **Champs figés rendus configurables (GC-COOLING-10/11/12)** : densité/fraction d'éclairage
  (`occupancy_profile.lighting_power_density_wm2`/`lighting_usage_fraction`, remplace le `6`/`0.6` en dur),
  puissance ventilateur et bypass été (`ventilation_profile.fan_power_w`/`bypass_active`, remplace `30`/
  `False` en dur), décalage de consigne nocturne (`cooling_study.night_setpoint_offset_c`, remplace le
  `+1°C` en dur). Toujours hors périmètre : plusieurs profils d'occupation par étude (le premier reste
  seul utilisé, décision de portée MVP), calendrier hebdomadaire détaillé.
- **API de sous-ressources — ajoutée (comblant un vrai trou de GC-COOLING-02)** : jusqu'ici l'API ne
  permettait de créer/modifier que l'étude elle-même ; il n'existait aucune route pour la spécification
  thermique, les profils d'occupation/ventilation, les protections solaires ou les lignes d'équipement.
  Ajouté : `GET`/`PUT /studies/<id>/thermal-specification` (avec façades), `GET`/`PUT
  /studies/<id>/occupancy-profile`, `GET`/`PUT /studies/<id>/ventilation-profile`, `GET`/`PUT
  /studies/<id>/shading`, `GET`/`POST /studies/<id>/equipment-loads` +
  `PATCH`/`DELETE /equipment-loads/<id>`.
- **Frontend branché sur l'API réelle — fait (le point le plus significatif de ce lot)** : le frontend
  n'était plus un simple mock isolé. `src/sync/syncStudy.ts` pousse l'état du wizard vers les nouvelles
  routes ci-dessus (création de l'étude au premier sync, `backendId` stocké dans le store). `ReviewStep`
  appelle réellement `GET /studies/<id>/validation` (fiabilité, points bloquants) et
  `POST /assumptions/confirm` au lieu d'un score de fiabilité inventé (`24 - pénalités`). `ResultsPage`
  déclenche `POST /studies/<id>/calculations` et affiche le résultat backend au lieu d'exécuter le port
  TypeScript de MERCURE dans le navigateur. `EquipmentSelectionPage` appelle
  `POST /studies/<id>/equipment-recommendations` et `POST /equipment-selections` au lieu d'utiliser
  `api/mockCatalog.ts`. Les ports TS (`mercure/engine.ts`, `equipment/compatibility.ts`) et
  `mockCatalog.ts` restent dans le repo (ils ont servi de référence au portage Python et à
  `engine.test.ts`) mais ne sont plus appelés par aucune page.
  Limite assumée à cette date (2026-07-18) : pas de TanStack Query/autosave. **Mise à jour du
  2026-07-20 :** un autosave debouncé existe depuis (`frontend/src/sync/useAutosave.ts`, 1,5 s après la
  dernière modification, statuts local/dirty/saving/synced/error visibles dans `AppHeader`) — voir la
  section « Lot P0 — clôture des 3 manques restants » plus bas. TanStack Query, lui, n'a toujours pas été
  introduit : la synchronisation reste un ensemble d'appels `fetch` directs dans `api/study.ts`, pas des
  requêtes mises en cache/invalidées par une lib dédiée — alors même que `@tanstack/react-query` est
  présent dans `package.json` depuis le début de ce dépôt, jamais importé nulle part dans `src/`.
- **Catalogue équipement réel — ajouté** : `data/cooling_equipment_data.xml` (6 `product.template` avec
  `is_cooling_equipment=True`, mêmes caractéristiques que l'ancien `mockCatalog.ts`), chargé au lot data
  (pas demo) donc disponible en production.
- **GC-COOLING-05A/15 (Honeybee/EnergyPlus) — orchestration posée, sans simulation** :
  `services/energyplus.py` détecte réellement la présence de `honeybee-energy`/`ladybug`
  (pip) et du binaire `energyplus` (aucun n'est installé dans cet environnement). `action_calculate()`
  accepte désormais `engine` (`quick_solver`/`energyplus`/`both`, via `POST /calculations` body
  `{"engine": ...}`) : quand EnergyPlus est demandé et indisponible, un avertissement explicite
  (`ENERGYPLUS_UNAVAILABLE`) est ajouté au résultat plutôt que d'inventer un chiffre, et le résultat passe
  en état `partial` si EnergyPlus était le *seul* moteur demandé. Si le stack était installé, la
  traduction géométrie→Honeybee et la simulation elle-même restent à écrire (ce n'était pas non plus fait
  dans le lot précédent) — `run_energyplus_simulation()` le signale explicitement
  (`EnergyPlusSimulationError`) plutôt que de silencieusement retomber sur MERCURE sans le dire.
- **Idempotence et verrouillage optimiste (partie de GC-COOLING-02/13)** : en-tête `Idempotency-Key` lu
  sur `POST /studies/<id>/calculations` (rejoue le résultat existant au lieu de recalculer) ; en-tête
  `If-Match` (comparé à `updated_at`) sur `PATCH /studies/<id>`, retourne 409
  `COOLING_STUDY_VERSION_CONFLICT` en cas de conflit.
- **Données de démonstration ajoutées** : `demo/greencube_cooling_demo.xml` (une étude studio complète à
  Lyon avec spécification, façades, occupation, équipements, ventilation), chargée uniquement avec
  `--with-demo` (clé `demo` du manifeste, pas `data`).

## Lot de stabilisation (2026-07-20) : suite à l'audit fonctionnel

`Audit_fonctionnel_GreenCube_Cooling_18-07-2026.md` (score 40/100, verdict NO-GO) listait 6 blocages P0.
Ce lot corrige ceux qui sont du ressort du code de ce dépôt :

- **P0-01 (build cassé)** : `client.ts` n'autorisait pas `PUT` alors que `study.ts` en émet quatre ;
  `syncStudy.ts` déclarait `wallAreaM2` sans l'utiliser. `npm run build` passe à nouveau.
- **P0-02 (contrat de calcul incohérent)** : `POST /calculations` a toujours renvoyé une enveloppe de job
  (`{job_id, result_id, ...}`), mais le frontend attendait un `BackendResult` complet directement. Le
  frontend suit maintenant le parcours job → résultat (`calculate()` renvoie le job, `getResult(result_id)`
  récupère le résultat). Ce découplage est volontaire : il prépare un futur moteur EnergyPlus asynchrone
  sans nouvelle rupture de contrat.
- **P0-03 (rôle User non fonctionnel)** : `greencube.thermal.specification`/`.facade` étaient en lecture
  seule pour le groupe User. Un `ir.rule` dédié (`rule_thermal_specification_user_owns_private` /
  `rule_thermal_facade_user_owns_private`) autorise désormais l'écriture/création/suppression uniquement
  sur les spécifications **privées** (`standard_model=False`) rattachées à une étude dont l'utilisateur est
  propriétaire ; les modèles de catalogue (`standard_model=True`) restent manager-only en écriture. Le
  contrôleur force un fork (création d'une copie privée) dès qu'une étude référence un modèle standard,
  au lieu d'essayer de l'éditer en place.
- **P0-05 (IDOR sur les sous-modèles)** : aucun `ir.rule` n'existait pour les profils d'occupation, les
  apports internes, la ventilation, les protections solaires, les résultats et leurs composants — un
  utilisateur du groupe User pouvait lire/écrire n'importe quelle ligne d'un autre utilisateur en devinant
  son id. Des règles calquées sur celles de l'étude (`study_id.user_id` pour les users,
  `study_id.company_id` en filtre global, visibilité élargie pour les techniciens) ont été ajoutées pour
  chacun de ces modèles. Toutes les routes du contrôleur sont maintenant décorées avec `@_guarded`, qui
  transforme les `AccessError`/`MissingError` ORM en enveloppe JSON standard (`COOLING_ACCESS_DENIED` /
  `COOLING_NOT_FOUND`) au lieu de laisser Odoo répondre avec sa page d'erreur par défaut.
- **P0-04 (Odoo pas source de vérité)** : `StudiesListPage` interroge maintenant `GET /studies` et affiche
  aussi les études qui existent côté Odoo sans brouillon local (créées ailleurs, ou après un vidage du
  `localStorage`), avec une action d'import (`loadStudyFromBackend`, reverse-mapping best-effort des
  endpoints GET thermal-specification/occupancy-profile/ventilation-profile/equipment-loads déjà
  existants) qui matérialise un brouillon local éditable dans l'assistant. Le bandeau d'en-tête
  n'affiche plus « Enregistré » de façon statique : `AppHeader` prend un `syncState` explicite
  (`local`/`synced`) que chaque page renseigne selon `study.backendId`.
  **Limite assumée** : le wizard continue d'utiliser un id local (uuid) comme clé de route/état — ce lot
  ne re-clé pas l'intégralité des routes sur l'id Odoo, ce qui serait un chantier plus large et plus
  risqué à valider sans navigateur réel dans cet environnement.
- **P0-06 (CORS/CSRF non finalisé)** : `vite.config.ts` proxie désormais `/api/v1/greencube/cooling` vers
  Odoo (`VITE_ODOO_ORIGIN`, défaut `http://localhost:8069`) pendant `npm run dev`, pour que le navigateur
  ne voie qu'une seule origine et que le cookie de session Odoo reste same-origin. **Ceci ne couvre que le
  développement local** : en production, il faut reproduire ce même-origine avec un reverse proxy
  (nginx/traefik) devant Odoo et les assets du frontend — aucune infrastructure de ce type n'est livrée
  dans ce dépôt. Les routes mutatives restent en `csrf=False` avec auth par cookie de session ; tant
  qu'elles ne sont accessibles que same-origin via ce proxy, le risque CSRF classique (formulaire tiers)
  est limité, mais ce n'est pas une protection CSRF explicite (double-submit token, `SameSite=Strict`,
  etc.) — à faire avant toute exposition multi-origine réelle.
- Corrections ponctuelles associées : `dense_urban`/`urban_dense` (le frontend utilisait la mauvaise
  valeur d'énumération, P1-04) ; le calcul n'est plus déclenché automatiquement à chaque montage de
  `ResultsPage` (P1-06) — il l'est une seule fois depuis le bouton de `ReviewStep`, avec une
  `Idempotency-Key` générée côté client et transmise à `POST /calculations` ; `syncStudyToBackend` vide
  désormais les protections solaires côté Odoo quand elles sont retirées côté UI (P2-06, comportement
  auparavant destructif dans un seul sens).

**Non traité dans ce lot initial** (P1/P2 de l'audit) : cycle révision/validation absent du frontend
(P1-07 — **traité plus tard**, voir « Lot P1 » plus bas), immutabilité de la sélection d'équipement non
garantie en écriture (P1-08 — **traité plus tard**, voir ci-dessous), EnergyPlus toujours non
implémenté/non asynchrone (P1-09 — reste non traité, voir « Lot simulation »), et l'ensemble des écarts P2
restants — validation Zod/RHF complète (reste non traité), export (reste non traité), accessibilité
(partiellement traité, voir « Lot qualité »), tests Playwright (écrits mais **jamais exécutés**, voir
« Lot qualité »).

## Lot P0 — clôture des 3 manques restants (2026-07-20, suite)

Après un premier passage, trois points du "Lot de stabilisation P0" du plan de correction restaient
ouverts. Ce lot les referme :

- **CI** (`.github/workflows/ci.yml`, nouveau) : trois jobs — `frontend` (npm ci, lint, `npm run build`
  qui inclut `tsc -b`, vitest), `backend-pure-python` (parsing AST/XML de tout le module + les 21 tests
  purs), et `backend-odoo` qui installe le module sur une vraie image `odoo:18.0` + Postgres et exécute
  les tests `TransactionCase`/`HttpCase` via `--test-enable`. **Le job `backend-odoo` n'a jamais été
  exécuté** : il a été écrit à partir de la documentation de l'image Docker officielle et de l'API
  `HttpCase` d'Odoo 18, mais aucun Odoo n'est installé dans cet environnement pour le valider avant le
  premier vrai run sur GitHub Actions. Les deux premiers jobs, eux, reproduisent exactement les commandes
  utilisées manuellement tout au long de ce lot et donc sont bien couverts empiriquement.
- **Tests HTTP d'intégration** (`tests/test_http_api.py`, nouveau) : `HttpCase` réels (pas
  `TransactionCase`) couvrant le parcours complet création → spécification → occupation → ventilation →
  validation → calcul → résultat pour un utilisateur du groupe `User` simple, le contrat job → résultat
  (`POST /calculations` ne doit pas contenir le résultat complet), l'idempotence (même clé →
  même `result_id`), le refus IDOR cross-utilisateur/cross-société sur `PATCH/DELETE /equipment-loads/<id>`
  (403 `COOLING_ACCESS_DENIED`), et le conflit de version optimiste sur `PATCH /studies/<id>` (409). **Ces
  tests aussi sont non exécutés** dans cet environnement — voir l'avertissement en tête du fichier. C'est
  la même limite que celle déjà documentée pour `tests/test_cooling_study.py`.
- **Cache de brouillon contrôlé** : le store Zustand restait la seule source active pendant la saisie,
  sans autosave ni indicateur d'état réel. Ajout de `sync/useAutosave.ts` : un hook debouncé (1,5 s après
  la dernière modification) branché sur `StudyLayout` (donc actif sur les 7 étapes, `review` compris —
  `ResultsPage`/`EquipmentSelectionPage` restent en synchronisation explicite/synchrone comme avant, pas
  concernées). Statuts réels affichés dans `AppHeader` : `local` (jamais synchronisé), `dirty` (modifié
  depuis le dernier sync), `saving`, `synced`, `error` (avec message au survol). Le statut "saving/error"
  est volontairement non persisté (`useSyncStatusStore`, hors `zustand/persist`) pour ne pas afficher une
  fausse erreur après un rechargement de page ; `lastSyncedAt` (persisté sur `StudyDraft`) sert à calculer
  `dirty` vs `synced`. Limite assumée : chaque autosave repousse l'intégralité de l'étude (pas de diff
  partiel, l'API n'expose pas de PATCH granulaire par section) — donc plusieurs requêtes HTTP par cycle de
  sync, comme c'était déjà le cas aux points de contrôle existants.

## Lot P1 — fidélité métier (2026-07-20, suite)

Vague B du plan de correction (GC-COOLING-08/09/13/16, P1 de l'audit) :

- **GC-COOLING-08 — modèles GreenCube versionnés** : `data/thermal_specification_catalog_data.xml` ajoute
  un vrai catalogue (Studio/Bureau/Habitat/Commerce), chacun avec dimensions/U-values/façades distinctes.
  Nouvelle route `GET /thermal-specification-templates`. `ModelStep.tsx` charge ce catalogue au lieu de 4
  cartes codées en dur ; sélectionner un modèle applique réellement ses valeurs et enregistre
  `source_template_id`/`source_template_version` (nouveaux champs sur `greencube.thermal.specification`)
  pour la provenance.
- **GC-COOLING-09 — orientation et protections** : nouveau champ `main_orientation` sur l'étude (8 points
  cardinaux). Les 4 façades UI (avant/arrière/gauche/droite) sont tournées autour de cette orientation
  avant synchronisation, au lieu d'être toujours mappées nord/sud/est/ouest en identité — corrige l'audit
  P1-02. Chaque protection solaire a maintenant un `shading_type` et une efficacité distincts (au lieu de
  toujours `external_blind`) ; si plusieurs sont cochées, seule la plus efficace est appliquée et l'UI le
  signale explicitement (P1-03). Le ratio vitrage/mur est réellement contraint côté backend (l'ancien code
  gonflait artificiellement la surface de mur envoyée pour ne jamais déclencher la contrainte).
- **GC-COOLING-13 — confiance pré-calcul** : `get_validation()` renvoie désormais `completeness_score`
  (calculé depuis la complétude/provenance, disponible avant tout calcul) séparément de
  `confidence_score` (sortie du solveur, reste à 0 tant qu'aucun calcul n'a tourné) — corrige P1-05.
- **P1-07 — immutabilité + historisation** : `greencube.cooling.equipment.selection` bloque désormais
  `write()`/`unlink()` une fois `state=validated` (avant : seul `action_supersede` était protégé). Prix
  **et** données techniques (capacité à 45 °C, température extérieure max, SHR, EER, capacité nominale,
  nom produit) sont figés sur la sélection au moment de la création au lieu d'être relus en direct sur le
  produit catalogue — une sélection historique ne change plus silencieusement si le catalogue évolue.
  `EquipmentSelectionPage` affiche désormais l'historique des sélections avec ces valeurs figées.
- **P1-08 — champs utilisés/ignorés/estimés** : `ReviewStep` affiche la répartition `provenance_summary`
  (catalogue/API/confirmé/estimé/manquant) renvoyée par le backend. Les champs `wallComposition`,
  `insulationMm`, `glazingType` (affichés dans l'étape Modèle mais jamais transmis au solver) portent
  désormais la mention « ℹ️ non utilisé dans le calcul ». Six champs qui n'étaient ni affichés nulle part
  ni utilisés (`roofTiltDeg`, `comfortSensitivity`, `doorOpeningsPerDay`, `airingFrequency`,
  `airtightnessLevel`, `temperatureTolerance`) ont été supprimés du type `StudyDraft` : code mort, pas de
  champ à annoter puisqu'aucune UI ne les affichait.
- **P1-07 (autre volet) — révision/validation exposées au frontend** : `ReviewStep` affiche l'état
  (brouillon/prête/calculée/validée) et le numéro de révision, avec un bouton « Valider cette étude »
  (`POST /studies/<id>/validate`) et, une fois verrouillée, « Créer une révision » (`POST
  /studies/<id>/revisions`) — jusqu'ici ces actions backend existaient mais n'étaient atteignables que
  directement dans Odoo. Créer une révision fait basculer le brouillon local sur le nouvel id backend (même
  étude du point de vue de l'utilisateur, nouvelle révision Odoo dessous).
  **Reste non fait** : pas de vue de diff entre révisions, pas d'historique de toutes les révisions passées
  (seul le numéro de la révision courante est visible).

## Lot simulation — GC-COOLING-05A/15 (2026-07-20, suite)

**Important — niveau de preuve différent du reste de ce README.** Contrairement aux lots précédents,
aucun run Odoo réel n'a été possible pour ce lot (toujours pas d'Odoo installé dans cet environnement).
Seule la partie pure Python (`services/mercure/honeybee_translator.py`) a été réellement exécutée et
vérifiée (7 tests, voir `tests/test_honeybee_translator.py`, exécutable via
`python3 -m unittest test_honeybee_translator.py` sans Odoo). Tout le reste — modèles, ACL, `ir.rule`,
cron, câblage dans `action_calculate()` — est écrit avec le même soin que le reste du module mais **non
exécuté**, au même titre que `tests/test_http_api.py` déjà signalé dans le lot P0. Ne pas le déclarer
fonctionnel avant une installation réelle.

- **`services/mercure/honeybee_translator.py`** (nouveau, pur Python, testé) : `build_honeybee_model(mercure_input)`
  produit un JSON déterministe et checksummé (SHA-256), inspiré du schéma Honeybee (Model/Room/Face/
  Aperture) sans dépendre du package `honeybee-energy` (absent ici). Mappe géométrie, enveloppe (U
  équivalent, pas de matériaux en couches), vitrages (une ouverture par façade avec transmittance
  statique combinant protection/ombrage), occupation, éclairage, équipements agrégés en densité de
  puissance, infiltration, ventilation et consignes. Refuse explicitement (`HoneybeeTranslationError`)
  une géométrie non positive ou un vitrage dépassant la surface du mur — jamais de valeur inventée.
  Chaque appel retourne aussi une liste `diagnostics.assumptions` documentant les simplifications MVP.
- **`greencube.cooling.calculation.job`** (nouveau modèle) : le `job_id` de l'API référence désormais un
  vrai enregistrement (`study_id`, `snapshot_id`, `requested_engine`, `status`, `result_id`,
  `idempotency_key`, horodatage, `energyplus_processing_status`) au lieu de réutiliser l'id du résultat.
  `action_calculate()` crée ce job avant de lancer MERCURE et le complète juste après — le comportement
  synchrone existant n'est pas modifié, seul son suivi devient un vrai objet.
- **`greencube.cooling.simulation.artifact`** (nouveau modèle) : pointeur typé et checksummé vers un
  fichier produit pendant le traitement d'un job (`honeybee_json`/`epw`/`idf`/`sql`/`log`), stocké comme
  `ir.attachment` standard plutôt qu'un gros champ binaire directement sur le modèle. Immuable dès la
  création.
- **Feature flag `GC_COOLING_ENERGYPLUS_ENABLED`** (défaut : désactivé) : tant qu'il n'est pas à `true`,
  demander `engine=energyplus`/`both` ne déclenche même pas la traduction Honeybee — juste un
  avertissement `ENERGYPLUS_DISABLED`. Une fois activé, la traduction (rapide, pur Python) est tentée
  dans la requête HTTP elle-même (elle ne fait rien de lourd), mais **jamais** l'exécution EnergyPlus :
  `action_calculate()` n'appelle jamais `services.energyplus.run_energyplus_simulation()`.
- **Isolation dans un worker séparé (GC-COOLING-15)** : ce n'est plus un cron Odoo in-process (ancienne
  approche, remplacée — voir `migrations/18.0.3.0.0/post-migrate.py`) mais un processus autonome,
  `energyplus_worker/` (racine du dépôt, hors de l'addon), qui ne parle à Odoo que via deux routes HTTP
  authentifiées par secret partagé : `POST /energyplus-jobs/claim` et
  `POST /energyplus-jobs/<id>/complete` (`controllers/api.py`). Ce worker n'ouvre jamais de connexion
  PostgreSQL, n'importe jamais `odoo`, et ne détient aucun identifiant de base de données — voir
  `energyplus_worker/README.md` pour le déploiement (unité systemd, utilisateur non-root). Il est
  seul autorisé à appeler `run_energyplus_simulation`, qui reste une fonction pur Python sans
  dépendance ORM (`services/energyplus.py`). En pratique, cette fonction lève toujours
  `EnergyPlusUnavailableError` aujourd'hui (aucun binaire EnergyPlus ni honeybee-energy/ladybug n'est
  installé dans un déploiement cible de ce MVP) — le worker rapporte alors
  `energyplus_processing_status = simulation_unavailable` via `/complete`, sans jamais fabriquer de
  résultat. Vérifié par `energyplus_worker/test_worker.py` (12 tests, exécutés réellement, pur Python) ;
  les deux routes HTTP elles-mêmes n'ont jamais été exercées contre un vrai Odoo.
- **Comparaison MERCURE/EnergyPlus et règle de résultat canonique : non traité.** Comme aucune simulation
  EnergyPlus ne peut aboutir dans cet environnement (ni probablement dans un déploiement MVP proche),
  écrire une logique de comparaison entre deux résultats dont l'un n'existe jamais aurait été du code
  mort non vérifiable. `greencube.cooling.result.state` a toujours les valeurs `success`/`partial`/
  `failed`/`superseded` : `partial` est déjà utilisé quand `engine=energyplus` seul et que la simulation
  ne s'est pas terminée (MERCURE reste alors la seule source du nombre affiché).
- **Bug de sécurité corrigé au passage** : `greencube.cooling.result`/`.result.component` interdisaient
  `create` au groupe User (`perm_create=0`) alors qu'`action_calculate()` les crée sans `sudo()` —
  un utilisateur standard appelant le calcul via l'API aurait dû recevoir une `AccessError`. Voir le
  détail dans `docs/cooling_security_matrix.md`. Une règle de propriété manquante sur
  `greencube.cooling.calculation.snapshot` (oubliée lors du balayage P0-05 initial) a été corrigée en
  même temps, découverte en écrivant les règles du nouveau `calculation.job`.

## Lot qualité — P2 (2026-07-20, suite)

- **Tests de composants React — ajoutés et exécutés.** `@testing-library/react`, `@testing-library/user-event`
  et `@testing-library/jest-dom` étaient déjà dans `package.json` mais n'étaient utilisés nulle part
  (seul `mercure/engine.test.ts` existait). Ajout de 36 tests réels, tous exécutés avec succès
  (`npm test`, 49 tests au total avec les 13 déjà existants) :
  - `sync/syncStudy.test.ts` (11 tests) : vérifie mathématiquement la rotation d'orientation
    (`rotatedOrientation`/`facadeSlotForOrientation`, aller-retour exhaustif sur les 8 orientations × 4
    façades, aucune collision) et la résolution de protection dominante — la logique GC-COOLING-09 n'avait
    jusqu'ici été vérifiée que par relecture, jamais exécutée.
  - `store/studyStore.test.ts` (7 tests) : `createStudy`/`updateStudy`/`markSynced`/`findByBackendId`,
    en particulier que `markSynced` ne déclenche pas de boucle d'autosave infinie.
  - `components/layout/AppHeader.test.tsx` (12 tests) : les 5 états de synchronisation, l'ouverture/
    fermeture du panneau d'aide (y compris Échap), l'absence de faux positif « Synchronisé ».
  - `routes/steps/ModelStep.test.tsx` (6 tests) : le catalogue est bien chargé depuis l'API (pas de
    données codées en dur), l'état de chargement/erreur, et — le plus important — que sélectionner un
    modèle applique réellement ses dimensions (a révélé un bug du premier jet du test lui-même : le mock
    de `useOutletContext` n'était pas réactif aux mises à jour du store, corrigé en réutilisant le vrai
    `<Outlet context>` comme le fait `StudyLayout` en production).
- **Tests Playwright — écrits, jamais exécutés.** `playwright.config.ts` + `e2e/wizard.spec.ts` (parcours
  complet localisation → ... → résultats → sélection). Nécessitent un Odoo réel démarré séparément
  (`VITE_ODOO_ORIGIN`) et une session authentifiée — aucun des deux n'est disponible dans cet
  environnement. `npx playwright test --list` confirme que la config et le fichier sont au moins
  syntaxiquement valides ; rien de plus n'a pu être vérifié.
- **Concurrence/idempotence/deux sociétés — étendu dans `tests/test_http_api.py`** (~~toujours non
  exécuté~~ — exécuté réellement depuis, voir « Lot vérification réelle Odoo » ci-dessous) :
  `test_two_companies_full_isolation_on_direct_ids` (étude,
  résultat et liste jamais visibles depuis l'autre société) et
  `test_idempotency_key_survives_repeated_retries` (3 requêtes identiques → un seul job/résultat). **Limite
  assumée :** ce sont des vérifications séquentielles dans un seul thread de test, pas une vraie
  concurrence parallèle (plusieurs threads/process simultanés) — cela nécessiterait une instance Odoo
  multi-workers réellement démarrée, ce que cet environnement ne permet pas de mettre en place ni de
  vérifier.
- **Accessibilité clavier — amélioration ciblée, pas un audit complet.** La base était déjà correcte
  (tous les éléments cliquables du wizard sont des `<button>`/`<Link>`, tous les champs sont dans un
  `<label>`). Ajouté : fermeture du panneau d'aide au clavier (Échap), `role="dialog"` +
  `aria-label` dessus, `aria-live="polite"` sur l'indicateur de statut de synchronisation. **Non fait** :
  audit complet (contraste des couleurs, ordre de tabulation sur les grilles de cartes, lecteurs d'écran
  réels), responsive mobile (jamais testé sur un vrai viewport étroit — la CSS Tailwind utilise des
  breakpoints `sm:`/`lg:` mais rien ne garantit qu'ils rendent correctement en dessous).
- **README — nettoyage des affirmations contradictoires.** La ligne affirmant l'absence d'autosave
  (section « Lot suivant », 2026-07-18) contredisait l'autosave ajouté depuis (section « Lot P0 »,
  2026-07-20) ; corrigée avec un renvoi explicite. Idem pour la liste « non traité » du lot de
  stabilisation, qui ne pointait pas vers les lots où ces points ont ensuite été traités.
- **Documents obligatoires du Master V2 — partiellement traités.** GC-COOLING-17 (`GC_COOLING_PROMPTS/`)
  définit précisément ce qui est attendu : `docs/cooling_v2_initial_state.md` (état initial constaté) et
  une matrice de traçabilité GC-COOLING-01 à 18. Le premier existe déjà sous une autre forme
  (`Audit_fonctionnel_GreenCube_Cooling_18-07-2026.md`, à la racine du dépôt — c'est l'état initial
  documenté avant tous les lots de correction de cette session, pas la peine de le dupliquer). La matrice
  de traçabilité, elle, n'existait pas : ajoutée dans `docs/cooling_v2_traceability_matrix.md`.
  ~~Migrations de schéma : aucune n'a été nécessaire pour l'ensemble des lots de cette session~~ — plus
  vrai depuis : `migrations/18.0.2.0.0/` et `migrations/18.0.3.0.0/` existent désormais (voir « Lot
  vérification réelle Odoo » ci-dessous et `migrations/README.md` pour la politique). Le reste de
  GC-COOLING-17 (Docker/compose, sauvegarde/restauration, rollback, healthchecks, logs structurés,
  décision GO/NO-GO formelle) n'a pas été traité.
- **Découverte, non traitée** : `@tanstack/react-query`, `zod`, `react-hook-form` et
  `@hookform/resolvers` sont présents dans `package.json` depuis le début de ce dépôt mais ne sont
  importés nulle part dans `src/`. Soit un reliquat d'un scaffold jamais branché, soit une intention non
  réalisée — à clarifier avant de les utiliser ou de les retirer.

## Lot vérification réelle Odoo — GC-COOLING-01/02/13/15/16 (2026-07-20, suite)

Toutes les sessions précédentes de ce fichier avaient développé/corrigé du code Odoo sans jamais
disposer d'une instance Odoo installée dans leur environnement d'exécution — chaque section ci-dessus le
documente honnêtement ("jamais exécuté", "à revalider"). Cette fois, un environnement avec Odoo 18 déjà
installé (`/opt/odoo/odoo18`, PostgreSQL 17) était disponible, et a été utilisé pour rejouer réellement
l'installation, la suite de tests complète, les deux scripts de migration, et un aller-retour HTTP complet
du wizard plus les deux nouvelles routes worker EnergyPlus — sur une base de test dédiée
(`greencube_test_20260720`), jamais une base existante, supprimée après coup.

**4 bugs réels trouvés et corrigés** (pas seulement des échecs de test) :

1. **`tests/__init__.py` n'importait jamais `test_http_api.py` ni `test_honeybee_translator.py`** — ces
   deux suites étaient invisibles au test-runner Odoo depuis le début, silencieusement, sans erreur ni
   avertissement. Le "39 tests, 0 échec" du lot GC-COOLING-13 ci-dessus était donc réel mais incomplet :
   `test_http_api.py` (10 tests) et `test_honeybee_translator.py` (7 tests, déjà vérifié en standalone
   mais jamais sous Odoo) n'y étaient pas.
2. **Bug ACL réel** : `_sync_climate_scenario_records()` (appelée en interne par `action_calculate()`)
   écrivait sur `greencube.cooling.climate.scenario` sans `sudo()`, alors que ce modèle est
   volontairement technicien-only en écriture directe. Conséquence réelle : **un simple "User" ne
   pouvait jamais terminer un calcul** via l'API. Corrigé avec `sudo()` sur cette écriture interne (aucune
   route API n'expose ce modèle en écriture directe, donc la sécurité effective ne change pas).
3. **Fixtures de test cassées** : études de test sans `climate_confirmed` (10 échecs
   `test_cooling_study.py`) ; utilisateurs HTTP de test créés avec `groups_id: [(6, 0, [group])]`, qui
   *remplace* tous les groupes au lieu d'ajouter — supprimant `base.group_user`, nécessaire ne serait-ce
   que pour lire `ir.sequence` (5 échecs `test_http_api.py`). Corrigées.
4. **`greencube.cooling.solver.version` est scopé par société** (même convention que
   `greencube.thermal.specification`) : les sociétés de test HTTP n'avaient pas leur propre version de
   solver, donc `action_calculate()` échouait avec `SOLVER_VERSION_MISSING`. Corrigé en créant une
   version de solver par société de test.

**Résultat final : 45 tests, 0 échec, 0 erreur** (`--test-tags greencube_cooling`, incluant désormais tout
le module). Les deux scripts de migration (`18.0.2.0.0`, `18.0.3.0.0`) ont été exécutés directement contre
des données fabriquées simulant un état pré-migration et vérifiés corrects (pas seulement `ast.parse`). Le
flux complet du wizard (création → spécification → occupation → ventilation → validation → calcul →
résultat) et les routes `/energyplus-jobs/claim`/`/complete` ont été exercés avec un client HTTP réel —
y compris en lançant le vrai `energyplus_worker/worker.py --once` contre le serveur, qui a réellement
réclamé un job, réellement tenté la simulation (échec honnête `EnergyPlusUnavailableError`, stack absent),
et réellement rapporté le résultat. Voir `docs/cooling_v2_traceability_matrix.md` pour le détail lot par
lot mis à jour. Environnement restauré après coup (mot de passe Postgres temporaire retiré, base de test
supprimée) ; le service Odoo de production n'a pas été touché.

## Lot multi-société — provisionnement automatique du solver et du catalogue (2026-07-20, suite)

Le point "solver de test par société" ci-dessus ne corrigeait qu'une fixture — pas le vrai défaut de
production. Vérifié explicitement avec un utilisateur non-superutilisateur d'une deuxième société, dans
une base fraîche : ni la version MERCURE active ni aucun modèle catalogue GreenCube n'étaient visibles
(`SOLVER_VERSION_MISSING` + `MODEL_MISSING` bloquants), car `data/solver_version_data.xml` et
`data/thermal_specification_catalog_data.xml` ne créent leurs lignes que pour la société active à
l'installation (`company_id` y est `required=True`).

**Corrigé automatiquement** (version 18.0.3.0.0 → 18.0.4.0.0) : `models/solver_version.py` et
`models/thermal_specification.py` gagnent chacun une méthode `_provision_*_for_companies()` qui copie les
données de référence existantes vers toute société qui n'en a pas ; `models/res_company.py` (nouveau)
surcharge `create()` pour les nouvelles sociétés ; `post_init_hook` couvre les sociétés déjà présentes à
l'installation ; `migrations/18.0.4.0.0/post-migrate.py` couvre le même cas pour une mise à niveau.

**Piège Odoo réel rencontré** : `record.copy({"company_id": ...})` réinitialise silencieusement `state` à
sa valeur par défaut — comportement documenté d'Odoo pour tout champ nommé exactement `state`
(`odoo/fields.py`), sans annotation explicite dans notre code. La première version du correctif créait
donc bien la ligne, mais en `draft`, donc toujours invisible pour `get_validation()`. Découvert en
vérifiant l'état réel en base plutôt qu'en supposant que `copy()` préserve tout par défaut ; corrigé en
passant `"state": "active"` explicitement.

**Vérifié réellement, deux fois** (avant et après ce correctif) : société créée après installation
(chemin `res.company.create()`) et société déjà présente avant l'installation du module (chemin
`post_init_hook`), dans les deux cas avec un vrai utilisateur non-admin et `.with_user()` (jamais en
sudo, qui contourne `ir.rule`). Suite complète rejouée : toujours 45/45, 0 échec — après avoir retiré le
provisionnement manuel désormais redondant dans `test_http_api.py::setUpClass`, qui entrait en conflit
avec le nouveau provisionnement automatique (`_check_single_active`).

## Ce qui reste en suspens

Le runtime Odoo est maintenant disponible et a été utilisé pour toutes les vérifications ci-dessus.
Ce qui reste néanmoins non couvert par ce lot :

- **Rendu visuel des vues** : les vues se chargent sans erreur XML/action (vérifié), mais leur rendu dans
  le navigateur (ergonomie, disposition) n'a pas été inspecté visuellement.
- **Tests de charge / performance** : aucun test de volumétrie ou de temps de réponse sous charge.
- **Frontend non branché sur cette API** : toujours un store Zustand mocké, cf. limitations ci-dessous.
- **GC-COOLING-13 : uniquement le backend est traité.** L'écran React `/cooling/studies/:id/review` décrit
  dans le prompt (~30 composants : `SectionCompletionOverview`, `ConfidenceOverview`, `SnapshotPreview`,
  `StudyVersionConflictDialog`, etc.), les hooks TanStack Query, les schémas Zod, et les suites de tests
  unitaires/intégration/Playwright associées n'ont pas été implémentés — décision explicite pour rester
  dans une portée vérifiable réellement en une session (voir le choix fait avec l'utilisateur). Non
  traités côté backend non plus : sélection du moteur de calcul (`quick_solver`/`energyplus`/`both` — le
  champ existe sur le snapshot mais rien ne l'exploite), détection des données obsolètes (`stale`),
  détection des valeurs aberrantes, conflits de version optimiste, clé d'idempotence HTTP dédiée
  (`Idempotency-Key`).
- Tout ce qui est listé dans "Limitations connues de ce lot" ci-dessous (climat, Honeybee/EnergyPlus,
  matériaux détaillés, démo).

## Limitations connues de ce lot

- ~~**Climat (GC-COOLING-03/04)** non implémenté~~ — traité, voir "Lot suivant" ci-dessus (Open-Meteo réel
  + repli heuristique).
- ~~**Snapshot** (`action_create_snapshot`) construit un hash simplifié...~~ — traité : voir
  `greencube.cooling.calculation.snapshot` dans "Ce qui a été réellement vérifié".
- **Honeybee / EnergyPlus** : orchestration posée honnêtement (détection réelle de disponibilité,
  avertissement explicite au lieu d'un faux résultat — voir "Lot suivant"), mais la traduction
  géométrie→Honeybee et la simulation elle-même restent à écrire même si le stack était installé.
  `greencube.cooling.calculation.job` n'existe toujours pas en tant que modèle séparé — le contrôleur
  traite toujours le résultat comme un job `completed` synchrone (à revoir si EnergyPlus devient réel :
  il doit être asynchrone et isolé du process web).
- **`greencube.material.layer`** (couches de matériaux détaillées) non implémenté — hors périmètre MVP.
- ~~**`greencube.cooling.climate.dataset`** non implémenté~~ — ajouté (cache 90 j des scénarios
  historiques réels, voir "Lot suivant").
- **CRM/Sales, devis, facturation** : explicitement hors périmètre, conformément aux limites du Master Prompt.
- ~~**Frontend non branché sur cette API**~~ — traité, voir "Lot suivant" : le wizard synchronise
  explicitement vers l'API à des points de contrôle (pas d'autosave par champ/TanStack Query).
- ~~**Aucune donnée de démonstration**~~ — ajoutée (`demo/greencube_cooling_demo.xml`).
- **Toujours hors périmètre** : plusieurs profils d'occupation par étude, calendrier hebdomadaire détaillé,
  détection de données obsolètes (`stale`)/valeurs aberrantes, écran React dédié pour GC-COOLING-13
  (~30 composants spécifiés : `SectionCompletionOverview`, `ConfidenceOverview`, etc. — `ReviewStep.tsx`
  reste une version simplifiée qui appelle la vraie API mais sans ce niveau de détail visuel).

## Prochaines étapes suggérées

1. ~~Faire tourner ce module sur une vraie instance Odoo 18~~ — fait (voir "Ce qui a été réellement
   vérifié").
2. ~~Écrire les tests Odoo `TransactionCase` (§27 du prompt GC-COOLING-01)~~ — fait
   (`tests/test_cooling_study.py`, 12 tests).
3. ~~Exercer en HTTP réel toutes les routes API~~ — fait : les 13 routes du contrôleur sont désormais
   toutes vérifiées avec un client HTTP authentifié réel (voir "Ce qui a été réellement vérifié").
4. ~~Traiter le backend de GC-COOLING-13~~ — fait : snapshot immuable, validation structurée, confirmation
   d'hypothèses (voir "Ce qui a été réellement vérifié"). L'écran React associé reste à faire.
5. Implémenter l'écran `/cooling/studies/:id/review` de GC-COOLING-13 (composants, hooks, Zod, tests).
6. Brancher le frontend React sur cette API (remplacer `store/studyStore.ts` mock par TanStack Query + fetch).
7. Traiter GC-COOLING-03/04 (géolocalisation, climat) pour remplacer l'heuristique de scénarios climatiques.
8. Ajouter des données de démonstration (`demo/greencube_cooling_demo.xml`) avant une recette utilisateur.
