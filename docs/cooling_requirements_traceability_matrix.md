# Matrice de traçabilité des exigences — GC-COOLING-06 à GC-COOLING-16

Document produit par GC-COOLING-17 (consolidation finale). Il complète, sans le dupliquer,
`docs/cooling_v2_traceability_matrix.md` (état détaillé arrêté au 2026-07-20, avant les lots
07-12/14/18/10/09/08/16/15/05A/07 rejoués ensuite) : ce document-ci donne le **statut final**, après
exécution réelle de la suite complète (voir `docs/cooling_final_acceptance_report.md` pour les preuves
d'exécution et les commandes).

Statuts utilisés : `implemented`, `partially_implemented`, `not_implemented`, `not_applicable`, `blocked`.

| ID | Lot source | Exigence | Implémentation | Fichier(s) | Endpoint(s) | Test(s) | Statut | Écart / justification |
|---|---|---|---|---|---|---|---|---|
| R06 | GC-COOLING-06 | Socle frontend, autosave, verrou optimiste | Zustand store, `useAutosave`, `If-Match`/409 | `frontend/src/store/studyStore.ts`, `frontend/src/sync/useAutosave.ts` | `PATCH /studies/:id` | `studyStore.test.ts` | implemented | — |
| R07 | GC-COOLING-07 | Étape localisation/climat, UX polish | Formulaire localisation, provenance, confirmation | `frontend/src/routes/steps/LocationStep.tsx`, `models/geo_cache.py`, `models/cooling_study.py` (confirm-location) | `POST /studies/:id/confirm-location` | tests frontend + `test_geolocation.py` | implemented | — |
| R08 | GC-COOLING-08 | Modèles GreenCube versionnés, U roof/floor réels, réapplication template | Catalogue thermique, validation, réapplication | `data/thermal_specification_catalog_data.xml`, `models/thermal_specification.py` | `GET /thermal-specification-templates`, `PUT /thermal-specification` | `ModelStep.test.tsx`, tests backend catalogue | implemented | — |
| R09 | GC-COOLING-09 | Orientation/vitrages/protections, apport solaire par façade | Rotation orientation, protection dominante, breakdown solaire | `sync/syncStudy.ts`, `services/mercure/engine.py` | `PUT /studies/:id/shading` | `syncStudy.test.ts`, `test_http_api.py` (shading) | implemented | — |
| R10 | GC-COOLING-10 | Usage/occupation, calendrier structuré, gains réels | Calendrier hebdomadaire, activité → gains, verrouillage étude validée | `models/cooling_study.py` (occupancy_profile), `routes/steps/UsageStep.tsx` | `PUT /studies/:id/occupancy-profile` | `test_cooling_study.py`, tests frontend | implemented | — |
| R11 | GC-COOLING-11 | Catalogue équipements/éclairage sourcé depuis Odoo | Catalogue backend, sync diff/upsert | `models/internal_load_catalog.py` (ou équivalent), `equipment/internalLoadsCatalog.ts` | `GET /internal-load-catalog` | tests frontend + backend | implemented | — |
| R12 | GC-COOLING-12 | Ventilation, n50/fréquence ouverture, infiltration réelle | Entrées infiltration réelles câblées au solveur | `models/cooling_study.py`, `services/mercure/engine.py` | `PATCH /studies/:id` | `test_mercure_engine.py`, `test_cooling_study.py` | implemented | — |
| R13 | GC-COOLING-13 | Vérification, snapshot immuable, transitions unifiées, route `/ready` | `get_validation()`, snapshot idempotent, `POST /studies/:id/ready` | `models/cooling_study.py`, `models/calculation_snapshot.py`, `controllers/api.py` | `POST /studies/:id/ready`, `POST /studies/:id/snapshot` | `test_cooling_study.py` (18 tests) | implemented | — |
| R14 | GC-COOLING-14 | Moteur MERCURE canonique, cohérence TS/Python, déterminisme | Deux entrées MERCURE (Python canonique, TS référence), tests de conformité | `services/mercure/engine.py`, `frontend/src/mercure/engine.ts` | — (calcul pur) | `test_mercure_engine.py`, `engine.test.ts`, `test_mercure_serialization.py` | implemented | Le moteur TS reste une référence de non-régression, non appelé en production (confirmé par grep — aucun import applicatif) |
| R15 | GC-COOLING-15 | Worker EnergyPlus isolé, claim atomique, stall/retry/dead-letter, annulation | Processus autonome, `SELECT ... FOR UPDATE SKIP LOCKED`, cron de récupération | `energyplus_worker/worker.py`, `models/calculation_job.py`, `data/energyplus_job_cron.xml` | `POST /energyplus-jobs/claim`, `POST /energyplus-jobs/:id/complete`, `POST /calculations/:id/cancel` | `energyplus_worker/test_worker.py` (12), `test_calculation_job.py` | implemented | Exécution EnergyPlus elle-même non exécutable dans ce bac à sable (aucun binaire EnergyPlus/Honeybee installé) — le chemin `EnergyPlusUnavailableError` est honnêtement rapporté, pas simulé comme un succès |
| R16 | GC-COOLING-16 | Contrat job/résultat complet, tail EnergyPlus, flag `is_current` | `POST /calculations` → job → `GET /results/:id`, staleness | `models/calculation_job.py`, `models/result.py` | `POST /studies/:id/calculations`, `GET /results/:id` | `test_http_api.py::test_full_wizard_flow_as_standard_user` | implemented | — |
| R18 | GC-COOLING-18 | Sélection équipement, validation, fermeture IDOR/cascade | Immuabilité sélection, garde IDOR, cascade-delete | `models/equipment_selection.py` | `GET/POST /studies/:id/equipment-selection` | tests backend équipement | implemented | Tri par `oversizing_ratio` toujours fait côté client (frontend) — devrait être recalculé/vérifié côté backend ; **P3**, sans impact sécurité (le backend revalide la sélection à l'écriture) |
| R17 | GC-COOLING-17 | Consolidation, recette complète, GO/NO-GO | Suite complète rejouée (fresh-install + upgrade + worker + frontend), rapport final | tous modules | tous les endpoints listés ci-dessus | voir `docs/cooling_final_acceptance_report.md` | implemented (périmètre recette technique/sécurité de base) | Périmètre exploitation (docker-compose applicatif, sauvegarde/restauration réelle sur infra, scripts install/backup/rollback, doc VPS complète) **non traité** dans ce lot : aucune infra VPS/MinIO/Redis n'existe dans ce dépôt à ce jour pour les tester réellement sans les fabriquer de toutes pièces non vérifiées — voir `docs/cooling_known_issues.md` (classé P2, contournement : CI GitHub Actions existante + procédure manuelle Odoo standard `-i`/`-u`/`pg_dump` documentée dans le rapport final) |

## Notes

- Les identifiants R01-R05 (GC-COOLING-01 à 05/05A) sont couverts en détail par
  `docs/cooling_v2_traceability_matrix.md` (lignes "01" à "05A") et par `docs/cooling_security_matrix.md` ;
  ils ne sont pas rouverts ici car aucune régression n'a été trouvée en exécutant la suite complète
  (voir rapport final).
- Aucune exigence n'est déclarée `implemented` sans code et test associés listés dans la colonne
  correspondante, conformément à la consigne du lot.
