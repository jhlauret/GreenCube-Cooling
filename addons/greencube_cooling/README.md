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

- **Climat (GC-COOLING-03/04)** non implémenté : `_build_climate_scenarios()` dans `cooling_study.py`
  reproduit la même heuristique que le mock frontend (température de base selon l'altitude/l'environnement)
  plutôt que d'interroger un vrai service climatique. À remplacer par le lot climat quand il sera livré.
- ~~**Snapshot** (`action_create_snapshot`) construit un hash simplifié...~~ — traité : voir
  `greencube.cooling.calculation.snapshot` dans "Ce qui a été réellement vérifié". Reste néanmoins hors
  périmètre : sélection de moteur, détection d'obsolescence/conflit de version, écran frontend (cf.
  "Ce qui reste en suspens").
- **Honeybee / EnergyPlus** non implémenté : seul MERCURE est câblé. `greencube.cooling.calculation.job`
  n'existe pas encore en tant que modèle séparé — le contrôleur traite le résultat MERCURE comme un job
  toujours `completed` de façon synchrone (acceptable pour MERCURE seul, insuffisant pour EnergyPlus qui
  doit être asynchrone et isolé du process web).
- **`greencube.material.layer`** (couches de matériaux détaillées) non implémenté — hors périmètre MVP.
- **`greencube.cooling.climate.dataset`** non implémenté — seul `climate.scenario` existe.
- **CRM/Sales, devis, facturation** : explicitement hors périmètre, conformément aux limites du Master Prompt.
- **Frontend non branché sur cette API** : le frontend React construit précédemment utilise encore un store
  Zustand mocké (`localStorage`) ; le remplacer par de vrais appels à `/api/v1/greencube/cooling/...` est la
  prochaine étape d'intégration.
- **Aucune donnée de démonstration** n'a été créée (`demo/greencube_cooling_demo.xml` absent) — à ajouter
  avant une recette utilisateur.

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
