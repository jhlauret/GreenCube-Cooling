# GC-COOLING-12 — Ventilation, infiltration et niveau de confort

## Objectif

Implémenter l’écran :

```text
6 — Ventilation, infiltration et niveau de confort
```

L’écran doit permettre de :

- sélectionner un système de ventilation ;
- saisir le débit d’air neuf ;
- utiliser des unités en m³/h, ACH, débit par personne ou débit par surface ;
- définir les calendriers de ventilation ;
- gérer la ventilation nocturne ;
- renseigner la récupération sensible et latente ;
- gérer le bypass d’été ;
- renseigner la puissance des ventilateurs ;
- définir la part de chaleur des ventilateurs dissipée dans la zone ;
- renseigner l’étanchéité à l’air ;
- saisir une valeur `n50` ;
- saisir ou estimer l’infiltration naturelle ;
- renseigner l’exposition au vent ;
- modéliser l’ouverture des fenêtres ;
- modéliser l’ouverture des portes ;
- définir les consignes de température de jour et de nuit ;
- définir les limites d’humidité ;
- choisir un niveau de confort et de résilience ;
- prévisualiser les charges sensibles et latentes liées à l’air extérieur ;
- afficher la provenance et le score de confiance ;
- sauvegarder la section dans Odoo ;
- fournir un payload au solver rapide ;
- documenter le mapping Honeybee/EnergyPlus ;
- passer à l’écran Vérification avant calcul.

Odoo Community 18 reste la source de vérité.

Les calculs frontend sont uniquement indicatifs. Le backend doit recalculer les débits, infiltrations, charges sensibles et charges latentes.

---

## Stack attendue

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

---

## Prérequis

Le lot suppose disponibles :

- une étude GreenCube Cooling ;
- une localisation confirmée ;
- un contexte climatique ;
- un modèle GreenCube ;
- un volume intérieur ;
- une enveloppe thermique ;
- une orientation ;
- des vitrages et protections solaires ;
- un profil d’usage ;
- un profil d’occupation ;
- des équipements et charges internes ;
- les permissions et statuts ;
- la provenance ;
- les scores de confiance ;
- le verrouillage optimiste ;
- la gestion des révisions.

---

## Vérifications préalables

Avant toute modification :

- inspecter les écrans précédents ;
- vérifier la route et le stepper ;
- vérifier le store Zustand ;
- vérifier le client API ;
- vérifier les query keys ;
- vérifier les composants de formulaire ;
- inspecter les modèles Odoo de ventilation, infiltration et confort ;
- vérifier les unités ;
- vérifier les conventions ACH et `n50` ;
- vérifier les règles de récupération ;
- vérifier les profils horaires ;
- vérifier le mapping Honeybee/EnergyPlus ;
- vérifier les règles d’invalidation ;
- vérifier les endpoints existants ;
- exécuter lint, TypeScript, tests et build ;
- ne supprimer aucun composant ;
- ne coder aucun profil de ventilation en dur ;
- ne jamais modifier un profil catalogue depuis l’étude.

---

## Route

```text
/cooling/studies/:studyId/comfort
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
StudyEditableGuard
```

Prérequis minimaux :

- étude existante ;
- modèle configuré ;
- volume intérieur disponible ;
- profil d’usage disponible.

Pour une étude calculée ou validée :

- afficher en lecture seule ;
- proposer une révision ;
- interdire la modification directe.

---

## Structure de la page

Créer :

```tsx
<CoolingComfortPage />
```

Structure recommandée :

```text
CoolingLayout
├── Introduction
├── VentilationModeCard
├── FreshAirFlowCard
├── VentilationScheduleCard
├── HeatRecoveryCard
├── FanPowerCard
├── AirtightnessCard
├── InfiltrationCard
├── WindowOpeningCard
├── DoorOpeningCard
├── ComfortSetpointCard
├── HumiditySetpointCard
├── ResilienceLevelCard
├── AirLoadPreviewCard
├── ProvenanceAndConfidence
├── ValidationWarnings
└── CoolingFooter
```

---

## Modes de ventilation

Créer :

```tsx
<VentilationModeCard />
<VentilationModeSelector />
```

Modes possibles :

```text
none
natural
single_flow_exhaust
single_flow_supply
balanced_double_flow
mechanical_supply_exhaust
mixed_mode
custom
```

Labels possibles :

```text
Aucune ventilation dédiée
Ventilation naturelle
Simple flux par extraction
Simple flux par insufflation
Double flux équilibrée
Insufflation et extraction mécaniques
Mode mixte
Configuration personnalisée
```

Les profils doivent venir d’Odoo.

---

## Profils de ventilation

Créer :

```ts
useCoolingVentilationProfiles()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/ventilation-profiles
```

La réponse doit idéalement contenir :

- identifiant ;
- code ;
- nom ;
- description ;
- type de système ;
- débit nominal ;
- plage de débit ;
- récupération ;
- rendement sensible ;
- rendement latent ;
- puissance ventilateurs ;
- profil horaire ;
- statut ;
- version ;
- provenance.

---

## Modes profil et personnalisé

Prévoir :

```text
profile
custom
```

Créer :

```tsx
<VentilationConfigurationModeSelector />
```

### Mode profil

- charger les valeurs depuis Odoo ;
- préremplir le débit ;
- préremplir la récupération ;
- préremplir la puissance ventilateur ;
- conserver l’identifiant et la version ;
- permettre les modifications autorisées.

### Mode personnalisé

- saisir directement les débits ;
- saisir les rendements ;
- saisir les calendriers ;
- afficher les hypothèses ;
- réduire la confiance si les données sont estimées.

---

## Modes de saisie du débit

Prévoir :

```text
airflow_m3h
air_changes_per_hour
per_person
per_area
```

Créer :

```tsx
<AirflowInputModeSelector />
```

Labels :

```text
Débit total en m³/h
Renouvellements par heure
Débit par personne
Débit par surface
```

Une seule méthode doit rester la source principale.

---

## Débit total

Créer :

```tsx
<FreshAirFlowField />
```

Unité :

```text
m³/h
```

Validation indicative :

```text
0 à 100 000 m³/h
```

Une valeur très élevée doit déclencher un avertissement.

---

## Renouvellement d’air ACH

Créer :

```tsx
<AirChangesPerHourField />
```

Unité :

```text
ACH
```

Relation indicative :

```text
airflow_m3h =
ACH
× volume_m3
```

Le backend doit recalculer.

---

## Débit par personne

Unité :

```text
m³/h/personne
```

Calcul indicatif :

```text
airflow_m3h =
airflow_per_person
× design_occupants
```

Le nombre d’occupants doit venir de l’étape Usage.

---

## Débit par surface

Unité :

```text
m³/h/m²
```

Calcul indicatif :

```text
airflow_m3h =
airflow_per_area
× floor_area_m2
```

Le backend doit définir la valeur finale.

---

## Conversions

Créer :

```tsx
<AirflowConversionSummary />
```

Afficher :

- débit total ;
- ACH ;
- débit par personne ;
- débit par surface ;
- méthode source ;
- volume utilisé ;
- nombre d’occupants utilisé.

Ne pas écraser la valeur source.

---

## Calendrier de ventilation

Créer :

```tsx
<VentilationScheduleCard />
<VentilationScheduleEditor />
```

Modes :

```text
follow_occupancy
always_on
catalog_schedule
custom_schedule
night_purge
```

Permettre :

- suivi de l’occupation ;
- fonctionnement permanent ;
- planning personnalisé ;
- fonctionnement nocturne ;
- modulation du débit.

---

## Fraction de fonctionnement

Champ :

```text
operation_fraction
```

Plage :

```text
0 à 1
```

Exemples :

```text
0 = arrêt
0,5 = demi-débit
1 = débit nominal
```

---

## Ventilation nocturne

Créer :

```tsx
<NightVentilationCard />
```

Champs :

```text
night_ventilation_enabled
night_airflow_mode
night_airflow_value
night_start_time
night_end_time
outdoor_temperature_condition
indoor_temperature_condition
```

La ventilation nocturne doit permettre de représenter une stratégie de rafraîchissement passif.

---

## Conditions d’activation nocturne

Modes possibles :

```text
always
outdoor_cooler_than_indoor
outdoor_below_threshold
indoor_above_threshold
combined
backend_default
```

Exemple :

```text
Activer si l’air extérieur est au moins 2 °C plus frais que l’air intérieur.
```

---

## Récupération de chaleur ou de fraîcheur

Créer :

```tsx
<HeatRecoveryCard />
```

Champs :

```text
heat_recovery_enabled
sensible_recovery_efficiency
latent_recovery_efficiency
bypass_enabled
summer_bypass_enabled
```

Plage :

```text
0 à 1
```

---

## Rendement sensible

Exemple :

```text
0,80 = 80 % de récupération sensible
```

Le backend doit gérer :

- la récupération hivernale ;
- la récupération estivale ;
- le bypass ;
- le free cooling ;
- les conditions extérieures.

---

## Rendement latent

Champ facultatif :

```text
latent_recovery_efficiency
```

Ne pas supposer qu’un échangeur standard transfère l’humidité.

---

## Bypass d’été

Créer :

```tsx
<SummerBypassField />
```

Modes :

```text
none
manual
automatic
backend_default
```

Afficher les conditions d’activation et l’effet attendu.

---

## Puissance des ventilateurs

Créer :

```tsx
<FanPowerCard />
```

Modes :

```text
total_power_w
specific_fan_power
catalog_value
```

Unités possibles :

```text
W
W/(m³/s)
W/(m³/h)
```

Choisir une unité interne unique côté backend.

---

## Chaleur produite par les ventilateurs

Champ :

```text
fan_heat_to_zone_fraction
```

Plage :

```text
0 à 1
```

Cas :

- moteur dans la zone ;
- moteur hors zone ;
- gaines dans la zone ;
- gaines hors zone.

---

## Étanchéité à l’air

Créer :

```tsx
<AirtightnessCard />
```

Modes :

```text
n50
natural_ach
leakage_area
airtightness_class
reference_profile
```

Pour le MVP, privilégier :

```text
n50
natural_ach
reference_profile
```

---

## Valeur n50

Créer :

```tsx
<N50Field />
```

Unité :

```text
vol/h à 50 Pa
```

Validation indicative :

```text
0 à 30 vol/h
```

Afficher :

- valeur ;
- source ;
- date de mesure ;
- méthode ;
- confiance.

---

## Infiltration naturelle

Créer :

```tsx
<InfiltrationRateField />
```

Unité recommandée :

```text
ACH
```

La conversion entre `n50` et infiltration naturelle doit être réalisée côté backend avec une méthode documentée.

---

## Profils d’étanchéité

Créer :

```ts
useCoolingAirtightnessProfiles()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/airtightness-profiles
```

Profils possibles :

```text
very_tight
tight
standard
leaky
very_leaky
custom
```

Les valeurs doivent venir d’Odoo.

---

## Exposition au vent

Créer :

```tsx
<WindExposureSelector />
```

Valeurs possibles :

```text
sheltered
normal
exposed
very_exposed
```

La suggestion peut venir du contexte géographique.

---

## Ouverture des fenêtres

Créer :

```tsx
<WindowOpeningCard />
```

Modes :

```text
never
manual
scheduled
temperature_controlled
night_purge
mixed
```

Champs possibles :

- nombre de fenêtres ouvrantes ;
- surface ouvrable ;
- fraction maximale d’ouverture ;
- calendrier ;
- seuil intérieur ;
- seuil extérieur ;
- verrouillage pendant les fortes chaleurs ;
- comportement nocturne.

---

## Surface ouvrable

Champ :

```text
operable_window_area_m2
```

ou :

```text
operable_fraction
```

La surface ouvrable ne doit jamais dépasser la surface vitrée correspondante.

---

## Stratégies d’ouverture

Prévoir :

```text
windows_closed_during_hot_day
windows_open_when_outdoor_cooler
manual_user_behavior
backend_default
```

Le backend doit appliquer la règle finale.

---

## Ouverture des portes

Créer :

```tsx
<DoorOpeningCard />
```

Champs :

- nombre de portes ;
- fréquence d’ouverture ;
- durée moyenne ;
- surface ;
- calendrier ;
- type d’usage.

Modes simplifiés :

```text
low
medium
high
custom
```

Les valeurs doivent venir d’un référentiel backend.

---

## Consigne de température

Créer :

```tsx
<ComfortSetpointCard />
<TemperatureSetpointField />
```

Champs :

```text
cooling_setpoint_day_c
cooling_setpoint_night_c
maximum_acceptable_temperature_c
```

Plage indicative :

```text
16 à 35 °C
```

Une consigne très basse doit produire un avertissement.

---

## Température de jour et de nuit

Permettre :

- la même consigne ;
- des consignes différentes ;
- un relâchement nocturne ;
- un arrêt nocturne ;
- une stratégie de résilience.

Exemple :

```text
Jour : 25 °C
Nuit : 27 °C
```

---

## Humidité

Créer :

```tsx
<HumiditySetpointCard />
```

Champs :

```text
humidity_control_enabled
maximum_relative_humidity_percent
target_relative_humidity_percent
```

Plage :

```text
20 à 90 %
```

---

## Déshumidification

Modes :

```text
no_active_humidity_control
humidity_limit
active_dehumidification
backend_default
```

Ne pas supposer qu’un climatiseur garantit automatiquement une humidité cible précise.

---

## Niveau de confort

Créer :

```tsx
<ResilienceLevelCard />
<ComfortLevelSelector />
```

Niveaux possibles :

```text
basic
standard
enhanced
resilient
critical
custom
```

Labels :

```text
Confort minimal
Confort standard
Confort renforcé
Résilience canicule
Usage critique
Personnalisé
```

Les profils doivent venir d’Odoo.

---

## Profils de confort

Créer :

```ts
useCoolingComfortProfiles()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/comfort-profiles
```

La réponse peut contenir :

- température jour ;
- température nuit ;
- humidité maximale ;
- tolérance ;
- scénario dimensionnant ;
- marge ;
- niveau de résilience ;
- statut ;
- version ;
- provenance.

---

## Résilience canicule

Le niveau résilient peut définir :

- température maximale intérieure ;
- maintien de l’occupation nocturne ;
- durée de maintien ;
- mode dégradé ;
- priorité aux personnes fragiles ;
- scénario canicule prolongée.

---

## Usage critique

Pour un usage critique :

- consigne stricte ;
- fonctionnement continu ;
- marge de sécurité ;
- absence de relâchement nocturne ;
- future redondance.

---

## Prévisualisation des charges d’air

Créer :

```tsx
<AirLoadPreviewCard />
```

Prévisualisation sensible :

```text
Q_sensible_air =
rho_air
× cp_air
× airflow_m3s
× delta_temperature
```

Prévisualisation latente :

```text
Q_latent_air =
air_mass_flow
× delta_humidity_ratio
× latent_heat
```

Le backend doit effectuer le calcul définitif.

---

## Scénarios climatiques

Afficher les charges pour :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Pour chaque scénario :

- température extérieure ;
- humidité extérieure ;
- débit ;
- infiltration ;
- charge sensible ;
- charge latente ;
- effet de récupération ;
- charge nette.

---

## Récapitulatif des flux d’air

Créer :

```tsx
<AirflowSummaryCard />
```

Afficher :

- ventilation mécanique ;
- infiltration ;
- ouverture des fenêtres ;
- ouverture des portes ;
- débit total estimé ;
- débit récupéré ;
- débit non récupéré ;
- période critique.

Éviter tout double comptage.

---

## Risque de double comptage

Distinguer clairement :

- ventilation contrôlée ;
- infiltration ;
- ouverture volontaire des fenêtres ;
- ouverture des portes ;
- extraction process ;
- rejet d’équipement.

Créer des validations empêchant les doublons évidents.

---

## Mapping solver rapide

Payload minimal possible :

```json
{
  "ventilation": {
    "airflow_m3h": 120,
    "air_changes_per_hour": 1.5,
    "sensible_recovery_efficiency": 0.75,
    "latent_recovery_efficiency": 0.0,
    "schedule": {}
  },
  "infiltration": {
    "natural_ach": 0.25,
    "n50": 1.5,
    "wind_exposure": "normal"
  },
  "window_opening": {
    "enabled": true,
    "strategy": "outdoor_cooler_than_indoor"
  },
  "comfort": {
    "cooling_setpoint_day_c": 25,
    "cooling_setpoint_night_c": 27,
    "maximum_relative_humidity_percent": 60
  }
}
```

Le backend doit construire le payload final.

---

## Mapping Honeybee/EnergyPlus

Le service doit pouvoir produire :

- `Ventilation` ;
- `Infiltration` ;
- `Setpoint` ;
- calendriers ;
- contrôle d’humidité si disponible ;
- ventilation naturelle ;
- récupération d’énergie ;
- puissance ventilateurs ;
- disponibilité HVAC.

Créer une documentation dédiée.

---

## Méthodes de ventilation Honeybee

Préciser si le débit utilise :

```text
flow_per_person
flow_per_area
air_changes_per_hour
flow_per_zone
```

Conserver la méthode source.

---

## Infiltration Honeybee

Documenter :

- ACH ;
- débit par surface ;
- débit par façade ;
- calendrier ;
- coefficient de référence.

Ne pas convertir `n50` sans méthode documentée.

---

## Setpoints Honeybee

Le mapping doit produire :

- consigne de refroidissement ;
- calendrier jour/nuit ;
- consigne de chauffage éventuelle ;
- humidité minimale ou maximale si prise en charge.

---

## Provenance

Utiliser :

```tsx
<DataSourceBadge />
```

Sources possibles :

```text
ventilation_profile
equipment_catalog
measured
commissioning_data
user_confirmed
estimated_reference
climate_context
backend_default
missing_fallback
```

Afficher la provenance pour :

- débit ;
- ACH ;
- récupération ;
- puissance ventilateur ;
- `n50` ;
- infiltration ;
- fenêtres ;
- portes ;
- consignes ;
- humidité ;
- niveau de confort.

---

## Score de confiance

Créer :

```tsx
<ComfortVentilationConfidencePanel />
```

Composantes possibles :

```text
ventilation_system
airflow
schedule
heat_recovery
fan_power
airtightness
infiltration
window_opening
door_opening
temperature_setpoint
humidity_setpoint
```

Exemple :

```text
Confiance globale : 79 %

Ventilation : 95 %
Débit : 90 %
Récupération : 85 %
Étanchéité : 60 %
Infiltration : 65 %
Ouverture des fenêtres : 55 %
Consignes : 100 %
```

---

## Données manquantes

Créer :

```tsx
<MissingComfortDataAlert />
```

Exemples :

- débit absent ;
- récupération inconnue ;
- `n50` absent ;
- infiltration inconnue ;
- fenêtres ouvrantes non renseignées ;
- consigne nocturne absente ;
- humidité non définie.

Pour chaque donnée :

- indiquer si elle est bloquante ;
- proposer une valeur de référence ;
- demander confirmation ;
- réduire la confiance ;
- conserver la provenance.

---

## Sauvegarde

Créer :

```ts
useSaveCoolingComfortSection()
```

Endpoint possible :

```text
PATCH /api/v1/greencube/cooling/studies/<id>
```

ou :

```text
PUT /api/v1/greencube/cooling/studies/<id>/comfort
```

Payload possible :

```json
{
  "ventilation": {
    "configuration_mode": "profile",
    "profile_id": 6,
    "profile_version": "2.0",
    "system_type": "balanced_double_flow",
    "airflow_input_mode": "airflow_m3h",
    "airflow_m3h": 120,
    "air_changes_per_hour": 1.48,
    "sensible_recovery_efficiency": 0.80,
    "latent_recovery_efficiency": 0.0,
    "summer_bypass_enabled": true,
    "fan_power_w": 45,
    "schedule": {
      "mode": "follow_occupancy"
    }
  },
  "airtightness": {
    "input_mode": "n50",
    "n50_ach": 1.5,
    "natural_infiltration_ach": 0.25,
    "wind_exposure": "normal"
  },
  "window_opening": {
    "mode": "temperature_controlled",
    "operable_area_m2": 2.4,
    "maximum_opening_fraction": 0.5,
    "night_purge_enabled": true
  },
  "comfort": {
    "profile_id": 3,
    "profile_version": "1.4",
    "cooling_setpoint_day_c": 25,
    "cooling_setpoint_night_c": 27,
    "maximum_acceptable_temperature_c": 29,
    "humidity_control_enabled": true,
    "maximum_relative_humidity_percent": 60,
    "resilience_level": "resilient"
  },
  "version": "server-version"
}
```

Adapter au contrat réel.

---

## Invalidation

Une modification peut invalider :

- charges sensibles ;
- charges latentes ;
- calcul rapide ;
- simulation EnergyPlus ;
- consommation estimée ;
- capacité recommandée ;
- rapport PDF.

Afficher :

```text
La modification de la ventilation, de l’étanchéité ou des consignes de confort rendra le résultat de refroidissement actuel obsolète.
```

---

## Formulaire React Hook Form

Créer :

```tsx
<ComfortVentilationForm />
```

Organisation :

```text
ventilationMode
ventilationProfile
airflow
schedule
heatRecovery
fanPower
airtightness
infiltration
windowOpening
doorOpening
temperatureSetpoints
humiditySetpoints
resilienceLevel
```

Utiliser :

- `useForm` ;
- `FormProvider` ;
- `useFieldArray` si nécessaire ;
- Zod ;
- dirty tracking ;
- reset contrôlé.

---

## Schéma Zod

Exemple :

```ts
const ventilationSchema = z.object({
  systemType: z.enum([
    "none",
    "natural",
    "single_flow_exhaust",
    "single_flow_supply",
    "balanced_double_flow",
    "mechanical_supply_exhaust",
    "mixed_mode",
    "custom",
  ]),
  airflowInputMode: z.enum([
    "airflow_m3h",
    "air_changes_per_hour",
    "per_person",
    "per_area",
  ]),
  airflowM3h: z.number().min(0).max(100000).nullable(),
  airChangesPerHour: z.number().min(0).max(50).nullable(),
  sensibleRecoveryEfficiency: z.number().min(0).max(1),
  latentRecoveryEfficiency: z.number().min(0).max(1),
  summerBypassEnabled: z.boolean(),
  fanPowerW: z.number().min(0).max(100000),
});
```

Compléter avec l’étanchéité, les fenêtres, les portes et le confort.

---

## Validations croisées

Utiliser `superRefine` pour vérifier :

- débit requis selon la méthode ;
- ventilation nulle cohérente avec le mode ;
- ACH cohérent avec le volume ;
- récupération compatible avec le système ;
- rendement latent cohérent ;
- bypass compatible ;
- `n50` requis selon le mode ;
- infiltration valide ;
- surface ouvrable inférieure aux vitrages ouvrants ;
- température maximale supérieure ou égale à la consigne ;
- humidité requise si contrôle actif ;
- planning valide ;
- absence de double comptage.

---

## Store temporaire

Ajouter uniquement :

```ts
interface CoolingComfortDraft {
  selectedVentilationProfileId?: number | null;
  selectedComfortProfileId?: number | null;
  activeSection?: string;
  hasUnconfirmedChanges: boolean;
}
```

Les données complètes restent dans React Hook Form et Odoo.

---

## Autosave

Autosave possible si :

- le débit est valide ;
- les rendements sont cohérents ;
- l’étanchéité est cohérente ;
- les consignes sont valides ;
- aucun changement de profil non confirmé ;
- aucune invalidation non confirmée.

Ne pas autosauvegarder :

- débit partiel ;
- rendement incohérent ;
- `n50` incomplet ;
- surface ouvrable invalide ;
- humidité incomplète ;
- changement de profil non confirmé.

---

## Accessibilité

Respecter :

- sélection clavier des profils ;
- labels ;
- fieldsets ;
- descriptions des unités ;
- erreurs associées ;
- focus lors des changements de mode ;
- annonces des conversions ;
- tableaux accessibles ;
- graphiques avec alternative textuelle ;
- couleurs non utilisées seules.

---

## Responsive

### Desktop

```text
Colonne gauche : ventilation et infiltration
Colonne droite : confort, récupération et résumé
```

### Tablette

- cartes en deux colonnes ;
- prévisualisation sous le formulaire.

### Mobile

- sections en accordéons ;
- conversions compactes ;
- horaires en cartes ;
- résumé sous le formulaire ;
- footer sticky.

---

## États de chargement

Prévoir :

- skeleton profils ;
- chargement des valeurs catalogue ;
- profil introuvable ;
- version archivée ;
- données partielles ;
- calcul de conversion ;
- calcul de prévisualisation ;
- erreur de référentiel.

---

## Gestion des erreurs

Codes possibles :

```text
VENTILATION_PROFILE_NOT_FOUND
VENTILATION_PROFILE_ARCHIVED
VENTILATION_PROFILE_VERSION_MISMATCH
INVALID_VENTILATION_TYPE
INVALID_AIRFLOW
INVALID_AIR_CHANGES_PER_HOUR
INVALID_HEAT_RECOVERY
INVALID_LATENT_RECOVERY
INVALID_FAN_POWER
INVALID_AIRTIGHTNESS
INVALID_N50
INVALID_INFILTRATION
INVALID_WINDOW_OPENING
INVALID_DOOR_OPENING
INVALID_TEMPERATURE_SETPOINT
INVALID_HUMIDITY_SETPOINT
INVALID_RESILIENCE_LEVEL
DOUBLE_COUNTED_AIRFLOW
MISSING_COMFORT_DATA
CONFLICT
INVALID_STATE
ACCESS_DENIED
```

Pour chaque erreur :

- message compréhensible ;
- champ concerné ;
- action ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires

Tester :

### Ventilation

- aucune ;
- naturelle ;
- simple flux ;
- double flux ;
- mode mixte ;
- profil archivé.

### Débits

- m³/h ;
- ACH ;
- par personne ;
- par surface ;
- conversions ;
- valeurs invalides.

### Récupération

- sensible ;
- latente ;
- bypass ;
- système incompatible.

### Ventilateurs

- puissance ;
- chaleur dans la zone ;
- localisation du moteur.

### Étanchéité

- `n50` ;
- infiltration naturelle ;
- profil ;
- exposition au vent.

### Fenêtres

- ouverture ;
- surface ;
- stratégie nocturne ;
- surface excessive.

### Portes

- fréquence ;
- durée ;
- niveau faible, moyen, élevé.

### Confort

- consigne jour ;
- consigne nuit ;
- humidité ;
- résilience ;
- valeurs incohérentes.

### Sauvegarde

- succès ;
- conflit ;
- invalidation ;
- lecture seule.

---

## Tests d’intégration

Tester :

1. chargement des profils ;
2. sélection d’une double flux ;
3. saisie du débit ;
4. conversion ACH ;
5. récupération ;
6. bypass été ;
7. puissance ventilateur ;
8. saisie `n50` ;
9. infiltration ;
10. ouverture nocturne ;
11. ouverture des portes ;
12. consignes ;
13. humidité ;
14. niveau résilient ;
15. prévisualisation ;
16. sauvegarde ;
17. réouverture ;
18. invalidation ;
19. conflit ;
20. étude validée ;
21. création d’une révision.

---

## Tests Playwright

Créer au minimum :

1. double flux avec récupération et bypass été ;
2. ventilation naturelle avec ouverture nocturne ;
3. simple flux avec infiltration standard ;
4. GreenCube très étanche avec `n50` mesuré ;
5. GreenCube peu étanche avec valeur de référence ;
6. usage résidentiel avec consigne jour/nuit ;
7. usage critique avec humidité maximale ;
8. surface ouvrable incohérente ;
9. changement de profil avec invalidation ;
10. étude validée en lecture seule.

---

## Mock API

Créer des mocks pour :

- ventilation naturelle ;
- simple flux ;
- double flux ;
- système mixte ;
- récupération sensible ;
- récupération enthalpique ;
- bypass été ;
- `n50` mesuré ;
- profil très étanche ;
- profil standard ;
- profil peu étanche ;
- ouverture nocturne ;
- consigne standard ;
- profil résilient ;
- profil critique ;
- données partielles ;
- profil archivé.

Les mocks doivent respecter l’OpenAPI réel.

---

## Composants à créer ou compléter

```text
CoolingComfortPage
VentilationModeCard
VentilationModeSelector
VentilationConfigurationModeSelector
FreshAirFlowCard
FreshAirFlowField
AirChangesPerHourField
AirflowInputModeSelector
AirflowConversionSummary
VentilationScheduleCard
VentilationScheduleEditor
NightVentilationCard
HeatRecoveryCard
SummerBypassField
FanPowerCard
AirtightnessCard
N50Field
InfiltrationRateField
WindExposureSelector
WindowOpeningCard
DoorOpeningCard
ComfortSetpointCard
TemperatureSetpointField
HumiditySetpointCard
ResilienceLevelCard
ComfortLevelSelector
AirLoadPreviewCard
AirflowSummaryCard
ComfortVentilationConfidencePanel
MissingComfortDataAlert
ComfortVentilationForm
```

---

## Documentation

Créer :

```text
docs/cooling_ventilation_comfort_screen.md
docs/cooling_ventilation_energyplus_mapping.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

Mapping attendu :

```text
Profils ventilation
→ GET /cooling/ventilation-profiles

Profils étanchéité
→ GET /cooling/airtightness-profiles

Profils confort
→ GET /cooling/comfort-profiles

Sauvegarde confort
→ PATCH /studies/<id>
ou endpoint dédié

Révision
→ POST /studies/<id>/revisions
```

Le mapping énergétique doit contenir :

```text
champ Odoo
→ champ frontend
→ solver rapide
→ objet Honeybee
→ objet EnergyPlus
→ unité
→ transformation
```

---

## Critères d’acceptation

Le lot est accepté si :

- la route fonctionne ;
- les prérequis sont contrôlés ;
- les profils viennent d’Odoo ;
- aucun profil n’est codé en dur ;
- les modes profil et personnalisé fonctionnent ;
- les systèmes de ventilation sont gérés ;
- les débits en m³/h, ACH, par personne et par surface sont gérés ;
- les conversions sont affichées ;
- les calendriers sont gérés ;
- la ventilation nocturne est gérée ;
- la récupération sensible est gérée ;
- la récupération latente est gérée ;
- le bypass été est géré ;
- la puissance ventilateur est gérée ;
- la dissipation des ventilateurs est gérée ;
- le `n50` est géré ;
- l’infiltration naturelle est gérée ;
- l’exposition au vent est gérée ;
- l’ouverture des fenêtres est gérée ;
- l’ouverture des portes est gérée ;
- les consignes jour et nuit sont gérées ;
- l’humidité est gérée ;
- le niveau de résilience est géré ;
- les charges sensibles et latentes sont prévisualisées ;
- les doubles comptages sont détectés ;
- le mapping solver est documenté ;
- le mapping Honeybee/EnergyPlus est documenté ;
- la provenance est visible ;
- la confiance est visible ;
- les données manquantes sont identifiées ;
- la sauvegarde met à jour Odoo ;
- les conflits sont gérés ;
- les résultats dépendants sont invalidés ;
- l’étude validée est en lecture seule ;
- la révision fonctionne ;
- l’accessibilité est assurée ;
- le responsive fonctionne ;
- les tests passent ;
- TypeScript strict passe ;
- le lint passe ;
- le build passe ;
- aucun secret n’est exposé ;
- aucun fichier n’est supprimé.

---

## Rapport final attendu

### Architecture

- page ;
- composants ;
- hooks ;
- store ;
- formulaires ;
- prévisualisations.

### Ventilation

- systèmes ;
- débits ;
- calendriers ;
- récupération ;
- ventilateurs.

### Étanchéité et infiltration

- `n50` ;
- ACH ;
- profils ;
- exposition ;
- conversions.

### Ouvertures

- fenêtres ;
- portes ;
- stratégies ;
- calendriers.

### Confort

- températures ;
- humidité ;
- résilience ;
- scénarios.

### Mappings

- solver rapide ;
- Honeybee ;
- EnergyPlus ;
- unités ;
- transformations.

### Fichiers

- créés ;
- modifiés ;
- non modifiés ;
- supprimés, normalement aucun.

### API

Pour chaque appel :

- endpoint ;
- payload ;
- réponse ;
- erreurs ;
- tests.

### Tests

- commandes ;
- résultats ;
- couverture ;
- tests non exécutés ;
- raisons.

### Performance

- profils ;
- conversions ;
- prévisualisations ;
- re-renders ;
- bundle ;
- limites.

### Sécurité

- permissions ;
- stockage ;
- secrets ;
- logs ;
- données mesurées.

### Patch

- diff ;
- patch réintégrable ;
- instructions ;
- rollback.

---

## Contrôle final

Avant conclusion :

1. lancer le lint ;
2. lancer TypeScript strict ;
3. lancer les tests unitaires ;
4. lancer les tests d’intégration ;
5. lancer Playwright ;
6. construire le frontend ;
7. vérifier les profils ;
8. vérifier les systèmes ;
9. vérifier les débits ;
10. vérifier les conversions ;
11. vérifier les calendriers ;
12. vérifier la ventilation nocturne ;
13. vérifier la récupération ;
14. vérifier le bypass ;
15. vérifier les ventilateurs ;
16. vérifier le `n50` ;
17. vérifier l’infiltration ;
18. vérifier l’exposition ;
19. vérifier les fenêtres ;
20. vérifier les portes ;
21. vérifier les consignes ;
22. vérifier l’humidité ;
23. vérifier la résilience ;
24. vérifier les charges sensibles ;
25. vérifier les charges latentes ;
26. vérifier les doubles comptages ;
27. vérifier la provenance ;
28. vérifier la confiance ;
29. vérifier les données manquantes ;
30. vérifier la sauvegarde ;
31. vérifier l’invalidation ;
32. vérifier les conflits ;
33. vérifier la lecture seule ;
34. vérifier la révision ;
35. vérifier l’accessibilité ;
36. vérifier le responsive ;
37. vérifier l’absence de secrets ;
38. vérifier qu’aucun fichier n’a été supprimé ;
39. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente uniquement l’écran Ventilation, infiltration et niveau de confort.

Il ne finalise pas encore :

- la synthèse avant calcul ;
- le solver thermique rapide ;
- l’orchestration EnergyPlus ;
- l’écran de résultats ;
- la sélection d’un équipement de refroidissement.

Il doit fournir des données d’air extérieur, d’étanchéité et de confort suffisamment structurées et traçables pour permettre le calcul complet du besoin de refroidissement.
