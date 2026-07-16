# GC-COOLING-MASTER-V2

## Audit, consolidation intégrale et livraison canonique de GreenCube Cooling — GC-COOLING-01 à GC-COOLING-18

---

## Objectif

Auditer, rationaliser, compléter, tester et livrer l’intégralité de GreenCube Cooling.

Ce Master V2 couvre explicitement :

```text
GC-COOLING-01 — Module et modèles Odoo
GC-COOLING-02 — API Odoo
GC-COOLING-03 — Géolocalisation, altitude et fuseau
GC-COOLING-04 — Service climatique historique
GC-COOLING-05A — Socle initial Honeybee / EnergyPlus
GC-COOLING-06 — Socle frontend React
GC-COOLING-07 — Localisation et contexte climatique
GC-COOLING-08 — Modèle et caractéristiques thermiques
GC-COOLING-09 — Orientation, vitrages et protections
GC-COOLING-10 — Usage et occupation
GC-COOLING-11 — Équipements et apports internes
GC-COOLING-12 — Ventilation, infiltration et confort
GC-COOLING-13 — Vérification et snapshot
GC-COOLING-14 — Moteur MERCURE
GC-COOLING-15 — Orchestration avancée Honeybee / EnergyPlus
GC-COOLING-16 — Résultats et recommandation
GC-COOLING-17 — Consolidation MVP
GC-COOLING-18 — Sélection d’équipement
```

La démarche obligatoire est :

```text
inspecter l’existant
→ inventorier les lots réellement appliqués
→ établir une matrice 01–18
→ identifier les doublons
→ identifier les conflits
→ choisir les composants canoniques
→ migrer sans perte de données
→ compléter les écarts
→ tester
→ sécuriser
→ documenter
→ produire un patch réintégrable
→ décider GO ou NO-GO
```

Il est interdit de réécrire aveuglément le dépôt.

---

## Parcours fonctionnel final

Le système doit permettre :

```text
Création d’une étude
→ rattachement à une société et un utilisateur
→ saisie ou recherche de la localisation
→ résolution latitude / longitude / altitude / fuseau
→ collecte et analyse climatique
→ génération des scénarios climatiques
→ choix du modèle GreenCube
→ géométrie et caractéristiques thermiques
→ orientation
→ vitrages
→ protections solaires
→ usage
→ occupation
→ éclairage
→ équipements internes
→ ventilation
→ infiltration
→ consignes de confort
→ revue de complétude
→ résolution des erreurs
→ confirmation des hypothèses
→ création d’une révision
→ création d’un snapshot immuable
→ calcul MERCURE
→ simulation Honeybee / EnergyPlus
→ suivi des jobs
→ comparaison des moteurs
→ résultat canonique
→ recommandation de puissance
→ sélection d’un équipement compatible
→ conservation de l’historique
```

---

## Principes non négociables

1. Odoo Community 18 est la source de vérité métier.
2. Le frontend ne conserve jamais la source primaire des études, résultats, produits ou prix.
3. Un snapshot utilisé est immuable.
4. Un résultat terminé est immuable.
5. Une sélection d’équipement validée est historique et immuable.
6. Toute modification postérieure crée une nouvelle révision.
7. EnergyPlus ne s’exécute jamais dans le processus web Odoo.
8. Honeybee et EnergyPlus n’accèdent jamais directement à PostgreSQL/Odoo.
9. Aucun catalogue produit ne doit être codé en dur dans le frontend.
10. Aucun résultat de test ne doit être déclaré réussi sans exécution réelle.
11. Aucun ancien fichier ne doit être supprimé sans justification.
12. Aucun développement postérieur ne doit être écrasé.
13. Les changements de schéma utilisent des migrations.
14. Les fonctions optionnelles utilisent des feature flags.
15. Les noms et contrats du modèle canonique doivent être uniques.
16. Les implémentations doublonnées doivent être fusionnées ou dépréciées explicitement.

---

## État initial obligatoire

Créer :

```text
docs/cooling_v2_initial_state.md
```

Inclure :

- arborescence ;
- branche Git ;
- statut Git ;
- fichiers modifiés ;
- fichiers non suivis ;
- derniers commits ;
- addons Odoo ;
- frontend ;
- microservices ;
- workers ;
- Docker ;
- migrations ;
- tests ;
- documentation ;
- API ;
- fichiers d’environnement ;
- dépendances ;
- versions.

Identifier les versions réelles de :

```text
Odoo
Python
PostgreSQL
Node.js
React
TypeScript
Vite
Redis
Honeybee
Ladybug Tools
OpenStudio
EnergyPlus
Docker
```

Exécuter si disponibles :

```text
lint
typecheck
tests
build
tests Odoo
tests Python
tests API
healthchecks
```

Conserver les erreurs initiales.

---

## Inventaire des prompts appliqués

Créer :

```text
docs/cooling_prompt_application_inventory.md
```

Pour chaque lot 01–18 :

```text
prompt_id
title
files_expected
files_found
models_expected
models_found
endpoints_expected
endpoints_found
tests_expected
tests_found
status
evidence
notes
```

Statuts :

```text
fully_applied
partially_applied
not_applied
conflicting
obsolete
superseded
unknown
```

---

## Matrice d’exigences intégrale

Créer :

```text
docs/cooling_v2_requirements_matrix.md
```

Pour chaque exigence :

```text
requirement_id
source_prompt
domain
requirement
current_implementation
canonical_implementation
status
gap
conflict
priority
planned_action
test
evidence
final_status
```

Priorités :

```text
P0 — sécurité, perte de données, architecture bloquante
P1 — parcours principal ou calcul incorrect
P2 — fonction importante avec contournement
P3 — amélioration non bloquante
```

Ne pas commencer les corrections avant cette matrice.

---

## Carte des dépendances

Créer :

```text
docs/cooling_v2_dependency_map.md
```

Dépendances canoniques :

```text
01 Module Odoo
→ 02 API
→ 03 Géolocalisation
→ 04 Service climatique
→ 05A Moteur physique initial

01–05A
→ 06 Socle frontend
→ 07–12 Écrans de configuration
→ 13 Validation et snapshot
→ 14 MERCURE
→ 15 Orchestration EnergyPlus avancée
→ 16 Résultats
→ 17 Consolidation
→ 18 Sélection d’équipement
```

Détecter toute dépendance circulaire.

---

## Modèle de données canonique

Créer :

```text
docs/cooling_v2_canonical_data_model.md
```

Le modèle canonique doit au minimum contenir :

```text
greencube.cooling.study
greencube.cooling.study.revision
greencube.cooling.location
greencube.cooling.climate.dataset
greencube.cooling.climate.event
greencube.cooling.climate.scenario
greencube.cooling.assumption
greencube.cooling.validation.issue
greencube.cooling.calculation.snapshot
greencube.cooling.calculation.job
greencube.cooling.simulation.artifact
greencube.cooling.result
greencube.cooling.result.scenario
greencube.cooling.result.line
greencube.cooling.result.comparison
greencube.cooling.equipment.profile
greencube.cooling.equipment.performance.point
greencube.cooling.equipment.rule
greencube.cooling.equipment.compatibility
greencube.cooling.equipment.selection
greencube.cooling.equipment.comparison
```

Réutiliser les modèles existants équivalents lorsque possible.

Ne pas créer deux modèles pour la même notion.

---

## Règles de nommage canonique

Établir une table de correspondance :

```text
ancien_nom
nouveau_nom_canonique
type_de_migration
compatibilité
date_de_dépréciation
```

Unifier notamment :

```text
simulation
calculation
calculation_job
energy_simulation
result
simulation_result
artifact
simulation_artifact
```

Une seule désignation canonique doit être retenue.

---

## Consolidation critique GC-COOLING-05A / GC-COOLING-15

### Rôle canonique de 05A

```text
payload versionné
validation
constructeur Honeybee
géométrie
constructions
charges
météo
runner EnergyPlus
parser
normaliseur
```

### Rôle canonique de 15

```text
jobs
file d’attente
workers
heartbeats
timeouts
retries
artefacts
comparaison MERCURE
persistance avancée
observabilité
```

### Règle d’intégration

```text
05A = bibliothèque ou service de calcul
15 = orchestration de ce même service
```

Il est interdit de conserver :

- deux runners EnergyPlus ;
- deux constructeurs Honeybee ;
- deux schémas d’entrée concurrents ;
- deux modèles de simulation ;
- deux modèles d’artefact ;
- deux systèmes de résultats ;
- deux règles de recommandation de capacité ;
- deux mécanismes de gestion météo.

Créer :

```text
docs/cooling_v2_05a_15_consolidation.md
```

---

## Architecture canonique

```text
Frontend React
        │
        ▼
API Odoo / BFF
        │
        ▼
Odoo Community 18
├── études
├── révisions
├── climat
├── snapshots
├── jobs
├── résultats
├── catalogue
└── sélections
        │
        ▼
Queue / Worker
        │
        ▼
Cooling Simulation Service
├── Honeybee Builder
├── Weather Resolver
├── EnergyPlus Runner
├── Result Parser
└── Result Normalizer
        │
        ▼
Stockage privé des artefacts
```

MERCURE reste un moteur rapide testable indépendamment de l’ORM.

---

## Source de vérité

```text
Odoo
→ données métier

snapshot
→ entrées immuables d’un calcul

job
→ état d’exécution

worker
→ exécution technique

result
→ résultat immuable

artifact
→ fichier technique

frontend
→ interface et cache

product.template / product.product
→ catalogue équipement
```

---

## Révisions et immuabilité

Flux obligatoire :

```text
étude existante
→ nouvelle révision
→ nouvelles données
→ nouvelle validation
→ nouveau snapshot
→ nouveau calcul
→ nouveau résultat
→ nouvelle sélection
```

Interdire :

- modification d’un snapshot existant ;
- modification d’un résultat terminé ;
- modification rétroactive d’une sélection ;
- écrasement d’un dataset climatique utilisé.

---

## Socle Odoo — GC-COOLING-01

Auditer :

- manifest ;
- dépendances ;
- modèles ;
- vues ;
- menus ;
- séquences ;
- ACL ;
- record rules ;
- multi-société ;
- configuration ;
- tests ;
- migrations.

Vérifier :

```text
_name
_description
company_id
active
relations
constraints
indexes
tracking
copy behavior
unlink behavior
```

---

## API — GC-COOLING-02

Unifier sous :

```text
/api/v1/greencube/cooling
```

Créer :

```text
docs/cooling_v2_api_contract_matrix.md
```

Pour chaque endpoint :

```text
method
path
request schema
response schema
permissions
idempotency
versioning
status codes
errors
tests
```

Les contrôleurs doivent rester légers.

---

## Géolocalisation — GC-COOLING-03

Consolider :

- recherche d’adresse ;
- latitude ;
- longitude ;
- altitude ;
- fuseau IANA ;
- précision ;
- source ;
- confiance ;
- correction manuelle ;
- carte ;
- audit.

Le frontend ne doit pas devenir la source officielle de la localisation.

---

## Climat — GC-COOLING-04

Vérifier :

- fournisseurs ;
- Open-Meteo ;
- interface provider ;
- normalisation ;
- contrôle qualité ;
- fuseaux ;
- percentiles ;
- degrés-heures ;
- nuits chaudes ;
- vagues de chaleur ;
- signal récent ;
- scénarios ;
- cache ;
- stale-if-error ;
- fallback ;
- persistance ;
- immuabilité.

Scénarios obligatoires :

```text
reference_summer
hot_weather
prolonged_heatwave
```

---

## Frontend — GC-COOLING-06

Stack cible :

```text
React 18
TypeScript strict
Vite
Tailwind CSS
React Router v6
Zustand
React Hook Form
Zod
TanStack Query
Vitest
Testing Library
Playwright
```

Le store Zustand ne doit contenir que l’état temporaire d’interface.

---

## Routes frontend

```text
/cooling/studies
/cooling/studies/new
/cooling/studies/:studyId
/cooling/studies/:studyId/location
/cooling/studies/:studyId/model
/cooling/studies/:studyId/orientation
/cooling/studies/:studyId/usage
/cooling/studies/:studyId/equipment
/cooling/studies/:studyId/comfort
/cooling/studies/:studyId/review
/cooling/studies/:studyId/results
/cooling/studies/:studyId/equipment-selection
```

Vérifier :

- deep links ;
- guards ;
- permissions ;
- rafraîchissement ;
- responsive ;
- mode lecture seule ;
- révision ;
- erreurs réseau.

---

## Étapes 07 à 12

### Localisation et climat

- adresse ;
- carte ;
- coordonnées ;
- altitude ;
- fuseau ;
- environnement ;
- contexte climatique ;
- scénarios ;
- qualité ;
- provenance.

### Modèle thermique

- modèle GreenCube ;
- dimensions ;
- parois ;
- valeurs U ;
- matériaux ;
- plancher ;
- toiture ;
- portes.

### Orientation et vitrages

- azimut ;
- surfaces ;
- U-value ;
- SHGC ;
- protections ;
- masques.

### Usage et occupation

- usage ;
- personnes ;
- calendriers ;
- activité ;
- sensible ;
- latent.

### Équipements internes

- éclairage ;
- appareils ;
- informatique ;
- cuisson ;
- charges permanentes ;
- calendriers.

### Ventilation et confort

- air neuf ;
- ventilation ;
- infiltration ;
- récupération ;
- consignes ;
- humidité ;
- confort.

---

## Validation et snapshot — GC-COOLING-13

La validation officielle est backend.

Gravités :

```text
error
warning
info
```

Une erreur bloque le snapshot.

Le snapshot doit contenir :

- étude ;
- révision ;
- localisation ;
- climat ;
- géométrie ;
- enveloppe ;
- vitrages ;
- protections ;
- occupation ;
- équipements ;
- éclairage ;
- ventilation ;
- infiltration ;
- confort ;
- hypothèses ;
- versions ;
- référentiels ;
- checksum.

---

## MERCURE — GC-COOLING-14

Le moteur doit calculer :

```text
transmissions
ponts thermiques
apports solaires
occupants sensibles
occupants latents
équipements sensibles
équipements latents
éclairage
ventilation sensible
ventilation latente
infiltration sensible
infiltration latente
autres charges
```

Sorties :

```text
charge sensible
charge latente
charge totale
SHR
marge
puissance recommandée
scénario dimensionnant
confiance
trace
```

Le cœur de calcul doit être indépendant de l’ORM.

---

## EnergyPlus — GC-COOLING-05A et 15

Chaîne canonique :

```text
snapshot
→ payload versionné
→ Honeybee Builder
→ modèle validé
→ météo
→ EnergyPlus isolé
→ parsing
→ normalisation
→ résultat
```

EnergyPlus doit utiliser :

- `shell=False` ;
- utilisateur non root ;
- timeout ;
- CPU limité ;
- mémoire limitée ;
- disque limité ;
- workspace isolé ;
- réseau désactivé si possible.

---

## Jobs

Statuts canoniques :

```text
queued
validating
building_model
preparing_weather
running
parsing_results
normalizing_results
comparing
persisting
completed
failed
cancelled
timed_out
superseded
```

Champs :

```text
job_id
study_id
revision_id
snapshot_id
company_id
engine
engine_version
status
current_step
progress
heartbeat_at
timeout_at
attempt_count
idempotency_key
request_id
error_code
result_id
```

---

## Artefacts

Types canoniques :

```text
snapshot_json
input_json
honeybee_json
openstudio_osm
energyplus_idf
energyplus_epjson
weather_epw
energyplus_sql
energyplus_err
energyplus_eio
energyplus_html
normalized_result_json
logs
```

Définir une politique de rétention.

---

## Résultats — GC-COOLING-16

Schéma canonique :

```text
engine
engine_version
scenario
sensible_load_w
latent_load_w
total_load_w
shr
margin_w
recommended_capacity_w
recommended_capacity_kw
recommended_capacity_btu_h
peak_timestamp
annual_energy_kwh
cooling_electricity_kwh
max_indoor_temperature_c
max_indoor_humidity_percent
hours_above_setpoint
confidence_score
breakdown
warnings
assumptions
provenance
```

Le frontend ne recalcule aucun résultat officiel.

---

## Comparaison MERCURE / EnergyPlus

Calculer :

```text
absolute_difference_w
relative_difference_percent
```

Statuts :

```text
acceptable
warning
critical
not_comparable
```

Modes de décision :

```text
energyplus_preferred
maximum_of_both
engineer_review
mercure_fallback
```

La règle doit être versionnée.

---

## Sélection d’équipement — GC-COOLING-18

Réutiliser Odoo :

```text
product.template
product.product
product.category
product.attribute
product.attribute.value
product.supplierinfo
```

Comparer :

- capacité nominale ;
- capacité aux conditions réelles ;
- sensible ;
- latent ;
- modulation ;
- plage extérieure ;
- alimentation ;
- phases ;
- courant ;
- bruit ;
- condensats ;
- dimensions ;
- rendement ;
- qualité de données ;
- disponibilité ;
- prix si activé.

---

## Compatibilité équipement

Statuts :

```text
recommended
strong_alternative
compatible
compatible_with_conditions
not_recommended
incompatible
insufficient_data
```

Un produit incompatible ne doit jamais être recommandé.

---

## Dégradation à haute température

Utiliser :

```text
capacité à 35 °C
capacité à 40 °C
capacité à 45 °C
courbe de performance
```

Ne pas utiliser uniquement la capacité nominale.

Ne pas extrapoler silencieusement.

---

## API canonique

```text
GET    /api/v1/greencube/cooling/studies
POST   /api/v1/greencube/cooling/studies
GET    /api/v1/greencube/cooling/studies/<id>
PATCH  /api/v1/greencube/cooling/studies/<id>

POST   /api/v1/greencube/cooling/studies/<id>/revisions
POST   /api/v1/greencube/cooling/studies/<id>/validate
POST   /api/v1/greencube/cooling/studies/<id>/snapshots

POST   /api/v1/greencube/cooling/studies/<id>/climate-context
GET    /api/v1/greencube/cooling/studies/<id>/climate-context
GET    /api/v1/greencube/cooling/studies/<id>/climate-scenarios

POST   /api/v1/greencube/cooling/studies/<id>/calculations
GET    /api/v1/greencube/cooling/calculations/<job_id>
POST   /api/v1/greencube/cooling/calculations/<job_id>/cancel

GET    /api/v1/greencube/cooling/results/<result_id>
GET    /api/v1/greencube/cooling/studies/<id>/results
GET    /api/v1/greencube/cooling/results/<id>/comparison

GET    /api/v1/greencube/cooling/equipment-catalog
POST   /api/v1/greencube/cooling/studies/<id>/equipment-recommendations
POST   /api/v1/greencube/cooling/equipment/compare
POST   /api/v1/greencube/cooling/studies/<id>/equipment-selections
GET    /api/v1/greencube/cooling/studies/<id>/equipment-selections
```

---

## OpenAPI

Créer ou compléter :

```text
openapi/cooling.yaml
```

Les types TypeScript et Python doivent s’aligner sur ce contrat.

Éviter les DTO concurrents.

---

## Format d’erreur canonique

```json
{
  "error": {
    "code": "COOLING_RESULT_STALE",
    "message": "Le résultat ne correspond plus à la version actuelle de l’étude.",
    "field": null,
    "section": "results",
    "action": "create_revision",
    "request_id": "req-..."
  }
}
```

Ne jamais exposer de stack trace, SQL, chemin local ou secret.

---

## Idempotence

Utiliser `Idempotency-Key` pour :

- création d’étude si nécessaire ;
- création de révision ;
- contexte climatique ;
- snapshot ;
- calcul ;
- annulation ;
- sélection d’équipement.

Tester :

- double clic ;
- retry réseau ;
- réponse perdue ;
- deux onglets ;
- timeout client.

---

## Verrouillage optimiste

Utiliser :

```text
version
etag
updated_at
```

Aucun écrasement silencieux.

---

## Permissions

Rôles possibles :

```text
cooling_user
cooling_engineer
cooling_manager
cooling_admin
```

Tester les droits sur :

- études ;
- climat ;
- snapshots ;
- calculs ;
- résultats ;
- artefacts ;
- catalogue ;
- règles ;
- sélections ;
- configuration.

---

## Multi-société

Chaque objet métier pertinent doit avoir :

```text
company_id
```

Tester systématiquement les accès croisés.

---

## Feature flags canoniques

```text
enable_climate_history
enable_climate_recent_signal
enable_energyplus_calculation
enable_annual_energyplus_simulation
enable_advanced_natural_ventilation
enable_solver_payload_preview
enable_cooling_what_if
enable_result_version_comparison
enable_cooling_equipment_selection
enable_cooling_equipment_prices
enable_cooling_equipment_stock
enable_cooling_equipment_annual_energy
enable_cooling_quote_preparation
```

Éliminer les flags doublons ou contradictoires.

---

## Sécurité

### Authentification

- sessions ;
- tokens ;
- cookies ;
- CORS ;
- CSRF ;
- expiration ;
- révocation.

### Autorisation

- ACL ;
- record rules ;
- rôles ;
- multi-société ;
- artefacts ;
- prix.

### Entrées

- Zod ;
- validation Python ;
- limites ;
- enums ;
- NaN ;
- infinis ;
- payload volumineux ;
- injections.

### Réseau

- SSRF ;
- URLs arbitraires ;
- redirections ;
- IP privées ;
- métadonnées cloud.

### Exécution

- `shell=False` ;
- non-root ;
- timeout ;
- CPU ;
- mémoire ;
- disque ;
- nettoyage.

### Secrets

- dépôt ;
- `.env` ;
- logs ;
- CI ;
- Docker ;
- documentation.

---

## Tests obligatoires

### Odoo

- modèles ;
- contraintes ;
- ACL ;
- record rules ;
- multi-société ;
- migrations.

### API

- endpoints ;
- erreurs ;
- idempotence ;
- conflits ;
- permissions.

### Climat

- fuseaux ;
- années bissextiles ;
- qualité ;
- percentiles ;
- nuits chaudes ;
- vagues de chaleur ;
- scénarios ;
- cache.

### Frontend

- routes ;
- formulaires ;
- stepper ;
- erreurs ;
- responsive ;
- accessibilité.

### MERCURE

- cas de référence ;
- propriétés monotones ;
- sensible ;
- latent ;
- unités.

### EnergyPlus

- géométrie ;
- météo ;
- exécution réelle ;
- timeout ;
- fatal ;
- parsing ;
- artefacts.

### Résultats

- comparaison ;
- confiance ;
- historique ;
- révisions.

### Équipements

- compatibilité ;
- haute température ;
- sensible ;
- latent ;
- électricité ;
- bruit ;
- condensats ;
- sélection.

---

## Tests Playwright

Créer au minimum :

1. création d’une étude ;
2. localisation ;
3. analyse climatique ;
4. modèle thermique ;
5. orientation et vitrages ;
6. usage et occupation ;
7. équipements internes ;
8. ventilation et confort ;
9. erreur bloquante ;
10. confirmation des hypothèses ;
11. snapshot ;
12. calcul MERCURE ;
13. calcul EnergyPlus ;
14. suivi de job ;
15. fallback ;
16. comparaison ;
17. révision ;
18. sélection d’équipement ;
19. produit incompatible ;
20. résultat obsolète ;
21. accès inter-sociétés refusé ;
22. parcours mobile.

---

## Tests de panne

Tester :

- PostgreSQL indisponible ;
- Redis indisponible ;
- fournisseur météo indisponible ;
- cache périmé ;
- worker indisponible ;
- EnergyPlus absent ;
- fichier EPW absent ;
- processus tué ;
- timeout ;
- stockage indisponible ;
- catalogue vide ;
- données produit insuffisantes.

---

## Migrations et compatibilité

Créer :

```text
docs/cooling_v2_migration_plan.md
```

Inclure :

- anciens modèles ;
- modèles canoniques ;
- renommages ;
- copies de données ;
- dépréciations ;
- compatibilité temporaire ;
- rollback ;
- tests de migration.

Ne pas supprimer immédiatement un ancien champ utilisé en production.

---

## Dépréciation

Pour chaque composant remplacé :

```text
component
replacement
deprecated_since
compatibility_period
removal_condition
migration_status
```

Aucune suppression brutale.

---

## Performance

Mesurer :

- bundle frontend ;
- temps API ;
- requêtes SQL ;
- N+1 ;
- taille snapshot ;
- durée MERCURE ;
- durée EnergyPlus ;
- consommation mémoire ;
- taille artefacts ;
- temps catalogue ;
- temps de classement produit.

---

## Docker et VPS

Services possibles :

```text
nginx
frontend
odoo
postgres
redis
cooling-worker
simulation-worker
minio
```

Ne conserver que les services nécessaires.

Créer ou compléter :

```text
docker-compose.yml
docker-compose.production.yml
Dockerfile.frontend
Dockerfile.odoo
Dockerfile.simulation
```

---

## Healthchecks

Créer ou compléter :

```text
/health
/health/deep
```

Vérifier :

- frontend ;
- Odoo ;
- PostgreSQL ;
- Redis ;
- workers ;
- stockage ;
- climat ;
- MERCURE ;
- EnergyPlus ;
- écriture temporaire.

---

## Sauvegarde, restauration et rollback

Documenter et tester :

- PostgreSQL ;
- filestore ;
- stockage objet ;
- fichiers météo ;
- artefacts métier ;
- configurations ;
- paramètres ;
- versions.

Créer :

```text
docs/cooling_v2_backup_restore.md
docs/cooling_v2_rollback.md
```

---

## Documentation obligatoire

Créer ou compléter :

```text
README_GC_COOLING_MASTER_V2.md
CHANGELOG_GC_COOLING_V2.md
MANIFEST_GC_COOLING_V2.txt

docs/cooling_v2_initial_state.md
docs/cooling_prompt_application_inventory.md
docs/cooling_v2_requirements_matrix.md
docs/cooling_v2_dependency_map.md
docs/cooling_v2_canonical_data_model.md
docs/cooling_v2_05a_15_consolidation.md
docs/cooling_v2_api_contract_matrix.md
docs/cooling_v2_migration_plan.md
docs/cooling_v2_architecture.md
docs/cooling_v2_state_machine.md
docs/cooling_v2_security_audit.md
docs/cooling_v2_accessibility_audit.md
docs/cooling_v2_performance_report.md
docs/cooling_v2_backup_restore.md
docs/cooling_v2_rollback.md
docs/cooling_v2_known_issues.md
docs/cooling_v2_final_acceptance_report.md
```

---

## Packaging final

Produire :

```text
GC_COOLING_MASTER_V2_RELEASE/
├── addons/
├── frontend/
├── workers/
├── simulation-service/
├── deployment/
├── scripts/
├── migrations/
├── openapi/
├── tests/
├── docs/
├── README_GC_COOLING_MASTER_V2.md
├── CHANGELOG_GC_COOLING_V2.md
└── MANIFEST_GC_COOLING_V2.txt
```

---

## Patch réintégrable

Produire :

```text
PATCH_GC_COOLING_MASTER_V2.diff
PATCH_GC_COOLING_MASTER_V2_README.md
MANIFEST_GC_COOLING_V2.txt
```

Le patch doit :

- être limité au périmètre ;
- éviter le formatage global ;
- préserver les changements récents ;
- inclure les migrations ;
- documenter les conflits ;
- inclure les tests ;
- inclure le rollback ;
- distinguer créations, modifications et dépréciations.

---

## Gate GO / NO-GO

Le GO est possible uniquement si :

```text
0 P0 ouverts
0 P1 ouverts sur le parcours principal
0 conflit non résolu entre 05A et 15
0 modèle métier doublonné actif
0 endpoint canonique doublonné
0 vulnérabilité critique
0 secret exposé
migrations validées
installation vierge validée
mise à jour validée
test réel EnergyPlus validé
tests MERCURE validés
tests Playwright critiques validés
multi-société validé
backup validé
restore validé
rollback documenté
```

Sinon :

```text
NO-GO
```

---

## Critères d’acceptation fonctionnels

Le Master V2 est accepté si :

1. les 18 prompts sont inventoriés ;
2. toutes les exigences sont matricées ;
3. le modèle canonique est défini ;
4. les doublons sont résolus ;
5. 05A et 15 utilisent le même moteur ;
6. Odoo reste la source de vérité ;
7. la géolocalisation fonctionne ;
8. le service climatique fonctionne ;
9. les trois scénarios climatiques sont produits ;
10. le frontend couvre toutes les étapes ;
11. la validation fonctionne ;
12. le snapshot est immuable ;
13. MERCURE fonctionne ;
14. EnergyPlus fonctionne réellement ;
15. les jobs sont suivis ;
16. les résultats sont comparables ;
17. le résultat canonique est produit ;
18. sensible, latent et SHR sont disponibles ;
19. les révisions fonctionnent ;
20. les historiques sont préservés ;
21. le catalogue Odoo est utilisé ;
22. la compatibilité équipement fonctionne ;
23. les sélections sont persistées ;
24. les permissions fonctionnent ;
25. le multi-société fonctionne.

---

## Critères d’acceptation techniques

Le Master V2 est accepté si :

- TypeScript strict passe ;
- lint frontend passe ;
- build frontend passe ;
- tests frontend passent ;
- Playwright critique passe ;
- lint Python passe ;
- format Python passe ;
- tests Python passent ;
- tests Odoo passent ;
- tests API passent ;
- tests migrations passent ;
- tests climat passent ;
- tests MERCURE passent ;
- test réel EnergyPlus passe ;
- tests équipement passent ;
- images Docker se construisent ;
- healthchecks passent ;
- installation vierge fonctionne ;
- mise à jour fonctionne ;
- sauvegarde et restauration sont testées ;
- rollback est documenté.

---

## Critères d’acceptation architecture

Le Master V2 est accepté si :

- un seul modèle canonique existe par notion ;
- un seul runner EnergyPlus est actif ;
- un seul constructeur Honeybee est actif ;
- un seul contrat d’entrée simulation est canonique ;
- un seul modèle d’artefact est canonique ;
- un seul modèle de résultat est canonique ;
- un seul endpoint canonique existe par action ;
- les anciens composants sont migrés ou dépréciés ;
- aucune perte de données n’est constatée.

---

## Rapport final obligatoire

### Synthèse

- état initial ;
- état final ;
- GO/NO-GO ;
- P0 ;
- P1 ;
- risques ;
- limites.

### Couverture 01–18

- prompt ;
- statut ;
- preuves ;
- écarts ;
- correctifs.

### Consolidation 05A/15

- composants retenus ;
- composants supprimés ou dépréciés ;
- migrations ;
- tests.

### Modèle canonique

- modèles ;
- relations ;
- contraintes ;
- index ;
- source de vérité.

### API

- endpoints ;
- contrats ;
- versions ;
- idempotence ;
- erreurs.

### Calculs

- climat ;
- MERCURE ;
- Honeybee ;
- EnergyPlus ;
- comparaison ;
- règles finales.

### Frontend

- routes ;
- écrans ;
- hooks ;
- store ;
- responsive ;
- accessibilité.

### Équipements

- catalogue ;
- profils ;
- performance ;
- compatibilité ;
- classement ;
- sélection.

### Sécurité

- authentification ;
- autorisation ;
- SSRF ;
- exécution ;
- secrets ;
- multi-société.

### Tests

- commandes ;
- résultats ;
- codes retour ;
- tests non exécutés ;
- preuves.

### Déploiement

- Docker ;
- VPS ;
- variables ;
- scripts ;
- healthchecks ;
- backup ;
- restore ;
- rollback.

---

## Contrôle final obligatoire

Avant conclusion :

1. vérifier les 18 prompts ;
2. vérifier la matrice complète ;
3. vérifier les dépendances ;
4. vérifier le modèle canonique ;
5. vérifier les noms ;
6. vérifier les migrations ;
7. vérifier Odoo ;
8. vérifier l’API ;
9. vérifier la géolocalisation ;
10. vérifier le climat ;
11. vérifier les scénarios ;
12. vérifier 05A ;
13. vérifier 15 ;
14. vérifier qu’ils partagent le même moteur ;
15. vérifier le frontend ;
16. vérifier les routes ;
17. vérifier les écrans 07–12 ;
18. vérifier la validation ;
19. vérifier les hypothèses ;
20. vérifier le snapshot ;
21. vérifier MERCURE ;
22. vérifier EnergyPlus ;
23. vérifier les jobs ;
24. vérifier les artefacts ;
25. vérifier les résultats ;
26. vérifier la comparaison ;
27. vérifier les révisions ;
28. vérifier le catalogue ;
29. vérifier la compatibilité ;
30. vérifier les sélections ;
31. vérifier OpenAPI ;
32. vérifier l’idempotence ;
33. vérifier les verrous ;
34. vérifier les permissions ;
35. vérifier le multi-société ;
36. vérifier les feature flags ;
37. vérifier la sécurité ;
38. vérifier SSRF ;
39. vérifier les secrets ;
40. vérifier les logs ;
41. vérifier les performances ;
42. vérifier Docker ;
43. vérifier les healthchecks ;
44. vérifier les tests ;
45. vérifier l’installation vierge ;
46. vérifier la mise à jour ;
47. vérifier le backup ;
48. vérifier le restore ;
49. vérifier le rollback ;
50. vérifier la documentation ;
51. vérifier le patch ;
52. vérifier le manifest ;
53. vérifier les known issues ;
54. vérifier qu’aucun snapshot historique n’a été modifié ;
55. vérifier qu’aucun résultat historique n’a été modifié ;
56. vérifier qu’aucune sélection historique n’a été modifiée ;
57. vérifier qu’aucun dataset climatique utilisé n’a été modifié ;
58. vérifier qu’aucun fichier n’a été supprimé sans justification ;
59. vérifier qu’aucun doublon architectural actif ne subsiste ;
60. décider GO ou NO-GO uniquement sur preuves réelles.

---

## Limites du Master V2

Ce Master V2 consolide GreenCube Cooling depuis le socle Odoo jusqu’à la sélection technique du système de refroidissement.

Il ne finalise pas automatiquement :

```text
devis commercial complet
rapport PDF commercial définitif
paiement
facturation
commande fournisseur
planification d’installation
commissioning
maintenance
```

Ces fonctions relèvent de futurs lots distincts.

Le résultat attendu est une version intégrale, canonique, sans doublons architecturaux, testée, sécurisée, documentée et livrable de GreenCube Cooling.
