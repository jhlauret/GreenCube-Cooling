# MASTER PROMPT GC-COOLING

## Audit, assemblage, implémentation complète et livraison du configurateur GreenCube Cooling

---

## Objectif

Auditer, compléter, consolider et livrer l’ensemble du projet :

```text
GreenCube Cooling
```

Le Master Prompt reprend les exigences des lots :

```text
GC-COOLING-06
GC-COOLING-07
GC-COOLING-08
GC-COOLING-09
GC-COOLING-10
GC-COOLING-11
GC-COOLING-12
GC-COOLING-13
GC-COOLING-14 — MERCURE
GC-COOLING-15 — Honeybee / EnergyPlus
GC-COOLING-16 — Résultats
GC-COOLING-17 — Consolidation MVP
GC-COOLING-18 — Sélection d’équipement
```

L’objectif n’est pas de réécrire aveuglément le projet.

La démarche attendue est :

```text
inspecter l’existant
→ identifier ce qui est déjà implémenté
→ mesurer les écarts
→ préserver les développements récents
→ compléter uniquement ce qui manque
→ corriger les incohérences
→ tester
→ sécuriser
→ documenter
→ produire un patch réintégrable
→ décider GO ou NO-GO
```

Odoo Community 18 reste la source de vérité métier.

Le frontend ne doit jamais devenir la source de vérité des études, calculs, résultats, produits, prix ou sélections.

Aucune réussite de test, migration, sauvegarde, restauration, build ou déploiement ne doit être affirmée sans exécution réelle.

---

## Parcours fonctionnel cible

La version finale doit permettre :

```text
Création d’une étude
→ identification du projet
→ localisation
→ contexte climatique
→ sélection du modèle GreenCube
→ géométrie
→ orientation
→ vitrages
→ protections solaires
→ usage
→ occupation
→ équipements
→ éclairage
→ ventilation
→ infiltration
→ consignes de confort
→ vérification
→ résolution des erreurs
→ confirmation des hypothèses
→ création d’un snapshot immuable
→ calcul rapide MERCURE
→ simulation Honeybee / EnergyPlus si activée
→ comparaison des moteurs
→ recommandation de puissance
→ analyse sensible et latente
→ analyse du confort
→ recommandations d’optimisation
→ sélection d’un équipement compatible
→ enregistrement de la sélection
→ historique et révisions
```

La version finale doit être :

- fonctionnelle ;
- testée ;
- sécurisée ;
- versionnée ;
- documentée ;
- observable ;
- installable ;
- réversible ;
- compatible VPS ;
- réintégrable dans une branche ayant évolué.

---

## Règles de travail impératives

- inspecter avant de modifier ;
- ne jamais supposer qu’un lot précédent a été appliqué ;
- ne jamais supposer qu’un lot précédent est absent ;
- préserver les fonctionnalités existantes ;
- préserver les développements postérieurs ;
- éviter les réécritures globales ;
- éviter les reformatages inutiles ;
- éviter les renommages massifs ;
- ne supprimer aucun fichier sans nécessité démontrée ;
- ne modifier aucun ancien résultat ;
- ne modifier aucun ancien snapshot ;
- ne modifier aucune sélection historique ;
- utiliser des migrations pour les changements de schéma ;
- utiliser des feature flags pour les fonctions optionnelles ;
- ne pas placer de logique thermique officielle dans le frontend ;
- ne jamais exécuter EnergyPlus dans le processus web Odoo ;
- ne jamais coder un catalogue produit en dur ;
- ne jamais inventer de caractéristiques techniques absentes ;
- ne jamais exposer de secret ;
- ne jamais déclarer un test réussi sans preuve.

---

## Stack cible

### Frontend

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

### Backend métier

```text
Odoo Community 18
Python
PostgreSQL
```

### Calculs avancés

```text
Honeybee
Ladybug Tools
EnergyPlus
worker Python
Redis ou file existante
Docker
stockage objet ou système existant
```

### Catalogue produit

Réutiliser en priorité :

```text
product.template
product.product
product.category
product.attribute
product.attribute.value
product.supplierinfo
```

---

## Phase 0 — État initial obligatoire

Avant toute modification, produire un rapport d’état initial.

### Arborescence

Inspecter :

- racine du dépôt ;
- addons Odoo ;
- frontend ;
- workers ;
- scripts ;
- Docker ;
- migrations ;
- tests ;
- documentation ;
- OpenAPI ;
- CI/CD ;
- fichiers d’environnement.

### Versions

Identifier les versions réellement présentes de :

- Odoo ;
- Python ;
- Node.js ;
- React ;
- TypeScript ;
- Vite ;
- PostgreSQL ;
- Redis ;
- Honeybee ;
- Ladybug Tools ;
- EnergyPlus ;
- Docker ;
- images déployées.

### Modules

Identifier :

- modules GreenCube ;
- modules Cooling ;
- modèles ;
- contrôleurs ;
- services ;
- hooks ;
- routes ;
- composants ;
- workers ;
- tests ;
- scripts.

### État Git

Si disponible, analyser :

- branche ;
- workspace ;
- fichiers modifiés ;
- fichiers non suivis ;
- derniers commits ;
- conflits potentiels ;
- patches appliqués.

Ne pas écraser un travail non commité.

### Diagnostic initial

Exécuter si possible :

- installation des dépendances ;
- lint ;
- TypeScript ;
- tests ;
- build ;
- tests Python ;
- tests Odoo ;
- healthchecks.

Conserver les résultats initiaux, y compris les erreurs.

---

## Matrice d’implémentation GC-COOLING-06 à 18

Créer :

```text
docs/cooling_master_implementation_matrix.md
```

Pour chaque exigence :

```text
requirement_id
source_prompt
domain
requirement
current_status
implementation_location
test_location
gap
priority
planned_action
final_status
evidence
```

Statuts :

```text
implemented
partially_implemented
missing
conflicting
obsolete
not_applicable
blocked
```

Priorités :

```text
P0
P1
P2
P3
```

Ne pas commencer les corrections avant d’avoir établi cette matrice.

---

## Architecture fonctionnelle attendue

L’application doit couvrir :

```text
Study Management
Location
Climate
GreenCube Model
Geometry
Orientation
Glazing
Solar Protection
Usage
Occupancy
Equipment Loads
Lighting
Ventilation
Infiltration
Comfort
Review
Validation
Assumptions
Snapshot
MERCURE
EnergyPlus
Calculation Jobs
Results
Result Comparison
Optimization
Equipment Catalog
Equipment Compatibility
Equipment Selection
Revision History
Audit
```

Chaque domaine doit disposer de :

- modèle métier ;
- API ;
- permissions ;
- validation ;
- frontend ;
- tests ;
- documentation.

---

## Routes frontend attendues

Vérifier ou implémenter :

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

Routes secondaires possibles :

```text
/cooling/studies/:studyId/results/:resultId
/cooling/studies/:studyId/calculations/:jobId
/cooling/studies/:studyId/equipment-selection/:productId
/cooling/studies/:studyId/equipment-comparison
```

Vérifier :

- deep links ;
- rafraîchissement direct ;
- guards ;
- permissions ;
- étude inconnue ;
- étude archivée ;
- résultat obsolète ;
- navigation mobile ;
- retour arrière ;
- erreurs réseau.

---

## Design système

Respecter :

```text
fond blanc
typographie noire
accents verts
design lean
cartes simples
navigation claire
faible bruit visuel
hiérarchie forte
```

Éviter :

- duplication des boutons ;
- variations arbitraires de couleurs ;
- densité excessive ;
- modales inutiles ;
- textes techniques non expliqués ;
- tableaux illisibles sur mobile.

---

## Stepper et état de préparation

Le stepper doit utiliser le statut backend.

Il doit indiquer :

- étape courante ;
- étape complète ;
- étape incomplète ;
- étape en erreur ;
- étude prête ;
- calcul disponible ;
- résultat obsolète ;
- sélection d’équipement disponible.

Le frontend ne doit pas reconstruire seul les règles de complétude.

---

## Modèles Odoo attendus

Inspecter, créer ou compléter :

```text
greencube.cooling.study
greencube.cooling.study.revision
greencube.cooling.scenario
greencube.cooling.assumption
greencube.cooling.validation.issue
greencube.cooling.calculation.snapshot
greencube.cooling.calculation.job
greencube.cooling.result
greencube.cooling.result.scenario
greencube.cooling.result.line
greencube.cooling.result.comparison
greencube.cooling.simulation.artifact
greencube.cooling.equipment.profile
greencube.cooling.equipment.performance.point
greencube.cooling.equipment.rule
greencube.cooling.equipment.compatibility
greencube.cooling.equipment.selection
greencube.cooling.equipment.comparison
```

Pour chaque modèle, vérifier :

- relations ;
- contraintes SQL ;
- contraintes Python ;
- index ;
- `company_id` ;
- règles d’accès ;
- archivage ;
- immuabilité ;
- tracking ;
- suppression ;
- performances.

---

## Sources de vérité et immuabilité

Garantir :

```text
Odoo
= source de vérité métier

snapshot
= image immuable des données d’entrée

calculation result
= résultat immuable

equipment selection
= sélection historique immuable

frontend
= interface, validation ergonomique et cache

worker
= exécution technique

storage
= artefacts techniques
```

Toute modification après calcul doit suivre :

```text
nouvelle révision
→ validation
→ nouveau snapshot
→ nouveau calcul
→ nouvelle sélection
```

---

## Gestion des révisions

Vérifier ou implémenter :

- création d’une révision ;
- duplication contrôlée ;
- lien parent/enfant ;
- auteur ;
- date ;
- motif ;
- statut ;
- ancien résultat obsolète ;
- ancienne sélection remplacée ;
- historique conservé.

Une révision ne doit jamais modifier l’étude historique.

---

## Validation et écran de revue

L’écran de revue doit afficher :

- complétude ;
- erreurs bloquantes ;
- avertissements ;
- informations ;
- hypothèses ;
- provenance ;
- confiance ;
- scénarios ;
- payload envoyé au moteur.

Gravités :

```text
error
warning
info
```

Une erreur bloquante doit empêcher la création du snapshot.

---

## Hypothèses

Chaque hypothèse doit contenir :

```text
code
label
value
unit
source
version
confidence
impact
confirmation_required
confirmed_by
confirmed_at
```

La confirmation doit être :

- auditée ;
- versionnée ;
- liée à l’étude ;
- liée à la révision ;
- incluse dans le snapshot.

---

## Snapshot immuable

Le snapshot doit contenir :

- étude ;
- révision ;
- utilisateur ;
- société ;
- date ;
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
- scénarios ;
- hypothèses ;
- référentiels ;
- versions ;
- empreinte cryptographique.

Il doit être :

- sérialisable ;
- reproductible ;
- validé ;
- immuable ;
- compatible MERCURE et EnergyPlus.

---

## MERCURE

Le moteur rapide doit calculer :

```text
transmission murs
transmission toiture
transmission plancher
transmission portes
transmission vitrages
ponts thermiques
apports solaires
occupants sensibles
occupants latents
équipements sensibles
équipements latents
éclairage
ventilateurs
ventilation sensible
ventilation latente
infiltration sensible
infiltration latente
ouvertures
autres charges
```

Résultats :

```text
charge sensible
charge latente
charge totale
SHR
marge
puissance recommandée
W
kW
BTU/h
scénario dimensionnant
confiance
avertissements
trace
version
```

Le cœur mathématique doit rester indépendant de l’ORM.

---

## Équations principales MERCURE

### Transmission

```text
Q = U × A × ΔT
```

### Ventilation sensible

```text
Q = ρ × cp × débit × ΔT
```

### Charge latente

```text
Q = débit massique
× différence de ratio d’humidité
× chaleur latente
```

### Solaire vitrage

```text
Q =
surface
× rayonnement
× facteur solaire
× protection
× masque
```

### Puissance recommandée

```text
recommended_capacity =
total_load
× (1 + margin_fraction)
```

Toutes les constantes, unités et méthodes doivent être versionnées.

---

## Scénarios climatiques

Supporter :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Chaque scénario doit contenir :

- température extérieure ;
- humidité ;
- rayonnement ;
- vent ;
- consigne intérieure ;
- température du sol si nécessaire ;
- période ;
- source ;
- version.

---

## Honeybee / EnergyPlus

Chaîne attendue :

```text
snapshot
→ modèle Honeybee
→ modèle EnergyPlus
→ météo
→ exécution isolée
→ parsing
→ normalisation
→ comparaison MERCURE
```

EnergyPlus doit être exécuté :

- hors processus web ;
- dans un worker ;
- idéalement dans un conteneur ;
- avec timeout ;
- avec limites CPU et mémoire ;
- sans commande shell libre ;
- avec nettoyage.

---

## Modèle Honeybee

Le mapping doit couvrir :

- géométrie ;
- zones ;
- frontières ;
- constructions ;
- vitrages ;
- ombrages ;
- calendriers ;
- personnes ;
- équipements ;
- éclairage ;
- ventilation ;
- infiltration ;
- consignes ;
- HVAC idéal ;
- météo.

Pour le MVP :

```text
1 GreenCube = 1 zone thermique
```

L’architecture doit rester multi-zone compatible.

---

## Fichiers météo

Supporter :

```text
EPW
```

Vérifier :

- format ;
- localisation ;
- altitude ;
- fuseau ;
- nombre d’heures ;
- checksum ;
- source ;
- version.

En cas de weather morphing :

- conserver la source ;
- conserver la méthode ;
- conserver les deltas ;
- créer un checksum ;
- signaler le caractère synthétique.

---

## Jobs de calcul

Statuts possibles :

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

Champs importants :

```text
job_id
study_id
snapshot_id
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

## Worker

Le worker doit :

1. verrouiller le job ;
2. vérifier permissions et snapshot ;
3. vérifier l’idempotence ;
4. créer un workspace ;
5. générer le modèle ;
6. préparer la météo ;
7. lancer le calcul ;
8. maintenir le heartbeat ;
9. parser les résultats ;
10. normaliser ;
11. comparer ;
12. persister ;
13. stocker les artefacts ;
14. nettoyer ;
15. clôturer le job.

---

## Résultats normalisés

Le résultat doit fournir :

```text
engine
engine_version
scenario
sensible_load_w
latent_load_w
total_load_w
margin_w
recommended_capacity_w
recommended_capacity_kw
recommended_capacity_btu_h
peak_timestamp
annual_energy_kwh
max_indoor_temperature_c
max_indoor_humidity_percent
hours_above_setpoint
confidence_score
breakdown
warnings
assumptions
```

---

## Comparaison MERCURE / EnergyPlus

Comparer :

- sensible ;
- latent ;
- total ;
- recommandation ;
- scénario dimensionnant ;
- contributions principales.

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

Modes de décision possibles :

```text
energyplus_preferred
maximum_of_both
engineer_review
mercure_fallback
```

---

## Écran de résultats

Afficher :

- statut du job ;
- progression ;
- erreurs ;
- puissance recommandée ;
- charge brute ;
- marge ;
- W, kW, BTU/h ;
- sensible ;
- latent ;
- total ;
- SHR ;
- scénario dimensionnant ;
- moteur retenu ;
- scénarios ;
- répartition des charges ;
- comparaison MERCURE/EnergyPlus ;
- confiance ;
- avertissements ;
- hypothèses ;
- recommandations ;
- confort ;
- historique ;
- artefacts pour les rôles autorisés.

Le frontend ne doit jamais recalculer les résultats officiels.

---

## Sélection d’équipement

La sélection doit utiliser le résultat actif.

Prérequis :

- résultat courant ;
- puissance recommandée ;
- aucune revue bloquante ;
- catalogue disponible ;
- données produit suffisantes.

Route :

```text
/cooling/studies/:studyId/equipment-selection
```

---

## Catalogue produit

Le catalogue doit utiliser Odoo.

Caractéristiques minimales :

```text
type
capacité nominale
capacité minimale
capacité maximale
capacité aux conditions de calcul
puissance électrique
EER
SEER
capacité sensible
capacité latente
SHR
déshumidification
débit d’air
bruit
plage extérieure
alimentation
courant
dimensions
poids
condensats
fluide
connectivité
garantie
qualité des données
provenance
```

---

## Moteur de compatibilité produit

Comparer :

```text
besoin thermique
↔ capacité produit
↔ conditions climatiques
↔ sensible
↔ latent
↔ modulation
↔ alimentation
↔ bruit
↔ installation
```

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

## Règles de compatibilité critiques

Vérifier :

- capacité à la température de calcul ;
- capacité minimale ;
- surdimensionnement ;
- sensible ;
- latent ;
- SHR ;
- température extérieure maximale ;
- alimentation ;
- phases ;
- courant ;
- bruit ;
- condensats ;
- dimensions ;
- unité extérieure ;
- fluide autorisé ;
- disponibilité ;
- qualité des données.

---

## Dégradation à haute température

Utiliser si disponible :

- courbe de capacité ;
- points de performance ;
- capacité à 35 °C ;
- capacité à 40 °C ;
- capacité à 45 °C.

Créer ou réutiliser :

```text
greencube.cooling.equipment.performance.point
```

Ne jamais extrapoler silencieusement.

---

## Classement des produits

Facteurs possibles :

```text
technical_compatibility
capacity_match
modulation_quality
sensible_match
latent_match
high_temperature_performance
energy_efficiency
noise
installation_fit
electrical_fit
data_quality
availability
price
maintenance
connectivity
```

Les pondérations doivent être :

- versionnées ;
- administrables ;
- explicables ;
- adaptées à l’usage.

---

## Comparaison produit

Comparer 2 à 4 produits selon :

- capacité ;
- modulation ;
- sensible ;
- latent ;
- EER ;
- SEER ;
- puissance électrique ;
- bruit ;
- température maximale ;
- dimensions ;
- condensats ;
- alimentation ;
- connectivité ;
- garantie ;
- prix ;
- disponibilité ;
- score ;
- réserves.

---

## Sélection persistée

Une sélection doit rester liée à :

- étude ;
- révision ;
- snapshot ;
- résultat ;
- produit ;
- variante ;
- profil technique ;
- version de règle ;
- version de données ;
- prix ;
- utilisateur ;
- date.

Statuts possibles :

```text
draft
selected
validated
superseded
cancelled
quoted
```

Une nouvelle sélection ne doit pas supprimer l’ancienne.

---

## API cible

### Études

```text
GET /api/v1/greencube/cooling/studies
POST /api/v1/greencube/cooling/studies
GET /api/v1/greencube/cooling/studies/<id>
PATCH /api/v1/greencube/cooling/studies/<id>
```

### Révisions

```text
POST /api/v1/greencube/cooling/studies/<id>/revisions
```

### Validation

```text
POST /api/v1/greencube/cooling/studies/<id>/validate
```

### Snapshot

```text
POST /api/v1/greencube/cooling/studies/<id>/snapshots
```

### Calcul

```text
POST /api/v1/greencube/cooling/studies/<id>/calculations
GET /api/v1/greencube/cooling/calculations/<job_id>
POST /api/v1/greencube/cooling/calculations/<job_id>/cancel
```

### Résultats

```text
GET /api/v1/greencube/cooling/results/<result_id>
GET /api/v1/greencube/cooling/studies/<study_id>/results
GET /api/v1/greencube/cooling/results/<result_id>/comparison
```

### Artefacts

```text
GET /api/v1/greencube/cooling/calculations/<job_id>/artifacts
```

### Équipements

```text
GET /api/v1/greencube/cooling/equipment-catalog
POST /api/v1/greencube/cooling/studies/<id>/equipment-recommendations
GET /api/v1/greencube/cooling/equipment/<product_id>
GET /api/v1/greencube/cooling/equipment/<product_id>/compatibility
POST /api/v1/greencube/cooling/equipment/compare
POST /api/v1/greencube/cooling/studies/<id>/equipment-selections
GET /api/v1/greencube/cooling/studies/<id>/equipment-selections
```

---

## OpenAPI

Créer ou compléter :

```text
openapi/cooling.yaml
```

Inclure :

- schémas ;
- enums ;
- unités ;
- exemples ;
- erreurs ;
- pagination ;
- permissions ;
- idempotence ;
- versioning ;
- statuts.

Aligner les types TypeScript sur ce contrat.

---

## Format d’erreur standard

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

Ne jamais exposer :

- stack trace ;
- SQL ;
- chemin local ;
- secret ;
- configuration interne.

---

## Idempotence

Utiliser `Idempotency-Key` pour :

- snapshot ;
- calcul ;
- relance ;
- annulation si nécessaire ;
- sélection d’équipement ;
- création de révision si pertinente.

Tester :

- double clic ;
- retry réseau ;
- timeout client ;
- réponse perdue ;
- deux onglets.

---

## Verrouillage optimiste

Utiliser :

```text
version
etag
updated_at
```

ou équivalent.

Tester les conflits sur :

- étude ;
- révision ;
- hypothèses ;
- snapshot ;
- résultat ;
- produit ;
- sélection.

Aucun écrasement silencieux ne doit être possible.

---

## Permissions

Rôles possibles :

```text
cooling_user
cooling_engineer
cooling_manager
cooling_admin
```

Vérifier les droits sur :

- études ;
- révisions ;
- validation ;
- snapshot ;
- calcul ;
- résultats ;
- traces ;
- artefacts ;
- catalogue ;
- règles ;
- sélection ;
- configuration ;
- archivage.

---

## Multi-société

Chaque objet métier pertinent doit avoir :

```text
company_id
```

Tester :

- lecture inter-sociétés ;
- modification inter-sociétés ;
- calcul inter-sociétés ;
- artefacts inter-sociétés ;
- catalogue partagé ou spécifique ;
- prix ;
- fournisseurs ;
- sélections.

---

## Feature flags

Recenser, créer ou aligner :

```text
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

Pour chaque flag :

- valeur par défaut ;
- environnement ;
- dépendances ;
- comportement désactivé ;
- permissions ;
- test.

---

## Query hooks frontend

Créer ou compléter :

```text
useCoolingStudy
useCoolingStudySection
useCoolingValidation
useCoolingSnapshot
useCoolingCalculationJob
useCoolingResult
useCoolingStudyResults
useCoolingResultComparison
useCoolingCalculationArtifacts
useRerunCoolingCalculation
useCoolingEquipmentRecommendations
useCoolingEquipmentDetail
useCoolingEquipmentCompatibility
useCoolingEquipmentComparison
useCoolingEquipmentSelections
useSelectCoolingEquipment
```

Le cache doit être géré avec TanStack Query.

---

## Store frontend

Zustand doit contenir uniquement l’état temporaire d’interface.

État acceptable :

```text
étape affichée
sections ouvertes
filtres
produits comparés
onglet sélectionné
drawer ouvert
```

Ne pas y stocker comme source primaire :

- étude ;
- snapshot ;
- résultat ;
- catalogue ;
- prix ;
- sélection.

---

## Formulaires frontend

Utiliser React Hook Form et Zod.

Vérifier :

- validation client ;
- validation serveur ;
- erreurs de champ ;
- erreurs globales ;
- sauvegarde ;
- autosave si prévu ;
- conflit de version ;
- valeurs par défaut ;
- unités ;
- accessibilité.

Les résultats doivent rester en lecture seule.

---

## Accessibilité

Viser WCAG 2.1 AA.

Vérifier :

- navigation clavier ;
- focus visible ;
- focus après erreur ;
- labels ;
- messages associés ;
- tableaux ;
- alternatives aux graphiques ;
- dialogues ;
- accordéons ;
- annonces de statut ;
- contraste ;
- unités ;
- zoom 200 % ;
- responsive.

Créer ou compléter :

```text
docs/cooling_accessibility_audit.md
```

---

## Responsive

Tester au minimum :

```text
360 × 800
390 × 844
768 × 1024
1024 × 768
1366 × 768
1440 × 900
1920 × 1080
```

Vérifier :

- débordements ;
- cartes ;
- tableaux ;
- graphiques ;
- formulaires ;
- drawers ;
- dialogues ;
- footer sticky ;
- clavier mobile.

---

## Sécurité

### Authentification

- routes privées ;
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
- multi-société ;
- rôles ;
- artefacts ;
- traces ;
- catalogue ;
- prix.

### Entrées

- Zod ;
- validation Python ;
- longueurs ;
- nombres ;
- NaN ;
- infinis ;
- enums ;
- dates ;
- payloads volumineux ;
- injections.

### Fichiers

- path traversal ;
- MIME ;
- extensions ;
- tailles ;
- checksum ;
- stockage privé ;
- URLs temporaires.

### Exécution

- `shell=False` ;
- commandes autorisées ;
- utilisateur non root ;
- timeout ;
- CPU ;
- mémoire ;
- nettoyage.

### Secrets

- dépôt ;
- `.env` ;
- logs ;
- Docker ;
- CI ;
- tests ;
- documentation.

---

## Audits de dépendances

Exécuter si disponibles :

```text
npm audit
pip-audit
scanner d’image Docker
scanner de secrets
scanner SCA
```

Classer :

```text
critical
high
medium
low
```

Aucune vulnérabilité critique ne doit rester ouverte pour un GO.

---

## Logs et audit

Logs structurés :

```text
request_id
study_id
revision_id
snapshot_id
job_id
result_id
selection_id
company_id
user_id
engine
status
duration_ms
error_code
```

Ne pas journaliser :

- secrets ;
- tokens ;
- payloads complets sensibles ;
- documents complets ;
- URLs signées ;
- SQL brut en production.

---

## Artefacts

Gérer :

```text
snapshot_json
honeybee_json
energyplus_idf
energyplus_epjson
weather_epw
energyplus_sql
energyplus_err
energyplus_eio
energyplus_html
results_json
logs
```

Conserver :

- type ;
- stockage ;
- checksum ;
- taille ;
- société ;
- accès ;
- date ;
- rétention.

---

## Politique de rétention

Définir une politique pour :

- fichiers intermédiaires ;
- logs ;
- artefacts ;
- jobs ;
- résultats ;
- snapshots ;
- audits ;
- sélections.

Les snapshots, résultats et sélections métier ne doivent pas être supprimés arbitrairement.

---

## Performance

### Frontend

Mesurer :

- bundle ;
- chargement ;
- requêtes ;
- re-renders ;
- graphiques ;
- polling ;
- cache ;
- lazy loading.

### Backend

Mesurer :

- temps API ;
- SQL ;
- N+1 ;
- index ;
- sérialisation ;
- taille des snapshots ;
- MERCURE ;
- résultats ;
- catalogue ;
- classement.

### Simulation

Mesurer :

- durée par scénario ;
- CPU ;
- mémoire ;
- disque ;
- nombre de jobs simultanés.

---

## Limite de concurrence

Configurer :

```text
max_concurrent_energyplus_jobs
```

Tester :

- file pleine ;
- plusieurs sociétés ;
- worker arrêté ;
- job bloqué ;
- timeout ;
- annulation ;
- retry.

---

## Migrations

Vérifier :

- installation base vierge ;
- mise à jour base existante ;
- données préservées ;
- index ;
- contraintes ;
- référentiels ;
- idempotence ;
- rollback documenté.

Créer si nécessaire :

```text
migrations/<version>/pre-migration.py
migrations/<version>/post-migration.py
```

Ne pas réécrire une migration historique livrée.

---

## Données de démonstration

Prévoir :

```text
Studio standard
Bureau vitré ouest
Local technique
Canicule prolongée
GreenCube performant
Faible confiance
Forte charge latente
Aucun produit compatible
```

Les données doivent être non sensibles et clairement identifiées.

---

## Tests frontend

Tester :

- formulaires ;
- validations ;
- stepper ;
- revue ;
- statuts de job ;
- résultats ;
- W/kW/BTU/h ;
- sensible ;
- latent ;
- SHR ;
- comparaison ;
- avertissements ;
- sélection produit ;
- filtres ;
- tri ;
- compatibilité ;
- dialogue de sélection.

---

## Tests backend

Tester :

- validations ;
- snapshots ;
- idempotence ;
- conflits ;
- MERCURE ;
- psychrométrie ;
- scénarios ;
- jobs ;
- parsing EnergyPlus ;
- comparaison ;
- catalogue ;
- compatibilité produit ;
- classement ;
- sélection ;
- permissions ;
- multi-société.

---

## Tests MERCURE

Cas minimums :

```text
Studio standard
Bureau vitré ouest
Local technique
Canicule prolongée
GreenCube performant
Faible confiance
```

Propriétés monotones :

- plus de vitrage ne réduit pas le solaire ;
- plus d’occupation ne réduit pas les gains ;
- plus d’air chaud ne réduit pas la charge ;
- meilleure récupération ne doit pas augmenter la charge ;
- consigne plus élevée ne doit pas augmenter la charge.

---

## Tests EnergyPlus

Tester :

- modèle simple ;
- géométrie ;
- constructions ;
- vitrage ;
- météo ;
- exécution ;
- timeout ;
- erreur fatale ;
- parsing ;
- artefacts ;
- nettoyage ;
- comparaison MERCURE.

Un test minimal doit prouver que l’installation EnergyPlus fonctionne réellement.

---

## Tests de compatibilité produit

Tester :

- capacité insuffisante ;
- capacité correcte ;
- surdimensionnement ;
- haute température ;
- sensible insuffisant ;
- latent insuffisant ;
- monophasé ;
- triphasé ;
- bruit excessif ;
- condensats ;
- dimensions ;
- données manquantes ;
- produit archivé ;
- produit conditionnel ;
- produit recommandé.

---

## Tests Playwright

Créer au minimum :

1. création complète d’une étude ;
2. validation avec erreur bloquante ;
3. confirmation d’hypothèse ;
4. snapshot ;
5. calcul MERCURE ;
6. calcul BOTH ;
7. suivi d’un job ;
8. EnergyPlus échoué avec fallback ;
9. comparaison des résultats ;
10. création de révision ;
11. sélection d’un équipement ;
12. produit incompatible ;
13. aucun produit compatible ;
14. résultat obsolète ;
15. accès inter-sociétés interdit ;
16. parcours mobile.

---

## Tests de panne

Tester :

- PostgreSQL indisponible ;
- Redis indisponible ;
- worker indisponible ;
- stockage indisponible ;
- météo absente ;
- EnergyPlus indisponible ;
- processus tué ;
- job bloqué ;
- timeout ;
- réponse réseau interrompue ;
- prix indisponible ;
- catalogue vide.

Le système doit échouer proprement.

---

## Récupération des jobs bloqués

Créer ou vérifier :

```text
cooling_recover_stalled_jobs
```

La commande doit :

- identifier les heartbeats expirés ;
- vérifier le worker ;
- éviter les doublons ;
- marquer ou relancer ;
- auditer l’action.

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

Créer ou compléter :

```text
docker-compose.yml
docker-compose.production.yml
Dockerfile.frontend
Dockerfile.odoo
Dockerfile.simulation
```

Ne pas ajouter de service inutile.

---

## Variables d’environnement

Créer ou compléter :

```text
.env.example
```

Documenter :

```text
nom
obligatoire
défaut
description
secret
service
```

Exemples :

```text
ODOO_DB_HOST
ODOO_DB_USER
ODOO_DB_PASSWORD
REDIS_URL
ENERGYPLUS_ENABLED
ENERGYPLUS_VERSION
SIMULATION_TIMEOUT_SECONDS
MAX_CONCURRENT_ENERGYPLUS_JOBS
COOLING_STORAGE_ENDPOINT
COOLING_STORAGE_BUCKET
```

Aucune vraie valeur secrète ne doit être incluse.

---

## Scripts

Créer ou compléter :

```text
scripts/install.sh
scripts/update.sh
scripts/rollback.sh
scripts/healthcheck.sh
scripts/backup.sh
scripts/restore.sh
scripts/smoke_test_cooling.sh
```

Les scripts Bash doivent utiliser si possible :

```text
set -euo pipefail
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
- MERCURE ;
- EnergyPlus ;
- écriture temporaire.

Distinguer si possible :

```text
liveness
readiness
```

---

## Sauvegarde et restauration

Documenter et tester :

- PostgreSQL ;
- filestore Odoo ;
- stockage objet ;
- configurations ;
- météo ;
- paramètres ;
- artefacts critiques.

Créer ou compléter :

```text
docs/cooling_backup_restore.md
```

Tester une restauration hors production.

---

## CI

Le pipeline doit exécuter selon les composants présents :

```text
lint frontend
TypeScript strict
tests frontend
build frontend
lint Python
format check Python
type check Python
tests Python
tests Odoo
tests API
tests migrations
tests sécurité
build Docker
smoke tests
```

Les gates critiques doivent bloquer la livraison.

---

## Documentation obligatoire

Créer ou compléter :

```text
README_GC_COOLING_MASTER.md
CHANGELOG_GC_COOLING.md
docs/cooling_master_implementation_matrix.md
docs/cooling_architecture.md
docs/cooling_state_machine.md
docs/cooling_frontend_api_mapping.md
docs/cooling_mercure_equations.md
docs/cooling_energyplus_architecture.md
docs/cooling_equipment_compatibility_matrix.md
docs/cooling_accessibility_audit.md
docs/cooling_security_audit.md
docs/cooling_backup_restore.md
docs/cooling_deployment_vps.md
docs/cooling_user_guide.md
docs/cooling_odoo_admin_guide.md
docs/cooling_developer_guide.md
docs/cooling_operations_runbook.md
docs/cooling_troubleshooting.md
docs/cooling_known_issues.md
docs/cooling_final_acceptance_report.md
```

Ne pas dupliquer une documentation existante équivalente.

---

## Packaging final

Produire une livraison structurée :

```text
GC_COOLING_MASTER_RELEASE/
├── addons/
├── frontend/
├── workers/
├── deployment/
├── scripts/
├── docs/
├── openapi/
├── migrations/
├── tests/
├── README_GC_COOLING_MASTER.md
├── CHANGELOG_GC_COOLING.md
└── MANIFEST_GC_COOLING_MASTER.txt
```

---

## Patch réintégrable

Produire :

```text
PATCH_GC_COOLING_MASTER.diff
PATCH_GC_COOLING_MASTER_README.md
MANIFEST_GC_COOLING_MASTER.txt
```

Le patch doit :

- rester limité à GreenCube Cooling ;
- éviter le formatage global ;
- éviter les suppressions ;
- éviter les fichiers générés ;
- documenter les conflits ;
- inclure les migrations ;
- inclure les dépendances ;
- inclure les tests ;
- inclure le rollback.

---

## README du patch

Documenter :

1. branche source ;
2. branche cible ;
3. prérequis ;
4. sauvegarde ;
5. application du patch ;
6. conflits possibles ;
7. dépendances ;
8. migrations ;
9. build ;
10. tests ;
11. smoke tests ;
12. rollback ;
13. exclusions ;
14. limitations connues.

Ne pas livrer uniquement un ZIP à écraser.

---

## Changelog

Créer ou compléter :

```text
CHANGELOG_GC_COOLING.md
```

Sections :

```text
Added
Changed
Fixed
Security
Deprecated
Removed
Known limitations
```

Ne documenter que les changements réellement effectués.

---

## Known issues

Créer :

```text
docs/cooling_known_issues.md
```

Pour chaque anomalie :

```text
id
severity
description
impact
workaround
future_action
release_decision
```

---

## Recette finale

Créer :

```text
docs/cooling_final_acceptance_report.md
```

Inclure :

- environnement ;
- versions ;
- date ;
- commandes ;
- codes retour ;
- durées ;
- tests réussis ;
- tests échoués ;
- tests non exécutés ;
- anomalies ;
- risques ;
- décision finale.

---

## Gate GO / NO-GO

Le GO est possible uniquement si :

```text
0 P0 ouverts
0 P1 ouverts sur le parcours principal
0 vulnérabilité critique ouverte
0 secret exposé
migrations validées
installation vierge validée
mise à jour validée
smoke tests validés
parcours principal validé
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

Le Master Prompt est accepté si :

- une étude peut être créée ;
- les étapes GC-COOLING-06 à 12 fonctionnent ;
- la validation fonctionne ;
- les erreurs bloquent correctement ;
- les hypothèses sont confirmables ;
- le snapshot est créé ;
- le snapshot est immuable ;
- MERCURE fonctionne ;
- EnergyPlus fonctionne si activé ;
- les jobs sont suivis ;
- le fallback MERCURE fonctionne ;
- les résultats sont affichés ;
- sensible, latent, total et SHR sont disponibles ;
- les scénarios sont comparés ;
- la confiance est affichée ;
- les avertissements sont affichés ;
- les recommandations sont affichées ;
- les révisions fonctionnent ;
- les historiques sont préservés ;
- la sélection d’équipement fonctionne ;
- les incompatibilités sont expliquées ;
- la sélection est persistée ;
- les permissions fonctionnent ;
- le multi-société fonctionne ;
- les feature flags fonctionnent.

---

## Critères d’acceptation techniques

Le Master Prompt est accepté si :

- TypeScript strict passe ;
- le lint frontend passe ;
- le build frontend passe ;
- les tests frontend passent ;
- Playwright passe ;
- le lint Python passe ;
- le formatage Python passe ;
- le contrôle de types Python passe ;
- les tests Python passent ;
- les tests Odoo passent ;
- les tests API passent ;
- les migrations passent ;
- les tests MERCURE passent ;
- les tests EnergyPlus passent si activé ;
- les tests produit passent ;
- les tests de non-régression passent ;
- les smoke tests passent ;
- les healthchecks passent ;
- les images Docker sont construites ;
- l’installation vierge fonctionne ;
- la mise à jour fonctionne ;
- la sauvegarde est testée ;
- la restauration est testée ;
- le rollback est documenté ;
- aucun fichier n’est supprimé sans justification.

---

## Critères d’acceptation sécurité

Le Master Prompt est accepté si :

- aucune route privée n’est publique ;
- les ACL sont testées ;
- les record rules sont testées ;
- le multi-société est testé ;
- les fichiers sont privés ;
- les artefacts sont protégés ;
- EnergyPlus est isolé ;
- aucune commande dangereuse n’est utilisée ;
- les secrets sont absents ;
- les logs ne contiennent aucun secret ;
- les dépendances critiques sont corrigées ;
- les entrées sont validées ;
- les erreurs internes sont masquées ;
- les téléchargements sont contrôlés ;
- les URLs temporaires expirent ;
- les sauvegardes sont protégées.

---

## Rapport final attendu

### Synthèse

- version ;
- périmètre ;
- état initial ;
- état final ;
- GO/NO-GO ;
- P0 ;
- P1 ;
- risques ;
- limites.

### Matrice

- exigences implémentées ;
- exigences partielles ;
- exigences absentes ;
- exigences non applicables ;
- preuves.

### Architecture

- frontend ;
- Odoo ;
- API ;
- MERCURE ;
- EnergyPlus ;
- workers ;
- stockage ;
- catalogue ;
- sélection ;
- déploiement.

### Modèles Odoo

- créés ;
- modifiés ;
- contraintes ;
- index ;
- ACL ;
- record rules ;
- migrations.

### API

Pour chaque endpoint :

- méthode ;
- contrat ;
- statut ;
- permissions ;
- idempotence ;
- tests.

### Calculs

- MERCURE ;
- équations ;
- scénarios ;
- EnergyPlus ;
- résultats ;
- comparaison ;
- tolérances.

### Produits

- catalogue ;
- caractéristiques ;
- provenance ;
- règles ;
- classement ;
- sélection ;
- historique.

### Frontend

- routes ;
- composants ;
- hooks ;
- cache ;
- store ;
- responsive ;
- accessibilité.

### Tests

- commandes ;
- codes retour ;
- durée ;
- couverture ;
- échecs ;
- tests non exécutés ;
- preuves.

### Sécurité

- authentification ;
- autorisation ;
- multi-société ;
- fichiers ;
- secrets ;
- dépendances ;
- exécution ;
- vulnérabilités.

### Performance

- frontend ;
- API ;
- MERCURE ;
- EnergyPlus ;
- catalogue ;
- base ;
- limites.

### Déploiement

- Docker ;
- VPS ;
- variables ;
- scripts ;
- healthchecks ;
- monitoring ;
- sauvegarde ;
- restauration ;
- rollback.

### Livraison

- patch ;
- manifest ;
- checksums ;
- migrations ;
- dépendances ;
- instructions ;
- exclusions.

### Known issues

- ouverts ;
- gravité ;
- impact ;
- contournement ;
- décision.

---

## Contrôle final obligatoire

Avant conclusion :

1. vérifier l’état Git ;
2. vérifier l’arborescence ;
3. vérifier la matrice GC-COOLING-06 à 18 ;
4. vérifier les routes ;
5. vérifier le stepper ;
6. vérifier les modèles Odoo ;
7. vérifier les statuts ;
8. vérifier les transitions ;
9. vérifier les révisions ;
10. vérifier la validation ;
11. vérifier les hypothèses ;
12. vérifier le snapshot ;
13. vérifier l’immuabilité ;
14. vérifier MERCURE ;
15. vérifier les unités ;
16. vérifier les scénarios ;
17. vérifier Honeybee ;
18. vérifier EnergyPlus ;
19. vérifier les jobs ;
20. vérifier les heartbeats ;
21. vérifier les timeouts ;
22. vérifier le parsing ;
23. vérifier les résultats ;
24. vérifier la comparaison ;
25. vérifier les artefacts ;
26. vérifier l’écran de résultats ;
27. vérifier le catalogue ;
28. vérifier la compatibilité produit ;
29. vérifier la haute température ;
30. vérifier sensible et latent ;
31. vérifier l’électricité ;
32. vérifier le bruit ;
33. vérifier les condensats ;
34. vérifier le classement ;
35. vérifier la sélection ;
36. vérifier l’historique ;
37. vérifier les API ;
38. vérifier OpenAPI ;
39. vérifier l’idempotence ;
40. vérifier les conflits ;
41. vérifier les permissions ;
42. vérifier le multi-société ;
43. vérifier les feature flags ;
44. vérifier l’accessibilité ;
45. vérifier le responsive ;
46. vérifier les erreurs ;
47. vérifier les logs ;
48. vérifier les secrets ;
49. vérifier les dépendances ;
50. vérifier les performances ;
51. vérifier les migrations ;
52. vérifier l’installation vierge ;
53. vérifier la mise à jour ;
54. vérifier les tests unitaires ;
55. vérifier les tests Odoo ;
56. vérifier les tests API ;
57. vérifier Playwright ;
58. vérifier les tests MERCURE ;
59. vérifier les tests EnergyPlus ;
60. vérifier les tests produit ;
61. vérifier les tests de panne ;
62. vérifier les smoke tests ;
63. vérifier Docker ;
64. vérifier les variables ;
65. vérifier les scripts ;
66. vérifier les healthchecks ;
67. vérifier le monitoring ;
68. vérifier la sauvegarde ;
69. vérifier la restauration ;
70. vérifier le rollback ;
71. vérifier la documentation ;
72. vérifier le changelog ;
73. vérifier les known issues ;
74. vérifier le patch ;
75. vérifier le manifest ;
76. déterminer GO ou NO-GO ;
77. vérifier qu’aucun ancien snapshot n’a été modifié ;
78. vérifier qu’aucun ancien résultat n’a été modifié ;
79. vérifier qu’aucune ancienne sélection n’a été modifiée ;
80. vérifier qu’aucun fichier n’a été supprimé sans justification ;
81. ne jamais prétendre qu’une opération a réussi sans preuve réelle.

---

## Livrables minimums

Produire au minimum :

```text
README_GC_COOLING_MASTER.md
CHANGELOG_GC_COOLING.md
MANIFEST_GC_COOLING_MASTER.txt
PATCH_GC_COOLING_MASTER.diff
PATCH_GC_COOLING_MASTER_README.md
openapi/cooling.yaml
docs/cooling_master_implementation_matrix.md
docs/cooling_architecture.md
docs/cooling_state_machine.md
docs/cooling_frontend_api_mapping.md
docs/cooling_mercure_equations.md
docs/cooling_energyplus_architecture.md
docs/cooling_equipment_compatibility_matrix.md
docs/cooling_accessibility_audit.md
docs/cooling_security_audit.md
docs/cooling_backup_restore.md
docs/cooling_deployment_vps.md
docs/cooling_user_guide.md
docs/cooling_odoo_admin_guide.md
docs/cooling_developer_guide.md
docs/cooling_operations_runbook.md
docs/cooling_troubleshooting.md
docs/cooling_known_issues.md
docs/cooling_final_acceptance_report.md
.env.example
scripts/install.sh
scripts/update.sh
scripts/rollback.sh
scripts/healthcheck.sh
scripts/backup.sh
scripts/restore.sh
scripts/smoke_test_cooling.sh
```

Adapter les chemins à l’architecture réelle sans créer de doublons inutiles.

---

## Limites du Master Prompt

Ce Master Prompt consolide les lots GC-COOLING-06 à GC-COOLING-18.

Il ne doit pas ajouter silencieusement :

- un devis commercial complet ;
- une facturation ;
- un paiement ;
- une commande fournisseur ;
- une planification d’installation ;
- un commissioning ;
- une étude réglementaire officielle ;
- une promesse de conformité réglementaire ;
- un déploiement automatique en production sans instruction explicite.

Le résultat attendu est une version complète, cohérente, testée, sécurisée, documentée et livrable du configurateur GreenCube Cooling, depuis la création de l’étude jusqu’à la sélection technique d’un système de refroidissement.
