# GC-COOLING-05A — Intégration initiale Honeybee Energy / EnergyPlus

## Objectif

Mettre en place le premier socle complet de simulation thermique physique de GreenCube Cooling.

La chaîne cible est :

```text
Étude GreenCube Odoo
→ validation des données d’entrée
→ génération du modèle Honeybee
→ traduction vers OpenStudio / EnergyPlus
→ préparation du fichier météo
→ exécution sécurisée
→ extraction des résultats
→ normalisation
→ conversion des unités
→ recommandation de capacité
→ persistance Odoo
```

Ce lot doit être :

- fonctionnel ;
- testable ;
- sécurisé ;
- reproductible ;
- versionné ;
- exploitable indépendamment ;
- compatible avec une future orchestration avancée.

Odoo Community 18 reste la source de vérité métier.

Honeybee et EnergyPlus ne doivent jamais accéder directement à la base Odoo.

Le frontend React ne doit jamais :

- exécuter Honeybee ;
- exécuter EnergyPlus ;
- transmettre une commande système ;
- transmettre un chemin local ;
- fournir un fichier IDF arbitraire ;
- fournir un script Python arbitraire ;
- définir librement des coefficients internes ;
- recalculer les résultats officiels ;
- modifier un résultat terminé.

---

## Questions fonctionnelles couvertes

Le service doit permettre de déterminer :

- la puissance frigorifique de pointe ;
- la part sensible ;
- la part latente ;
- l’heure du pic ;
- la température intérieure maximale ;
- les heures au-dessus de la consigne ;
- l’énergie frigorifique nécessaire ;
- la consommation électrique estimée ;
- la capacité commerciale recommandée ;
- les hypothèses qui réduisent la confiance.

---

## Périmètre

Ce lot couvre :

```text
microservice interne
contrat de données Odoo → simulation
validation du payload
construction Honeybee
géométrie
enveloppe
vitrages
ombrages
charges internes
calendriers
ventilation
infiltration
consignes
HVAC idéal
fichier météo
EnergyPlus
exécution sécurisée
parsing des résultats
normalisation
conversion des unités
estimation de consommation
recommandation de capacité
persistance Odoo
tests
documentation
patch
```

Il ne finalise pas encore :

- l’orchestration distribuée complète ;
- la file de jobs industrielle ;
- la comparaison avancée MERCURE / EnergyPlus ;
- l’écran final de résultats ;
- la sélection commerciale d’un climatiseur ;
- le devis ;
- le paiement ;
- la facturation ;
- le commissioning.

---

## Prérequis

Le lot suppose normalement disponibles :

```text
GC-COOLING-01
→ modèles métier Odoo

GC-COOLING-02
→ API JSON

GC-COOLING-03
→ géolocalisation, altitude et fuseau

GC-COOLING-04
→ service climatique et scénarios météo
```

Vérifier :

```text
greencube.cooling.study
greencube.cooling.model
greencube.cooling.climate.dataset
greencube.cooling.climate.scenario
```

---

## Vérifications préalables

Avant toute modification :

- inspecter l’arborescence ;
- inspecter le module Odoo ;
- inspecter les modèles de l’étude ;
- inspecter les caractéristiques thermiques ;
- inspecter la géométrie ;
- inspecter les vitrages ;
- inspecter les protections solaires ;
- inspecter l’occupation ;
- inspecter les équipements ;
- inspecter l’éclairage ;
- inspecter la ventilation ;
- inspecter l’infiltration ;
- inspecter les consignes ;
- inspecter le service climatique ;
- inspecter les fichiers EPW ;
- inspecter les endpoints ;
- inspecter les workers ;
- inspecter Docker ;
- inspecter les dépendances Python ;
- inspecter les versions Honeybee ;
- inspecter les versions Ladybug ;
- inspecter OpenStudio ;
- inspecter EnergyPlus ;
- inspecter les licences ;
- inspecter les variables d’environnement ;
- inspecter le stockage ;
- inspecter les logs ;
- inspecter les ACL ;
- inspecter le multi-société ;
- inspecter les tests ;
- exécuter les tests existants ;
- ne supprimer aucun fichier ;
- ne remplacer aucune infrastructure sans justification ;
- ne modifier aucun résultat historique ;
- ne modifier aucun fichier météo source ;
- ne jamais déclarer EnergyPlus opérationnel sans test réel.

---

## Architecture cible

Créer un microservice interne nommé par exemple :

```text
greencube-energy-simulation
```

Architecture recommandée :

```text
Odoo Community 18
        │
        ▼
Simulation API Client
        │
        ▼
Internal Simulation API
        │
        ├── Payload Validator
        ├── Model Builder
        ├── Geometry Builder
        ├── Construction Builder
        ├── Aperture Builder
        ├── Shade Builder
        ├── Schedule Builder
        ├── Load Builder
        ├── Ventilation Builder
        ├── Infiltration Builder
        ├── Setpoint Builder
        ├── HVAC Builder
        ├── Weather Resolver
        ├── EnergyPlus Runner
        ├── Result Parser
        ├── Result Normalizer
        ├── Consumption Estimator
        └── Capacity Selector
        │
        ▼
Temporary Workspace
        │
        ▼
EnergyPlus
        │
        ▼
Normalized Result
        │
        ▼
Odoo
```

Le microservice doit être accessible uniquement sur le réseau interne.

---

## Technologies

Utiliser selon compatibilité réelle :

```text
honeybee-core
honeybee-energy
honeybee-openstudio
ladybug-core
ladybug-geometry
OpenStudio si requis
EnergyPlus
FastAPI ou framework interne
Pydantic
Python
Docker
```

Les versions doivent être :

- compatibles ;
- épinglées ;
- documentées ;
- testées ;
- reproductibles.

---

## Structure de code recommandée

```text
greencube-energy-simulation/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── logging_config.py
│   ├── errors.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── simulation_request.py
│   │   ├── simulation_result.py
│   │   └── artifacts.py
│   ├── services/
│   │   ├── model_builder.py
│   │   ├── geometry_builder.py
│   │   ├── construction_builder.py
│   │   ├── aperture_builder.py
│   │   ├── shade_builder.py
│   │   ├── schedule_builder.py
│   │   ├── load_builder.py
│   │   ├── ventilation_builder.py
│   │   ├── infiltration_builder.py
│   │   ├── setpoint_builder.py
│   │   ├── hvac_builder.py
│   │   ├── weather_builder.py
│   │   ├── simulation_runner.py
│   │   ├── result_parser.py
│   │   ├── result_normalizer.py
│   │   ├── consumption_estimator.py
│   │   ├── capacity_selector.py
│   │   └── artifact_manager.py
│   └── api/
│       ├── health.py
│       └── simulations.py
├── tests/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Contrat d’entrée

Créer un payload versionné contenant :

```text
schema_version
request_id
study
location
geometry
envelope
apertures
shades
occupancy
lighting
equipment
ventilation
infiltration
setpoints
weather
simulation_options
```

Le service ne doit jamais accepter :

- pickle ;
- archive exécutable ;
- script Python ;
- commande système ;
- URL arbitraire ;
- chemin local arbitraire ;
- fichier IDF arbitraire ;
- fichier EPJSON arbitraire ;
- template libre ;
- macro EnergyPlus libre ;
- objet sérialisé non contrôlé ;
- expression à évaluer.

---

## Versionnement du payload

Créer :

```text
SIMULATION_INPUT_SCHEMA_VERSION = "1"
```

Conserver :

- version du schéma ;
- version du builder ;
- version Honeybee ;
- version EnergyPlus ;
- version météo ;
- version des règles de capacité.

Refuser toute version inconnue.

---

## Validation des entrées

Vérifier :

```text
étude existante
révision existante
société autorisée
dimensions positives
volume fermé
orientation valide
surfaces cohérentes
vitrages dans les limites des façades
valeurs U positives
facteurs solaires entre 0 et 1
charges non négatives
débits non négatifs
infiltration plausible
consignes cohérentes
fuseau valide
météo disponible
```

Niveaux :

```text
error
warning
info
```

Une erreur doit bloquer la simulation.

---

## Géométrie GreenCube

Pour le MVP :

```text
1 GreenCube simple = 1 zone thermique
```

Prévoir une architecture compatible multi-zone.

Gérer :

- longueur ;
- largeur ;
- hauteur ;
- niveau du sol ;
- orientation ;
- toiture ;
- plancher ;
- murs ;
- portes ;
- vitrages ;
- ombrages.

Convention métier :

```text
0° = nord
90° = est
180° = sud
270° = ouest
```

Créer une fonction unique de conversion vers Honeybee.

---

## Validation géométrique

Vérifier :

- volume positif ;
- faces planes ;
- sommets non dupliqués ;
- surfaces non nulles ;
- normales cohérentes ;
- vitrage dans la façade ;
- absence de chevauchement important ;
- porte dans le mur ;
- cohérence toiture/plancher ;
- tolérance géométrique.

---

## Parois opaques

Gérer :

```text
murs
toiture
plancher
portes opaques
```

Conserver :

- type ;
- surface ;
- orientation ;
- valeur U ;
- couches si disponibles ;
- source ;
- confiance ;
- condition limite.

Lorsque les couches sont connues :

```text
épaisseur
conductivité
densité
capacité thermique massique
résistance thermique
absorptance solaire
absorptance thermique
rugosité
```

Lorsque seule la valeur U est connue :

- utiliser une construction simplifiée ;
- documenter la méthode ;
- signaler l’absence d’inertie détaillée ;
- ne pas inventer de couches physiques.

---

## Ponts thermiques

Méthodes possibles :

```text
coefficient global additionnel
ou
majoration de la valeur U
```

La méthode doit être :

- configurable ;
- explicite ;
- versionnée ;
- auditée.

Éviter le double comptage.

---

## Vitrages

Pour chaque vitrage, gérer :

```text
façade
position
largeur
hauteur
surface
valeur U
SHGC
transmission visible
type de cadre
fraction de cadre
ouverture éventuelle
source
confiance
```

Lorsque seules U-value et SHGC sont disponibles, utiliser un vitrage simplifié compatible Honeybee.

---

## Protections solaires

Gérer :

```text
casquette
auvent
brise-soleil
store extérieur
store intérieur
volet
masque fixe
bâtiment voisin simplifié
végétation simplifiée
```

Différencier :

- géométrie d’ombrage ;
- facteur de réduction ;
- calendrier d’utilisation.

---

## Occupation

Le modèle d’occupation doit contenir :

```text
nombre maximal de personnes
densité d’occupation
calendrier
activité métabolique
fraction sensible
fraction latente
présence intermittente
usage principal
```

Conserver :

- méthode ;
- hypothèse ;
- source ;
- confiance.

---

## Calendriers

Créer :

```text
build_schedule()
```

Supporter :

```text
constant
daily_profile
weekly_profile
annual_profile
```

Les calendriers doivent être :

- bornés ;
- validés ;
- normalisés ;
- versionnés ;
- réutilisables.

---

## Éclairage

Gérer :

```text
puissance totale
puissance surfacique
calendrier
fraction convective
fraction radiative
```

Éviter de renseigner simultanément puissance totale et densité sans règle de priorité.

---

## Équipements internes

Gérer :

```text
informatique
électroménager
cuisson
équipements techniques
charge permanente
charge intermittente
```

Conserver :

- puissance ;
- quantité ;
- calendrier ;
- fraction sensible ;
- fraction latente ;
- fraction perdue ;
- source ;
- confiance.

Ne pas considérer tous les équipements comme purement sensibles.

---

## Consignes de confort

Gérer :

```text
cooling_setpoint_c
heating_setpoint_c
humidity_setpoint_percent
setback
availability_schedule
```

Vérifier :

```text
heating_setpoint < cooling_setpoint
```

---

## Ventilation

Gérer séparément :

```text
air neuf hygiénique
ventilation mécanique
ventilation naturelle
récupération de chaleur
ventilation intermittente
```

Ne pas confondre ventilation et infiltration.

Unités supportées :

```text
m³/h
m³/s
L/s
L/s/personne
L/s/m²
ACH
```

---

## Infiltration

Supporter :

```text
ACH
débit total
débit surfacique
débit par façade
```

Conserver :

```text
value
unit
method
source
confidence
```

Les valeurs estimées doivent être identifiées.

---

## HVAC idéal

Utiliser un système idéal de type :

```text
Ideal Air Loads
```

Objectifs :

- déterminer la charge nécessaire ;
- éviter de dépendre d’un produit commercial ;
- séparer besoin thermique et sélection produit.

Modes de simulation :

```text
ideal_loads_peak
free_floating_comfort
annual_energy
```

Le MVP peut activer en priorité :

```text
ideal_loads_peak
```

---

## Météo

Le service doit accepter uniquement :

```text
weather_artifact_id
weather_checksum
weather_type
scenario_code
```

Types supportés :

```text
EPW historique
EPW de référence
EPW modifié
profil de scénario synthétique
Design Day
```

Le service ne doit jamais accepter une URL météo arbitraire.

---

## Validation EPW

Vérifier :

- fichier existant ;
- format ;
- taille ;
- nombre de lignes ;
- localisation ;
- altitude ;
- fuseau ;
- période ;
- checksum ;
- cohérence avec l’étude.

---

## Construction du modèle Honeybee

Créer :

```text
build_honeybee_model()
```

Le modèle doit contenir :

- identifiant stable ;
- zone ;
- faces ;
- apertures ;
- doors ;
- shades ;
- constructions ;
- loads ;
- schedules ;
- setpoints ;
- ventilation ;
- infiltration ;
- HVAC idéal ;
- metadata.

Métadonnées :

```text
study_id
revision_id
company_id
request_id
schema_version
builder_version
created_at
weather_checksum
input_checksum
```

---

## Validation Honeybee

Avant traduction :

- valider la géométrie ;
- valider les constructions ;
- valider les calendriers ;
- valider les charges ;
- valider le HVAC ;
- valider la météo ;
- produire un rapport de validation.

Une erreur Honeybee doit bloquer l’exécution.

---

## Traduction vers EnergyPlus

Utiliser la chaîne compatible avec la stack :

```text
Honeybee → OpenStudio → EnergyPlus
ou
Honeybee → EnergyPlus
```

Documenter la chaîne réellement utilisée.

---

## Workspace temporaire

Chaque simulation doit utiliser un répertoire serveur dédié :

```text
/workspaces/<request_id>/
```

Le frontend ne doit jamais fournir ce chemin.

Contenu possible :

```text
input.json
model.hbjson
model.osm
model.idf
model.epjson
weather.epw
EnergyPlus outputs
normalized_result.json
logs
```

---

## Exécution EnergyPlus

Créer :

```text
run_energyplus()
```

Exécuter via :

- liste d’arguments ;
- `shell=False` ;
- chemin binaire configuré ;
- timeout ;
- utilisateur non root ;
- environnement limité ;
- répertoire contrôlé ;
- sortie capturée.

Interdire :

```text
shell=True
commande concaténée
chemin fourni par le client
script arbitraire
plugin arbitraire
macro libre
```

---

## Isolation

Idéalement exécuter EnergyPlus dans un conteneur dédié avec :

- utilisateur non root ;
- réseau désactivé ;
- filesystem temporaire ;
- CPU limité ;
- mémoire limitée ;
- nombre de processus limité ;
- timeout ;
- nettoyage ;
- aucune clé secrète.

Variables :

```text
SIMULATION_TIMEOUT_SECONDS
SIMULATION_CPU_LIMIT
SIMULATION_MEMORY_LIMIT
SIMULATION_DISK_LIMIT
SIMULATION_MAX_OUTPUT_SIZE
```

---

## Statuts d’exécution

```text
pending
validating
building_model
preparing_weather
running
parsing
normalizing
completed
failed
timed_out
cancelled
```

---

## Modèles Odoo

### `greencube.cooling.simulation`

Champs possibles :

```text
name
study_id
revision_id
company_id
request_id
schema_version
builder_version
honeybee_version
energyplus_version
weather_artifact_id
weather_checksum
mode
status
started_at
finished_at
duration_seconds
input_checksum
result_checksum
error_code
error_message
confidence_score
result_id
active
```

### `greencube.cooling.simulation.artifact`

Types possibles :

```text
input_json
hbjson
osm
idf
epjson
epw
err
eio
eso
sql
html
normalized_result
log
```

Les artefacts doivent être privés.

---

## Parsing des résultats

Créer :

```text
parse_energyplus_results()
```

Utiliser en priorité :

- SQLite EnergyPlus ;
- CSV standardisé ;
- outputs déclarés ;
- fichiers structurés.

Éviter de dépendre du HTML.

Variables possibles :

```text
Zone Ideal Loads Supply Air Total Cooling Energy
Zone Ideal Loads Zone Total Cooling Energy
Zone Ideal Loads Zone Sensible Cooling Energy
Zone Air Temperature
Zone Air Relative Humidity
Zone Operative Temperature
Facility Total HVAC Electricity Demand Rate
Site Outdoor Air Drybulb Temperature
```

Adapter aux versions réelles.

---

## Résultats de pointe

Extraire :

```text
peak_total_cooling_load_w
peak_sensible_cooling_load_w
peak_latent_cooling_load_w
peak_timestamp
outdoor_temperature_at_peak_c
indoor_temperature_at_peak_c
indoor_relative_humidity_at_peak_percent
```

---

## Résultats énergétiques

Extraire ou calculer :

```text
cooling_energy_kwh_thermal
cooling_electricity_kwh
fan_electricity_kwh
total_hvac_electricity_kwh
annual_cooling_hours
```

Distinguer clairement énergie thermique et énergie électrique.

---

## Résultats de confort

Extraire :

```text
maximum_indoor_temperature_c
minimum_indoor_temperature_c
maximum_indoor_relative_humidity_percent
hours_above_cooling_setpoint
degree_hours_above_setpoint
hours_above_26_c
hours_above_28_c
hours_above_30_c
```

---

## Sensible, latent et SHR

Extraire ou calculer :

```text
sensible_load_w
latent_load_w
total_load_w
SHR
```

Formule :

```text
SHR = sensible_load / total_load
```

Gérer le cas d’une charge totale nulle.

---

## Conversion des unités

Centraliser :

```text
J → kWh
W → kW
W → BTU/h
kg/s → m³/h si densité connue
°C conservé
fraction → %
```

Sorties attendues :

```text
recommended_capacity_w
recommended_capacity_kw
recommended_capacity_btu_h
```

---

## Estimation de consommation électrique

Créer :

```text
estimate_electrical_consumption()
```

Méthodes possibles :

```text
EnergyPlus direct
charge thermique / EER
énergie thermique / SEER
```

Toujours retourner :

- méthode ;
- hypothèses ;
- confiance ;
- rendement utilisé.

Ne pas utiliser le SEER pour une puissance instantanée de pointe sans justification.

---

## Sélection de capacité

Créer :

```text
select_commercial_capacity()
```

Entrées :

```text
peak_total_cooling_load_w
margin_percent
available_capacity_steps
minimum_modulation
confidence
```

Sorties :

```text
raw_peak_w
margin_w
recommended_capacity_w
commercial_capacity_w
commercial_capacity_btu_h
selection_method
warnings
```

La marge doit être :

- configurable ;
- visible ;
- versionnée ;
- limitée ;
- adaptée à la confiance.

---

## Capacités commerciales

Prévoir une liste configurable :

```text
2.0 kW
2.5 kW
3.5 kW
5.0 kW
7.0 kW
```

Cette liste n’est pas encore un catalogue produit.

Le système doit signaler :

- surdimensionnement ;
- faible modulation ;
- risque de cycles courts ;
- déshumidification potentiellement insuffisante ;
- incertitude élevée.

---

## Résultat normalisé

Le résultat doit contenir :

```text
schema_version
simulation_id
status
engine
engine_version
mode
peak
energy
comfort
recommendation
confidence
warnings
provenance
```

Provenance :

```text
study_id
revision_id
input_checksum
weather_checksum
model_checksum
engine
engine_version
honeybee_version
builder_version
schema_version
simulation_mode
created_at
```

---

## Confiance

Calculer selon :

- qualité géométrique ;
- qualité des constructions ;
- qualité des vitrages ;
- qualité des calendriers ;
- qualité des charges ;
- qualité de la ventilation ;
- qualité de l’infiltration ;
- qualité météo ;
- valeurs estimées ;
- convergence ;
- avertissements EnergyPlus.

Niveaux :

```text
very_low
low
medium
high
very_high
```

---

## Warnings EnergyPlus

Parser :

```text
Warning
Severe
Fatal
```

Règles :

```text
Fatal → simulation échouée
Severe → échec ou invalidation selon règle
Warning → résultat possible avec avertissement
```

---

## Persistance Odoo

Créer ou compléter :

```text
greencube.cooling.result
```

Champs possibles :

```text
simulation_id
study_id
revision_id
company_id
engine
engine_version
schema_version
status
peak_total_load_w
peak_sensible_load_w
peak_latent_load_w
shr
peak_timestamp
cooling_energy_kwh
cooling_electricity_kwh
maximum_indoor_temperature_c
maximum_indoor_humidity_percent
hours_above_setpoint
recommended_capacity_w
recommended_capacity_kw
recommended_capacity_btu_h
commercial_capacity_w
confidence_score
result_json
warnings_json
provenance_json
checksum
active
```

Un résultat `completed` doit être immuable.

---

## Endpoints

### Microservice interne

```text
POST /internal/v1/simulations
GET /internal/v1/simulations/<simulation_id>
GET /health
GET /health/deep
```

### API Odoo

```text
POST /api/v1/greencube/cooling/studies/<study_id>/energy-simulations
GET /api/v1/greencube/cooling/energy-simulations/<simulation_id>
GET /api/v1/greencube/cooling/energy-simulations/<simulation_id>/result
```

---

## Idempotence et verrouillage

Utiliser :

```text
Idempotency-Key
```

Associer la clé à :

```text
study_id
revision_id
input_checksum
weather_checksum
simulation_mode
```

Empêcher deux simulations identiques de s’exécuter simultanément.

---

## Authentification interne

Options possibles :

```text
réseau Docker interne
clé serveur
mTLS
JWT de service
```

Le service ne doit pas être public.

Odoo reste responsable :

- de l’authentification ;
- de la société ;
- de l’étude ;
- de la révision ;
- du rôle ;
- de la construction du payload.

---

## Protection SSRF

Le microservice ne doit jamais télécharger une météo depuis une URL fournie par le client.

Les fichiers météo doivent être :

- déjà stockés ;
- référencés par identifiant ;
- résolus côté serveur ;
- contrôlés par liste blanche.

---

## Logs structurés

Inclure :

```text
request_id
simulation_id
study_id
revision_id
company_id
step
status
duration_ms
engine_version
input_checksum
weather_checksum
error_code
warning_count
severe_count
```

Ne pas journaliser le payload complet en production.

---

## Erreurs métier

Codes possibles :

```text
SIMULATION_INPUT_INVALID
SIMULATION_GEOMETRY_INVALID
SIMULATION_CONSTRUCTION_INVALID
SIMULATION_SCHEDULE_INVALID
SIMULATION_WEATHER_MISSING
SIMULATION_WEATHER_INVALID
SIMULATION_MODEL_BUILD_FAILED
SIMULATION_HONEYBEE_VALIDATION_FAILED
SIMULATION_TRANSLATION_FAILED
SIMULATION_ENERGYPLUS_NOT_AVAILABLE
SIMULATION_ENERGYPLUS_FAILED
SIMULATION_ENERGYPLUS_FATAL
SIMULATION_TIMED_OUT
SIMULATION_OUTPUT_TOO_LARGE
SIMULATION_RESULT_PARSE_FAILED
SIMULATION_RESULT_INVALID
SIMULATION_ALREADY_RUNNING
SIMULATION_RESULT_NOT_FOUND
SIMULATION_VERSION_CONFLICT
ACCESS_DENIED
```

Ne jamais exposer :

- stack trace ;
- commande système ;
- chemin local ;
- secret ;
- contenu complet de fichier ;
- configuration interne.

---

## Nettoyage et rétention

Créer :

```text
cleanup_simulation_workspace()
```

Le nettoyage doit intervenir :

- après succès ;
- après échec ;
- après timeout ;
- après annulation.

Définir une politique pour :

```text
workspace temporaire
logs
fichiers intermédiaires
artefacts métier
résultats
simulations échouées
```

---

## Docker

Créer un Dockerfile dédié avec :

- image de base épinglée ;
- utilisateur non root ;
- EnergyPlus installé ;
- versions vérifiables ;
- aucun secret ;
- dépendances verrouillées ;
- healthcheck ;
- répertoire temporaire ;
- nettoyage des caches d’installation.

---

## Variables d’environnement

Créer `.env.example` avec :

```text
ENERGYPLUS_PATH
ENERGYPLUS_VERSION
OPENSTUDIO_PATH
SIMULATION_TIMEOUT_SECONDS
SIMULATION_CPU_LIMIT
SIMULATION_MEMORY_LIMIT
SIMULATION_DISK_LIMIT
SIMULATION_MAX_OUTPUT_SIZE
SIMULATION_WORKSPACE_ROOT
SIMULATION_ARTIFACT_RETENTION_DAYS
INTERNAL_API_KEY
LOG_LEVEL
```

Ne pas inclure de vraie clé.

---

## Fixtures obligatoires

Créer :

```text
GreenCube standard
GreenCube fortement vitré ouest
GreenCube performant
GreenCube à forte occupation
GreenCube à forte charge latente
GreenCube avec ventilation élevée
GreenCube à infiltration forte
GreenCube incomplet
géométrie invalide
vitrage invalide
EPW valide
EPW invalide
canicule de 3 jours
canicule prolongée
```

---

## Tests obligatoires

### Géométrie

- cube simple ;
- dimensions nulles ;
- dimensions négatives ;
- volume ouvert ;
- vitrage hors façade ;
- chevauchement ;
- orientations cardinales ;
- tolérance ;
- plusieurs vitrages.

### Constructions

- couches complètes ;
- valeur U seule ;
- mur ;
- toiture ;
- plancher ;
- porte ;
- valeur U invalide ;
- matériau manquant ;
- source estimée ;
- pont thermique.

### Vitrages

- U-value ;
- SHGC ;
- dimensions ;
- orientation ;
- cadre ;
- protection solaire ;
- vitrage hors mur ;
- facteur solaire invalide.

### Calendriers

- constant ;
- journée ;
- semaine ;
- année ;
- valeurs hors 0–1 ;
- heure manquante ;
- changement d’heure ;
- année bissextile.

### Charges

- occupants ;
- éclairage ;
- équipements ;
- sensible ;
- latent ;
- charges nulles ;
- charges négatives ;
- calendrier absent.

### Ventilation et infiltration

- m³/h ;
- m³/s ;
- L/s ;
- ACH ;
- débit par personne ;
- débit surfacique ;
- récupération ;
- valeur nulle ;
- valeur négative ;
- estimation.

### Météo

- EPW valide ;
- EPW absent ;
- EPW corrompu ;
- localisation incohérente ;
- fuseau incohérent ;
- checksum invalide ;
- scénario synthétique ;
- Design Day.

### Runner

- succès ;
- binaire absent ;
- timeout ;
- processus tué ;
- sortie trop grande ;
- erreur fatale ;
- workspace inaccessible ;
- nettoyage.

### Parser et normalisation

- SQL valide ;
- CSV valide ;
- sortie manquante ;
- variable manquante ;
- unité inattendue ;
- résultat nul ;
- W ;
- kW ;
- BTU/h ;
- J ;
- kWh ;
- timestamps ;
- SHR ;
- provenance.

### Capacité

- charge faible ;
- charge exacte ;
- marge ;
- arrondi commercial ;
- surdimensionnement ;
- faible confiance ;
- capacité hors gamme ;
- BTU/h.

### API et sécurité

- création ;
- statut ;
- résultat ;
- idempotence ;
- conflit ;
- permission ;
- multi-société ;
- payload invalide ;
- météo absente ;
- timeout ;
- résultat immuable ;
- chemin injecté ;
- URL externe ;
- commande shell ;
- fichier arbitraire ;
- payload volumineux ;
- secret dans les logs ;
- accès public ;
- accès inter-sociétés.

---

## Test réel EnergyPlus

Créer un test minimal réel qui :

1. construit un GreenCube simple ;
2. charge un EPW local ;
3. génère le modèle ;
4. exécute EnergyPlus ;
5. vérifie le code retour ;
6. vérifie l’absence de `Fatal` ;
7. extrait une charge ;
8. produit un résultat normalisé.

Ne jamais déclarer EnergyPlus opérationnel sans ce test.

---

## Tests de non-régression

Conserver des références pour :

```text
peak_total_load_w
peak_sensible_load_w
peak_latent_load_w
SHR
cooling_energy_kwh
maximum_indoor_temperature_c
hours_above_setpoint
recommended_capacity_w
```

Définir :

```text
absolute_tolerance
relative_tolerance
engine_version
fixture_version
```

---

## Performance

Mesurer :

- construction du modèle ;
- traduction ;
- lancement ;
- durée EnergyPlus ;
- parsing ;
- normalisation ;
- mémoire ;
- disque ;
- taille des artefacts.

---

## Documentation

Créer :

```text
docs/cooling_energy_simulation_overview.md
docs/cooling_energy_simulation_architecture.md
docs/cooling_energy_simulation_input_schema.md
docs/cooling_honeybee_geometry.md
docs/cooling_honeybee_constructions.md
docs/cooling_honeybee_loads.md
docs/cooling_energyplus_weather.md
docs/cooling_energyplus_runner.md
docs/cooling_energyplus_outputs.md
docs/cooling_energyplus_security.md
docs/cooling_energyplus_api.md
docs/cooling_energyplus_testing.md
docs/cooling_energyplus_operations.md
docs/cooling_energyplus_troubleshooting.md
```

Documenter également les hypothèses :

- zone unique ;
- HVAC idéal ;
- valeurs U simplifiées ;
- inertie ;
- infiltration ;
- ventilation ;
- calendriers ;
- charges ;
- météo ;
- marge ;
- rendement électrique ;
- capacité commerciale.

---

## Migrations Odoo

Vérifier :

- installation sur base vierge ;
- mise à jour ;
- création des modèles ;
- création des champs ;
- index ;
- contraintes ;
- ACL ;
- record rules ;
- préservation des données ;
- idempotence.

Créer si nécessaire :

```text
migrations/<version>/pre-migration.py
migrations/<version>/post-migration.py
```

---

## Permissions et multi-société

Rôles possibles :

```text
cooling_user
cooling_engineer
cooling_manager
cooling_admin
```

Chaque simulation, résultat et artefact doit contenir :

```text
company_id
```

Tester :

- lecture croisée ;
- lancement croisé ;
- résultat croisé ;
- artefact croisé ;
- configuration spécifique ;
- météo partagée sans fuite métier.

---

## Sauvegarde et rollback

Inclure dans la sauvegarde :

- simulations ;
- résultats ;
- artefacts métier ;
- fichiers météo ;
- configuration ;
- versions ;
- checksums.

Documenter le rollback pour :

- microservice ;
- image Docker ;
- dépendances ;
- modèles Odoo ;
- migrations ;
- variables ;
- endpoints ;
- artefacts ;
- tâches planifiées.

Ne jamais supprimer les résultats existants lors du rollback.

---

## Critères d’acceptation fonctionnels

Le lot est accepté si :

- Odoo construit un payload valide ;
- le microservice accepte uniquement un schéma contrôlé ;
- une géométrie GreenCube simple est construite ;
- la zone est fermée ;
- les orientations sont correctes ;
- les parois sont créées ;
- les constructions sont appliquées ;
- les vitrages sont positionnés ;
- les ombrages sont pris en compte ;
- les occupants sont appliqués ;
- l’éclairage est appliqué ;
- les équipements sont appliqués ;
- les calendriers fonctionnent ;
- la ventilation est appliquée ;
- l’infiltration est appliquée ;
- les consignes sont appliquées ;
- le HVAC idéal est créé ;
- la météo est validée ;
- le modèle Honeybee est valide ;
- la traduction fonctionne ;
- EnergyPlus s’exécute réellement ;
- les erreurs fatales sont détectées ;
- les résultats sont parsés ;
- la charge totale est extraite ;
- la charge sensible est extraite ;
- la charge latente est extraite ;
- le SHR est calculé ;
- le pic est horodaté ;
- l’énergie frigorifique est disponible ;
- la consommation électrique est distinguée ;
- les indicateurs de confort sont disponibles ;
- la capacité recommandée est calculée ;
- les unités W, kW et BTU/h sont fournies ;
- la confiance est calculée ;
- la provenance est conservée ;
- le résultat est persisté ;
- le résultat terminé est immuable ;
- les artefacts sont privés ;
- le multi-société est respecté ;
- les erreurs sont explicables.

---

## Critères d’acceptation techniques

Le lot est accepté si :

- les dépendances sont épinglées ;
- le lint Python passe ;
- le formatage passe ;
- le contrôle de types passe si présent ;
- les tests unitaires passent ;
- les tests Odoo passent ;
- les tests API passent ;
- le test réel EnergyPlus passe ;
- les tests sans Internet passent ;
- les tests de non-régression passent ;
- l’image Docker se construit ;
- le healthcheck passe ;
- le timeout fonctionne ;
- le nettoyage fonctionne ;
- les limites de ressources sont documentées ;
- aucun secret n’est exposé ;
- aucun ancien résultat n’est modifié ;
- aucun fichier n’est supprimé sans justification.

---

## Critères d’acceptation sécurité

Le lot est accepté si :

- le service n’est pas public ;
- l’authentification interne fonctionne ;
- aucune commande libre n’est acceptée ;
- aucun chemin client n’est accepté ;
- aucune URL arbitraire n’est acceptée ;
- `shell=False` est utilisé ;
- EnergyPlus s’exécute en utilisateur non root ;
- le réseau est limité ;
- CPU et mémoire sont limités ;
- le timeout est actif ;
- la taille des sorties est limitée ;
- les workspaces sont isolés ;
- les artefacts sont privés ;
- les logs ne contiennent aucun secret ;
- le multi-société est testé ;
- les erreurs internes ne sont pas exposées.

---

## Rapport final attendu

### Architecture

- Odoo ;
- microservice ;
- Honeybee ;
- OpenStudio ;
- EnergyPlus ;
- stockage ;
- Docker ;
- flux.

### Versions

- Python ;
- Honeybee ;
- Ladybug ;
- OpenStudio ;
- EnergyPlus ;
- image Docker ;
- schéma d’entrée ;
- builder.

### Données d’entrée

- géométrie ;
- enveloppe ;
- vitrages ;
- ombrages ;
- charges ;
- calendriers ;
- ventilation ;
- infiltration ;
- consignes ;
- météo.

### Construction du modèle

- zones ;
- faces ;
- apertures ;
- shades ;
- constructions ;
- loads ;
- schedules ;
- HVAC.

### Exécution

- commande ;
- isolation ;
- timeout ;
- CPU ;
- mémoire ;
- workspace ;
- nettoyage.

### Résultats

- pointe ;
- sensible ;
- latent ;
- SHR ;
- énergie ;
- confort ;
- capacité ;
- confiance ;
- provenance.

### Odoo

- modèles ;
- champs ;
- contraintes ;
- ACL ;
- record rules ;
- migrations ;
- immuabilité.

### API

- méthode ;
- URL ;
- payload ;
- réponse ;
- erreurs ;
- permissions ;
- idempotence.

### Tests

- commandes ;
- codes retour ;
- durée ;
- test réel EnergyPlus ;
- couverture ;
- tests non exécutés ;
- raisons.

### Sécurité

- isolation ;
- commandes ;
- chemins ;
- URLs ;
- fichiers ;
- secrets ;
- logs ;
- ressources ;
- multi-société.

### Patch

- fichiers créés ;
- fichiers modifiés ;
- migrations ;
- dépendances ;
- Docker ;
- installation ;
- rollback.

---

## Contrôle final

Avant conclusion :

1. vérifier l’arborescence ;
2. vérifier les versions ;
3. vérifier les dépendances ;
4. vérifier le contrat d’entrée ;
5. vérifier la validation ;
6. vérifier la sécurité du payload ;
7. vérifier la géométrie ;
8. vérifier le volume fermé ;
9. vérifier les orientations ;
10. vérifier les parois ;
11. vérifier les constructions ;
12. vérifier les vitrages ;
13. vérifier les ombrages ;
14. vérifier les portes ;
15. vérifier les conditions limites ;
16. vérifier l’occupation ;
17. vérifier l’éclairage ;
18. vérifier les équipements ;
19. vérifier les charges latentes ;
20. vérifier les calendriers ;
21. vérifier les consignes ;
22. vérifier la ventilation ;
23. vérifier l’infiltration ;
24. vérifier le HVAC idéal ;
25. vérifier les modes de simulation ;
26. vérifier la météo ;
27. vérifier l’EPW ;
28. vérifier les Design Days ;
29. vérifier la conversion des scénarios ;
30. vérifier le modèle Honeybee ;
31. vérifier sa validation ;
32. vérifier la traduction ;
33. vérifier le workspace ;
34. vérifier `shell=False` ;
35. vérifier l’utilisateur non root ;
36. vérifier le timeout ;
37. vérifier les ressources ;
38. vérifier les statuts ;
39. vérifier les artefacts ;
40. vérifier le parsing ;
41. vérifier les variables de sortie ;
42. vérifier la pointe ;
43. vérifier le sensible ;
44. vérifier le latent ;
45. vérifier le SHR ;
46. vérifier l’énergie ;
47. vérifier le confort ;
48. vérifier les unités ;
49. vérifier la consommation électrique ;
50. vérifier la capacité recommandée ;
51. vérifier la marge ;
52. vérifier le surdimensionnement ;
53. vérifier le résultat normalisé ;
54. vérifier la provenance ;
55. vérifier la confiance ;
56. vérifier les warnings EnergyPlus ;
57. vérifier la persistance Odoo ;
58. vérifier l’immuabilité ;
59. vérifier les endpoints ;
60. vérifier l’idempotence ;
61. vérifier les verrous ;
62. vérifier l’authentification interne ;
63. vérifier les permissions ;
64. vérifier SSRF ;
65. vérifier les logs ;
66. vérifier les erreurs ;
67. vérifier le nettoyage ;
68. vérifier la rétention ;
69. vérifier Docker ;
70. vérifier les variables d’environnement ;
71. vérifier les fixtures ;
72. vérifier les tests de géométrie ;
73. vérifier les tests de constructions ;
74. vérifier les tests de vitrages ;
75. vérifier les tests de charges ;
76. vérifier les tests de ventilation ;
77. vérifier les tests météo ;
78. exécuter le test réel EnergyPlus ;
79. vérifier le runner ;
80. vérifier le parser ;
81. vérifier le normaliseur ;
82. vérifier la capacité ;
83. vérifier les tests API ;
84. vérifier les tests de sécurité ;
85. vérifier les tests de non-régression ;
86. vérifier les tolérances ;
87. vérifier les performances ;
88. vérifier la documentation ;
89. vérifier les migrations ;
90. vérifier le multi-société ;
91. vérifier la sauvegarde ;
92. vérifier le rollback ;
93. vérifier qu’aucun ancien résultat n’a été modifié ;
94. vérifier qu’aucun fichier météo source n’a été modifié ;
95. vérifier qu’aucun fichier n’a été supprimé sans justification ;
96. ne jamais déclarer EnergyPlus opérationnel sans preuve réelle.

---

## Livrables obligatoires

Produire au minimum :

```text
microservice interne
contrat d’entrée versionné
schemas Pydantic
constructeur Honeybee
constructeur géométrique
constructeur de parois
constructeur de vitrages
constructeur d’ombrages
constructeur de calendriers
constructeur de charges
constructeur de ventilation
constructeur d’infiltration
constructeur de consignes
constructeur HVAC idéal
résolveur météo
runner EnergyPlus
parser
normaliseur
estimateur de consommation
sélecteur de capacité
modèles Odoo
ACL et record rules
migrations
API Odoo
API interne
Dockerfile
.env.example
healthchecks
fixtures
tests
documentation
patch réintégrable
rapport de tests
procédure de rollback
```

---

## Limites du lot

Ce lot fournit le premier socle opérationnel Honeybee / EnergyPlus de GreenCube Cooling.

Il ne doit pas :

- sélectionner directement un climatiseur commercial ;
- générer un devis ;
- permettre au frontend de lancer une commande libre ;
- accepter un modèle EnergyPlus arbitraire ;
- remplacer une étude thermique réglementaire ;
- garantir une conformité réglementaire ;
- présenter une estimation comme une mesure réelle ;
- masquer les hypothèses ;
- déclarer une simulation réussie sans exécution réelle.

Le résultat attendu est un service interne sécurisé et reproductible capable de transformer une étude GreenCube validée en modèle Honeybee, d’exécuter EnergyPlus et de restituer dans Odoo une puissance frigorifique, des indicateurs énergétiques, des indicateurs de confort et une recommandation de capacité auditables.
