# GC-COOLING-18 — Sélection du système de refroidissement

## Objectif

Implémenter l’étape :

```text
9 — Sélection du système de refroidissement
```

Cette étape doit permettre de :

- rechercher les équipements disponibles dans Odoo ;
- filtrer les équipements techniquement compatibles ;
- comparer plusieurs produits ;
- vérifier la capacité nominale de refroidissement ;
- vérifier la capacité aux conditions climatiques dimensionnantes ;
- vérifier la modulation minimale et maximale ;
- vérifier la charge sensible ;
- vérifier la charge latente ;
- vérifier la déshumidification ;
- vérifier la compatibilité électrique ;
- vérifier le niveau sonore ;
- vérifier les contraintes d’installation ;
- vérifier la plage de température extérieure ;
- vérifier les condensats ;
- estimer la consommation électrique ;
- distinguer capacité thermique et puissance électrique ;
- expliquer les recommandations ;
- expliquer les exclusions ;
- enregistrer une sélection dans Odoo ;
- préparer la future génération du devis ;
- conserver la traçabilité du résultat thermique utilisé.

Odoo Community 18 reste la source de vérité pour :

- le catalogue ;
- les variantes ;
- les caractéristiques ;
- les prix ;
- les fournisseurs ;
- les disponibilités ;
- la sélection finale ;
- le lien avec le résultat thermique.

Le frontend ne doit jamais inventer une caractéristique produit.

---

## Prérequis

Le lot suppose disponibles :

```text
GC-COOLING-13
→ étude vérifiée
→ snapshot immuable

GC-COOLING-14
→ résultat MERCURE

GC-COOLING-15
→ résultat Honeybee / EnergyPlus

GC-COOLING-16
→ puissance recommandée
→ charge sensible
→ charge latente
→ SHR
→ scénario dimensionnant
→ confiance

GC-COOLING-17
→ MVP consolidé
→ API stabilisée
→ sécurité et recette
```

---

## Périmètre

Ce lot couvre :

```text
catalogue produit
normalisation des caractéristiques
filtres techniques
moteur de compatibilité
classement
comparaison
estimation électrique
sélection
persistance Odoo
préparation du devis
```

Il ne finalise pas encore :

- le devis complet ;
- le paiement ;
- la facturation ;
- la commande fournisseur ;
- la planification d’installation ;
- le commissioning ;
- le rapport PDF final.

---

## Types d’équipements

Prévoir au minimum :

```text
monobloc
split mural
console
cassette
gainable
climatiseur mobile
pompe à chaleur air-air
unité compacte
système réversible
solution passive ou hybride
```

Pour le MVP, privilégier :

```text
split mural
console
monobloc fixe
pompe à chaleur air-air réversible
solution compacte dédiée
```

Les types actifs doivent venir d’Odoo.

---

## Vérifications préalables

Avant toute modification :

- inspecter `product.template` ;
- inspecter `product.product` ;
- inspecter les catégories ;
- inspecter les attributs et variantes ;
- inspecter Search & Select si connecté ;
- inspecter ETIM ou IEC 61360 ;
- inspecter les champs techniques ;
- inspecter les unités ;
- inspecter les prix ;
- inspecter les listes de prix ;
- inspecter les fournisseurs ;
- inspecter les stocks si utilisés ;
- inspecter les résultats GC-COOLING-16 ;
- inspecter les règles de sélection ;
- inspecter les feature flags ;
- inspecter les permissions ;
- inspecter le multi-société ;
- inspecter OpenAPI ;
- inspecter les routes frontend ;
- inspecter les composants de comparaison ;
- exécuter les tests existants ;
- ne dupliquer aucun produit ;
- ne coder aucun catalogue en dur ;
- ne modifier aucune caractéristique importée sans traçabilité ;
- ne mélanger ni prix catalogue ni prix final ;
- ne recommander aucun produit sans données minimales suffisantes.

---

## Route

```text
/cooling/studies/:studyId/equipment-selection
```

Routes secondaires possibles :

```text
/cooling/studies/:studyId/equipment-selection/:productId
/cooling/studies/:studyId/equipment-comparison
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
CoolingResultRequiredGuard
CoolingEquipmentSelectionGuard
```

Prérequis :

- résultat thermique disponible ;
- résultat non obsolète ;
- puissance recommandée présente ;
- confiance suffisante ou dérogation ;
- aucune revue ingénieur bloquante.

---

## Structure de la page

Créer :

```tsx
<CoolingEquipmentSelectionPage />
```

Structure recommandée :

```text
CoolingLayout
├── EquipmentSelectionHeader
├── CoolingRequirementSummary
├── SelectionReadinessBanner
├── RecommendedEquipmentCard
├── CompatibleEquipmentList
├── ConditionalEquipmentList
├── ExcludedEquipmentPanel
├── EquipmentFilters
├── EquipmentComparisonDrawer
├── EnergyConsumptionEstimator
├── InstallationConstraintsPanel
├── SelectionExplanationPanel
└── EquipmentSelectionFooter
```

---

## Résumé du besoin thermique

Créer :

```tsx
<CoolingRequirementSummary />
```

Afficher :

- puissance recommandée ;
- puissance brute ;
- marge ;
- scénario dimensionnant ;
- charge sensible ;
- charge latente ;
- SHR ;
- température extérieure de calcul ;
- humidité extérieure ;
- consigne intérieure ;
- confiance ;
- moteur retenu ;
- date du résultat ;
- version du snapshot.

Exemple :

```text
Besoin recommandé : 3,5 kW
Charge sensible : 2,72 kW
Charge latente : 0,36 kW
SHR : 0,88
Scénario : Canicule prolongée
Température extérieure : 39 °C
```

---

## Disponibilité de la sélection

Créer :

```tsx
<SelectionReadinessBanner />
```

États possibles :

```text
ready
low_confidence
engineer_review_required
stale_result
missing_result
no_catalog
```

Bloquer la sélection si :

- le résultat est obsolète ;
- la capacité recommandée est absente ;
- une validation ingénieur est requise ;
- aucun produit ne possède les données minimales ;
- l’utilisateur n’a pas la permission.

---

## Modèles Odoo

Créer ou compléter :

```text
greencube.cooling.equipment.profile
greencube.cooling.equipment.selection
greencube.cooling.equipment.compatibility
greencube.cooling.equipment.rule
greencube.cooling.equipment.comparison
```

Réutiliser :

```text
product.template
product.product
product.category
product.attribute
product.attribute.value
product.supplierinfo
```

Éviter toute duplication inutile des caractéristiques produit.

---

## Profil technique produit

Créer si nécessaire :

```text
greencube.cooling.equipment.profile
```

Champs possibles :

```text
product_tmpl_id
product_variant_id
equipment_type
cooling_capacity_nominal_w
cooling_capacity_min_w
cooling_capacity_max_w
cooling_capacity_at_design_w
heating_capacity_nominal_w
power_input_cooling_w
power_input_heating_w
eer
seer
cop
scop
sensible_capacity_w
latent_capacity_w
sensible_heat_ratio
dehumidification_l_h
airflow_min_m3h
airflow_max_m3h
sound_pressure_indoor_db_a
sound_pressure_outdoor_db_a
sound_power_db_a
outdoor_temp_cooling_min_c
outdoor_temp_cooling_max_c
indoor_temp_cooling_min_c
indoor_temp_cooling_max_c
refrigerant_type
refrigerant_charge_kg
gwp
power_supply_type
voltage_v
phases
frequency_hz
rated_current_a
maximum_current_a
recommended_breaker_a
cable_section_mm2
condensate_drain_required
condensate_pump_included
fresh_air_connection
ducted
indoor_unit_width_mm
indoor_unit_height_mm
indoor_unit_depth_mm
outdoor_unit_width_mm
outdoor_unit_height_mm
outdoor_unit_depth_mm
indoor_unit_weight_kg
outdoor_unit_weight_kg
wifi_available
modbus_available
bacnet_available
home_assistant_compatible
warranty_years
active
data_quality_status
confidence_score
source
source_version
```

---

## Référentiels techniques

Utiliser si disponibles :

```text
ETIM
IEC 61360
eCl@ss
product.template
manufacturer datasheet
Search & Select normalized technical facts
```

Créer une matrice :

```text
référentiel source
→ caractéristique Odoo
→ unité source
→ unité interne
→ transformation
→ confiance
```

---

## Données minimales requises

Un produit ne peut pas être pleinement recommandé sans :

```text
type d’équipement
capacité de refroidissement
plage de modulation ou capacité minimale
puissance électrique ou EER
plage de température extérieure
compatibilité électrique
niveau sonore intérieur
dimensions principales
source technique
```

Selon l’usage, exiger également :

- capacité latente ;
- débit d’air ;
- condensats ;
- unité extérieure ;
- fluide frigorigène ;
- connectivité.

---

## Qualité des données

Statuts possibles :

```text
verified
manufacturer_data
catalog_data
estimated
incomplete
conflicting
obsolete
```

Créer :

```tsx
<ProductDataQualityBadge />
```

Un produit `incomplete` ou `conflicting` ne doit pas être recommandé sans avertissement.

---

## Provenance

Pour chaque caractéristique critique, conserver :

```text
value
unit
source
source_document
source_version
extracted_at
validated_at
confidence
```

Sources possibles :

```text
manufacturer_datasheet
manufacturer_api
supplier_catalog
search_select
manual_admin
legacy_import
estimated_reference
```

---

## Catalogue API

Créer :

```ts
useCoolingEquipmentCatalog()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/equipment-catalog
```

Filtres possibles :

```text
equipment_type
minimum_capacity_w
maximum_capacity_w
minimum_outdoor_temperature_c
maximum_outdoor_temperature_c
maximum_sound_level_db_a
power_supply_type
phases
refrigerant_type
manufacturer_id
availability_status
data_quality_status
```

---

## Moteur de compatibilité

Créer côté backend :

```python
evaluate_cooling_equipment_compatibility()
```

Comparer :

```text
besoin thermique
↔ caractéristiques produit
```

Statuts :

```text
compatible
compatible_with_conditions
not_recommended
incompatible
insufficient_data
```

Structure possible :

```python
class CoolingEquipmentCompatibilityResult:
    product_id: int
    status: str
    score: float
    hard_failures: list
    warnings: list
    matched_requirements: list
    missing_data: list
    ranking_factors: dict
    estimated_performance: dict
```

---

## Règles bloquantes

Exclure un produit si :

- capacité maximale insuffisante ;
- plage extérieure incompatible ;
- alimentation électrique incompatible ;
- phases incompatibles ;
- courant maximal incompatible ;
- type d’unité impossible à installer ;
- dimensions incompatibles ;
- fluide frigorigène interdit ;
- données critiques contradictoires ;
- produit archivé ou indisponible selon la règle active.

---

## Capacité aux conditions de calcul

Comparer :

```text
required_capacity_w
product_capacity_at_design_conditions_w
```

Règle :

```text
product_capacity_at_design_conditions_w
>= required_capacity_w
```

ou tolérance configurable.

Ne pas comparer uniquement la capacité nominale standard.

---

## Dégradation à haute température

Utiliser si disponibles :

- courbes de performance ;
- capacité à 35 °C ;
- capacité à 40 °C ;
- capacité à 45 °C ;
- facteur de dégradation.

Ne pas supposer une capacité constante à 40 °C.

---

## Courbe de performance

Créer éventuellement :

```text
greencube.cooling.equipment.performance.point
```

Champs :

```text
equipment_profile_id
outdoor_temperature_c
indoor_temperature_c
indoor_humidity_percent
cooling_capacity_w
power_input_w
eer
source
version
```

Interpoler uniquement entre des points valides.

---

## Capacité minimale et modulation

Vérifier :

```text
cooling_capacity_min_w
```

Une capacité minimale trop élevée peut provoquer :

- cycles courts ;
- inconfort ;
- baisse de rendement ;
- bruit ;
- déshumidification insuffisante.

Créer une règle versionnée de modulation.

---

## Surdimensionnement

Calcul :

```text
oversizing_ratio =
product_capacity_at_design_w
÷ required_capacity_w
```

Statuts possibles :

```text
well_sized
slightly_oversized
oversized
severely_oversized
```

Les seuils doivent être configurables.

---

## Charge sensible

Comparer si possible :

```text
product_sensible_capacity_w
>= required_sensible_load_w
```

Une capacité totale suffisante peut rester insuffisante en sensible.

---

## Charge latente

Comparer :

```text
product_latent_capacity_w
>= required_latent_load_w
```

ou utiliser :

```text
dehumidification_l_h
```

avec une méthode versionnée.

Si les données sont absentes :

- afficher un avertissement ;
- réduire la confiance ;
- interdire la recommandation si l’usage l’exige.

---

## Compatibilité SHR

Comparer :

```text
required_shr
product_shr
```

Le produit doit pouvoir traiter le profil sensible/latent du GreenCube.

---

## Plage extérieure

Vérifier :

```text
design_outdoor_temperature_c
<= product_outdoor_temp_cooling_max_c
```

Calculer :

```text
temperature_headroom_c =
product_max_outdoor_temp_c
- design_outdoor_temp_c
```

Une marge faible doit produire un avertissement.

---

## Compatibilité électrique

Vérifier :

```text
230 V monophasé
400 V triphasé
fréquence
courant nominal
courant maximal
disjoncteur
section de câble
```

Le projet doit fournir :

```text
available_voltage_v
available_phases
maximum_available_current_a
available_power_kw
electrical_standard
country_code
```

Si ces données manquent :

- afficher une hypothèse ;
- réduire la confiance ;
- demander validation avant sélection finale.

---

## Puissance thermique et électrique

Afficher séparément :

```text
cooling_capacity_kw
electrical_input_kw
```

Exemple :

```text
Capacité thermique : 3,5 kW
Puissance électrique nominale : 0,92 kW
```

---

## Rendement

Afficher :

```text
EER
SEER
COP
SCOP
```

Formule EER :

```text
EER =
cooling_capacity_w
÷ power_input_w
```

Le backend doit fournir ou valider la valeur.

---

## Estimation électrique

Créer côté backend :

```python
estimate_cooling_equipment_electricity()
```

Entrées :

- résultat thermique ;
- produit ;
- EER ou courbe de performance ;
- heures de fonctionnement ;
- profils d’usage ;
- scénario ;
- simulation annuelle si disponible.

Sorties :

```text
peak_electrical_input_kw
annual_electricity_kwh
heatwave_electricity_kwh
estimated_operating_hours
calculation_method
confidence_score
```

Deux niveaux :

```text
Niveau 1
electrical_power_kw = thermal_load_kw ÷ EER

Niveau 2
EnergyPlus annuel + courbe partielle + profil horaire
```

---

## Bruit

Vérifier :

```text
sound_pressure_indoor_db_a
sound_pressure_outdoor_db_a
sound_power_db_a
```

Comparer avec :

```text
sleeping
residential_day
office
technical_room
outdoor_sensitive
```

Une unité bruyante doit être pénalisée pour un studio occupé la nuit.

---

## Débit d’air

Vérifier :

```text
airflow_min_m3h
airflow_max_m3h
```

Comparer avec :

- volume ;
- brassage ;
- bruit ;
- vitesse d’air ;
- diffusion.

Ne pas assimiler débit de recirculation et air neuf.

---

## Contraintes d’installation

Vérifier :

- unité intérieure ;
- unité extérieure ;
- longueur frigorifique ;
- dénivelé ;
- dégagements ;
- maintenance ;
- condensats ;
- alimentation ;
- support ;
- traversée de paroi ;
- voisinage ;
- rejet d’air chaud.

---

## Condensats

Champs :

```text
condensate_drain_required
gravity_drain_possible
condensate_pump_required
condensate_pump_included
```

Une pompe requise doit être signalée.

---

## Monobloc et climatiseur mobile

Pour un monobloc, vérifier :

- traversées d’air ;
- rejet extérieur ;
- bruit ;
- étanchéité ;
- débit ;
- pont thermique ;
- condensats.

Un climatiseur mobile doit généralement être classé :

```text
temporary_solution
backup_solution
not_recommended_for_permanent_use
```

---

## Réversibilité chauffage

Afficher si disponible :

```text
heating_available
heating_capacity_kw
SCOP
minimum_heating_temperature_c
```

Ne pas modifier automatiquement le besoin de refroidissement.

---

## Fluide frigorigène

Afficher :

```text
refrigerant_type
refrigerant_charge_kg
GWP
```

Politiques possibles :

```text
allowed
discouraged
restricted
not_allowed
```

Les règles doivent être versionnées et administrables.

---

## Maintenance et connectivité

Afficher :

- garantie ;
- périodicité de maintenance ;
- accessibilité des filtres ;
- disponibilité des pièces ;
- Wi-Fi ;
- Modbus ;
- BACnet ;
- Matter ;
- API constructeur ;
- Home Assistant ;
- contact sec ;
- pilotage tarifaire.

Créer :

```tsx
<EquipmentConnectivityBadges />
```

---

## Disponibilité et prix

Statuts possibles :

```text
in_stock
available_to_order
supplier_confirmed
lead_time_unknown
temporarily_unavailable
discontinued
```

Ne pas confondre compatibilité technique et disponibilité.

Prix possibles :

```text
product_price
installation_estimate
accessories_estimate
total_estimate
currency
taxes_included
```

Le prix doit venir d’Odoo ou d’une estimation identifiée.

---

## Classement

Créer :

```python
rank_cooling_equipment()
```

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

Les pondérations doivent être configurables et versionnées.

---

## Score et catégories

Score :

```text
0 à 100
```

Catégories :

```text
recommended
strong_alternative
compatible
compatible_with_conditions
not_recommended
incompatible
insufficient_data
```

Labels :

```text
Recommandé
Très bonne alternative
Compatible
Compatible sous conditions
Non recommandé
Incompatible
Données insuffisantes
```

Le score doit toujours être accompagné de raisons.

---

## Recommandation principale

Créer :

```tsx
<RecommendedEquipmentCard />
```

Afficher :

- produit ;
- fabricant ;
- référence ;
- photo ;
- type ;
- capacité aux conditions de calcul ;
- capacité nominale ;
- puissance électrique ;
- EER ;
- SEER ;
- bruit ;
- modulation ;
- déshumidification ;
- score ;
- raisons ;
- prix indicatif ;
- disponibilité ;
- qualité des données.

---

## Alternatives et exclusions

Créer :

```tsx
<CompatibleEquipmentList />
<ConditionalEquipmentList />
<ExcludedEquipmentPanel />
```

Pour les produits conditionnels, afficher les conditions :

- pompe de condensats ;
- alimentation spécifique ;
- réduction acoustique ;
- capacité limite à haute température ;
- validation de la charge latente ;
- accessoire obligatoire.

Pour les exclus, afficher :

- motif principal ;
- règles échouées ;
- valeur requise ;
- valeur produit ;
- données manquantes.

---

## Filtres et tri

Créer :

```tsx
<EquipmentFilters />
```

Filtres possibles :

```text
type
fabricant
capacité
prix
bruit
efficacité
monophasé
triphasé
réversible
Wi-Fi
Modbus
Home Assistant
fluide
disponibilité
qualité des données
```

Tri :

```text
recommandation
capacité la plus proche
meilleur rendement
moins bruyant
prix le plus bas
meilleure disponibilité
meilleure qualité de données
```

Le tri par défaut doit être :

```text
recommandation
```

Les filtres ne doivent jamais contourner les règles bloquantes.

---

## Comparaison

Créer :

```tsx
<EquipmentComparisonDrawer />
<EquipmentComparisonTable />
```

Comparer de 2 à 4 produits sur :

- capacité nominale ;
- capacité aux conditions de calcul ;
- modulation ;
- sensible ;
- latent ;
- EER ;
- SEER ;
- puissance électrique ;
- bruit ;
- plage extérieure ;
- dimensions ;
- poids ;
- condensats ;
- alimentation ;
- connectivité ;
- garantie ;
- prix ;
- disponibilité ;
- score ;
- réserves.

---

## Fiche produit

Créer :

```tsx
<CoolingEquipmentDetailPanel />
```

Sections :

```text
Résumé
Performance
Capacité
Énergie
Acoustique
Électricité
Dimensions
Installation
Condensats
Réfrigérant
Connectivité
Documents
Provenance
Compatibilité
```

Documents possibles :

- fiche technique ;
- manuel d’installation ;
- déclaration CE ;
- fiche énergétique ;
- courbe de performance ;
- schéma électrique ;
- dimensions ;
- maintenance.

---

## Explication de la recommandation

Créer :

```tsx
<SelectionExplanationPanel />
```

Exemple :

```text
Ce produit est recommandé parce que :

- sa capacité à 40 °C reste supérieure au besoin ;
- sa modulation limite les cycles courts ;
- son niveau sonore est adapté à un usage nocturne ;
- sa déshumidification couvre la charge latente ;
- il fonctionne sur l’alimentation disponible.
```

Afficher également les réserves :

```text
- pompe de condensats non incluse ;
- unité extérieure à éloigner du couchage ;
- courbe de performance au-delà de 43 °C non disponible.
```

---

## Sélection finale

Créer :

```tsx
<SelectCoolingEquipmentDialog />
```

Afficher :

- étude ;
- résultat thermique ;
- snapshot ;
- produit ;
- variante ;
- capacité ;
- score ;
- réserves ;
- accessoires ;
- prix indicatif ;
- date ;
- utilisateur.

---

## Persistance Odoo

Créer :

```text
greencube.cooling.equipment.selection
```

Champs possibles :

```text
study_id
revision_id
snapshot_id
result_id
product_tmpl_id
product_variant_id
equipment_profile_id
compatibility_status
compatibility_score
selection_status
selected_by
selected_at
company_id
required_capacity_w
product_capacity_at_design_w
commercial_capacity_w
estimated_power_input_w
estimated_annual_electricity_kwh
currency_id
indicative_price
reservation_notes
rule_version
data_version
```

Statuts :

```text
draft
selected
validated
superseded
cancelled
quoted
```

Une nouvelle sélection doit remplacer l’ancienne sans la supprimer.

---

## Historique et versioning

La sélection doit rester liée à :

- un résultat ;
- un snapshot ;
- une version produit ;
- une version des règles ;
- une liste de prix.

Si le produit évolue :

- ne pas modifier la sélection historique ;
- signaler la nouvelle version ;
- proposer une nouvelle évaluation.

---

## Endpoints

### Recommandation

```text
POST /api/v1/greencube/cooling/studies/<study_id>/equipment-recommendations
```

### Sélection

```text
POST /api/v1/greencube/cooling/studies/<study_id>/equipment-selections
```

### Lecture

```text
GET /api/v1/greencube/cooling/studies/<study_id>/equipment-selections
GET /api/v1/greencube/cooling/equipment/<product_id>
GET /api/v1/greencube/cooling/equipment/<product_id>/compatibility?result_id=<id>
```

### Comparaison

```text
POST /api/v1/greencube/cooling/equipment/compare
```

---

## Idempotence et conflits

Utiliser :

```text
Idempotency-Key
```

Vérifier :

- version de l’étude ;
- version du résultat ;
- version du produit ;
- version du profil technique ;
- version des règles ;
- version de prix.

En cas de conflit :

- bloquer ;
- recharger ;
- expliquer ;
- proposer une nouvelle évaluation.

---

## Accessoires

Prévoir :

```text
pompe de condensats
support mural
silentblocs
liaison frigorifique
goulotte
protection électrique
câble
disjoncteur
commande
kit grand froid
déflecteur
protection extérieure
```

Statuts :

```text
required
recommended
optional
incompatible
```

Les accessoires doivent venir d’Odoo.

---

## Préparation du devis

La sélection doit produire un payload exploitable :

```json
{
  "study_id": 45,
  "result_id": 76,
  "selection_id": 18,
  "main_product_id": 1284,
  "required_accessory_ids": [202, 207],
  "recommended_accessory_ids": [215],
  "installation_context": {
    "wall_penetration": true,
    "condensate_pump": true,
    "electrical_upgrade": false
  }
}
```

Ne pas générer encore le devis final.

---

## Feature flags

Créer ou réutiliser :

```text
enable_cooling_equipment_selection
enable_cooling_equipment_prices
enable_cooling_equipment_stock
enable_cooling_equipment_annual_energy
enable_cooling_equipment_what_if
enable_cooling_quote_preparation
```

Chaque flag doit être documenté et testé.

---

## Store frontend

Ajouter uniquement :

```ts
interface CoolingEquipmentSelectionUiState {
  selectedProductIds: number[];
  comparisonProductIds: number[];
  filters: CoolingEquipmentFilters;
  sortMode: string;
  expandedProductId?: number | null;
}
```

Les recommandations et sélections restent dans Odoo.

---

## Query hooks

Créer :

```ts
useCoolingEquipmentRecommendations(studyId, resultId, filters)
useCoolingEquipmentDetail(productId)
useCoolingEquipmentCompatibility(productId, resultId)
useCoolingEquipmentComparison(resultId, productIds)
useCoolingEquipmentSelections(studyId)
useSelectCoolingEquipment()
```

---

## Validation Zod

Créer des schémas pour :

- filtres ;
- comparaison ;
- sélection ;
- commentaire ;
- acknowledgement des réserves.

Exemple :

```ts
const selectCoolingEquipmentSchema = z.object({
  resultId: z.number().int().positive(),
  productVariantId: z.number().int().positive(),
  acknowledgedWarningCodes: z.array(z.string()),
  comment: z.string().max(1000).optional(),
  idempotencyKey: z.string().uuid(),
});
```

---

## Accessibilité

Respecter :

- filtres accessibles ;
- comparaison au clavier ;
- tableaux avec en-têtes ;
- alternatives aux badges ;
- images avec texte alternatif ;
- unités lisibles ;
- avertissements annoncés ;
- dialogue accessible ;
- focus après filtre ;
- navigation mobile.

---

## Responsive

### Desktop

```text
Colonne principale : recommandation et liste
Colonne secondaire : besoin, filtres et résumé
```

### Tablette

- recommandation pleine largeur ;
- filtres repliables ;
- cartes en deux colonnes.

### Mobile

- résumé en premier ;
- filtres en drawer ;
- comparaison en cartes ;
- action de sélection sticky ;
- tableaux transformés.

---

## Formatage des unités

Créer :

```ts
formatCoolingCapacity()
formatElectricalPower()
formatEnergyEfficiency()
formatSoundLevel()
formatAirflow()
formatDimensions()
formatWeight()
formatAnnualEnergy()
formatPrice()
```

Ne pas afficher de précision artificielle.

---

## États de chargement

Prévoir :

- chargement du besoin ;
- chargement du catalogue ;
- évaluation en cours ;
- comparaison en cours ;
- sélection en cours ;
- prix indisponible ;
- stock indisponible ;
- données partielles ;
- aucun produit compatible ;
- erreur de référentiel.

---

## Aucun produit compatible

Afficher :

```text
Aucun équipement du catalogue actuel ne satisfait l’ensemble des contraintes.
```

Proposer :

- élargir certains filtres non bloquants ;
- consulter les produits conditionnels ;
- demander une revue ingénieur ;
- ajouter un produit au catalogue ;
- revoir le besoin via une révision.

Ne jamais recommander un produit incompatible.

---

## Erreurs backend

Codes possibles :

```text
COOLING_RESULT_REQUIRED
COOLING_RESULT_STALE
ENGINEER_REVIEW_REQUIRED
COOLING_CATALOG_EMPTY
COOLING_PRODUCT_NOT_FOUND
COOLING_PRODUCT_INACTIVE
COOLING_PRODUCT_DATA_INCOMPLETE
COOLING_PRODUCT_INCOMPATIBLE
COOLING_PRODUCT_VERSION_CONFLICT
COOLING_SELECTION_ALREADY_EXISTS
COOLING_SELECTION_NOT_ALLOWED
COOLING_PRICE_UNAVAILABLE
COOLING_STOCK_UNAVAILABLE
COOLING_RULE_VERSION_UNAVAILABLE
ACCESS_DENIED
```

Pour chaque erreur :

- message clair ;
- produit ;
- règle ;
- action ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires backend

Tester :

### Capacité

- insuffisante ;
- exacte ;
- marge correcte ;
- surdimensionnement ;
- haute température.

### Modulation

- adaptée ;
- cycles courts ;
- données absentes.

### Sensible et latent

- compatibles ;
- sensible insuffisant ;
- latent insuffisant ;
- données absentes.

### Température

- plage suffisante ;
- limite ;
- incompatible.

### Électricité

- monophasé ;
- triphasé ;
- courant insuffisant ;
- tension incompatible.

### Acoustique

- studio nuit ;
- bureau ;
- local technique.

### Installation

- pompe de condensats ;
- unité extérieure ;
- monobloc ;
- dimensions.

### Classement

- score ;
- pondérations ;
- données manquantes ;
- produit exclu ;
- alternative.

---

## Tests frontend

Tester :

- chargement ;
- filtres ;
- tri ;
- recommandation ;
- alternatives ;
- produits conditionnels ;
- exclusions ;
- comparaison ;
- fiche produit ;
- sélection ;
- erreur ;
- mobile ;
- accessibilité.

---

## Tests d’intégration

Tester :

1. lecture du résultat ;
2. récupération du catalogue ;
3. compatibilité ;
4. classement ;
5. recommandation principale ;
6. comparaison de trois produits ;
7. sélection ;
8. historique ;
9. idempotence ;
10. conflit de version ;
11. prix ;
12. disponibilité ;
13. accessoires ;
14. permissions ;
15. multi-société.

---

## Tests Playwright

Créer au minimum :

1. sélection d’un split mural adapté ;
2. exclusion pour capacité insuffisante ;
3. produit conditionnel avec pompe de condensats ;
4. comparaison de trois produits ;
5. produit silencieux recommandé pour usage nocturne ;
6. produit électriquement incompatible ;
7. forte charge latente ;
8. aucun produit compatible ;
9. résultat obsolète bloquant ;
10. accès inter-sociétés interdit.

---

## Mock API

Créer des mocks pour :

- catalogue complet ;
- produit recommandé ;
- alternative ;
- produit conditionnel ;
- produit incompatible ;
- données incomplètes ;
- haute température ;
- forte charge latente ;
- monophasé ;
- triphasé ;
- prix indisponible ;
- stock indisponible ;
- sélection existante ;
- conflit de version.

Les mocks doivent respecter OpenAPI.

---

## Composants à créer ou compléter

```text
CoolingEquipmentSelectionPage
EquipmentSelectionHeader
CoolingRequirementSummary
SelectionReadinessBanner
RecommendedEquipmentCard
CompatibleEquipmentList
CompatibleEquipmentCard
ConditionalEquipmentList
ExcludedEquipmentPanel
EquipmentFilters
EquipmentComparisonDrawer
EquipmentComparisonTable
CoolingEquipmentDetailPanel
EquipmentConnectivityBadges
ProductDataQualityBadge
EnergyConsumptionEstimator
InstallationConstraintsPanel
SelectionExplanationPanel
SelectCoolingEquipmentDialog
EquipmentSelectionFooter
```

---

## Documentation

Créer :

```text
docs/cooling_equipment_selection_overview.md
docs/cooling_equipment_catalog_model.md
docs/cooling_equipment_technical_mapping.md
docs/cooling_equipment_compatibility_rules.md
docs/cooling_equipment_ranking.md
docs/cooling_equipment_energy_estimation.md
docs/cooling_equipment_api.md
docs/cooling_equipment_frontend.md
docs/cooling_equipment_limitations.md
docs/cooling_equipment_compatibility_matrix.md
```

La matrice doit suivre :

```text
exigence projet
→ champ produit
→ règle
→ sévérité
→ statut possible
→ message
→ test
```

---

## Critères d’acceptation

Le lot est accepté si :

- la route fonctionne ;
- le résultat thermique est chargé ;
- un résultat obsolète bloque la sélection ;
- le catalogue vient d’Odoo ;
- aucun produit n’est codé en dur ;
- les caractéristiques sont normalisées ;
- la qualité des données est affichée ;
- la provenance est conservée ;
- la capacité nominale est affichée ;
- la capacité aux conditions de calcul est utilisée ;
- la dégradation à haute température est gérée ;
- la capacité minimale est gérée ;
- le surdimensionnement est détecté ;
- la charge sensible est vérifiée ;
- la charge latente est vérifiée ;
- le SHR est pris en compte ;
- la plage extérieure est vérifiée ;
- l’alimentation électrique est vérifiée ;
- le courant est vérifié ;
- le niveau sonore est vérifié ;
- le débit d’air est affiché ;
- les contraintes d’installation sont gérées ;
- les condensats sont gérés ;
- l’unité extérieure est gérée ;
- le fluide frigorigène est affiché ;
- la connectivité est affichée ;
- disponibilité et compatibilité sont séparées ;
- le prix vient d’Odoo ;
- le moteur de compatibilité fonctionne ;
- le classement fonctionne ;
- le score est explicable ;
- la recommandation principale est affichée ;
- les alternatives sont affichées ;
- les produits conditionnels sont affichés ;
- les exclusions sont expliquées ;
- les filtres fonctionnent ;
- le tri fonctionne ;
- la comparaison fonctionne ;
- la fiche produit fonctionne ;
- les accessoires sont gérés ;
- l’estimation électrique est affichée ;
- capacité thermique et puissance électrique sont distinguées ;
- la sélection est persistée ;
- l’idempotence fonctionne ;
- les conflits sont gérés ;
- l’historique est conservé ;
- la préparation du devis est disponible ;
- les permissions sont respectées ;
- le multi-société est respecté ;
- l’accessibilité est assurée ;
- le responsive fonctionne ;
- les tests passent ;
- TypeScript strict passe ;
- le lint passe ;
- le build passe ;
- aucun secret n’est exposé ;
- aucun fichier n’est supprimé sans justification.

---

## Rapport final attendu

### Architecture

- frontend ;
- Odoo ;
- API ;
- moteur de compatibilité ;
- moteur de classement ;
- estimation énergétique.

### Catalogue

- modèles ;
- champs ;
- unités ;
- référentiels ;
- qualité ;
- provenance ;
- versions.

### Compatibilité

- règles bloquantes ;
- règles conditionnelles ;
- capacité ;
- modulation ;
- sensible ;
- latent ;
- température ;
- électricité ;
- bruit ;
- installation.

### Classement

- facteurs ;
- pondérations ;
- score ;
- catégories ;
- explications.

### Sélection

- modèle Odoo ;
- historique ;
- idempotence ;
- version ;
- accessoires ;
- préparation du devis.

### API

Pour chaque endpoint :

- méthode ;
- URL ;
- payload ;
- réponse ;
- erreurs ;
- permissions ;
- cache ;
- idempotence.

### Tests

- commandes ;
- résultats ;
- couverture ;
- cas de référence ;
- tests non exécutés ;
- raisons.

### Performance

- taille du catalogue ;
- temps d’évaluation ;
- nombre de règles ;
- cache ;
- pagination ;
- re-renders ;
- bundle.

### Sécurité

- permissions ;
- multi-société ;
- prix ;
- fournisseurs ;
- documents ;
- logs ;
- artefacts.

### Patch

- diff ;
- patch réintégrable ;
- migrations ;
- installation ;
- rollback.

---

## Contrôle final

Avant conclusion :

1. lancer le lint frontend ;
2. lancer TypeScript strict ;
3. lancer les tests frontend ;
4. lancer Playwright ;
5. construire le frontend ;
6. lancer le lint Python ;
7. lancer le contrôle de types ;
8. lancer les tests backend ;
9. lancer les tests Odoo ;
10. lancer les tests API ;
11. vérifier les modèles ;
12. vérifier le catalogue ;
13. vérifier les unités ;
14. vérifier les référentiels ;
15. vérifier la provenance ;
16. vérifier la qualité des données ;
17. vérifier la capacité nominale ;
18. vérifier la capacité haute température ;
19. vérifier la modulation ;
20. vérifier le surdimensionnement ;
21. vérifier le sensible ;
22. vérifier le latent ;
23. vérifier le SHR ;
24. vérifier les températures ;
25. vérifier l’électricité ;
26. vérifier le bruit ;
27. vérifier le débit ;
28. vérifier l’installation ;
29. vérifier les condensats ;
30. vérifier l’unité extérieure ;
31. vérifier le fluide ;
32. vérifier la connectivité ;
33. vérifier la disponibilité ;
34. vérifier les prix ;
35. vérifier les règles ;
36. vérifier le score ;
37. vérifier la recommandation ;
38. vérifier les alternatives ;
39. vérifier les exclusions ;
40. vérifier les filtres ;
41. vérifier la comparaison ;
42. vérifier la sélection ;
43. vérifier l’historique ;
44. vérifier les accessoires ;
45. vérifier l’estimation électrique ;
46. vérifier la préparation du devis ;
47. vérifier l’idempotence ;
48. vérifier les conflits ;
49. vérifier les permissions ;
50. vérifier le multi-société ;
51. vérifier l’accessibilité ;
52. vérifier le responsive ;
53. vérifier l’absence de secrets ;
54. vérifier qu’aucun résultat historique n’a été modifié ;
55. vérifier qu’aucun fichier n’a été supprimé ;
56. ne jamais déclarer un test réussi sans l’avoir réellement exécuté.

---

## Limites du lot

Ce lot implémente :

- le catalogue d’équipements ;
- la normalisation technique ;
- le moteur de compatibilité ;
- le moteur de classement ;
- la comparaison ;
- l’estimation énergétique ;
- la sélection ;
- la préparation du devis.

Il ne finalise pas encore :

- le devis Odoo complet ;
- les remises commerciales ;
- la validation fournisseur ;
- la commande ;
- la facturation ;
- le paiement ;
- la planification d’installation ;
- le commissioning ;
- le rapport PDF final.

Le résultat attendu est une sélection d’équipement techniquement justifiée, explicable, traçable et exploitable par un futur workflow commercial Odoo.
