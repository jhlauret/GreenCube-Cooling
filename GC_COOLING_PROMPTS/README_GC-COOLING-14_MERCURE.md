# GC-COOLING-14 — MERCURE

## Nom du moteur

```text
MERCURE
```

Signification fonctionnelle proposée :

```text
Moteur Explicable de Refroidissement, Calcul Unifié et Recommandation Énergétique
```

---

## Objectif

Implémenter le moteur de calcul thermique rapide du configurateur GreenCube Cooling.

MERCURE doit fournir un résultat :

- immédiat ;
- déterministe ;
- explicable ;
- versionné ;
- reproductible ;
- auditable ;
- indépendant du frontend ;
- disponible même sans Honeybee/EnergyPlus ;
- comparable à une simulation dynamique avancée.

MERCURE est un moteur de pré-dimensionnement rapide.

Il ne doit pas être présenté comme une simulation thermique dynamique horaire complète.

Odoo Community 18 reste la source de vérité métier.

---

## Résultats attendus

Pour chaque scénario climatique, MERCURE doit calculer :

```text
Transmission murs
+ transmission toiture
+ transmission plancher
+ transmission portes
+ transmission vitrages
+ ponts thermiques
+ apports solaires vitrages
+ apports solaires opaques si activés
+ occupants sensibles
+ occupants latents
+ équipements sensibles
+ équipements latents
+ éclairage
+ ventilation sensible
+ ventilation latente
+ infiltration sensible
+ infiltration latente
+ ouverture des fenêtres
+ ouverture des portes
+ chaleur des ventilateurs
+ autres charges
= charge frigorifique totale
```

Le moteur doit distinguer :

```text
charge sensible
charge latente
charge totale
```

Il doit fournir :

- puissance en W ;
- puissance en kW ;
- puissance en BTU/h ;
- détail par composante ;
- détail par scénario ;
- scénario dimensionnant ;
- marge de sécurité ;
- puissance recommandée ;
- sensible heat ratio ;
- score de confiance ;
- hypothèses ;
- avertissements ;
- version du moteur ;
- empreinte du snapshot.

---

## Scénarios obligatoires

```text
reference_summer
hot_weather
prolonged_heatwave
```

Chaque scénario doit contenir :

- température extérieure ;
- humidité ;
- ratio d’humidité ou point de rosée ;
- température intérieure cible ;
- rayonnement par orientation ;
- vitesse du vent ;
- température du sol ou hypothèse ;
- durée d’exposition ;
- période de référence ;
- source ;
- version.

---

## Architecture recommandée

```text
Odoo Community 18
├── greencube.cooling.study
├── greencube.cooling.calculation.snapshot
├── greencube.cooling.calculation.job
├── greencube.cooling.result
├── greencube.cooling.result.scenario
├── greencube.cooling.result.line
└── service MERCURE
```

Structure Python recommandée :

```text
greencube_cooling/
├── models/
├── services/
│   └── mercure/
│       ├── __init__.py
│       ├── engine.py
│       ├── schemas.py
│       ├── constants.py
│       ├── conversions.py
│       ├── validation.py
│       ├── psychrometrics.py
│       ├── transmission.py
│       ├── solar.py
│       ├── occupancy.py
│       ├── equipment.py
│       ├── ventilation.py
│       ├── infiltration.py
│       ├── comfort.py
│       ├── margins.py
│       ├── recommendations.py
│       └── explainability.py
├── tests/
└── docs/
```

Le cœur du moteur doit pouvoir être testé sans démarrer Odoo.

---

## Principes impératifs

- utiliser uniquement un snapshot immuable ;
- ne jamais lire directement une étude modifiable pendant le calcul ;
- centraliser toutes les constantes ;
- centraliser toutes les conversions ;
- utiliser des unités explicites ;
- valider toutes les entrées ;
- versionner les méthodes ;
- rendre le calcul déterministe ;
- tracer chaque hypothèse ;
- structurer les erreurs ;
- structurer les avertissements ;
- ne jamais exposer une exception brute ;
- ne jamais calculer une étude obsolète ;
- ne jamais considérer le frontend comme autorité finale.

---

## Vérifications préalables

Avant implémentation :

- inspecter les modèles Odoo existants ;
- inspecter le snapshot GC-COOLING-13 ;
- inspecter le service climatique ;
- inspecter l’intégration Honeybee/EnergyPlus ;
- vérifier toutes les unités ;
- vérifier les structures de scénarios ;
- vérifier les conventions d’orientation ;
- vérifier le facteur solaire ;
- vérifier la ventilation ;
- vérifier l’infiltration ;
- vérifier les profils d’occupation ;
- vérifier les profils d’équipements ;
- vérifier les consignes ;
- vérifier les statuts de jobs ;
- vérifier les modèles de résultats ;
- vérifier les permissions ;
- vérifier le multi-société ;
- vérifier l’idempotence ;
- exécuter les tests existants ;
- ne supprimer aucun modèle ;
- ne jamais modifier les anciens snapshots ou résultats.

---

## Entrée principale

Créer un schéma immuable :

```python
class MercureInput:
    snapshot_id: int
    snapshot_hash: str
    study_id: int
    study_version: str
    company_id: int
    climate_scenarios: list
    geometry: dict
    envelope: dict
    glazing: dict
    occupancy: dict
    equipment: dict
    ventilation: dict
    infiltration: dict
    comfort: dict
    assumptions: list
    reference_versions: dict
```

Utiliser :

- `dataclasses` ;
- `pydantic` ;
- ou une structure typée équivalente.

Le schéma doit être indépendant de l’ORM.

---

## Snapshot obligatoire

Le snapshot doit contenir :

- données consolidées ;
- scénarios ;
- hypothèses confirmées ;
- versions des référentiels ;
- paramètres du moteur ;
- empreinte ;
- utilisateur ;
- société ;
- date.

Toute modification ultérieure nécessite :

- une nouvelle révision ;
- un nouveau snapshot ;
- un nouveau calcul.

---

## Résultat principal

Créer :

```python
class MercureResult:
    engine_code: str
    engine_version: str
    snapshot_id: int
    snapshot_hash: str
    scenario_results: list
    governing_scenario_code: str
    recommended_capacity_w: float
    recommended_capacity_kw: float
    recommended_capacity_btu_h: float
    confidence_score: float
    assumptions: list
    warnings: list
    calculation_trace: dict
```

---

## Résultat par scénario

Créer :

```python
class MercureScenarioResult:
    scenario_code: str
    sensible_load_w: float
    latent_load_w: float
    total_load_w: float
    margin_w: float
    recommended_load_w: float
    breakdown: dict
    warnings: list
    confidence_score: float
```

---

## Décomposition obligatoire

```text
envelope_walls
envelope_roof
envelope_floor
envelope_doors
glazing_conduction
thermal_bridges
solar_glazing
solar_opaque
occupants_sensible
occupants_latent
equipment_sensible
equipment_latent
lighting
fan_heat
ventilation_sensible
ventilation_latent
infiltration_sensible
infiltration_latent
window_opening_sensible
window_opening_latent
door_opening_sensible
door_opening_latent
other_sensible
other_latent
```

Ne jamais retourner uniquement un total.

---

## Unités internes

```text
longueur : m
surface : m²
volume : m³
température : °C
écart de température : K
puissance : W
énergie : Wh ou kWh
débit volumique : m³/h
débit massique : kg/s
coefficient U : W/m².K
conductivité : W/m.K
humidité relative : %
ratio d’humidité : kg/kg
facteur solaire : 0 à 1
rendement : 0 à 1
```

---

## Constantes physiques

Centraliser dans :

```text
constants.py
```

Exemples :

- densité de l’air ;
- capacité thermique massique de l’air ;
- chaleur latente de vaporisation ;
- conversion W vers BTU/h.

Chaque constante doit contenir :

- nom ;
- valeur ;
- unité ;
- source ;
- version ;
- plage d’utilisation.

---

## Conversions

Créer au minimum :

```python
watts_to_btu_per_hour()
m3h_to_m3s()
ach_to_m3h()
humidity_ratio_from_temperature_rh()
air_enthalpy()
```

Le résultat doit toujours fournir :

```text
W
kW
BTU/h
```

---

## Transmission

Formule :

```text
Q = U × A × ΔT
```

Calculer séparément :

```text
murs
toiture
plancher
portes
vitrages
```

Créer :

```python
calculate_transmission_loads()
```

---

## Écart de température

```text
ΔT = température extérieure - température intérieure cible
```

Si `ΔT ≤ 0` :

- ne pas créer une charge négative de refroidissement ;
- retourner zéro pour la composante sauf méthode explicitement activée.

Créer :

```python
positive_cooling_delta_t()
```

---

## Plancher

Prévoir :

```text
ground
outdoor_air
unconditioned_space
conditioned_space
unknown
```

Le calcul doit dépendre de la frontière réelle.

Si le plancher est sur sol :

- utiliser une température de sol ;
- tracer la source ;
- signaler une estimation ;
- réduire la confiance si nécessaire.

---

## Ponts thermiques

Modes :

```text
explicit_linear
percentage_adjustment
global_default
none
```

Formule linéaire :

```text
Q_pont = ψ × longueur × ΔT
```

Formule par correction :

```text
Q_pont = transmission_enveloppe × taux_correction
```

Ne jamais appliquer les deux méthodes simultanément.

---

## Apports solaires vitrages

Formule simplifiée :

```text
Q_solaire =
surface_vitrée
× rayonnement incident
× facteur solaire
× facteur de protection
× facteur de masque
× facteur de disponibilité
```

Créer :

```python
calculate_glazing_solar_gain()
```

Calculer par :

- façade ;
- ouverture ;
- scénario ;
- période critique si disponible.

---

## Rayonnement

Le rayonnement doit venir du scénario climatique :

- par azimut ;
- par façade ;
- ou par orientation cardinale.

Toute interpolation doit être :

- centralisée ;
- documentée ;
- testée ;
- traçable.

---

## Facteur solaire

Utiliser une valeur normalisée :

```text
0 à 1
```

Conserver :

- valeur source ;
- type source : `g-value` ou `SHGC` ;
- conversion ;
- version.

---

## Protections solaires

Adopter une convention unique.

Exemple recommandé :

```text
1 = aucune réduction
0 = apport totalement bloqué
```

Ne pas utiliser simultanément plusieurs conventions sans conversion centralisée.

---

## Masques extérieurs

Utiliser un facteur compris entre :

```text
0 et 1
```

Pour le MVP, utiliser un coefficient déjà calculé et validé côté backend.

---

## Apports solaires opaques

Feature flag :

```text
enable_opaque_solar_gain
```

Cette fonction peut utiliser :

- absorptivité ;
- surface ;
- rayonnement ;
- résistance thermique ;
- couleur ;
- facteur de correction.

Elle peut rester désactivée dans le MVP minimal.

---

## Occupants

Calcul :

```text
Q_sensible_occupants =
occupants_effectifs
× gain_sensible_par_personne

Q_latent_occupants =
occupants_effectifs
× gain_latent_par_personne
```

Créer :

```python
calculate_occupancy_gains()
```

Distinguer :

```text
usual_occupants
maximum_occupants
design_occupants
```

Conserver le nombre retenu dans la trace.

---

## Fraction d’occupation

```text
occupants_effectifs =
design_occupants
× occupancy_fraction
```

Pour le calcul de pointe, utiliser la période critique ou une règle définie côté backend.

---

## Équipements

Calcul par ligne :

```text
puissance_active =
quantité
× puissance_retenue
× facteur_de_charge
× facteur_de_simultanéité
× fraction_de_fonctionnement
```

Puis :

```text
chaleur_zone =
puissance_active
× fraction_dissipée_dans_zone
```

Puis :

```text
charge_sensible =
chaleur_zone
× fraction_sensible

charge_latente =
chaleur_zone
× fraction_latente
```

Créer :

```python
calculate_equipment_gains()
```

---

## Puissance retenue

Règle possible :

```text
average_power
sinon nominal_power × load_factor
sinon nominal_power
```

Ne pas appliquer deux fois le facteur de charge.

---

## Éclairage

Modes :

```text
fixtures
power_density
catalog_profile
```

Calcul par densité :

```text
Q_eclairage =
surface
× W/m²
× fraction_utilisation
× fraction_dissipée_zone
```

Créer :

```python
calculate_lighting_gain()
```

---

## Charges permanentes

Calculer séparément :

```text
permanent_load_w
night_permanent_load_w
```

Exemples :

- serveur ;
- routeur ;
- réfrigérateur ;
- batterie ;
- onduleur ;
- électronique de contrôle.

---

## Batteries et onduleurs

Ne jamais utiliser directement :

- la capacité en kWh ;
- la puissance maximale de sortie.

Utiliser uniquement :

- pertes de conversion ;
- puissance de veille ;
- pertes à la charge ;
- pertes à la décharge ;
- emplacement ;
- fraction dissipée dans la zone.

---

## Ventilation sensible

Formule :

```text
Q_sensible =
ρ_air
× cp_air
× débit_m³_s
× ΔT
× facteur_non_récupéré
```

Avec :

```text
facteur_non_récupéré =
1 - rendement_sensible_effectif
```

Créer :

```python
calculate_ventilation_sensible_load()
```

---

## Récupération effective

Tenir compte de :

- récupération active ;
- bypass ;
- mode été ;
- conditions extérieures ;
- disponibilité ;
- calendrier.

Ne pas appliquer le rendement si le bypass est actif.

---

## Ventilation latente

Formule générale :

```text
Q_latente =
débit_massique_air
× différence_ratio_humidité
× chaleur_latente
× facteur_non_récupéré_latent
```

Créer :

```python
calculate_ventilation_latent_load()
```

---

## Psychrométrie

Créer :

```text
psychrometrics.py
```

Fonctions minimales :

```python
humidity_ratio_from_temperature_rh()
air_enthalpy()
latent_load_from_humidity_ratio()
```

Utiliser une bibliothèque fiable si elle est déjà disponible.

Ne pas utiliser uniquement l’humidité relative sans température.

---

## Pression atmosphérique

Utiliser si possible :

- altitude ;
- pression du scénario ;
- pression calculée par un service centralisé.

Conserver la source.

---

## Infiltration

Calcul sensible :

```text
Q_sensible_infiltration =
ρ_air
× cp_air
× débit_infiltration_m³_s
× ΔT
```

Calcul latent :

```text
Q_latente_infiltration =
débit_massique
× différence_ratio_humidité
× chaleur_latente
```

Créer :

```python
calculate_infiltration_sensible_load()
calculate_infiltration_latent_load()
```

---

## Conversion ACH

```text
débit_m³_h =
ACH
× volume_m³
```

Créer :

```python
ach_to_m3h()
```

---

## Valeur n50

Ne pas convertir `n50` avec une constante universelle non documentée.

Le snapshot doit fournir :

- l’infiltration naturelle déjà calculée ;
- ou une méthode de conversion versionnée.

Si seule la valeur `n50` est disponible :

- utiliser un profil backend ;
- tracer la méthode ;
- produire un avertissement ;
- réduire la confiance.

---

## Ouverture des fenêtres

Pour le MVP :

- utiliser un débit d’air équivalent validé côté backend ;
- ne pas implémenter de CFD ou AirflowNetwork complet ;
- calculer sensible et latent séparément ;
- éviter le double comptage avec la ventilation naturelle.

---

## Ventilation nocturne

Pour le dimensionnement rapide :

- calculer la charge à la période critique ;
- afficher l’effet potentiel comme recommandation ;
- ne pas soustraire arbitrairement une charge sans modèle validé.

---

## Ouverture des portes

Utiliser :

- un débit équivalent ;
- ou un coefficient simplifié backend.

Calculer :

```text
door_opening_sensible
door_opening_latent
```

Conserver :

- méthode ;
- fréquence ;
- durée ;
- hypothèse.

---

## Chaleur des ventilateurs

```text
Q_ventilateur_zone =
puissance_ventilateur
× fraction_dissipée_zone
× fraction_fonctionnement
```

Ajouter cette valeur aux charges sensibles.

---

## Consignes intérieures

Utiliser :

```text
cooling_setpoint_day_c
cooling_setpoint_night_c
maximum_acceptable_temperature_c
```

La consigne retenue dépend :

- de la période critique ;
- du scénario ;
- de l’usage ;
- du niveau de résilience.

---

## Humidité intérieure cible

Le calcul latent doit utiliser :

- humidité maximale ;
- ratio d’humidité cible ;
- ou valeur de référence backend.

Ne pas convertir une humidité relative cible sans température intérieure associée.

---

## Charge sensible totale

```text
Q_sensible_total =
transmission
+ solaire
+ occupants_sensibles
+ équipements_sensibles
+ éclairage
+ ventilateurs
+ ventilation_sensible
+ infiltration_sensible
+ fenêtres_sensible
+ portes_sensible
+ autres_sensibles
```

---

## Charge latente totale

```text
Q_latente_total =
occupants_latents
+ équipements_latents
+ ventilation_latente
+ infiltration_latente
+ fenêtres_latente
+ portes_latente
+ autres_latents
```

---

## Charge totale

```text
Q_total =
Q_sensible_total
+ Q_latente_total
```

La charge totale ne doit jamais être inférieure à la charge sensible.

---

## Sensible Heat Ratio

```text
SHR =
Q_sensible_total / Q_total
```

Gérer explicitement le cas `Q_total = 0`.

---

## Marge de dimensionnement

Créer :

```python
calculate_design_margin()
```

Modes possibles :

```text
fixed_percentage
confidence_based
scenario_based
profile_based
custom
```

La marge doit être :

- configurable ;
- versionnée ;
- explicable.

Ne pas coder un pourcentage fixe dans le moteur.

---

## Marge basée sur la confiance

Principe possible :

```text
confiance élevée → marge faible
confiance moyenne → marge modérée
confiance faible → marge supérieure
```

La règle exacte doit venir d’Odoo ou d’une configuration versionnée.

---

## Marge par scénario

Exemples :

```text
été de référence → marge standard
forte chaleur → marge limitée
canicule prolongée → marge résilience
```

Éviter le double cumul de prudence.

---

## Puissance recommandée

```text
recommended_capacity_w =
total_load_w
× (1 + margin_fraction)
```

Afficher :

- charge brute ;
- marge ;
- charge recommandée ;
- justification de la marge.

---

## Capacité commerciale

Créer :

```python
recommend_commercial_capacity()
```

Le moteur peut retourner :

- la puissance brute ;
- une capacité commerciale supérieure issue d’un référentiel Odoo.

Ne pas coder les paliers commerciaux en dur.

---

## Limite fonctionnelle

MERCURE calcule le besoin total.

Il ne doit pas décider seul :

- du nombre d’unités ;
- du type de climatiseur ;
- de l’implantation ;
- du réseau frigorifique.

---

## Scénario dimensionnant

Créer :

```python
select_governing_scenario()
```

Le scénario dimensionnant est celui qui produit la plus forte :

```text
recommended_capacity_w
```

Conserver :

- scénario ;
- charge brute ;
- marge ;
- charge recommandée ;
- facteur déterminant.

---

## Facteurs principaux

Créer :

```python
identify_main_load_driver()
```

Identifier les trois contributions principales.

Exemples :

```text
apports solaires ouest
ventilation
équipements informatiques
vitrages
occupation
infiltration
toiture
```

---

## Recommandations

Créer :

```python
generate_mercure_recommendations()
```

Exemples :

- ajouter une protection solaire extérieure ;
- réduire le facteur solaire ;
- limiter les apports ouest ;
- améliorer l’étanchéité ;
- réduire l’infiltration ;
- activer la ventilation nocturne ;
- déplacer un onduleur ;
- réduire les charges permanentes ;
- augmenter la consigne de 1 °C ;
- améliorer la récupération.

Les règles doivent être versionnées.

---

## Impact indicatif

Le moteur peut fournir :

```text
low
medium
high
```

ou une estimation en W si elle est calculable.

Ne pas annoncer une économie exacte sans recalcul.

---

## Mode what-if

Prévoir éventuellement :

```text
what_if
```

Le mode doit :

- cloner les entrées ;
- appliquer une variation ;
- recalculer ;
- ne pas modifier le snapshot ;
- ne pas persister comme résultat officiel ;
- conserver la traçabilité.

Feature flag possible pour le MVP.

---

## Score de confiance

Le score doit être dérivé du snapshot et des hypothèses.

Composantes possibles :

- climat ;
- géométrie ;
- enveloppe ;
- vitrages ;
- occupation ;
- équipements ;
- ventilation ;
- infiltration ;
- psychrométrie ;
- qualité des profils.

---

## Avertissements

Codes possibles :

```text
LOW_CONFIDENCE_INFILTRATION
MISSING_GROUND_TEMPERATURE
ESTIMATED_SOLAR_FACTOR
ESTIMATED_EQUIPMENT_LOAD
HIGH_GLAZING_RATIO
VERY_LOW_SETPOINT
HIGH_LATENT_LOAD
HIGH_INTERNAL_LOAD_DENSITY
UNUSUAL_AIRFLOW
SIMPLIFIED_WINDOW_OPENING_MODEL
OPAQUE_SOLAR_GAIN_DISABLED
```

Chaque avertissement doit contenir :

- code ;
- niveau ;
- message ;
- composante ;
- hypothèse ;
- impact potentiel ;
- recommandation.

---

## Erreurs bloquantes

Codes possibles :

```text
INVALID_SNAPSHOT
SNAPSHOT_HASH_MISMATCH
UNSUPPORTED_SNAPSHOT_VERSION
MISSING_CLIMATE_SCENARIO
INVALID_GEOMETRY
INVALID_ENVELOPE
INVALID_GLAZING_DATA
INVALID_OCCUPANCY_DATA
INVALID_EQUIPMENT_DATA
INVALID_VENTILATION_DATA
INVALID_INFILTRATION_DATA
INVALID_COMFORT_DATA
INVALID_UNIT
INVALID_HUMIDITY_DATA
CALCULATION_NOT_REPRODUCIBLE
ENGINE_VERSION_UNAVAILABLE
```

Une erreur bloquante ne doit jamais produire un résultat officiel partiel.

---

## Version du moteur

Définir :

```text
engine_code = MERCURE
engine_version = x.y.z
calculation_method_version = x.y
```

Une nouvelle version ne doit jamais modifier les anciens résultats.

---

## Configuration Odoo

Créer des paramètres ou référentiels pour :

- constantes physiques ;
- marges ;
- seuils d’avertissement ;
- règles de confiance ;
- méthodes d’infiltration ;
- profils de température du sol ;
- règles d’arrondi ;
- règles de recommandation ;
- feature flags.

Éviter les paramètres cachés dans le code.

---

## Job de calcul

Créer ou compléter :

```text
greencube.cooling.calculation.job
```

Champs possibles :

```text
name
study_id
snapshot_id
engine_code
engine_version
status
progress
queued_at
started_at
finished_at
duration_ms
attempt_count
idempotency_key
request_id
error_code
error_message
result_id
company_id
```

---

## Statuts du job

```text
queued
running
completed
failed
cancelled
superseded
```

Pour le MVP, MERCURE peut être exécuté rapidement mais doit conserver un modèle de job homogène avec EnergyPlus.

---

## Endpoint de lancement

```text
POST /api/v1/greencube/cooling/studies/<id>/calculations
```

Payload possible :

```json
{
  "snapshot_id": 45,
  "engine": "MERCURE",
  "scenario_codes": [
    "reference_summer",
    "hot_weather",
    "prolonged_heatwave"
  ],
  "idempotency_key": "uuid"
}
```

---

## Réponse de lancement

Réponse synchrone possible :

```json
{
  "job_id": 102,
  "status": "completed",
  "result_id": 76,
  "engine": "MERCURE",
  "engine_version": "1.0.0",
  "request_id": "req-..."
}
```

Réponse asynchrone possible :

```json
{
  "job_id": 102,
  "status": "queued",
  "request_id": "req-..."
}
```

---

## Endpoints de lecture

```text
GET /api/v1/greencube/cooling/calculations/<job_id>
GET /api/v1/greencube/cooling/results/<result_id>
```

---

## Idempotence

Utiliser :

```text
Idempotency-Key
```

La même combinaison :

```text
snapshot
+ moteur
+ version
+ scénarios
+ idempotency key
```

ne doit pas créer plusieurs résultats officiels.

---

## Persistance des résultats

Créer ou compléter :

```text
greencube.cooling.result
greencube.cooling.result.scenario
greencube.cooling.result.line
```

Le résultat principal doit contenir :

- étude ;
- snapshot ;
- job ;
- moteur ;
- version ;
- scénario dimensionnant ;
- puissance recommandée ;
- confiance ;
- statut ;
- empreinte ;
- date ;
- société.

---

## Lignes de résultat

Chaque ligne doit contenir :

```text
scenario_code
category
component_code
label
sensible_w
latent_w
total_w
percentage_of_total
source
assumption_code
calculation_method
```

---

## Trace de calcul

Exemple :

```json
{
  "formula": "U × A × ΔT",
  "inputs": {
    "u_value_w_m2k": 0.18,
    "area_m2": 42.5,
    "delta_t_k": 12
  },
  "result_w": 91.8
}
```

La trace doit être structurée.

---

## Explicabilité

Créer :

```python
build_explainability_report()
```

Pour chaque composante :

- formule ;
- entrées ;
- unités ;
- résultat ;
- source ;
- hypothèse ;
- confiance ;
- avertissement.

---

## Audit

Auditer :

- lancement ;
- moteur ;
- version ;
- snapshot ;
- scénarios ;
- résultat ;
- erreur ;
- relance ;
- annulation ;
- utilisateur ;
- société ;
- request ID.

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

- utilisateur : lancer MERCURE ;
- ingénieur : consulter les traces ;
- manager : valider les résultats ;
- administrateur : configurer les paramètres.

Respecter le multi-société.

---

## Sécurité

Vérifier :

- snapshot rattaché à l’étude ;
- étude rattachée à la société ;
- utilisateur autorisé ;
- moteur autorisé ;
- version disponible ;
- limites de taille ;
- protection contre les doubles requêtes ;
- logs sans données sensibles inutiles.

---

## Performance

Objectif MVP :

```text
calcul complet en quelques secondes au maximum
```

Optimiser :

- fonctions pures ;
- validation unique ;
- pas de requêtes ORM dans les boucles ;
- préchargement des données ;
- calcul en mémoire ;
- persistance groupée ;
- pas de recalcul inutile.

---

## Fonctions pures

Exemple :

```python
result = calculate_component(input_data, scenario, settings)
```

Les fonctions ne doivent pas :

- accéder directement à l’ORM ;
- modifier les entrées ;
- utiliser l’heure courante ;
- lire des paramètres non versionnés.

---

## Arrondis

Conserver une précision suffisante en interne.

Appliquer les arrondis uniquement :

- à l’affichage ;
- aux capacités commerciales ;
- aux exports.

Ne pas arrondir chaque étape.

---

## Valeurs négatives

Règles :

- charge de refroidissement négative : zéro si la méthode le prévoit ;
- charge latente négative : pas de réduction sans méthode explicite ;
- marge négative : interdite ;
- surface négative : erreur ;
- débit négatif : erreur.

---

## Tolérances numériques

Centraliser les tolérances pour :

- sommes de fractions ;
- valeurs proches de 1 ;
- valeurs quasi nulles ;
- comparaisons de résultats.

Ne pas comparer strictement les flottants.

---

## Tests unitaires

Tester :

### Conversions

- W vers kW ;
- W vers BTU/h ;
- m³/h vers m³/s ;
- ACH vers m³/h ;
- humidité relative vers ratio d’humidité.

### Transmission

- murs ;
- toiture ;
- plancher ;
- portes ;
- vitrages ;
- ΔT négatif ;
- ponts thermiques.

### Solaire

- nord ;
- sud ;
- ouest ;
- protection ;
- masque ;
- facteur solaire nul ;
- vitrage absent.

### Occupants

- zéro occupant ;
- occupation habituelle ;
- occupation maximale ;
- activité jour ;
- activité nuit ;
- sensible ;
- latent.

### Équipements

- quantité ;
- puissance moyenne ;
- facteur de charge ;
- simultanéité ;
- veille ;
- dissipation ;
- fractions.

### Éclairage

- luminaires ;
- densité ;
- calendrier ;
- dissipation.

### Ventilation

- débit ;
- récupération ;
- bypass ;
- sensible ;
- latent.

### Infiltration

- ACH ;
- sensible ;
- latent ;
- `n50` sans conversion ;
- exposition.

### Confort

- consigne jour ;
- consigne nuit ;
- humidité ;
- température maximale.

### Marge

- marge fixe ;
- marge par confiance ;
- marge par scénario ;
- absence de double prudence.

### Résultat

- sensible total ;
- latent total ;
- total ;
- SHR ;
- scénario dimensionnant ;
- recommandations.

---

## Cas de référence

Créer au minimum :

### Cas 1 — Studio standard

- 30 m² ;
- 2 occupants ;
- vitrage modéré ;
- faible charge interne ;
- ventilation standard.

### Cas 2 — Bureau fortement vitré à l’ouest

- 30 m² ;
- 4 occupants ;
- forte baie ouest ;
- informatique ;
- aucun store.

### Cas 3 — Local technique

- faible occupation ;
- charges permanentes ;
- onduleur ;
- batterie ;
- ventilation mécanique.

### Cas 4 — Studio canicule

- occupation jour et nuit ;
- canicule prolongée ;
- infiltration moyenne ;
- ventilation nocturne.

### Cas 5 — GreenCube performant

- forte isolation ;
- bonne étanchéité ;
- protections solaires ;
- récupération.

### Cas 6 — Faible confiance

- infiltration estimée ;
- équipements personnalisés ;
- facteur solaire par défaut.

---

## Tests de propriétés

Vérifier notamment que :

- augmenter la surface vitrée ne diminue pas la charge solaire ;
- augmenter le facteur solaire ne diminue pas la charge solaire ;
- augmenter le débit d’air extérieur chaud ne diminue pas la charge ;
- améliorer la récupération ne doit pas augmenter la charge de ventilation ;
- augmenter les occupants ne doit pas diminuer les gains humains ;
- augmenter la consigne ne doit pas augmenter la charge de transmission ;
- réduire la dissipation dans la zone ne doit pas augmenter la charge interne.

---

## Tests d’intégration Odoo

Tester :

1. lecture du snapshot ;
2. validation ;
3. création du job ;
4. exécution MERCURE ;
5. création du résultat ;
6. création des lignes ;
7. scénario dimensionnant ;
8. persistance de la version ;
9. idempotence ;
10. conflit de snapshot ;
11. permissions ;
12. multi-société ;
13. résultat en lecture seule ;
14. recalcul après révision.

---

## Tests API

Tester :

- lancement valide ;
- snapshot absent ;
- snapshot obsolète ;
- moteur indisponible ;
- doublon idempotent ;
- utilisateur non autorisé ;
- scénario invalide ;
- résultat disponible ;
- job échoué ;
- trace restreinte.

---

## Non-régression

Créer un jeu de snapshots de référence.

Pour chaque version :

- conserver les résultats attendus ;
- détecter les écarts ;
- documenter les changements ;
- ne pas modifier les anciens résultats sans justification.

---

## Comparaison EnergyPlus

Créer :

```python
compare_mercure_energyplus()
```

Comparer :

- charge de pointe ;
- sensible ;
- latent ;
- scénario dimensionnant ;
- écart absolu ;
- écart relatif.

Prévoir des seuils :

```text
acceptable
warning
critical
```

---

## Documentation

Créer :

```text
docs/mercure_overview.md
docs/mercure_equations.md
docs/mercure_input_schema.md
docs/mercure_output_schema.md
docs/mercure_assumptions.md
docs/mercure_versioning.md
docs/mercure_odoo_integration.md
docs/mercure_testing.md
docs/mercure_limitations.md
```

Pour chaque équation, documenter :

- objectif ;
- formule ;
- unités ;
- source ;
- hypothèses ;
- limites ;
- exemple ;
- tests associés.

---

## Limites fonctionnelles

MERCURE :

- n’est pas une simulation horaire complète ;
- simplifie l’inertie ;
- simplifie les ouvertures de fenêtres ;
- simplifie certains masques ;
- simplifie la température des parois ;
- ne remplace pas une étude réglementaire ;
- ne remplace pas un bureau d’études pour les projets complexes ;
- sert au pré-dimensionnement explicable.

---

## Critères d’acceptation

Le lot est accepté si :

- MERCURE utilise un snapshot immuable ;
- le moteur est indépendant du frontend ;
- les entrées sont validées ;
- les unités sont explicites ;
- les constantes sont centralisées ;
- le moteur est versionné ;
- les calculs sont déterministes ;
- la transmission est calculée ;
- les apports solaires sont calculés ;
- les gains occupants sont calculés ;
- les gains équipements sont calculés ;
- l’éclairage est calculé ;
- la ventilation sensible et latente est calculée ;
- l’infiltration sensible et latente est calculée ;
- les ouvertures sont prises en compte ;
- la charge sensible totale est calculée ;
- la charge latente totale est calculée ;
- la charge totale est calculée ;
- le SHR est calculé ;
- les trois scénarios sont calculés ;
- le scénario dimensionnant est identifié ;
- la marge est versionnée ;
- la puissance recommandée est calculée ;
- les résultats sont fournis en W, kW et BTU/h ;
- les principales contributions sont identifiées ;
- les recommandations sont explicables ;
- la confiance est calculée ;
- les avertissements sont structurés ;
- les erreurs sont structurées ;
- le résultat est persisté dans Odoo ;
- les lignes de détail sont persistées ;
- la trace de calcul est disponible ;
- l’idempotence est assurée ;
- les permissions sont respectées ;
- le multi-société est respecté ;
- les anciens résultats restent immuables ;
- les tests passent ;
- aucune constante critique n’est cachée ;
- aucun secret n’est exposé ;
- aucun fichier n’est supprimé sans justification.

---

## Rapport final attendu

### Architecture

- package MERCURE ;
- services ;
- modèles ;
- jobs ;
- résultats ;
- endpoints.

### Équations

- transmission ;
- solaire ;
- occupants ;
- équipements ;
- éclairage ;
- ventilation ;
- infiltration ;
- latent ;
- marges.

### Données

- schéma d’entrée ;
- schéma de sortie ;
- unités ;
- conversions ;
- constantes ;
- versions.

### Résultats

- détail par scénario ;
- scénario dimensionnant ;
- sensible ;
- latent ;
- total ;
- SHR ;
- marge ;
- recommandation.

### Explicabilité

- trace ;
- hypothèses ;
- avertissements ;
- recommandations ;
- facteurs principaux.

### Odoo

- modèles créés ;
- modèles modifiés ;
- ACL ;
- règles multi-sociétés ;
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
- jeux de référence ;
- tests non exécutés ;
- raisons.

### Performance

- durée moyenne ;
- durée maximale ;
- requêtes ORM ;
- mémoire ;
- limites.

### Sécurité

- permissions ;
- validation ;
- audit ;
- logs ;
- snapshot ;
- immuabilité.

### Patch

- diff ;
- patch réintégrable ;
- installation ;
- mise à jour ;
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
8. installer le module sur une base vierge ;
9. mettre à jour une base existante ;
10. vérifier le snapshot ;
11. vérifier l’empreinte ;
12. vérifier les scénarios ;
13. vérifier les unités ;
14. vérifier les constantes ;
15. vérifier la transmission ;
16. vérifier le solaire ;
17. vérifier les occupants ;
18. vérifier les équipements ;
19. vérifier l’éclairage ;
20. vérifier la ventilation ;
21. vérifier l’infiltration ;
22. vérifier la psychrométrie ;
23. vérifier le sensible ;
24. vérifier le latent ;
25. vérifier le total ;
26. vérifier le SHR ;
27. vérifier les marges ;
28. vérifier la puissance recommandée ;
29. vérifier le scénario dimensionnant ;
30. vérifier les recommandations ;
31. vérifier la confiance ;
32. vérifier les avertissements ;
33. vérifier les erreurs ;
34. vérifier les jobs ;
35. vérifier l’idempotence ;
36. vérifier les permissions ;
37. vérifier le multi-société ;
38. vérifier l’audit ;
39. vérifier l’immuabilité ;
40. vérifier l’absence de secrets ;
41. vérifier qu’aucun fichier n’a été supprimé ;
42. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente le moteur thermique rapide MERCURE.

Il ne finalise pas encore :

- l’orchestration Honeybee/EnergyPlus ;
- la comparaison avancée avec EnergyPlus ;
- l’écran frontend complet de résultats ;
- le catalogue de climatiseurs ;
- la sélection commerciale ;
- le rapport PDF final ;
- la simulation économique annuelle.

MERCURE doit néanmoins fournir un premier résultat MVP complet, explicable et exploitable pour le pré-dimensionnement du refroidissement GreenCube.
