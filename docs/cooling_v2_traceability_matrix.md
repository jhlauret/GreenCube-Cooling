# Matrice de traçabilité GC-COOLING-01 à 18

Document demandé par GC-COOLING-17 pt.2 (`GreenCube_Cooling_Prompts_Detailles_20-07-2026.md`). L'état
initial constaté avant les lots de correction listés ici est `Audit_fonctionnel_GreenCube_Cooling_18-07-2026.md`
(racine du dépôt) — ce document-ci ne le duplique pas, il trace ce qui a changé depuis.

**Colonne « Preuve »** : fichier(s) de code + test(s) associé(s). **Colonne « Exécuté »** indique si la
preuve a été réellement vérifiée dans cette session (voir la note d'environnement en bas) — beaucoup de
code Odoo listé ici n'a été vérifié que par `ast.parse`/lecture, pas par une exécution réelle contre un
Odoo installé. Ne pas confondre « code écrit » et « comportement prouvé ».

| Lot | État | Preuve (code) | Preuve (tests) | Exécuté ? |
|---|---|---|---|---|
| 01 — Modèle Odoo, droits | Partiel avancé | `security/ir.model.access.csv`, `security/greencube_cooling_rules.xml`, `write()`/`unlink()` sur `result`/`snapshot`/`equipment.selection`/`calculation.job`/`simulation.artifact`, `migrations/18.0.2.0.0/post-migrate.py` (backfill `maximum_acceptable_temperature_c`, version bumpée 18.0.1.0.0 → 18.0.2.0.0), `migrations/README.md` (politique de migration) | `tests/test_cooling_study.py::TestCoolingStudySecurity`, `docs/cooling_security_matrix.md` §procédure manuelle | Non (TransactionCase et script de migration jamais lancés contre un vrai Odoo) |
| 02 — API contrats | Partiel avancé | `controllers/api.py` (`@_guarded`, enveloppe erreur, pagination `GET /studies`, contrat job→résultat) | `tests/test_http_api.py` (10 tests HttpCase) | Non (jamais lancé) |
| 03 — Géolocalisation | Partiel avancé | `services/geo.py`, `models/geo_cache.py`, `main_orientation`, fix `climate_confirmed` vs troncature 0/0 | — | Non |
| 04 — Climat historique | Partiel avancé (lot antérieur, non retouché cette session) | `services/climate.py`, `models/climate_dataset.py` | — | Non |
| 05A — Socle Honeybee | Partiel | `services/mercure/honeybee_translator.py`, `services/energyplus.py` (flag `GC_COOLING_ENERGYPLUS_ENABLED`) | `tests/test_honeybee_translator.py` (7 tests) | **Oui** — seul lot simulation réellement exécuté (pur Python, sans Odoo) |
| 06 — Frontend build/état | Largement traité | `api/client.ts` (PUT), `sync/useAutosave.ts`, `store/studyStore.ts` (`markSynced`), `routes/StudiesListPage.tsx` (lecture Odoo) | `npm run build`, `npm test` (49 tests), `store/studyStore.test.ts`, `components/layout/AppHeader.test.tsx` | **Oui** |
| 07 — UI localisation/climat | Partiel (lot antérieur) | `routes/steps/LocationStep.tsx` | — | Non |
| 08 — Modèles GreenCube versionnés | Traité | `data/thermal_specification_catalog_data.xml`, `GET /thermal-specification-templates`, `routes/steps/ModelStep.tsx` | `routes/steps/ModelStep.test.tsx` (6 tests) | **Oui** (frontend) / Non (backend) |
| 09 — Orientation/vitrages/protections | Traité | `sync/syncStudy.ts` (`rotatedOrientation`, `resolveDominantProtection`), `models/cooling_study.py` (`main_orientation`) | `sync/syncStudy.test.ts` (11 tests, aller-retour exhaustif 8×4) | **Oui** (frontend) / Non (backend) |
| 10 — Usage/occupation | Partiel — bug de constantes divergentes corrigé (aperçu apports humains alignait 70W/50g·h alors que le backend défaut 75W/60g·h), calendrier/activité toujours non exposés en UI | `routes/steps/UsageStep.tsx` | `npm test` | **Oui** (frontend) |
| 11 — Équipements/apports internes | Partiel — sync corrigé en diff/upsert (`sync/syncStudy.ts::syncEquipment`, id catalogue stable via `equipment/internalLoadsCatalog.ts`) au lieu d'un delete+recreate complet à chaque sauvegarde ; le catalogue `EquipmentStep.tsx` reste codé en dur (pas de catalogue Odoo) | `sync/syncStudy.ts`, `equipment/internalLoadsCatalog.ts` | `npm test`, `tsc -b`, `npm run build` | **Oui** (frontend) / Non (backend jamais lancé) |
| 12 — Ventilation/confort | Partiel — la borne basse de température n'est plus tronquée : `targetTemperatureMinC`/`targetTemperatureMaxC` (deux champs numériques) remplacent la plage texte et alimentent respectivement `cooling_setpoint_c` et le nouveau champ `maximum_acceptable_temperature_c` (avant : codé en dur `cooling_setpoint_c + 2`) ; l'humidité reste une valeur cible unique (MERCURE ne modélise pas de plage humidité) | `models/cooling_study.py`, `routes/steps/ComfortStep.tsx`, `sync/syncStudy.ts` | `npm test`, `tsc -b`, `npm run build`, `ast.parse` | **Oui** (frontend) / Non (contrainte Odoo `_check_comfort_temperature_band` jamais lancée contre un vrai Odoo) |
| 13 — Review/validation/snapshot/révision | Traité | `get_validation()` (`completeness_score`), `ReviewStep.tsx` (boutons Valider/Créer une révision) | `tests/test_cooling_study.py` (existant) | Non |
| 14 — MERCURE canonique | Statu quo, documenté | `services/mercure/engine.py` (canonique) vs `frontend/src/mercure/engine.ts` (référence, non appelé en prod — commenté explicitement) | `tests/test_mercure_engine.py` (13), `frontend/src/mercure/engine.test.ts` (13) | **Oui** (les deux) |
| 15 — Worker EnergyPlus | Partiel — isolation réelle ajoutée : cron in-process supprimé, remplacé par `energyplus_worker/` (processus autonome, aucun accès direct PostgreSQL), routes `POST /energyplus-jobs/claim` et `POST /energyplus-jobs/<id>/complete` authentifiées par secret partagé | `models/calculation_job.py` (`_claim_next_for_worker`, `_complete_from_worker`), `controllers/api.py`, `energyplus_worker/worker.py`, `energyplus_worker/addon_bridge.py`, `migrations/18.0.3.0.0/post-migrate.py` (nettoyage du cron obsolète) | `energyplus_worker/test_worker.py` (12 tests) | **Oui** (worker, pur Python) / Non (routes HTTP elles-mêmes, jamais contre un vrai Odoo) — et l'exécution EnergyPlus elle-même ne peut toujours pas aboutir (aucun binaire disponible, par design) |
| 16 — Résultats/recommandation | Traité | `POST /calculations` → job → `GET /results/<id>` | `tests/test_http_api.py::test_full_wizard_flow_as_standard_user` | Non |
| 17 — Consolidation CI/recette | Partiel | `.github/workflows/ci.yml`, ce document | — | Job `backend-odoo` du CI jamais lancé ; pas de Docker/backup/rollback/healthchecks |
| 18 — Sélection équipement | Traité | `models/equipment_selection.py` (immuabilité + champs figés), `EquipmentSelectionPage.tsx` (historique) | — | Non |

## Ce que « Exécuté : Oui » signifie précisément ici

Aucun Odoo n'a été installé dans l'environnement où ce document a été rédigé (voir la section
correspondante du `README.md` du module). « Exécuté : Oui » signifie donc uniquement :
- **Frontend** : `npm run build` (tsc + vite), `npm test` (vitest) et `npm run lint` ont réellement tourné
  et sont verts.
- **Python pur** (`services/mercure/*`, `services/mercure/honeybee_translator.py`) : exécuté via
  `python3 -m unittest`, sans dépendance à l'ORM Odoo.

Tout le reste — modèles Odoo, `ir.rule`, contrôleurs HTTP, crons — n'a été vérifié que par
`ast.parse`/`xml.etree.ElementTree.parse` (syntaxe) et relecture attentive, jamais par une exécution
réelle. C'est la même réserve que celle documentée pour `tests/test_cooling_study.py` et
`tests/test_http_api.py` dans le `README.md` du module — ce document ne fait que la rendre visible lot
par lot plutôt que noyée dans le texte.

## Prochaine étape pour clore GC-COOLING-17

Dans l'ordre de valeur/risque :
1. Installer une vraie instance Odoo 18 + PostgreSQL et exécuter réellement `tests/test_cooling_study.py`
   et `tests/test_http_api.py` — c'est la seule façon de transformer les « Non » ci-dessus en preuve
   réelle, et probablement où se cachent d'autres bugs du type de celui découvert dans le lot simulation
   (ACL `perm_create=0` bloquant `action_calculate()` pour un utilisateur standard).
2. Lancer le job `backend-odoo` du CI une première fois et corriger les problèmes de chemin/configuration
   qui ne manqueront pas d'apparaître.
3. Traiter GC-COOLING-10/11/12 (usage, apports internes, ventilation/confort) — seuls lots fonctionnels
   du plan encore entièrement non commencés.
4. Docker/compose, sauvegarde/restauration, rollback, healthchecks (reste de GC-COOLING-17).
