# Matrice de traçabilité GC-COOLING-01 à 18

Document demandé par GC-COOLING-17 pt.2 (`GreenCube_Cooling_Prompts_Detailles_20-07-2026.md`). L'état
initial constaté avant les lots de correction listés ici est `Audit_fonctionnel_GreenCube_Cooling_18-07-2026.md`
(racine du dépôt) — ce document-ci ne le duplique pas, il trace ce qui a changé depuis.

**Colonne « Preuve »** : fichier(s) de code + test(s) associé(s). **Colonne « Exécuté »** indique si la
preuve a été réellement vérifiée — soit par exécution réelle contre un Odoo 18 installé (voir la section
« Ce que ça a impliqué » ci-dessous), soit seulement par `ast.parse`/lecture. Ne pas confondre « code
écrit » et « comportement prouvé ».

## Mise à jour majeure (2026-07-20) : premier passage réel contre un vrai Odoo 18

Cette session a installé le module sur une vraie instance Odoo 18 (`/opt/odoo/odoo18`, Python 3.13,
PostgreSQL 17, base de test dédiée `greencube_test_20260720`, jamais une base existante) et exécuté
réellement l'ensemble de la suite de tests, plus un aller-retour HTTP complet du wizard et des deux
nouvelles routes worker EnergyPlus. **4 bugs réels ont été trouvés et corrigés** (pas seulement des
échecs de test — de vrais défauts fonctionnels/sécurité) :

1. **Découverte de tests cassée** : `tests/__init__.py` n'importait jamais `test_http_api.py` ni
   `test_honeybee_translator.py` — ces deux suites étaient donc invisibles au test-runner Odoo dans
   *toutes* les sessions précédentes, silencieusement, sans erreur. Corrigé en les ajoutant à
   `tests/__init__.py`.
2. **Bug ACL réel bloquant tout utilisateur non-technicien** : `_sync_climate_scenario_records()`
   (appelée en interne par `action_calculate()` pour mettre en cache les scénarios climatiques utilisés)
   écrivait sur `greencube.cooling.climate.scenario` sans `sudo()`, alors que l'ACL de ce modèle réserve
   volontairement `perm_create`/`perm_write` aux techniciens. Résultat concret : **un simple "User"
   ne pouvait jamais terminer un calcul** via l'API — `AccessError` systématique. Corrigé avec `sudo()`
   sur cette écriture interne (le modèle reste technicien-only pour tout accès direct — aucune route
   API n'expose ce modèle en écriture).
3. **Fixtures de test cassées** (`tests/test_cooling_study.py`, `tests/test_http_api.py`) : les études
   de test ne renseignaient jamais `climate_confirmed` (10 échecs), et les utilisateurs de test HTTP
   étaient créés avec `groups_id: [(6, 0, [group])]`, qui *remplace* tous les groupes au lieu d'ajouter
   — supprimant silencieusement `base.group_user` ("Internal User"), nécessaire ne serait-ce que pour
   lire `ir.sequence` (5 échecs). Corrigées.
4. **Design multi-société non anticipé par les fixtures** : `greencube.cooling.solver.version` est
   scopé par société (même convention que `greencube.thermal.specification`) ; les sociétés de test
   HTTP n'avaient pas leur propre version de solver, donc `action_calculate()` échouait avec
   `SOLVER_VERSION_MISSING` bien que l'étude soit par ailleurs complète. Corrigé en créant une version
   de solver par société de test (pas un changement de la règle de sécurité elle-même).

**Résultat final : 45 tests, 0 échec, 0 erreur** (`--test-tags greencube_cooling`, incluant désormais
`test_http_api.py` et `test_honeybee_translator.py`). Les deux scripts de migration
(`18.0.2.0.0`, `18.0.3.0.0`) ont aussi été exécutés réellement (pas seulement `ast.parse`) contre des
données fabriquées simulant un état pré-migration, et vérifiés corrects. Le flux HTTP complet du wizard
(création → spécification thermique → occupation → ventilation → validation → calcul → résultat) et les
deux nouvelles routes `/energyplus-jobs/claim` et `/energyplus-jobs/<id>/complete` ont été exercés avec
un vrai client HTTP authentifié, y compris en lançant le vrai script `energyplus_worker/worker.py` contre
le serveur réel (pas une simulation de son comportement).

**Environnement restauré après coup** : mot de passe temporaire du rôle Postgres `odoo` remis à `NULL`,
base de test `greencube_test_20260720` supprimée. Le service `odoo.service` de production (base
`orange_dev`) n'a jamais été touché.

| Lot | État | Preuve (code) | Preuve (tests) | Exécuté ? |
|---|---|---|---|---|
| 01 — Modèle Odoo, droits | Partiel avancé | `security/ir.model.access.csv`, `security/greencube_cooling_rules.xml`, `write()`/`unlink()` sur `result`/`snapshot`/`equipment.selection`/`calculation.job`/`simulation.artifact`, `migrations/18.0.2.0.0/post-migrate.py`, `migrations/18.0.3.0.0/post-migrate.py`, `migrations/README.md` | `tests/test_cooling_study.py::TestCoolingStudySecurity` | **Oui** — installation réelle, 45/45 tests, les deux scripts de migration testés contre des données fabriquées (voir note ci-dessus) |
| 02 — API contrats | Partiel avancé | `controllers/api.py` (`@_guarded`, enveloppe erreur, pagination `GET /studies`, contrat job→résultat, routes worker EnergyPlus) | `tests/test_http_api.py` (10 tests HttpCase, désormais réellement découverts et exécutés) | **Oui** — 10/10 verts après correction des fixtures ; CSRF/CORS toujours non traité (tous les routes `csrf=False`), pas de contrat OpenAPI/JSON Schema versionné |
| 03 — Géolocalisation | Partiel avancé | `services/geo.py`, `models/geo_cache.py`, `main_orientation`, fix `climate_confirmed` vs troncature 0/0, fix `urban_dense`→`dense_urban` dans `mapStudyToInput.ts` | — | Non (pas de suite de tests dédiée) |
| 04 — Climat historique | Partiel avancé (lot antérieur, non retouché cette session) | `services/climate.py`, `models/climate_dataset.py` | — | Non |
| 05A — Socle Honeybee | Partiel | `services/mercure/honeybee_translator.py`, `services/energyplus.py` (flag `GC_COOLING_ENERGYPLUS_ENABLED`) | `tests/test_honeybee_translator.py` (7 tests) | **Oui** — exécuté en standalone (`python3 -m unittest`) de longue date, et désormais aussi sous le vrai test-runner Odoo (il n'y était jamais arrivé avant, voir bug #1 ci-dessus) |
| 06 — Frontend build/état | Largement traité | `api/client.ts` (PUT), `sync/useAutosave.ts`, `store/studyStore.ts` (`markSynced`, `patchSilently`), `routes/StudiesListPage.tsx` (lecture Odoo). Code mort supprimé : `api/mockCatalog.ts`, `equipment/compatibility.ts`, `mercure/mapStudyToInput.ts`. `mercure/engine.ts`/`engine.test.ts` conservés délibérément (13 tests réels, rôle de référence documenté). | `npm run build`, `npm test` (49 tests), `store/studyStore.test.ts`, `components/layout/AppHeader.test.tsx` | **Oui** |
| 07 — UI localisation/climat | Partiel (lot antérieur) | `routes/steps/LocationStep.tsx` | — | Non |
| 08 — Modèles GreenCube versionnés | Traité | `data/thermal_specification_catalog_data.xml`, `GET /thermal-specification-templates`, `routes/steps/ModelStep.tsx` | `routes/steps/ModelStep.test.tsx` (6 tests) | **Oui** (frontend) ; backend exercé manuellement via HTTP réel dans cette session (`PUT /thermal-specification` avec `source_template_id`), mais sans suite de tests dédiée |
| 09 — Orientation/vitrages/protections | Traité | `sync/syncStudy.ts` (`rotatedOrientation`, `resolveDominantProtection`), `models/cooling_study.py` (`main_orientation`) | `sync/syncStudy.test.ts` (11 tests, aller-retour exhaustif 8×4) | **Oui** (frontend) / backend non couvert par une suite dédiée |
| 10 — Usage/occupation | Partiel — bug de constantes divergentes corrigé (aperçu 70W/50g·h vs défaut backend 75W/60g·h), calendrier/activité toujours non exposés en UI | `routes/steps/UsageStep.tsx` | `npm test` | **Oui** (frontend) |
| 11 — Équipements/apports internes | Partiel — sync corrigé en diff/upsert (`sync/syncStudy.ts::syncEquipment`, id catalogue stable via `equipment/internalLoadsCatalog.ts`) ; le catalogue `EquipmentStep.tsx` reste codé en dur (pas de catalogue Odoo) | `sync/syncStudy.ts`, `equipment/internalLoadsCatalog.ts` | `npm test`, `tsc -b`, `npm run build` | **Oui** (frontend) ; backend exercé manuellement via HTTP réel (POST equipment-loads) mais sans suite dédiée |
| 12 — Ventilation/confort | Partiel — `targetTemperatureMinC`/`targetTemperatureMaxC` remplacent la plage texte tronquée, alimentent `cooling_setpoint_c` et le nouveau champ réel `maximum_acceptable_temperature_c` (avant : codé en dur `cooling_setpoint_c + 2`) | `models/cooling_study.py`, `routes/steps/ComfortStep.tsx`, `sync/syncStudy.ts` | `npm test`, `tsc -b`, `npm run build` | **Oui** (frontend + backend) — `_check_comfort_temperature_band` et le champ `maximum_acceptable_temperature_c` vérifiés via un vrai `PATCH /studies/<id>` HTTP contre un Odoo réel dans cette session |
| 13 — Review/validation/snapshot/révision | Traité | `get_validation()` (`completeness_score`), `ReviewStep.tsx` (boutons Valider/Créer une révision) | `tests/test_cooling_study.py` (18 tests dédiés) | **Oui** — 18/18 verts sous le vrai test-runner |
| 14 — MERCURE canonique | Statu quo, documenté | `services/mercure/engine.py` (canonique) vs `frontend/src/mercure/engine.ts` (référence, non appelé en prod — confirmé par grep, aucun import) | `tests/test_mercure_engine.py` (13), `frontend/src/mercure/engine.test.ts` (13) | **Oui** (les deux, + réellement rejoué sous le vrai test-runner Odoo cette session) |
| 15 — Worker EnergyPlus | Partiel — isolation réelle : cron in-process supprimé, remplacé par `energyplus_worker/` (processus autonome, aucun accès direct PostgreSQL), routes `POST /energyplus-jobs/claim` et `POST /energyplus-jobs/<id>/complete` authentifiées par secret partagé | `models/calculation_job.py` (`_claim_next_for_worker`, `_complete_from_worker`), `controllers/api.py`, `energyplus_worker/worker.py`, `migrations/18.0.3.0.0/post-migrate.py` | `energyplus_worker/test_worker.py` (12 tests) | **Oui, intégralement** — le vrai `energyplus_worker/worker.py --once` a été lancé contre un vrai serveur Odoo (port dédié), a réellement réclamé un job créé via l'API, réellement échoué sur `EnergyPlusUnavailableError` (stack absent, honnête), et réellement rapporté `simulation_unavailable` via `/complete`. Seule l'exécution EnergyPlus elle-même reste impossible (aucun binaire, par design) |
| 16 — Résultats/recommandation | Traité | `POST /calculations` → job → `GET /results/<id>` | `tests/test_http_api.py::test_full_wizard_flow_as_standard_user` | **Oui** — flux complet rejoué deux fois (suite automatisée + script HTTP manuel), résultat MERCURE réel avec breakdown complet obtenu |
| 17 — Consolidation CI/recette | Partiel | ce document | — | **Aucun CI n'existe dans ce dépôt** (`find . -path "*/.github/*"` : vide) — une version antérieure de ce document citait à tort `.github/workflows/ci.yml` comme preuve ; corrigé ici. Pas de Docker/backup/rollback/healthchecks |
| 18 — Sélection équipement | Traité | `models/equipment_selection.py` (immuabilité + champs figés), `EquipmentSelectionPage.tsx` (historique) | — | Non — tri par `oversizing_ratio` toujours fait côté client, devrait être exclusivement backend |

## Ce que ça a impliqué concrètement (pour reproduire)

- Environnement : checkout Odoo 18.0 existant à `/opt/odoo/odoo18` (venv dédié
  `/opt/odoo/odoo18-venv`), PostgreSQL 17 avec un rôle `odoo` existant (peer-auth uniquement — un mot de
  passe TCP temporaire a été nécessaire le temps des tests puisque `/root` n'est pas traversable par
  l'utilisateur système `odoo`, puis remis à `NULL`).
- Commande d'installation + suite complète :
  `odoo-bin -d <test_db> -i greencube_cooling --test-enable --test-tags greencube_cooling --stop-after-init`.
- Tests HTTP réels : serveur lancé sur un port dédié (8169), authentification via
  `/web/session/authenticate`, appels réels via `requests` sur toutes les routes du wizard plus les 2
  routes worker EnergyPlus, avec `GC_COOLING_ENERGYPLUS_ENABLED=true` pour exercer la voie de traduction
  Honeybee (pur Python, ne nécessite pas honeybee-energy/ladybug réels).
- Scripts de migration : exécutés directement (`migrate(cr, version)`) contre la base de test après avoir
  fabriqué un état "avant migration" (valeurs divergentes pour le backfill, enregistrement `ir.model.data`
  orphelin pour le nettoyage du cron).

## Ce qui reste non exécuté / prochaines étapes

Dans l'ordre de valeur/risque restant :
1. Mettre en place un vrai CI (le point le plus proche d'un vrai gain : ce qui vient d'être fait
   manuellement dans cette session devrait tourner automatiquement à chaque commit).
2. GC-COOLING-04/07 (climat historique, UI localisation) : lots antérieurs non retouchés, pas de suite de
   tests dédiée.
3. Remplacer le catalogue d'équipements codé en dur (`EquipmentStep.tsx`) par un vrai catalogue Odoo
   (GC-COOLING-11).
4. Déplacer le tri par `oversizing_ratio` côté backend exclusivement (GC-COOLING-18).
5. Docker/compose, sauvegarde/restauration, rollback, healthchecks (reste de GC-COOLING-17).
6. CSRF/CORS et contrat OpenAPI/JSON Schema versionné pour l'API (GC-COOLING-02).
