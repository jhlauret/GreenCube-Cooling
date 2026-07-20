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
  Limite assumée : pas de TanStack Query/autosave par champ — la synchronisation se fait par appel
  explicite à des points de contrôle (changement d'étape, ouverture de Review, lancement du calcul), pas
  en temps réel à chaque frappe.
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

**Non traité dans ce lot** (P1/P2 de l'audit, hors urgence de recette) : modèles GreenCube toujours
décoratifs (P1-01), orientation principale sans effet sur la géométrie (P1-02), protections solaires
réduites à un type générique (P1-03), score de fiabilité pré-calcul (P1-05), cycle révision/validation
absent du frontend (P1-07), immutabilité de la sélection d'équipement non garantie en écriture (P1-08),
EnergyPlus toujours non implémenté/non asynchrone (P1-09), et l'ensemble des écarts P2 (validation
Zod/RHF, pagination, export, accessibilité, tests Playwright/HTTP en CI...).

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
