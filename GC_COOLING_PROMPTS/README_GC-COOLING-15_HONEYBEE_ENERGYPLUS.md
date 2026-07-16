# GC-COOLING-15 — Orchestration Honeybee / EnergyPlus

## Objectif

Implémenter la chaîne avancée de simulation thermique :

```text
Snapshot GreenCube Cooling
→ validation
→ conversion Honeybee
→ génération EnergyPlus
→ préparation météo
→ exécution isolée
→ suivi du job
→ récupération des sorties
→ normalisation
→ comparaison avec MERCURE
→ persistance Odoo
```

La chaîne doit être :

- asynchrone ;
- isolée ;
- reproductible ;
- versionnée ;
- auditable ;
- idempotente ;
- observable ;
- sécurisée ;
- résistante aux erreurs ;
- compatible avec plusieurs scénarios climatiques ;
- indépendante du frontend ;
- comparable avec MERCURE.

Odoo Community 18 reste la source de vérité métier.

Honeybee et EnergyPlus ne doivent jamais accéder directement à la base Odoo.

---

## Positionnement

Ce lot intervient après :

```text
GC-COOLING-13
→ étude validée
→ snapshot créé
→ statut ready

GC-COOLING-14
→ calcul MERCURE disponible
```

Il doit fournir :

```text
moteur avancé EnergyPlus
+ orchestration des jobs
+ normalisation des résultats
+ comparaison MERCURE / EnergyPlus
```

L’écran frontend complet de résultats appartient au lot suivant.

---

## Architecture recommandée

```text
Frontend React
        │
        ▼
API Odoo / BFF
        │
        ▼
greencube.cooling.calculation.job
        │
        ▼
File ou worker
        │
        ▼
Service Cooling Simulation
├── Snapshot Validator
├── Honeybee Model Builder
├── Weather Resolver
├── EnergyPlus Runner
├── Result Parser
├── Result Normalizer
└── MERCURE Comparator
        │
        ▼
Stockage interne
        │
        ▼
Résultats Odoo
```

Composants possibles :

```text
Odoo Community 18
PostgreSQL
Redis
worker Python
stockage objet S3 ou MinIO
conteneurs Docker isolés
Honeybee
Ladybug Tools
EnergyPlus
```

Réutiliser l’infrastructure existante avant d’ajouter de nouveaux composants.

---

## Structure de code recommandée

```text
greencube_cooling/
├── models/
│   ├── cooling_calculation_job.py
│   ├── cooling_simulation_artifact.py
│   ├── cooling_result.py
│   └── cooling_result_comparison.py
├── services/
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── schemas.py
│   │   ├── validation.py
│   │   ├── honeybee_builder.py
│   │   ├── geometry_builder.py
│   │   ├── construction_builder.py
│   │   ├── aperture_builder.py
│   │   ├── schedule_builder.py
│   │   ├── load_builder.py
│   │   ├── ventilation_builder.py
│   │   ├── infiltration_builder.py
│   │   ├── setpoint_builder.py
│   │   ├── weather_resolver.py
│   │   ├── energyplus_runner.py
│   │   ├── result_parser.py
│   │   ├── result_normalizer.py
│   │   ├── comparison.py
│   │   ├── artifacts.py
│   │   └── errors.py
│   └── mercure/
├── workers/
│   └── cooling_simulation_worker.py
├── tests/
└── docs/
```

Le package technique doit être testable indépendamment de l’ORM lorsque possible.

---

## Vérifications préalables

Avant implémentation :

- inspecter le module `greencube_cooling` ;
- inspecter les modèles de snapshot ;
- inspecter les jobs MERCURE ;
- inspecter les modèles de résultats ;
- inspecter le service climatique ;
- inspecter les fichiers météo ;
- vérifier les versions de Python, Honeybee, Ladybug Tools et EnergyPlus ;
- vérifier la compatibilité de ces versions ;
- vérifier les images Docker ;
- vérifier le système de workers ;
- vérifier Redis ou la file existante ;
- vérifier le stockage de fichiers ;
- vérifier les règles multi-sociétés ;
- vérifier les ACL ;
- vérifier les limites CPU, mémoire et durée ;
- vérifier les feature flags ;
- vérifier les conventions d’unités ;
- vérifier les schémas MERCURE ;
- vérifier les scénarios climatiques ;
- vérifier les mappings Honeybee ;
- exécuter les tests existants ;
- ne supprimer aucun modèle ;
- ne modifier aucun ancien snapshot ;
- ne modifier aucun ancien résultat ;
- ne jamais lancer EnergyPlus dans le processus web Odoo.

---

## Feature flag

Créer ou réutiliser :

```text
enable_energyplus_calculation
```

Quand il est désactivé :

- MERCURE reste utilisable ;
- EnergyPlus n’est pas proposé ;
- les dépendances EnergyPlus ne bloquent pas le workflow ;
- les endpoints retournent une erreur métier claire.

Erreur possible :

```text
CALCULATION_ENGINE_DISABLED
```

---

## Moteurs disponibles

```text
MERCURE
ENERGYPLUS
BOTH
```

Le mode `BOTH` doit :

- lancer MERCURE ;
- lancer EnergyPlus ;
- comparer les deux résultats.

Ne pas relancer MERCURE si un résultat compatible existe déjà pour le même snapshot et la même version.

---

## Snapshot obligatoire

Honeybee/EnergyPlus doit utiliser le même snapshot immuable que MERCURE.

Entrées minimales :

```text
geometry
envelope
glazing
shading
occupancy
equipment
lighting
ventilation
infiltration
comfort
climate_scenarios
assumptions
reference_versions
```

Le service ne doit jamais relire directement l’étude modifiable.

---

## Schéma d’entrée

Créer :

```python
class CoolingSimulationInput:
    snapshot_id: int
    snapshot_hash: str
    study_id: int
    study_version: str
    company_id: int
    requested_engine: str
    scenario_codes: list[str]
    geometry: dict
    envelope: dict
    glazing: dict
    shading: dict
    occupancy: dict
    equipment: dict
    lighting: dict
    ventilation: dict
    infiltration: dict
    comfort: dict
    climate: dict
    assumptions: list[dict]
    reference_versions: dict
```

Utiliser Pydantic, dataclasses ou une structure typée équivalente.

---

## Validation préalable

Créer :

```python
validate_energyplus_input()
```

Contrôler :

- hash du snapshot ;
- version ;
- géométrie ;
- surfaces ;
- volume ;
- orientation ;
- constructions ;
- vitrages ;
- calendriers ;
- charges internes ;
- débits ;
- consignes ;
- fichier météo ;
- unités ;
- fractions ;
- scénarios ;
- versions moteurs.

Aucune simulation ne doit démarrer avec une erreur bloquante.

---

## Erreurs de validation

Codes possibles :

```text
INVALID_SIMULATION_SNAPSHOT
UNSUPPORTED_SNAPSHOT_VERSION
INVALID_SIMULATION_GEOMETRY
INVALID_ZONE_VOLUME
INVALID_CONSTRUCTION_DATA
INVALID_APERTURE_DATA
INVALID_SCHEDULE
INVALID_INTERNAL_LOAD
INVALID_VENTILATION
INVALID_INFILTRATION
INVALID_SETPOINT
WEATHER_FILE_NOT_FOUND
WEATHER_FILE_INVALID
ENERGYPLUS_VERSION_UNSUPPORTED
HONEYBEE_VERSION_UNSUPPORTED
```

Retourner :

- code ;
- message ;
- section ;
- champ ;
- action ;
- request ID.

---

## Modèle Honeybee

Créer :

```python
build_honeybee_model()
```

Le modèle doit inclure :

- identifiant stable ;
- nom de l’étude ;
- version ;
- unités ;
- zones ;
- constructions ;
- ouvertures ;
- protections ;
- charges ;
- calendriers ;
- ventilation ;
- infiltration ;
- consignes ;
- métadonnées du snapshot.

---

## Nombre de zones

Pour le MVP :

```text
1 GreenCube = 1 zone thermique
```

Prévoir une architecture compatible avec plusieurs zones :

- studio principal ;
- local technique ;
- salle de bain ;
- espace serveur ;
- mezzanine ;
- modules assemblés.

---

## Géométrie

Créer :

```python
build_honeybee_geometry()
```

Utiliser :

- longueur ;
- largeur ;
- hauteur ;
- orientation ;
- surfaces ;
- coordonnées si disponibles.

Vérifier :

- faces fermées ;
- normales ;
- volumes ;
- surfaces positives ;
- absence de chevauchement ;
- cohérence des ouvertures.

---

## Système de coordonnées

Documenter :

```text
axe X
axe Y
axe Z
origine
azimut
sens de rotation
nord géographique
```

Ne pas appliquer deux fois l’orientation.

---

## Géométrie simplifiée

Si aucune géométrie 3D complète n’est disponible :

- générer une boîte rectangulaire ;
- conserver la méthode ;
- ajouter une hypothèse ;
- réduire la confiance si nécessaire.

---

## Frontières

Supporter :

```text
outdoors
ground
adiabatic
unconditioned
conditioned
```

Les frontières doivent venir du snapshot.

---

## Constructions Honeybee

Créer :

```python
build_honeybee_constructions()
```

Éléments :

- murs ;
- toiture ;
- plancher ;
- portes ;
- vitrages.

Modes :

```text
layered_construction
equivalent_u_value
```

---

## Construction équivalente

Si seules les valeurs U sont disponibles :

- créer une construction équivalente ;
- documenter la méthode ;
- conserver le U cible ;
- vérifier le U obtenu ;
- signaler la simplification.

Ne pas inventer des couches réelles non fournies.

---

## Construction multicouche

Si les couches sont disponibles :

- matériau ;
- épaisseur ;
- conductivité ;
- densité ;
- chaleur spécifique ;
- résistance.

Vérifier les unités et l’ordre des couches.

---

## Inertie thermique

Quand les données sont absentes :

- utiliser une construction équivalente versionnée ;
- signaler la simplification ;
- ne pas prétendre modéliser précisément l’inertie.

---

## Vitrages

Créer :

```python
build_honeybee_apertures()
```

Pour chaque baie :

- façade ;
- surface ;
- position ;
- dimensions ;
- U vitrage ;
- facteur solaire ;
- transmission visible ;
- ouvrabilité ;
- protection ;
- masque.

---

## Positionnement simplifié des baies

Si seules les surfaces sont disponibles :

- générer une baie centrée ;
- respecter les marges ;
- vérifier qu’elle reste dans la façade ;
- conserver l’hypothèse.

---

## Protections solaires

Créer :

```python
build_honeybee_shading()
```

Supporter :

- auvent ;
- brise-soleil ;
- store extérieur simplifié ;
- masque par coefficient ;
- absence de protection.

Si aucune géométrie n’est disponible :

- utiliser un calendrier ou un facteur compatible ;
- documenter l’approximation.

---

## Calendriers

Créer :

```python
build_honeybee_schedules()
```

Calendriers requis :

- occupation ;
- activité ;
- équipements ;
- éclairage ;
- ventilation ;
- infiltration si variable ;
- consignes jour/nuit ;
- disponibilité HVAC ;
- protections mobiles ;
- ouverture des fenêtres.

---

## Résolution temporelle

Pour le MVP :

```text
pas horaire
```

Configuration :

```text
timestep_per_hour
```

Valeurs possibles :

```text
1
2
4
6
```

La valeur doit être versionnée et limitée.

---

## Conversion des calendriers

Convertir les calendriers Odoo vers des valeurs :

```text
0 à 1
```

Vérifier :

- semaine ;
- week-end ;
- saisonnalité ;
- jours fériés si pris en charge ;
- passage de minuit ;
- fuseau ;
- heure d’été.

---

## Occupants Honeybee

Créer :

```python
build_people_load()
```

Mapper :

- nombre absolu ;
- personnes par surface ;
- activité métabolique ;
- fraction radiante ;
- sensible ;
- latent ;
- calendrier.

Conserver la méthode source.

---

## Équipements Honeybee

Créer :

```python
build_electric_equipment_loads()
```

Mapper :

- puissance absolue ;
- puissance par surface ;
- calendrier ;
- fraction latente ;
- fraction radiante ;
- fraction perdue ;
- fraction dissipée dans la zone.

Ne pas appliquer deux fois les facteurs déjà consolidés.

---

## Éclairage Honeybee

Créer :

```python
build_lighting_load()
```

Mapper :

- puissance ;
- W/m² ;
- calendrier ;
- fraction radiante ;
- fraction visible ;
- fraction perdue.

---

## Ventilation Honeybee

Créer :

```python
build_ventilation_load()
```

Supporter :

```text
flow_per_zone
flow_per_person
flow_per_area
air_changes_per_hour
```

Conserver la méthode et la valeur source.

---

## Récupération

Choisir et documenter une stratégie :

- système HVAC Honeybee avec récupération ;
- prétraitement du débit ;
- ajustement des propriétés d’air ;
- simplification explicitement signalée.

Ne pas appliquer une récupération fictive.

---

## Infiltration Honeybee

Créer :

```python
build_infiltration_load()
```

Supporter :

- ACH ;
- débit par surface ;
- débit par zone ;
- coefficient de fuite.

Ne jamais injecter directement `n50` comme infiltration naturelle.

---

## Ouverture des fenêtres

### MVP simplifié

- débit équivalent ;
- calendrier ;
- conditions simples.

### Mode avancé futur

- ventilation naturelle détaillée ;
- AirflowNetwork ;
- vent ;
- ouverture dynamique.

Feature flag :

```text
enable_advanced_natural_ventilation
```

---

## Consignes

Créer :

```python
build_temperature_setpoints()
```

Mapper :

- consigne jour ;
- consigne nuit ;
- disponibilité ;
- mode inoccupé ;
- température maximale ;
- éventuelle consigne de chauffage technique.

---

## Contrôle de l’humidité

Créer :

```python
build_humidity_controls()
```

N’activer le contrôle que si :

- le système HVAC le permet ;
- les données sont complètes ;
- le scénario le demande.

Sinon :

- simuler l’humidité libre ;
- retourner les dépassements ;
- signaler l’absence de contrôle actif.

---

## Système HVAC

Pour le calcul de charge, utiliser :

```text
ideal_air_loads
```

ou équivalent.

Objectif :

- calculer le besoin thermique ;
- ne pas modéliser encore un climatiseur commercial précis.

Créer :

```python
build_ideal_air_system()
```

---

## Capacité

Pour le dimensionnement :

- utiliser une capacité suffisante ou illimitée ;
- extraire la charge requise.

Le mode capacité limitée peut rester derrière un feature flag pour les tests de résilience.

---

## Fichiers météo

Créer :

```python
resolve_weather_file()
```

Format attendu :

```text
EPW
```

Associer à chaque scénario :

- fichier ;
- période ;
- modifications ;
- source ;
- version ;
- empreinte.

---

## Scénarios climatiques

```text
reference_summer
hot_weather
prolonged_heatwave
```

Ils peuvent être représentés par :

- EPW différents ;
- design days ;
- périodes sélectionnées ;
- fichiers modifiés ;
- événements synthétiques.

La méthode doit être explicite et versionnée.

---

## Weather morphing

Si un EPW est modifié :

- conserver l’EPW source ;
- conserver la méthode ;
- conserver les deltas ;
- calculer une empreinte ;
- ne jamais remplacer le fichier source ;
- signaler le caractère synthétique.

---

## Validation météo

Vérifier :

- existence ;
- taille ;
- format ;
- en-tête ;
- localisation ;
- fuseau ;
- altitude ;
- nombre d’heures ;
- absence de corruption ;
- empreinte.

---

## Artefacts

Créer :

```text
greencube.cooling.simulation.artifact
```

Types possibles :

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

Champs :

```text
job_id
artifact_type
filename
storage_key
checksum
size_bytes
mime_type
created_at
retention_until
company_id
access_level
```

---

## Stockage

Éviter le stockage illimité dans PostgreSQL.

Préférer :

- stockage objet ;
- stockage de fichiers existant ;
- pièces jointes Odoo uniquement pour les petits fichiers utiles.

---

## Rétention

Exemple configurable :

```text
fichiers intermédiaires : 30 jours
logs détaillés : 90 jours
résultats normalisés : conservation métier
snapshot : conservation métier
fichiers d’erreur : 90 jours
```

---

## Job asynchrone

Réutiliser :

```text
greencube.cooling.calculation.job
```

Champs supplémentaires possibles :

```text
worker_id
container_id
heartbeat_at
timeout_at
current_step
progress_message
simulation_engine
simulation_version
weather_checksum
artifact_count
```

---

## Étapes du job

```text
queued
validating
building_model
preparing_weather
preparing_simulation
running
parsing_results
normalizing_results
comparing
persisting
completed
failed
cancelled
timed_out
```

---

## Progression

Prévoir une valeur indicative :

```text
0 à 100
```

Exemple :

```text
5 % validation
15 % géométrie
25 % modèle Honeybee
35 % préparation EnergyPlus
40–80 % exécution
85 % parsing
92 % comparaison
100 % terminé
```

---

## Heartbeat

Mettre à jour :

```text
heartbeat_at
```

Un job sans heartbeat au-delà d’un seuil devient :

```text
stalled
```

Le système doit pouvoir :

- détecter ;
- relancer si autorisé ;
- échouer proprement ;
- éviter les doubles exécutions.

---

## Timeout

Configuration :

```text
simulation_timeout_seconds
```

En cas de dépassement :

- arrêter le processus ;
- marquer `timed_out` ;
- conserver les logs ;
- nettoyer les ressources ;
- retourner une erreur structurée.

---

## Exécution isolée

EnergyPlus doit s’exécuter :

- dans un conteneur dédié ;
- avec un utilisateur non privilégié ;
- dans un filesystem temporaire ;
- avec limites CPU ;
- avec limites mémoire ;
- sans réseau si non requis ;
- avec un volume spécifique au job.

Ne jamais exécuter une commande arbitraire du frontend.

---

## Commandes autorisées

Utiliser :

- liste fixe de commandes ;
- arguments structurés ;
- `subprocess` sans `shell=True` ;
- chemins validés ;
- noms de fichiers générés côté serveur.

---

## Limites de ressources

Configurer :

```text
CPU
mémoire
durée
taille disque
nombre de fichiers
taille des sorties
```

Un dépassement doit produire un échec propre.

---

## Worker

Créer :

```python
run_cooling_simulation_job(job_id)
```

Étapes :

1. verrouiller le job ;
2. vérifier l’idempotence ;
3. vérifier le snapshot ;
4. créer l’espace de travail ;
5. générer les artefacts ;
6. lancer EnergyPlus ;
7. suivre l’exécution ;
8. parser ;
9. normaliser ;
10. comparer avec MERCURE ;
11. persister ;
12. nettoyer ;
13. terminer le job.

---

## Verrouillage

Utiliser :

- verrou base de données ;
- verrou de file ;
- ou mécanisme équivalent.

Un seul worker doit exécuter un job donné.

---

## Reprise après erreur

Distinguer :

```text
retryable
non_retryable
```

Relançables :

- worker interrompu ;
- stockage temporairement indisponible ;
- file indisponible ;
- erreur réseau interne.

Non relançables :

- géométrie invalide ;
- fichier météo corrompu ;
- modèle incompatible ;
- erreur EnergyPlus déterministe.

---

## Tentatives

Configurer :

```text
max_attempt_count
```

Conserver :

- tentative ;
- date ;
- cause ;
- worker ;
- durée.

Ne pas relancer indéfiniment.

---

## Annulation

Endpoint possible :

```text
POST /api/v1/greencube/cooling/calculations/<job_id>/cancel
```

Le worker doit :

- vérifier l’état ;
- arrêter le processus ;
- nettoyer ;
- marquer `cancelled` ;
- conserver l’audit.

---

## Runner EnergyPlus

Créer :

```python
run_energyplus()
```

Entrées :

- modèle ;
- fichier météo ;
- répertoire ;
- version ;
- timeout ;
- options.

Sorties :

- code retour ;
- durée ;
- stdout ;
- stderr ;
- fichiers ;
- statut.

---

## Versions

Conserver :

```text
energyplus_version
honeybee_version
ladybug_tools_version
simulation_method_version
```

Une mise à jour ne doit pas modifier les anciens résultats.

---

## Fichier d’erreurs

Parser :

```text
eplusout.err
```

Distinguer :

```text
warning
severe
fatal
```

Règles :

- fatal : échec ;
- severe : échec ou résultat non fiable selon configuration ;
- warning : résultat possible avec avertissement.

---

## Erreurs EnergyPlus

Codes possibles :

```text
ENERGYPLUS_EXECUTION_FAILED
ENERGYPLUS_FATAL_ERROR
ENERGYPLUS_SEVERE_ERRORS
ENERGYPLUS_TIMEOUT
ENERGYPLUS_OUTPUT_MISSING
ENERGYPLUS_SQL_INVALID
ENERGYPLUS_RESULT_PARSE_FAILED
```

---

## Extraction des résultats

Créer :

```python
parse_energyplus_results()
```

Sources possibles :

```text
eplusout.sql
eplusout.csv
eplusout.eso
HTML tables
```

Privilégier une source structurée et stable.

---

## Variables minimales

Extraire :

- charge sensible de refroidissement ;
- charge latente ;
- charge totale ;
- pic horaire ;
- date et heure du pic ;
- température intérieure ;
- humidité intérieure ;
- température opérative si disponible ;
- heures au-dessus de la consigne ;
- énergie annuelle de refroidissement si activée ;
- débit de ventilation ;
- infiltration ;
- gains internes ;
- apports solaires ;
- transmission.

---

## Grandeurs à distinguer

```text
zone_peak_cooling_load_w
system_peak_cooling_load_w
annual_cooling_energy_kwh
```

Ne pas confondre :

- puissance de pointe ;
- énergie annuelle ;
- puissance électrique ;
- charge thermique.

---

## Sensible et latent

Extraire :

```text
sensible_peak_w
latent_peak_w
total_peak_w
sensible_heat_ratio
```

Si une valeur est reconstruite :

- documenter la méthode ;
- conserver les variables sources.

---

## Date du pic

Retourner :

```text
peak_timestamp
```

Préciser :

- fuseau ;
- heure standard ou locale ;
- scénario ;
- pas de temps.

---

## Résilience

Extraire :

- température maximale ;
- température moyenne pendant la canicule ;
- heures au-dessus de la consigne ;
- heures au-dessus du maximum acceptable ;
- humidité maximale ;
- durée continue de dépassement.

---

## Modes de simulation

```text
design_period
annual
```

Recommandation :

- `design_period` pour la capacité ;
- `annual` derrière un feature flag.

Feature flag :

```text
enable_annual_energyplus_simulation
```

---

## Normalisation

Créer :

```python
normalize_energyplus_results()
```

Schéma commun avec MERCURE :

```python
class NormalizedCoolingResult:
    engine_code: str
    engine_version: str
    scenario_code: str
    sensible_load_w: float
    latent_load_w: float
    total_load_w: float
    recommended_capacity_w: float
    peak_timestamp: str | None
    annual_energy_kwh: float | None
    max_indoor_temperature_c: float | None
    hours_above_setpoint: float | None
    confidence_score: float
    breakdown: dict
    warnings: list
```

---

## Persistance

Réutiliser ou compléter :

```text
greencube.cooling.result
greencube.cooling.result.scenario
greencube.cooling.result.line
```

Conserver :

- moteur ;
- version ;
- snapshot ;
- scénario ;
- puissance ;
- énergie ;
- pic ;
- confort ;
- confiance ;
- avertissements ;
- artefacts ;
- empreinte.

---

## Immuabilité

Un résultat terminé doit être immuable.

Toute nouvelle simulation doit créer :

- un nouveau job ;
- un nouveau résultat ;
- un nouvel ensemble d’artefacts.

---

## Comparaison MERCURE / EnergyPlus

Créer :

```python
compare_mercure_energyplus()
```

Comparer par scénario :

- sensible ;
- latent ;
- total ;
- puissance recommandée ;
- scénario dimensionnant ;
- contributions principales ;
- date du pic.

---

## Calcul des écarts

```text
absolute_difference_w
relative_difference_percent
```

Formule :

```text
écart relatif =
(EnergyPlus - MERCURE)
÷ EnergyPlus
× 100
```

Gérer le cas où la référence vaut zéro.

---

## Seuils de comparaison

Créer des seuils versionnés :

```text
acceptable
warning
critical
```

Ne pas coder les seuils directement.

---

## Explication des écarts

Créer :

```python
explain_result_difference()
```

Causes possibles :

- inertie thermique ;
- profils horaires ;
- pics non simultanés ;
- rayonnement dynamique ;
- stockage thermique ;
- ventilation nocturne ;
- humidité ;
- protections dynamiques ;
- géométrie simplifiée ;
- récupération ;
- température du sol.

Retourner des causes probables.

---

## Modèle de comparaison

Créer ou compléter :

```text
greencube.cooling.result.comparison
```

Champs possibles :

```text
snapshot_id
mercure_result_id
energyplus_result_id
scenario_code
mercure_total_w
energyplus_total_w
absolute_difference_w
relative_difference_percent
comparison_status
main_explanations
created_at
method_version
```

---

## Scénario final

Retourner :

- scénario MERCURE ;
- scénario EnergyPlus ;
- scénario retenu.

Modes possibles :

```text
energyplus_preferred
maximum_of_both
engineer_review
mercure_fallback
```

---

## Règle de recommandation

Exemple possible :

```text
si EnergyPlus réussit et est fiable
→ utiliser EnergyPlus

si EnergyPlus échoue
→ utiliser MERCURE avec avertissement

si écart critique
→ demander une revue ingénieur
```

La règle doit être explicite et versionnée.

---

## Score de confiance EnergyPlus

Il peut dépendre de :

- qualité du snapshot ;
- géométrie réelle ou simplifiée ;
- construction réelle ou équivalente ;
- qualité météo ;
- calendriers ;
- erreurs EnergyPlus ;
- avertissements ;
- simplifications ;
- humidité ;
- ventilation naturelle.

---

## Alertes

Codes possibles :

```text
SIMPLIFIED_GEOMETRY
EQUIVALENT_CONSTRUCTION_USED
SIMPLIFIED_SHADING
SIMPLIFIED_NATURAL_VENTILATION
HUMIDITY_CONTROL_NOT_MODELED
WEATHER_MORPHING_USED
ENERGYPLUS_WARNINGS_PRESENT
ENERGYPLUS_SEVERE_ERRORS_PRESENT
LOW_SIMULATION_CONFIDENCE
MERCURE_ENERGYPLUS_DIFFERENCE_HIGH
```

---

## Endpoint de lancement

```text
POST /api/v1/greencube/cooling/studies/<id>/calculations
```

Payload EnergyPlus :

```json
{
  "snapshot_id": 45,
  "engine": "ENERGYPLUS",
  "scenario_codes": [
    "reference_summer",
    "hot_weather",
    "prolonged_heatwave"
  ],
  "simulation_mode": "design_period",
  "idempotency_key": "uuid"
}
```

Payload deux moteurs :

```json
{
  "snapshot_id": 45,
  "engine": "BOTH",
  "scenario_codes": [
    "reference_summer",
    "hot_weather",
    "prolonged_heatwave"
  ],
  "simulation_mode": "design_period",
  "idempotency_key": "uuid"
}
```

---

## Réponse de lancement

```json
{
  "job_id": 184,
  "status": "queued",
  "engine": "ENERGYPLUS",
  "snapshot_id": 45,
  "request_id": "req-..."
}
```

---

## Endpoint de suivi

```text
GET /api/v1/greencube/cooling/calculations/<job_id>
```

Réponse possible :

```json
{
  "job_id": 184,
  "status": "running",
  "current_step": "running",
  "progress": 64,
  "progress_message": "Simulation du scénario de canicule prolongée",
  "started_at": "2026-07-15T14:00:00Z",
  "heartbeat_at": "2026-07-15T14:02:10Z",
  "result_id": null,
  "request_id": "req-..."
}
```

---

## Endpoint des résultats

```text
GET /api/v1/greencube/cooling/results/<result_id>
```

Retourner un résultat normalisé, pas seulement des fichiers techniques.

---

## Endpoint des artefacts

```text
GET /api/v1/greencube/cooling/calculations/<job_id>/artifacts
```

Réserver aux rôles autorisés.

---

## Idempotence

La combinaison suivante doit être idempotente :

```text
snapshot
+ moteur
+ version moteur
+ scénarios
+ mode simulation
+ fichier météo
+ idempotency key
```

---

## Permissions

Rôles possibles :

```text
cooling_user
cooling_engineer
cooling_manager
cooling_admin
```

Exemples :

- utilisateur : lancer une simulation autorisée ;
- ingénieur : consulter erreurs et artefacts ;
- manager : valider ;
- administrateur : configurer versions et ressources.

Respecter le multi-société.

---

## Audit

Auditer :

- lancement ;
- snapshot ;
- moteur ;
- versions ;
- météo ;
- scénarios ;
- worker ;
- début ;
- fin ;
- erreur ;
- annulation ;
- retry ;
- résultat ;
- comparaison ;
- utilisateur ;
- société ;
- request ID.

---

## Observabilité

Logs structurés :

```text
request_id
job_id
snapshot_id
study_id
company_id
engine
engine_version
scenario_code
step
duration_ms
status
error_code
```

Ne pas journaliser de secrets ou de fichiers complets.

---

## Métriques

Prévoir :

- jobs lancés ;
- réussis ;
- échoués ;
- annulés ;
- expirés ;
- durée moyenne ;
- durée par étape ;
- mémoire maximale ;
- taux d’erreurs EnergyPlus ;
- écart moyen MERCURE/EnergyPlus ;
- taille des artefacts.

---

## Nettoyage

Après chaque job :

- arrêter le processus ;
- supprimer le répertoire temporaire ;
- conserver uniquement les artefacts configurés ;
- libérer les verrous ;
- mettre à jour le job.

Le nettoyage doit aussi s’exécuter en cas d’erreur.

---

## Sécurité des fichiers

Vérifier :

- chemins ;
- extensions ;
- tailles ;
- checksums ;
- permissions ;
- absence de path traversal ;
- noms générés côté serveur.

---

## Dépendances

Verrouiller les versions.

Créer ou compléter :

```text
requirements.txt
requirements-simulation.txt
Dockerfile.simulation
```

Documenter :

- Python ;
- Honeybee ;
- Ladybug Tools ;
- EnergyPlus ;
- bibliothèques de parsing ;
- compatibilités.

---

## Image Docker

Créer si nécessaire :

```text
Dockerfile.simulation
```

L’image doit :

- utiliser une base maîtrisée ;
- installer une version précise d’EnergyPlus ;
- installer les dépendances verrouillées ;
- utiliser un utilisateur non root ;
- définir un répertoire de travail ;
- ne contenir aucun secret ;
- inclure un healthcheck.

---

## Healthchecks

```text
GET /health
GET /health/deep
```

Le healthcheck profond peut vérifier :

- import Honeybee ;
- version EnergyPlus ;
- écriture temporaire ;
- stockage ;
- file de jobs.

---

## Tests unitaires

Tester :

### Validation

- snapshot valide ;
- hash invalide ;
- géométrie absente ;
- météo absente ;
- calendrier invalide ;
- unités invalides.

### Géométrie

- boîte simple ;
- orientation ;
- surface ;
- volume ;
- ouverture excessive ;
- face invalide.

### Constructions

- U équivalent ;
- multicouche ;
- vitrage ;
- plancher sol ;
- frontière adiabatique.

### Calendriers

- semaine ;
- week-end ;
- saison ;
- minuit ;
- valeurs 0 à 1.

### Charges

- occupants ;
- équipements ;
- éclairage ;
- ventilation ;
- infiltration ;
- consignes.

### Météo

- EPW valide ;
- EPW corrompu ;
- checksum ;
- scénario synthétique.

### Runner

- succès ;
- timeout ;
- processus interrompu ;
- code retour invalide ;
- fichier manquant.

### Parsing

- SQL valide ;
- sortie manquante ;
- avertissements ;
- erreurs sévères ;
- valeurs nulles.

### Comparaison

- écart nul ;
- acceptable ;
- warning ;
- critical ;
- division par zéro.

---

## Tests d’intégration

Tester :

1. lecture du snapshot ;
2. création du job ;
3. construction Honeybee ;
4. génération des fichiers ;
5. association météo ;
6. exécution EnergyPlus ;
7. récupération des sorties ;
8. parsing ;
9. normalisation ;
10. persistance ;
11. comparaison MERCURE ;
12. artefacts ;
13. permissions ;
14. multi-société ;
15. idempotence ;
16. annulation ;
17. timeout ;
18. retry.

---

## Cas de référence

### Cas 1 — Studio standard

- géométrie simple ;
- deux occupants ;
- ventilation standard ;
- faible charge interne.

### Cas 2 — Bureau vitré ouest

- apports solaires élevés ;
- équipements informatiques ;
- occupation de jour.

### Cas 3 — Local technique

- charge permanente ;
- faible occupation ;
- ventilation continue.

### Cas 4 — Canicule prolongée

- occupation nocturne ;
- météo synthétique ;
- ventilation nocturne.

### Cas 5 — Construction équivalente

- valeurs U uniquement ;
- inertie simplifiée ;
- avertissement attendu.

### Cas 6 — Données avancées

- multicouches ;
- protections ;
- récupération ;
- calendriers complets.

---

## Tests de non-régression

Créer des snapshots et résultats de référence.

Pour chaque version :

- conserver le modèle généré ;
- conserver les résultats normalisés ;
- comparer les écarts ;
- documenter les changements ;
- ne pas mettre à jour les références sans justification.

---

## Tests de charge

Tester :

- plusieurs jobs successifs ;
- plusieurs sociétés ;
- file pleine ;
- limite de concurrence ;
- jobs longs ;
- nettoyage ;
- stockage.

---

## Limite de concurrence

Configuration :

```text
max_concurrent_energyplus_jobs
```

La valeur dépend :

- des CPU ;
- de la mémoire ;
- du VPS ;
- du mode de déploiement.

---

## Tests API

Tester :

- lancement EnergyPlus ;
- lancement BOTH ;
- feature flag désactivé ;
- snapshot invalide ;
- scénario invalide ;
- moteur indisponible ;
- suivi du job ;
- annulation ;
- résultat ;
- artefacts protégés ;
- accès inter-sociétés interdit.

---

## Documentation

Créer :

```text
docs/cooling_energyplus_architecture.md
docs/cooling_honeybee_mapping.md
docs/cooling_energyplus_job_lifecycle.md
docs/cooling_energyplus_weather.md
docs/cooling_energyplus_outputs.md
docs/cooling_energyplus_artifacts.md
docs/cooling_mercure_energyplus_comparison.md
docs/cooling_simulation_security.md
docs/cooling_simulation_operations.md
docs/cooling_simulation_troubleshooting.md
```

---

## Matrice de mapping

Créer :

```text
champ snapshot
→ objet Honeybee
→ objet EnergyPlus
→ unité source
→ unité cible
→ conversion
→ hypothèse
→ test
```

Inclure :

- géométrie ;
- constructions ;
- vitrages ;
- protections ;
- occupants ;
- équipements ;
- éclairage ;
- ventilation ;
- infiltration ;
- consignes ;
- humidité ;
- météo.

---

## Documentation opérationnelle

Documenter :

- installation ;
- versions ;
- worker ;
- file ;
- stockage ;
- limites ;
- healthchecks ;
- logs ;
- métriques ;
- retry ;
- annulation ;
- nettoyage ;
- mise à jour EnergyPlus ;
- rollback.

---

## Critères d’acceptation

Le lot est accepté si :

- le feature flag fonctionne ;
- EnergyPlus ne s’exécute pas dans le processus web ;
- le calcul utilise un snapshot immuable ;
- les entrées sont validées ;
- le modèle Honeybee est généré ;
- la géométrie est générée ;
- les constructions sont générées ;
- les vitrages sont générés ;
- les protections sont prises en compte ;
- les calendriers sont générés ;
- les occupants sont mappés ;
- les équipements sont mappés ;
- l’éclairage est mappé ;
- la ventilation est mappée ;
- l’infiltration est mappée ;
- les consignes sont mappées ;
- les fichiers météo sont validés ;
- les scénarios climatiques sont gérés ;
- EnergyPlus s’exécute dans un environnement isolé ;
- les ressources sont limitées ;
- les jobs sont asynchrones ;
- les jobs sont verrouillés ;
- la progression est exposée ;
- le heartbeat fonctionne ;
- le timeout fonctionne ;
- l’annulation fonctionne ;
- les retries sont limités ;
- les sorties sont parsées ;
- les erreurs fatales sont détectées ;
- les avertissements sont structurés ;
- les résultats sont normalisés ;
- la puissance de pointe est extraite ;
- le sensible est extrait ;
- le latent est extrait ;
- le total est extrait ;
- la date du pic est extraite ;
- les températures sont extraites ;
- l’humidité est extraite ;
- les dépassements sont extraits ;
- les résultats sont persistés ;
- les résultats sont immuables ;
- les artefacts sont stockés ;
- les checksums sont conservés ;
- la rétention est configurable ;
- la comparaison MERCURE/EnergyPlus fonctionne ;
- les écarts sont calculés ;
- les causes probables sont expliquées ;
- le scénario final peut être déterminé ;
- l’idempotence fonctionne ;
- les permissions sont respectées ;
- le multi-société est respecté ;
- l’audit est complet ;
- les logs sont structurés ;
- les métriques sont disponibles ;
- les tests passent ;
- les dépendances sont verrouillées ;
- aucun secret n’est exposé ;
- aucun fichier n’est supprimé sans justification.

---

## Rapport final attendu

### Architecture

- services ;
- worker ;
- file ;
- stockage ;
- Odoo ;
- conteneur ;
- flux complet.

### Versions

- Python ;
- Honeybee ;
- Ladybug Tools ;
- EnergyPlus ;
- image Docker ;
- méthode de simulation.

### Mapping

- snapshot ;
- Honeybee ;
- EnergyPlus ;
- unités ;
- conversions ;
- hypothèses.

### Jobs

- statuts ;
- progression ;
- heartbeat ;
- timeout ;
- retry ;
- annulation ;
- concurrence.

### Météo

- sources ;
- fichiers ;
- validation ;
- scénarios ;
- morphing ;
- checksums.

### Résultats

- sorties ;
- normalisation ;
- sensible ;
- latent ;
- total ;
- énergie ;
- confort ;
- scénario dimensionnant.

### Comparaison

- MERCURE ;
- EnergyPlus ;
- écarts ;
- seuils ;
- explications ;
- règle finale.

### Artefacts

- types ;
- stockage ;
- accès ;
- checksums ;
- rétention ;
- nettoyage.

### Odoo

- modèles créés ;
- modèles modifiés ;
- ACL ;
- règles ;
- migrations ;
- paramètres.

### API

Pour chaque endpoint :

- méthode ;
- URL ;
- payload ;
- réponse ;
- erreurs ;
- permissions ;
- idempotence.

### Tests

- commandes ;
- résultats ;
- couverture ;
- cas de référence ;
- non-régression ;
- tests non exécutés ;
- raisons.

### Performance

- durée par scénario ;
- CPU ;
- mémoire ;
- concurrence ;
- taille des artefacts ;
- limites.

### Sécurité

- isolation ;
- utilisateur non root ;
- commandes ;
- chemins ;
- permissions ;
- logs ;
- secrets ;
- multi-société.

### Patch

- diff ;
- patch réintégrable ;
- installation ;
- variables d’environnement ;
- migration ;
- rollback.

---

## Contrôle final

Avant conclusion :

1. lancer le lint Python ;
2. lancer le formatage ;
3. lancer les contrôles de types ;
4. lancer les tests unitaires ;
5. lancer les tests d’intégration ;
6. lancer les tests API ;
7. lancer les tests de non-régression ;
8. construire l’image de simulation ;
9. exécuter le healthcheck ;
10. vérifier les versions ;
11. vérifier le feature flag ;
12. vérifier le snapshot ;
13. vérifier la géométrie ;
14. vérifier les constructions ;
15. vérifier les vitrages ;
16. vérifier les protections ;
17. vérifier les calendriers ;
18. vérifier les occupants ;
19. vérifier les équipements ;
20. vérifier l’éclairage ;
21. vérifier la ventilation ;
22. vérifier l’infiltration ;
23. vérifier les consignes ;
24. vérifier l’humidité ;
25. vérifier les fichiers météo ;
26. vérifier le weather morphing ;
27. vérifier l’exécution isolée ;
28. vérifier les limites CPU ;
29. vérifier les limites mémoire ;
30. vérifier le timeout ;
31. vérifier l’annulation ;
32. vérifier le heartbeat ;
33. vérifier les retries ;
34. vérifier l’idempotence ;
35. vérifier les sorties ;
36. vérifier le parsing ;
37. vérifier le sensible ;
38. vérifier le latent ;
39. vérifier le total ;
40. vérifier la date du pic ;
41. vérifier les dépassements ;
42. vérifier la normalisation ;
43. vérifier la persistance ;
44. vérifier les artefacts ;
45. vérifier les checksums ;
46. vérifier la rétention ;
47. vérifier la comparaison MERCURE ;
48. vérifier les seuils ;
49. vérifier les permissions ;
50. vérifier le multi-société ;
51. vérifier l’audit ;
52. vérifier les logs ;
53. vérifier les métriques ;
54. vérifier le nettoyage ;
55. vérifier l’absence de secrets ;
56. vérifier qu’aucun ancien résultat n’a été modifié ;
57. vérifier qu’aucun fichier n’a été supprimé ;
58. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente :

- la conversion du snapshot vers Honeybee ;
- la génération du modèle EnergyPlus ;
- l’exécution des simulations ;
- les jobs asynchrones ;
- les artefacts ;
- le parsing ;
- la normalisation ;
- la comparaison avec MERCURE.

Il ne finalise pas encore :

- l’écran frontend complet de résultats ;
- les graphiques utilisateurs ;
- la recommandation commerciale d’un climatiseur ;
- le rapport PDF ;
- l’analyse économique annuelle complète ;
- le devis Odoo.

Il doit fournir une chaîne EnergyPlus complète, robuste et exploitable par le prochain écran de résultats.
