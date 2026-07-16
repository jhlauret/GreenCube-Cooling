# GC-COOLING-04 — Service climatique historique et scénarios de dimensionnement

## Objectif

Implémenter dans **Odoo Community 18** le service climatique complet de GreenCube Cooling.

Le service doit transformer une localisation géographique en un contexte climatique structuré, versionné et exploitable par :

```text
GC-COOLING-07
→ écran Localisation et contexte climatique

GC-COOLING-13
→ validation et snapshot avant calcul

GC-COOLING-14
→ moteur thermique MERCURE

GC-COOLING-15
→ Honeybee / EnergyPlus
```

Il doit permettre de :

- récupérer l’historique météorologique d’un site ;
- récupérer ou reconstruire les variables horaires nécessaires ;
- normaliser les données de plusieurs fournisseurs ;
- contrôler leur qualité ;
- gérer les fuseaux horaires ;
- analyser les extrêmes ;
- calculer les percentiles ;
- détecter les nuits chaudes ;
- détecter les vagues de chaleur ;
- comparer le climat récent à une période de référence ;
- identifier les séquences climatiques sévères ;
- générer des scénarios de dimensionnement ;
- calculer un niveau de confiance ;
- conserver la provenance ;
- mettre en cache les réponses ;
- fonctionner en mode dégradé ;
- persister les résultats utiles dans Odoo ;
- fournir un contrat API stable ;
- éviter tout appel direct aux fournisseurs météo depuis le frontend.

Odoo Community 18 reste la source de vérité métier.

Le frontend React ne doit jamais :

- appeler directement Open-Meteo ou un autre fournisseur ;
- choisir une URL de fournisseur ;
- transmettre une clé d’API météo ;
- définir librement les seuils internes ;
- construire lui-même les scénarios officiels ;
- recalculer les agrégats officiels ;
- devenir la source de vérité climatique.

---

## Entrées et sorties

À partir de :

```text
latitude
longitude
altitude
fuseau horaire
pays
localité
```

le service doit produire :

```text
dataset climatique normalisé
→ contrôle qualité
→ agrégats
→ extrêmes
→ nuits chaudes
→ vagues de chaleur
→ signal climatique récent
→ scénarios de dimensionnement
→ score de confiance
→ persistance Odoo
```

Le service doit permettre de déterminer :

- la chaleur estivale habituelle ;
- les températures extrêmes ;
- les heures au-dessus de 26, 30, 35 et 40 °C ;
- les nuits chaudes ;
- les vagues de chaleur réelles ;
- la sévérité du climat récent ;
- le scénario d’été de référence ;
- le scénario de forte chaleur ;
- le scénario de canicule prolongée ;
- les données certaines, estimées, manquantes ou obsolètes.

---

## Périmètre

Ce lot couvre :

```text
fournisseurs météo
collecte historique
normalisation
contrôle qualité
fuseaux horaires
agrégations
percentiles
extrêmes
nuits chaudes
séquences de chaleur
signal climatique récent
scénarios de dimensionnement
cache
persistance Odoo
API
tests
sécurité
documentation
```

Il ne calcule pas encore :

- les transmissions thermiques ;
- les apports solaires à travers les vitrages ;
- les apports des occupants ;
- les apports des équipements ;
- les charges de ventilation intérieure ;
- la charge sensible finale ;
- la charge latente finale ;
- la puissance frigorifique finale ;
- la capacité commerciale ;
- la consommation électrique du climatiseur.

---

## Prérequis

Le lot suppose normalement disponibles :

```text
GC-COOLING-01
→ module Odoo et modèles principaux

GC-COOLING-02
→ API JSON versionnée

GC-COOLING-03
→ géocodage, altitude et fuseau horaire
```

Vérifier :

```text
greencube_cooling
greencube.cooling.study
greencube.cooling.climate.dataset
greencube.cooling.climate.scenario
```

---

## Vérifications préalables

Avant toute modification :

- inspecter l’arborescence ;
- inspecter le module `greencube_cooling` ;
- inspecter les modèles Odoo ;
- inspecter les contrôleurs API ;
- inspecter les services Python ;
- inspecter les paramètres système ;
- inspecter les jobs asynchrones ;
- inspecter les bibliothèques HTTP ;
- inspecter les bibliothèques statistiques ;
- inspecter les outils de cache ;
- inspecter Redis si présent ;
- inspecter les règles multi-sociétés ;
- inspecter les ACL ;
- inspecter les record rules ;
- inspecter les logs ;
- inspecter le stockage des clés ;
- inspecter les tests ;
- inspecter les fixtures ;
- inspecter OpenAPI ;
- inspecter les migrations ;
- identifier les versions Python et Odoo ;
- vérifier les conventions de dates et fuseaux ;
- vérifier les unités ;
- vérifier les datasets existants ;
- vérifier les doublons ;
- vérifier si Open-Meteo est déjà intégré ;
- vérifier les retries ;
- vérifier les timeouts ;
- vérifier les protections SSRF ;
- exécuter les tests existants ;
- ne supprimer aucun fichier ;
- ne remplacer aucun fournisseur sans justification ;
- ne modifier aucun dataset utilisé par un résultat validé.

---

## Architecture cible

Créer ou compléter :

```text
ClimateProvider
ClimateProviderRegistry
ClimateProviderConfig
OpenMeteoClimateProvider
MockClimateProvider
ClimateService
ClimateRequestValidator
ClimateNormalizer
ClimateQualityController
ClimateAggregator
ClimatePercentileCalculator
CoolingDegreeHourCalculator
HotNightDetector
HeatSequenceDetector
RecentClimateSignalAnalyzer
ClimateScenarioBuilder
ClimateConfidenceCalculator
ClimateCache
ClimateStorageService
ClimateSerializationService
ClimateAuditService
```

Flux cible :

```text
Localisation validée
→ résolution de la requête climatique
→ sélection du fournisseur
→ récupération des données
→ normalisation
→ contrôle qualité
→ agrégations
→ percentiles
→ détection des nuits chaudes
→ détection des séquences de chaleur
→ analyse du signal récent
→ génération des scénarios
→ calcul de confiance
→ persistance
→ réponse API
```

---

## Structure de code recommandée

```text
greencube_cooling/
├── models/
│   ├── cooling_climate_dataset.py
│   ├── cooling_climate_scenario.py
│   ├── cooling_climate_event.py
│   ├── cooling_climate_provider.py
│   └── cooling_climate_audit.py
├── controllers/
│   └── api_climate.py
├── services/
│   └── climate/
│       ├── provider.py
│       ├── provider_registry.py
│       ├── provider_config.py
│       ├── open_meteo_provider.py
│       ├── mock_provider.py
│       ├── request_validator.py
│       ├── normalizer.py
│       ├── quality.py
│       ├── aggregator.py
│       ├── percentiles.py
│       ├── cooling_degree_hours.py
│       ├── hot_nights.py
│       ├── heat_sequences.py
│       ├── recent_signal.py
│       ├── scenario_builder.py
│       ├── confidence.py
│       ├── cache.py
│       ├── storage.py
│       ├── serialization.py
│       ├── audit.py
│       ├── errors.py
│       └── service.py
├── data/
├── security/
├── migrations/
├── tests/
└── docs/
```

Le cœur statistique doit être testable sans ORM.

---

## Fournisseurs météo

### Interface fournisseur

Créer :

```python
class ClimateProvider:
    code: str
    version: str

    def fetch_hourly_history(self, request):
        ...

    def fetch_reference_climate(self, request):
        ...

    def healthcheck(self):
        ...
```

### Fournisseur MVP

Utiliser :

```text
Open-Meteo
```

Prévoir l’ajout futur de :

```text
Meteostat
Copernicus ERA5
ERA5-Land
Météo-France
MeteoSwiss
fournisseur privé
fichier local EPW
fichier CSV local
```

Le frontend ne doit jamais sélectionner directement le fournisseur.

---

## Configuration fournisseur

Prévoir :

```text
provider_code
provider_version
base_url
enabled
priority
timeout_seconds
retry_count
retry_backoff_seconds
maximum_response_size_bytes
cache_ttl_days
stale_if_error_days
history_years
reference_period_start
reference_period_end
variables
company_id
```

Valeurs initiales recommandées :

```text
historique principal : 13 ans
période récente : 3 ans
fenêtres récentes : 9 et 12 mois
étés récents : 3
seuils chauds : 26, 30, 35, 40 °C
seuils nocturnes : 20, 23, 25 °C
séquences : 3, 5, 7, 10 jours
timeout : 20 secondes
retries : 2
cache standard : 30 jours
```

---

## Feature flags

Créer ou réutiliser :

```text
enable_climate_history
enable_climate_recent_signal
enable_climate_reference_period
enable_climate_weather_morphing
enable_climate_raw_data_storage
enable_climate_provider_fallback
enable_climate_async_refresh
```

---

## Schéma de requête

Créer un schéma typé contenant :

```text
study_id
company_id
latitude
longitude
altitude_m
timezone
country_code
locality
start_date
end_date
variables
include_recent_signal
include_reference_period
include_raw_data
force_refresh
```

Valider :

```text
latitude entre -90 et 90
longitude entre -180 et 180
altitude plausible
fuseau IANA valide
période valide
durée maximale
nombre de variables limité
```

---

## Fenêtres climatiques

Analyser :

```text
référence climatologique
13 dernières années
3 dernières années
9 derniers mois
12 derniers mois
3 derniers étés complets
été en cours
```

Pour l’hémisphère nord, le MVP peut définir l’été étendu comme :

```text
1er mai → 30 septembre
```

Prévoir une logique adaptée à l’hémisphère sud.

---

## Variables climatiques

### Obligatoires

```text
air_temperature_c
relative_humidity_percent
global_horizontal_irradiance_w_m2
wind_speed_m_s
timestamp_utc
timestamp_local
timezone
```

### Recommandées

```text
dew_point_c
direct_normal_irradiance_w_m2
diffuse_horizontal_irradiance_w_m2
cloud_cover_percent
surface_pressure_hpa
precipitation_mm
apparent_temperature_c
wind_direction_deg
```

L’absence d’une variable secondaire ne doit pas bloquer tout le dataset.

---

## Liste blanche des variables fournisseur

Créer une liste blanche backend :

```text
temperature_2m
relative_humidity_2m
dew_point_2m
apparent_temperature
shortwave_radiation
direct_radiation
diffuse_radiation
wind_speed_10m
wind_direction_10m
surface_pressure
cloud_cover
precipitation
```

---

## Unités internes

Utiliser :

```text
température : °C
rayonnement instantané : W/m²
énergie solaire : Wh/m² ou kWh/m²
vitesse du vent : m/s
direction : degrés
pression : hPa
précipitations : mm
humidité : %
altitude : m
durée : heures
```

Toutes les conversions doivent être centralisées et testées.

---

## Gestion des timestamps

Conserver :

```text
UTC
heure locale
fuseau IANA
offset UTC
```

Gérer :

- heure d’été ;
- heure d’hiver ;
- heures dupliquées ;
- heures absentes ;
- années bissextiles ;
- ambiguïtés locales.

---

## Observation normalisée

Créer un objet contenant :

```text
timestamp_utc
timestamp_local
timezone
air_temperature_c
relative_humidity_percent
dew_point_c
global_horizontal_irradiance_w_m2
direct_normal_irradiance_w_m2
diffuse_horizontal_irradiance_w_m2
wind_speed_m_s
wind_direction_deg
surface_pressure_hpa
cloud_cover_percent
precipitation_mm
quality_flags
```

---

## Normalisation

Le normaliseur doit :

- convertir les noms de variables ;
- convertir les unités ;
- normaliser les dates ;
- trier les observations ;
- détecter les doublons ;
- ajouter les flags qualité ;
- conserver les données brutes séparément ;
- ne pas corriger silencieusement les valeurs suspectes.

---

## Contrôle qualité

Détecter :

- trous horaires ;
- heures dupliquées ;
- désordre temporel ;
- valeurs non numériques ;
- températures aberrantes ;
- humidité hors plage ;
- rayonnement négatif ;
- rayonnement nocturne anormal ;
- vent négatif ;
- pression aberrante ;
- données constantes suspectes ;
- fuseau incohérent ;
- période incomplète ;
- réponse partielle du fournisseur.

Plages de contrôle recommandées :

```text
température : -90 à +60 °C
humidité : 0 à 100 %
vent : 0 à 100 m/s
rayonnement : 0 à 1 500 W/m²
pression : 800 à 1 100 hPa selon altitude
précipitations : >= 0
```

---

## Flags qualité

Codes possibles :

```text
MISSING_HOUR
DUPLICATE_HOUR
INVALID_NUMBER
TEMPERATURE_OUT_OF_RANGE
HUMIDITY_OUT_OF_RANGE
NEGATIVE_RADIATION
NEGATIVE_WIND_SPEED
SUSPICIOUS_CONSTANT_SERIES
TIMEZONE_INCONSISTENT
PARTIAL_PROVIDER_RESPONSE
SOURCE_STALE
INTERPOLATED_VALUE
ESTIMATED_VALUE
```

---

## Statuts du dataset

```text
pending
available
partial
stale
failed
superseded
archived
```

---

## Score de qualité

Calculer un score de 0 à 100 selon :

```text
complétude
continuité temporelle
cohérence physique
variables obligatoires
variables secondaires
fraîcheur
qualité du fournisseur
niveau d’estimation
```

Conserver le détail du score.

---

## Valeurs manquantes

Stratégie recommandée :

```text
petit trou isolé
→ interpolation contrôlée

trou long
→ aucune interpolation

variable secondaire absente
→ dataset partiel

variable obligatoire absente
→ échec ou confiance fortement réduite
```

La méthode doit être explicite, versionnée et testée.

---

## Agrégations quotidiennes

Calculer :

- température minimale ;
- température maximale ;
- température moyenne ;
- température médiane ;
- minimum nocturne ;
- maximum nocturne ;
- humidité moyenne ;
- humidité maximale ;
- point de rosée moyen ;
- rayonnement total ;
- rayonnement maximal ;
- vent moyen ;
- vent maximal ;
- heures au-dessus des seuils ;
- degrés-heures de refroidissement ;
- complétude ;
- flags qualité.

Définition de la nuit MVP :

```text
22:00 → 06:00 heure locale
```

---

## Agrégations hebdomadaires

Calculer :

- minimum absolu ;
- maximum absolu ;
- moyenne ;
- moyenne des maxima ;
- moyenne des minima ;
- P90 ;
- P95 ;
- heures > 26 °C ;
- heures > 30 °C ;
- heures > 35 °C ;
- heures > 40 °C ;
- nuits > 20 °C ;
- nuits > 23 °C ;
- nuits > 25 °C ;
- rayonnement cumulé ;
- humidité moyenne ;
- degrés-heures ;
- complétude.

---

## Agrégations mensuelles

Calculer :

- minimum absolu ;
- maximum absolu ;
- moyenne ;
- moyenne des maxima ;
- moyenne des minima ;
- P90 ;
- P95 ;
- P97,5 ;
- P99 ;
- heures chaudes ;
- nuits chaudes ;
- séquence maximale ;
- rayonnement ;
- humidité ;
- degrés-heures ;
- anomalie par rapport à la référence ;
- qualité.

---

## Agrégations saisonnières

Pour chaque été :

- température maximale ;
- moyenne des maximales ;
- moyenne des minimales ;
- minimum nocturne moyen ;
- P95 ;
- P99 ;
- heures au-dessus des seuils ;
- nombre de nuits chaudes ;
- séquence la plus longue ;
- séquence la plus sévère ;
- rayonnement ;
- humidité ;
- degrés-heures ;
- anomalie ;
- qualité.

---

## Percentiles

Calculer :

```text
P50
P75
P90
P95
P97,5
P99
```

Appliquer selon pertinence à :

- température horaire ;
- maxima quotidiens ;
- minima nocturnes ;
- humidité ;
- point de rosée ;
- rayonnement ;
- vent.

La méthode statistique doit être explicite, déterministe, documentée et testée.

---

## Degrés-heures de refroidissement

Formule :

```text
Cooling degree-hours =
somme max(0, température extérieure - température de base)
```

Bases initiales :

```text
24 °C
26 °C
```

Calculer par :

- jour ;
- semaine ;
- mois ;
- saison ;
- année ;
- période complète.

---

## Heures chaudes

Calculer :

```text
hours_above_26_c
hours_above_30_c
hours_above_35_c
hours_above_40_c
```

---

## Nuits chaudes

Détecter les nuits dont le minimum reste supérieur à :

```text
20 °C
23 °C
25 °C
```

Conserver :

- date ;
- début ;
- fin ;
- minimum ;
- moyenne ;
- durée au-dessus du seuil ;
- humidité ;
- point de rosée ;
- température à 06:00 ;
- qualité.

Détecter également les séries de nuits chaudes consécutives.

---

## Refroidissement nocturne

Calculer :

```text
night_cooling_amplitude_c =
daily_max_temperature_c
- following_night_min_temperature_c
```

Identifier les périodes de faible refroidissement nocturne.

---

## Séquences de chaleur

Détecter des séquences de :

```text
3 jours
5 jours
7 jours
10 jours
```

Critères configurables :

- maximum quotidien ;
- minimum nocturne ;
- heures > 30 °C ;
- degrés-heures ;
- rayonnement ;
- humidité ;
- faible refroidissement nocturne.

Types possibles :

```text
hot_spell
heatwave
severe_heatwave
prolonged_heatwave
hot_night_sequence
humid_heat_sequence
dry_heat_sequence
```

---

## Résultat d’une séquence

Conserver :

```text
start_date
end_date
duration_days
maximum_temperature_c
average_daily_maximum_c
highest_night_minimum_c
average_night_minimum_c
hours_above_30_c
hours_above_35_c
hours_above_40_c
cooling_degree_hours_24
cooling_degree_hours_26
average_relative_humidity_percent
average_dew_point_c
maximum_radiation_w_m2
average_wind_speed_m_s
night_cooling_amplitude_c
severity_score
quality_score
source_dataset_id
```

Éviter les doublons liés aux séquences chevauchantes.

---

## Signal climatique récent

Comparer :

```text
9 derniers mois
12 derniers mois
3 dernières années
3 derniers étés
été en cours
```

Indicateurs :

- anomalie des températures moyennes ;
- anomalie des maximales ;
- anomalie des minimales nocturnes ;
- variation des heures chaudes ;
- variation des nuits chaudes ;
- variation des séquences ;
- variation des degrés-heures ;
- évolution des extrêmes ;
- évolution du point de rosée ;
- évolution du refroidissement nocturne.

Niveaux :

```text
insufficient_data
low
moderate
strong
very_strong
```

Ne pas conclure à un signal fort si les données sont insuffisantes ou non comparables.

---

## Scénarios climatiques à produire

Créer exactement :

```text
reference_summer
hot_weather
prolonged_heatwave
```

### `reference_summer`

Représente une journée estivale chaude mais courante.

Base possible :

```text
P90 ou P95 des maximales
rayonnement représentatif
humidité représentative
nuit normale
vent médian
```

### `hot_weather`

Représente une forte chaleur locale.

Base possible :

```text
P97,5 des maximales
rayonnement élevé
nuit chaude
durée de 3 jours
humidité cohérente
vent faible à médian
```

### `prolonged_heatwave`

Représente une canicule prolongée avec faible refroidissement nocturne.

Priorité :

```text
1. séquence historique réelle sévère
2. séquence récente sévère
3. séquence synthétique issue des percentiles
4. scénario partiel avec avertissement
```

Durée cible :

```text
7 à 10 jours
```

---

## Structure d’un scénario

Conserver :

```text
code
label
method
start_date
end_date
duration_days
hourly_profile
daily_max_temperature_c
night_min_temperature_c
average_relative_humidity_percent
dew_point_c
peak_radiation_w_m2
average_wind_speed_m_s
cooling_degree_hours_24
cooling_degree_hours_26
confidence_score
quality_score
provenance
warnings
```

Chaque scénario doit idéalement fournir un profil horaire.

---

## Scénarios historiques et synthétiques

### Scénario réel

Conserver :

- dates originales ;
- dataset source ;
- coordonnées ;
- fournisseur ;
- observations ;
- checksum ;
- méthode de sélection ;
- score de sévérité ;
- qualité.

### Scénario synthétique

- ne pas le présenter comme observation réelle ;
- conserver les percentiles sources ;
- conserver les transformations ;
- plafonner les corrections ;
- vérifier la cohérence horaire ;
- ajouter un avertissement ;
- réduire la confiance si nécessaire.

---

## Correction climatique récente

Une correction prudente peut être appliquée.

Elle doit être :

- distincte ;
- documentée ;
- plafonnée ;
- configurable ;
- versionnée ;
- visible ;
- réversible.

Prévoir :

```text
maximum_recent_temperature_adjustment_c
maximum_recent_night_adjustment_c
maximum_recent_radiation_adjustment_percent
```

---

## Compatibilité MERCURE

Fournir au minimum :

```text
outdoor_temperature_c
night_min_temperature_c
relative_humidity_percent
dew_point_c
global_solar_radiation_w_m2
wind_speed_m_s
duration_days
source
confidence_score
```

---

## Compatibilité EnergyPlus

Fournir ou référencer :

```text
EPW source
EPW modifié
design day
profil horaire
période historique
checksum
timezone
altitude
```

Le service climatique ne doit pas exécuter EnergyPlus.

---

## Fichiers EPW et weather morphing

Pour un EPW :

- vérifier le format ;
- vérifier la localisation ;
- vérifier l’altitude ;
- vérifier le fuseau ;
- calculer un checksum ;
- conserver la provenance ;
- ne jamais l’écraser.

Pour le weather morphing, conserver :

```text
source_weather_id
method
temperature_delta
humidity_delta
radiation_factor
wind_factor
created_at
checksum
version
```

---

## Score de confiance

Calculer selon :

- qualité du géocodage ;
- précision des coordonnées ;
- qualité de l’altitude ;
- durée de l’historique ;
- complétude ;
- continuité ;
- variables disponibles ;
- qualité du fournisseur ;
- période de référence ;
- présence d’une séquence réelle ;
- usage de données synthétiques ;
- fraîcheur ;
- cohérence des fournisseurs.

Niveaux :

```text
very_low
low
medium
high
very_high
```

---

## Cache climatique

La clé doit inclure :

```text
provider_code
provider_version
latitude arrondie
longitude arrondie
altitude
timezone
start_date
end_date
variables
schema_version
normalizer_version
```

TTL recommandés :

```text
historique clôturé : 180 jours
année en cours : 7 jours
été en cours : 1 jour
scénarios construits : 30 jours
```

---

## Stale-if-error et fallback

En cas d’échec fournisseur :

```text
fournisseur principal
→ fournisseur secondaire
→ cache périmé
→ échec structuré
```

Si un cache périmé est utilisé :

- marquer le dataset `stale` ;
- afficher la date réelle ;
- réduire la confiance ;
- ajouter un avertissement ;
- auditer le fallback.

Ne pas mélanger silencieusement plusieurs fournisseurs.

---

## Modèles Odoo

### `greencube.cooling.climate.dataset`

Champs possibles :

```text
name
study_id
revision_id
company_id
provider_code
provider_version
schema_version
normalizer_version
quality_version
latitude
longitude
altitude_m
timezone
country_code
locality
start_date
end_date
observation_count
expected_observation_count
status
quality_score
confidence_score
raw_artifact_id
summary_json
quality_json
provenance_json
checksum
fetched_at
expires_at
stale_at
superseded_by_id
active
```

### `greencube.cooling.climate.scenario`

```text
dataset_id
study_id
revision_id
company_id
code
label
method
source_type
start_date
end_date
duration_days
daily_max_temperature_c
night_min_temperature_c
relative_humidity_percent
dew_point_c
peak_radiation_w_m2
average_wind_speed_m_s
cooling_degree_hours_24
cooling_degree_hours_26
hourly_profile_json
confidence_score
quality_score
provenance_json
warnings_json
schema_version
builder_version
checksum
active
```

### `greencube.cooling.climate.event`

```text
dataset_id
event_type
start_at
end_at
duration_hours
duration_days
maximum_temperature_c
average_maximum_c
average_night_minimum_c
hours_above_30_c
hours_above_35_c
hours_above_40_c
severity_score
summary_json
quality_score
checksum
```

---

## Immuabilité et versionnement

Un dataset utilisé par :

- un snapshot ;
- un calcul ;
- un résultat ;
- une sélection d’équipement ;

ne doit jamais être modifié.

Toute actualisation doit créer :

```text
nouveau dataset
→ nouveaux scénarios
→ nouveau checksum
```

Versions à conserver :

```text
CLIMATE_SCHEMA_VERSION
CLIMATE_NORMALIZER_VERSION
CLIMATE_QUALITY_VERSION
CLIMATE_AGGREGATOR_VERSION
CLIMATE_HEAT_SEQUENCE_VERSION
CLIMATE_SCENARIO_BUILDER_VERSION
CLIMATE_CONFIDENCE_VERSION
```

---

## Endpoints API

### Création

```text
POST /api/v1/greencube/cooling/studies/<study_id>/climate-context
```

### Lecture

```text
GET /api/v1/greencube/cooling/studies/<study_id>/climate-context
```

### Historique

```text
GET /api/v1/greencube/cooling/studies/<study_id>/climate-context/history
```

### Rafraîchissement

```text
POST /api/v1/greencube/cooling/studies/<study_id>/climate-context/refresh
```

### Scénarios

```text
GET /api/v1/greencube/cooling/studies/<study_id>/climate-scenarios
```

---

## Calcul asynchrone

Statuts possibles :

```text
queued
fetching
normalizing
validating
aggregating
detecting_events
building_scenarios
persisting
completed
failed
cancelled
timed_out
```

Ne pas maintenir une requête HTTP très longue.

---

## Idempotence et verrouillage

La clé logique doit inclure :

```text
study
revision
location version
provider
period
variables
schema version
idempotency key
```

Un seul job doit traiter la même clé logique.

---

## Robustesse réseau

Appliquer :

- timeout de connexion ;
- timeout de lecture ;
- retries limités ;
- backoff ;
- jitter si nécessaire ;
- limite de taille ;
- découpage annuel ;
- limitation de concurrence ;
- validation du content type ;
- contrôle des redirections ;
- contrôle du statut HTTP ;
- absence de secret dans les logs.

---

## Protection SSRF

Le backend ne doit jamais accepter une URL fournisseur depuis le frontend.

Vérifier :

- HTTPS uniquement ;
- liste blanche de domaines ;
- résolution DNS contrôlée ;
- blocage des IP privées ;
- blocage des loopbacks ;
- blocage des métadonnées cloud ;
- contrôle des redirections.

---

## Rate limiting

Limiter :

- création de contexte ;
- rafraîchissement forcé ;
- accès aux données brutes ;
- appels administratifs.

---

## Erreurs métier

Codes possibles :

```text
CLIMATE_LOCATION_MISSING
CLIMATE_LOCATION_INVALID
CLIMATE_TIMEZONE_INVALID
CLIMATE_PERIOD_INVALID
CLIMATE_PROVIDER_DISABLED
CLIMATE_PROVIDER_UNAVAILABLE
CLIMATE_PROVIDER_TIMEOUT
CLIMATE_PROVIDER_RESPONSE_INVALID
CLIMATE_RESPONSE_TOO_LARGE
CLIMATE_REQUIRED_VARIABLE_MISSING
CLIMATE_DATA_QUALITY_TOO_LOW
CLIMATE_DATASET_NOT_FOUND
CLIMATE_DATASET_STALE
CLIMATE_SCENARIO_BUILD_FAILED
CLIMATE_REFERENCE_UNAVAILABLE
CLIMATE_RECENT_SIGNAL_UNAVAILABLE
CLIMATE_VERSION_CONFLICT
CLIMATE_REFRESH_ALREADY_RUNNING
ACCESS_DENIED
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

Chaque dataset et scénario doit être lié à :

```text
company_id
```

Tester :

- lecture inter-sociétés ;
- actualisation inter-sociétés ;
- cache partagé ou isolé ;
- fournisseurs spécifiques ;
- paramètres spécifiques ;
- pièces jointes ;
- données brutes.

---

## Logs et audit

Auditer :

- requête climatique ;
- fournisseur ;
- période ;
- variables ;
- cache hit ;
- cache miss ;
- fallback ;
- collecte ;
- erreur ;
- stale ;
- normalisation ;
- scénario ;
- rafraîchissement ;
- utilisateur ;
- société ;
- request ID.

Logs structurés :

```text
request_id
study_id
revision_id
company_id
dataset_id
provider_code
period_start
period_end
step
status
duration_ms
observation_count
quality_score
confidence_score
error_code
cache_status
```

---

## Métriques

Prévoir :

- nombre de requêtes ;
- taux de succès ;
- taux d’échec ;
- temps fournisseur ;
- temps de normalisation ;
- temps d’agrégation ;
- cache hit ratio ;
- stale-if-error ;
- datasets partiels ;
- qualité moyenne ;
- séquences détectées ;
- échecs de scénarios ;
- taille des données brutes.

---

## Rétention et nettoyage

Définir une politique pour :

```text
données brutes
agrégats
logs
datasets échoués
datasets superseded
pièces jointes
événements
```

Créer :

```text
cooling_cleanup_expired_climate_artifacts
```

Ne jamais supprimer un dataset référencé par un snapshot ou un résultat.

---

## Tests sans Internet

Aucun test automatisé ne doit dépendre d’Internet.

Utiliser :

- fournisseur mock ;
- fixtures JSON ;
- réponses enregistrées ;
- HTTP simulé ;
- horloge contrôlée.

---

## Fixtures obligatoires

Créer des fixtures pour :

```text
année normale
été chaud
canicule de 3 jours
canicule de 5 jours
canicule de 7 jours
canicule de 10 jours
nuits > 20 °C
nuits > 23 °C
nuits > 25 °C
chaleur humide
chaleur sèche
données incomplètes
données dupliquées
trous horaires
année bissextile
Europe/Paris
Europe/Zurich
Europe/Lisbon
altitude élevée
zone côtière
hémisphère sud
fournisseur indisponible
réponse trop volumineuse
cache périmé
```

---

## Tests obligatoires

Tester :

### Fournisseur

- requête ;
- variables ;
- période ;
- timeout ;
- retry ;
- réponse valide ;
- réponse partielle ;
- erreur HTTP ;
- réponse trop grande ;
- format inattendu.

### Normalisation

- unités ;
- tri ;
- doublons ;
- fuseau ;
- UTC ;
- DST ;
- années bissextiles ;
- NaN ;
- infinis ;
- valeurs aberrantes.

### Qualité

- dataset complet ;
- dataset partiel ;
- série constante ;
- trous ;
- doublons ;
- rayonnement négatif ;
- humidité hors plage ;
- score ;
- flags.

### Agrégations

- jour ;
- semaine ;
- mois ;
- été ;
- changement de mois ;
- changement d’année ;
- année bissextile ;
- période partielle ;
- seuils ;
- degrés-heures.

### Percentiles

- série paire ;
- série impaire ;
- petite série ;
- valeurs répétées ;
- valeurs manquantes ;
- reproductibilité.

### Nuits chaudes

- aucune nuit chaude ;
- > 20 °C ;
- > 23 °C ;
- > 25 °C ;
- série consécutive ;
- passage de minuit ;
- changement d’heure.

### Séquences

- 3 jours ;
- 5 jours ;
- 7 jours ;
- 10 jours ;
- chevauchements ;
- chaleur humide ;
- chaleur sèche ;
- score de sévérité.

### Signal récent

- faible ;
- modéré ;
- fort ;
- très fort ;
- données insuffisantes ;
- périodes non comparables ;
- été incomplet.

### Scénarios

- `reference_summer` ;
- `hot_weather` ;
- `prolonged_heatwave` ;
- historique ;
- synthétique ;
- partiel ;
- cohérence horaire ;
- provenance ;
- confiance ;
- checksum.

### Cache

- hit ;
- miss ;
- expiration ;
- force refresh ;
- changement de fournisseur ;
- changement de version ;
- stale-if-error ;
- concurrence.

### API et sécurité

- création ;
- lecture ;
- historique ;
- rafraîchissement ;
- permissions ;
- multi-société ;
- idempotence ;
- SSRF ;
- rate limiting ;
- request ID.

---

## Documentation

Créer :

```text
docs/cooling_climate_architecture.md
docs/cooling_climate_provider.md
docs/cooling_climate_schema.md
docs/cooling_climate_quality.md
docs/cooling_climate_aggregations.md
docs/cooling_climate_heat_sequences.md
docs/cooling_climate_recent_signal.md
docs/cooling_climate_scenarios.md
docs/cooling_climate_cache.md
docs/cooling_climate_security.md
docs/cooling_climate_api.md
docs/cooling_climate_operations.md
docs/cooling_climate_troubleshooting.md
```

---

## Migrations

Vérifier :

- installation sur base vierge ;
- mise à jour ;
- création des modèles ;
- création des champs ;
- index ;
- contraintes ;
- données par défaut ;
- ACL ;
- record rules ;
- conservation des datasets existants ;
- idempotence.

Créer si nécessaire :

```text
migrations/<version>/pre-migration.py
migrations/<version>/post-migration.py
```

---

## Critères d’acceptation fonctionnels

Le lot est accepté si :

- une localisation valide déclenche une analyse ;
- le fournisseur est abstrait ;
- Open-Meteo est encapsulé ;
- le frontend n’appelle aucun fournisseur ;
- l’historique est récupérable ;
- les variables sont normalisées ;
- les unités sont cohérentes ;
- UTC et heure locale sont conservés ;
- les changements d’heure sont gérés ;
- la qualité est calculée ;
- les trous sont détectés ;
- les doublons sont détectés ;
- les valeurs aberrantes sont signalées ;
- les agrégats quotidiens fonctionnent ;
- les agrégats hebdomadaires fonctionnent ;
- les agrégats mensuels fonctionnent ;
- les agrégats saisonniers fonctionnent ;
- les percentiles sont reproductibles ;
- les degrés-heures sont calculés ;
- les heures chaudes sont calculées ;
- les nuits chaudes sont détectées ;
- les séries nocturnes sont détectées ;
- les séquences de chaleur sont détectées ;
- les chevauchements sont gérés ;
- le score de sévérité fonctionne ;
- le signal récent fonctionne ;
- les données insuffisantes sont signalées ;
- les trois scénarios sont produits ;
- la provenance est conservée ;
- la confiance est calculée ;
- le cache fonctionne ;
- stale-if-error fonctionne ;
- le fallback fonctionne si activé ;
- les datasets sont persistés ;
- les scénarios sont persistés ;
- les datasets utilisés restent immuables ;
- les actualisations créent une nouvelle version ;
- le multi-société est respecté.

---

## Critères d’acceptation techniques

Le lot est accepté si :

- le lint Python passe ;
- le formatage passe ;
- le contrôle de types passe si présent ;
- les tests unitaires passent ;
- les tests Odoo passent ;
- les tests API passent ;
- les tests de migration passent ;
- les tests sans Internet passent ;
- les tests de cache passent ;
- les tests de fuseau passent ;
- les tests d’année bissextile passent ;
- les tests de non-régression passent ;
- les performances sont mesurées ;
- le fournisseur mock fonctionne ;
- les dépendances sont verrouillées ;
- aucun secret n’est exposé ;
- aucun ancien dataset n’est modifié ;
- aucun fichier n’est supprimé sans justification.

---

## Critères d’acceptation sécurité

Le lot est accepté si :

- aucune URL fournisseur ne vient du frontend ;
- les domaines sont contrôlés ;
- les IP privées sont bloquées ;
- les redirections sont contrôlées ;
- les timeouts sont configurés ;
- les retries sont limités ;
- la taille des réponses est limitée ;
- les variables sont en liste blanche ;
- les clés ne sont pas journalisées ;
- les pièces jointes sont privées ;
- les permissions sont testées ;
- le multi-société est testé ;
- les erreurs internes ne sont pas exposées ;
- le rate limiting fonctionne ;
- les dépendances critiques sont traitées.

---

## Rapport final attendu

### Architecture

- fournisseurs ;
- registre ;
- service ;
- normalisation ;
- qualité ;
- agrégation ;
- événements ;
- scénarios ;
- cache ;
- stockage.

### Fournisseurs

- fournisseur principal ;
- version ;
- variables ;
- configuration ;
- fallback ;
- limites.

### Modèles Odoo

- modèles créés ;
- modèles modifiés ;
- champs ;
- contraintes ;
- index ;
- ACL ;
- record rules ;
- migrations.

### Statistiques

- agrégations ;
- percentiles ;
- degrés-heures ;
- nuits chaudes ;
- séquences ;
- signal récent ;
- méthodes ;
- versions.

### Scénarios

- `reference_summer` ;
- `hot_weather` ;
- `prolonged_heatwave` ;
- méthodes ;
- provenance ;
- confiance ;
- avertissements.

### API

Pour chaque endpoint :

- méthode ;
- URL ;
- payload ;
- réponse ;
- erreurs ;
- permissions ;
- idempotence ;
- cache.

### Tests

- commandes ;
- code retour ;
- durée ;
- couverture ;
- fixtures ;
- tests non exécutés ;
- raisons.

### Sécurité

- SSRF ;
- timeouts ;
- retries ;
- taille ;
- secrets ;
- fichiers ;
- permissions ;
- multi-société ;
- logs.

### Performance

- collecte ;
- normalisation ;
- agrégation ;
- cache ;
- mémoire ;
- stockage.

### Patch

- diff ;
- fichiers créés ;
- fichiers modifiés ;
- migrations ;
- dépendances ;
- installation ;
- rollback.

---

## Contrôle final

Avant conclusion :

1. vérifier l’arborescence ;
2. vérifier les modèles ;
3. vérifier les migrations ;
4. vérifier les fournisseurs ;
5. vérifier la configuration ;
6. vérifier les variables ;
7. vérifier les unités ;
8. vérifier les dates ;
9. vérifier UTC ;
10. vérifier le fuseau ;
11. vérifier les changements d’heure ;
12. vérifier les données brutes ;
13. vérifier la normalisation ;
14. vérifier les trous ;
15. vérifier les doublons ;
16. vérifier les valeurs aberrantes ;
17. vérifier le score de qualité ;
18. vérifier les agrégations ;
19. vérifier les percentiles ;
20. vérifier les degrés-heures ;
21. vérifier les heures chaudes ;
22. vérifier les nuits chaudes ;
23. vérifier les séries nocturnes ;
24. vérifier les séquences ;
25. vérifier les chevauchements ;
26. vérifier le score de sévérité ;
27. vérifier le signal récent ;
28. vérifier les périodes comparables ;
29. vérifier `reference_summer` ;
30. vérifier `hot_weather` ;
31. vérifier `prolonged_heatwave` ;
32. vérifier les scénarios synthétiques ;
33. vérifier les corrections ;
34. vérifier les plafonds ;
35. vérifier MERCURE ;
36. vérifier EnergyPlus ;
37. vérifier les EPW ;
38. vérifier les checksums ;
39. vérifier la confiance ;
40. vérifier le cache ;
41. vérifier stale-if-error ;
42. vérifier le fallback ;
43. vérifier la persistance ;
44. vérifier l’immuabilité ;
45. vérifier le versionnement ;
46. vérifier les pièces jointes ;
47. vérifier les endpoints ;
48. vérifier l’idempotence ;
49. vérifier les verrous ;
50. vérifier les jobs ;
51. vérifier les erreurs ;
52. vérifier les permissions ;
53. vérifier le multi-société ;
54. vérifier l’audit ;
55. vérifier les logs ;
56. vérifier les métriques ;
57. vérifier la rétention ;
58. vérifier le nettoyage ;
59. vérifier les tests sans Internet ;
60. vérifier les fixtures ;
61. vérifier les performances ;
62. vérifier SSRF ;
63. vérifier le rate limiting ;
64. vérifier l’absence de secrets ;
65. vérifier la sauvegarde ;
66. vérifier le rollback ;
67. vérifier la documentation ;
68. vérifier qu’aucun dataset utilisé n’a été modifié ;
69. vérifier qu’aucun fichier n’a été supprimé sans justification ;
70. ne jamais déclarer une opération réussie sans preuve réelle.

---

## Livrables obligatoires

Produire au minimum :

```text
services Python du domaine climat
fournisseur Open-Meteo
fournisseur mock
registre des fournisseurs
normaliseur
contrôleur qualité
agrégateur
calculateur de percentiles
calculateur de degrés-heures
détecteur de nuits chaudes
détecteur de séquences de chaleur
analyseur du signal récent
constructeur de scénarios
calculateur de confiance
cache
stockage
modèles Odoo
ACL et record rules
migrations
endpoints API
OpenAPI
fixtures
tests
documentation
patch réintégrable
rapport de tests
procédure de rollback
```

---

## Limites du lot

Ce lot fournit le socle climatique complet de GreenCube Cooling.

Il ne doit pas :

- calculer la puissance frigorifique finale ;
- choisir un climatiseur ;
- produire un devis ;
- présenter un scénario synthétique comme une mesure réelle ;
- fournir une étude climatique réglementaire officielle ;
- promettre une prédiction météorologique future ;
- extrapoler abusivement une tendance récente ;
- remplacer une expertise météorologique réglementaire.

Le résultat attendu est un service climatique robuste, versionné, explicable, sécurisé et directement exploitable par MERCURE et Honeybee/EnergyPlus.
