# GC-COOLING-11 — Équipements, éclairage et apports internes

## Objectif

Implémenter l’écran :

```text
5 — Équipements, éclairage et apports internes
```

L’écran doit permettre de :

- sélectionner des équipements depuis le catalogue Odoo ;
- ajouter des équipements personnalisés ;
- indiquer les quantités ;
- renseigner les puissances nominales et moyennes ;
- gérer les puissances de veille ;
- définir les facteurs de charge ;
- définir les facteurs de simultanéité ;
- distinguer consommation électrique et chaleur dissipée ;
- renseigner les fractions sensible, latente, radiante et convective ;
- gérer les équipements permanents ;
- gérer l’éclairage ;
- gérer l’électroménager ;
- gérer les équipements informatiques ;
- gérer les batteries et onduleurs ;
- gérer les équipements techniques ;
- définir les calendriers d’utilisation ;
- visualiser les gains internes estimés ;
- identifier les charges de pointe ;
- afficher la provenance et le score de confiance ;
- sauvegarder la section dans Odoo ;
- produire un payload pour le solver rapide ;
- documenter le mapping Honeybee/EnergyPlus ;
- passer à l’étape Ventilation et confort.

Odoo Community 18 reste la source de vérité.

Le frontend ne doit jamais supposer que 100 % de la puissance électrique devient immédiatement une charge sensible dans la zone.

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
- un modèle GreenCube et son enveloppe ;
- une orientation ;
- des vitrages et protections solaires ;
- un profil d’usage ;
- un profil d’occupation ;
- des calendriers horaires ;
- les permissions et statuts de l’étude ;
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
- inspecter les modèles Odoo liés aux charges internes ;
- inspecter `product.template` et `product.product` ;
- vérifier les catégories de produits techniques ;
- vérifier les données thermiques du catalogue ;
- vérifier les unités ;
- vérifier les conventions de dissipation ;
- vérifier les profils horaires ;
- vérifier le mapping Honeybee/EnergyPlus ;
- vérifier les règles d’invalidation ;
- vérifier les endpoints existants ;
- exécuter lint, TypeScript, tests et build ;
- ne supprimer aucun composant ;
- ne coder aucun équipement en dur ;
- ne jamais modifier le catalogue Odoo depuis l’étude.

---

## Route

```text
/cooling/studies/:studyId/equipment
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
StudyEditableGuard
```

Pour une étude calculée ou validée :

- afficher en lecture seule ;
- proposer une révision ;
- interdire la modification directe.

---

## Structure de la page

Créer :

```tsx
<CoolingEquipmentPage />
```

Structure recommandée :

```text
CoolingLayout
├── Introduction
├── InternalLoadSummaryCard
├── EquipmentCatalogSearch
├── EquipmentList
├── LightingLoadCard
├── PermanentLoadsCard
├── CustomEquipmentCard
├── EquipmentScheduleCard
├── InternalGainBreakdown
├── PeakLoadAlert
├── ProvenanceAndConfidence
├── ValidationWarnings
└── CoolingFooter
```

---

## Catégories d’apports internes

Prévoir au minimum :

```text
lighting
office_equipment
it_equipment
household_appliance
cooking
technical_equipment
battery
inverter
server
medical_equipment
workshop_equipment
other
```

Les codes doivent venir d’Odoo ou d’un référentiel backend.

---

## Catalogue des équipements

Créer :

```ts
useCoolingEquipmentCatalog()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/equipment-products
```

La réponse doit idéalement contenir :

- identifiant ;
- produit ;
- variante ;
- code ;
- catégorie ;
- fabricant ;
- puissance nominale ;
- puissance moyenne ;
- puissance de veille ;
- fraction dissipée dans la zone ;
- fraction sensible ;
- fraction latente ;
- fraction convective ;
- fraction radiante ;
- profil horaire ;
- statut ;
- version ;
- provenance ;
- documentation.

Ne jamais coder les équipements directement dans le frontend.

---

## Recherche et filtres

Créer :

```tsx
<EquipmentCatalogSearch />
<EquipmentCatalogFilters />
<EquipmentCatalogResultCard />
```

Filtres possibles :

```text
category
manufacturer
power_min
power_max
permanent_load
has_thermal_data
availability
```

Fonctions :

- recherche par nom ;
- recherche par code ;
- filtres ;
- pagination ;
- sélection ;
- ajout à l’étude.

---

## Ajout d’un équipement catalogue

Lors de l’ajout :

- conserver `product_id` ;
- conserver `product_variant_id` si nécessaire ;
- conserver la version des données thermiques ;
- copier les valeurs dans la ligne d’étude ;
- permettre une personnalisation liée à l’étude ;
- ne jamais modifier la fiche produit.

Créer :

```tsx
<AddEquipmentDialog />
```

---

## Liste des équipements

Créer :

```tsx
<EquipmentList />
<EquipmentRow />
<EquipmentCard />
```

Afficher pour chaque ligne :

- nom ;
- catégorie ;
- quantité ;
- puissance nominale ;
- puissance active retenue ;
- puissance de veille ;
- facteur de charge ;
- facteur de simultanéité ;
- fraction dissipée ;
- calendrier ;
- apport sensible estimé ;
- apport latent estimé ;
- provenance ;
- confiance ;
- statut de validation.

---

## Structure d’une ligne

Exemple :

```ts
interface CoolingEquipmentDraft {
  id?: number;
  productId?: number | null;
  productVariantId?: number | null;
  customName?: string;
  categoryCode: string;
  quantity: number;
  nominalPowerW: number;
  averagePowerW?: number | null;
  standbyPowerW?: number | null;
  diversityFactor: number;
  zoneDissipationFraction: number;
  sensibleFraction: number;
  latentFraction: number;
  radiantFraction: number;
  convectiveFraction: number;
  scheduleId?: number | null;
  customSchedule?: CoolingSchedule;
  isPermanentLoad: boolean;
  provenance: string;
}
```

Adapter au backend réel.

---

## Quantité

Créer :

```tsx
<EquipmentQuantityField />
```

Validation initiale :

```text
0 à 10 000 unités
```

Règles :

- entier pour les appareils unitaires ;
- quantité positive ;
- suppression explicite pour retirer une ligne ;
- pas de quantité nulle sur une ligne active.

---

## Puissance nominale

Créer :

```tsx
<NominalPowerField />
```

Unité principale :

```text
W
```

Affichage secondaire possible :

```text
kW
```

Validation indicative :

```text
0 à 1 000 000 W par ligne
```

Une valeur très élevée doit produire un avertissement.

---

## Puissance moyenne

Champ facultatif :

```text
average_power_w
```

La puissance moyenne peut être différente de la puissance nominale.

Priorité possible côté backend :

```text
average_power
→ nominal_power × load_factor
→ nominal_power
```

La valeur retenue pour le calcul doit être affichée clairement.

---

## Puissance de veille

Créer :

```tsx
<StandbyPowerField />
```

La veille doit pouvoir s’appliquer :

- hors période active ;
- la nuit ;
- le week-end ;
- toute l’année.

Ne pas supposer que la veille est nulle.

---

## Facteur de charge

Champ :

```text
load_factor
```

Plage :

```text
0 à 1
```

Exemple :

```text
0,60 = fonctionnement moyen à 60 % de la puissance nominale
```

Ne pas le confondre avec le facteur de simultanéité.

---

## Facteur de simultanéité

Créer :

```tsx
<DiversityFactorField />
```

Plage :

```text
0 à 1
```

Exemple :

```text
0,75 = 75 % des équipements supposés fonctionner simultanément
```

Le facteur peut être défini :

- par ligne ;
- par groupe ;
- par catégorie ;
- par défaut backend.

Ne pas l’appliquer deux fois.

---

## Puissance active de prévisualisation

Calcul indicatif :

```text
active_power_w =
quantity
× selected_power_w
× load_factor
× diversity_factor
```

Le backend doit recalculer.

---

## Fraction dissipée dans la zone

Créer :

```tsx
<ZoneDissipationFractionField />
```

Plage :

```text
0 à 1
```

Exemples :

```text
1,00 = toute la puissance devient chaleur dans la zone
0,50 = la moitié est dissipée dans la zone
0,00 = chaleur rejetée à l’extérieur
```

Cas à distinguer :

- groupe extérieur ;
- hotte ;
- serveur ventilé ;
- onduleur en local adjacent ;
- batterie dans un compartiment séparé.

---

## Charge sensible et latente

Créer :

```tsx
<SensibleLatentSplitField />
```

Règle :

```text
sensible_fraction + latent_fraction ≤ 1
```

La plupart des équipements électriques sont principalement sensibles.

Certains équipements de cuisson, lavage ou séchage peuvent avoir une part latente.

---

## Fraction radiante et convective

Créer :

```tsx
<RadiantConvectiveSplitField />
```

Règle recommandée :

```text
radiant_fraction + convective_fraction = 1
```

Ne pas confondre :

- sensible / latent ;
- radiant / convectif.

---

## Prévisualisation des gains

Créer :

```tsx
<EquipmentHeatGainPreview />
```

Calculs indicatifs :

```text
zone_heat_gain_w =
active_power_w
× zone_dissipation_fraction

sensible_gain_w =
zone_heat_gain_w
× sensible_fraction

latent_gain_w =
zone_heat_gain_w
× latent_fraction

radiant_gain_w =
sensible_gain_w
× radiant_fraction

convective_gain_w =
sensible_gain_w
× convective_fraction
```

Le backend doit recalculer toutes les valeurs.

---

## Équipements permanents

Créer :

```tsx
<PermanentLoadsCard />
```

Exemples :

- routeur ;
- serveur ;
- réfrigérateur ;
- batterie ;
- onduleur ;
- alarme ;
- électronique de contrôle ;
- équipements médicaux ;
- équipements techniques.

Champs :

- fonctionnement permanent ;
- puissance active ;
- puissance nocturne ;
- calendrier ;
- criticité.

---

## Éclairage

Créer :

```tsx
<LightingLoadCard />
```

Modes :

```text
fixtures
power_density
catalog_profile
```

### Mode luminaires

Saisir :

- type ;
- quantité ;
- puissance unitaire ;
- calendrier ;
- facteur d’utilisation ;
- fraction dissipée.

### Mode densité

Unité :

```text
W/m²
```

Calcul indicatif :

```text
lighting_power_w =
lighting_power_density_w_m2
× floor_area_m2
```

### Mode profil catalogue

Sélectionner un profil Odoo versionné.

---

## Contrôle de l’éclairage

Feature flag possible :

```text
enable_advanced_lighting_control
```

Modes possibles :

```text
none
manual
dimming
occupancy_sensor
combined
```

Cette fonction peut rester simplifiée pour le MVP.

---

## Électroménager

Catégories possibles :

- réfrigérateur ;
- congélateur ;
- lave-vaisselle ;
- lave-linge ;
- sèche-linge ;
- four ;
- plaque de cuisson ;
- micro-ondes ;
- machine à café ;
- autre.

Pour chaque appareil :

- puissance ;
- cycle ;
- durée ;
- nombre de cycles ;
- veille ;
- chaleur sensible ;
- humidité potentielle ;
- rejet extérieur.

---

## Cuisson

Créer :

```tsx
<CookingEquipmentFields />
```

Champs :

- puissance ;
- type ;
- durée ;
- simultanéité ;
- captation de la hotte ;
- rejet extérieur ;
- part sensible ;
- part latente.

---

## Équipements informatiques

Exemples :

- ordinateur portable ;
- ordinateur fixe ;
- écran ;
- imprimante ;
- serveur ;
- switch ;
- routeur ;
- baie informatique.

Pour les serveurs :

- distinguer puissance IT ;
- chaleur rejetée dans la zone ;
- refroidissement dédié ;
- fonctionnement 24/7.

---

## Batteries et onduleurs

Créer :

```tsx
<BatteryInverterLoadFields />
```

Distinguer :

- pertes à la charge ;
- pertes à la décharge ;
- puissance de veille ;
- électronique de puissance ;
- emplacement ;
- ventilation ;
- compartiment séparé.

Ne jamais utiliser la capacité nominale de stockage comme charge thermique.

---

## Appareils produisant du froid

Cas :

- réfrigérateur ;
- congélateur ;
- groupe frigorifique ;
- petite climatisation.

Le backend doit définir la frontière du système :

- condenseur dans la zone ;
- condenseur à l’extérieur ;
- zone refroidie incluse ou non.

Ne pas déduire automatiquement une charge négative.

---

## Localisation du rejet thermique

Champ :

```text
heat_rejection_location
```

Valeurs :

```text
inside_zone
outside_zone
adjacent_zone
partially_outside
```

---

## Calendrier des équipements

Créer :

```tsx
<EquipmentScheduleCard />
<EquipmentScheduleEditor />
```

Modes :

```text
follow_occupancy
catalog_schedule
custom_schedule
always_on
```

Chaque équipement peut :

- suivre l’occupation ;
- utiliser un profil Odoo ;
- utiliser un planning personnalisé ;
- fonctionner en permanence ;
- utiliser un planning saisonnier.

---

## Structure du calendrier

Exemple :

```json
{
  "mode": "custom_schedule",
  "weekly_schedule": {
    "monday": [
      {
        "start": "08:00",
        "end": "18:00",
        "operation_fraction": 0.8
      }
    ]
  }
}
```

La fraction de fonctionnement doit rester entre 0 et 1.

---

## Relation avec l’occupation

Option :

```text
follow_occupancy_schedule
```

Si activée :

- l’équipement suit le profil d’occupation ;
- un coefficient complémentaire peut être appliqué ;
- la veille reste configurable.

---

## Groupes d’équipements

Créer éventuellement :

```tsx
<EquipmentGroup />
```

Permettre de regrouper :

- postes de travail ;
- luminaires ;
- appareils identiques ;
- équipements techniques ;
- charges permanentes.

Un groupe peut partager :

- calendrier ;
- simultanéité ;
- provenance ;
- catégorie.

---

## Presets d’équipements

Créer :

```tsx
<EquipmentPresetSelector />
```

Les presets doivent venir d’Odoo.

Exemple :

```text
Bureau standard
→ ordinateurs
→ écrans
→ imprimante
→ éclairage
→ routeur permanent
```

Règles :

- conserver la version ;
- permettre la personnalisation ;
- garder les modifications liées à l’étude ;
- ne jamais modifier le preset source.

---

## Détection des doublons

Lors de l’ajout :

- détecter un produit déjà présent ;
- proposer d’augmenter la quantité ;
- permettre une ligne distincte si le calendrier diffère ;
- ne pas fusionner automatiquement des lignes différentes.

---

## Apports par catégorie

Créer :

```tsx
<InternalGainBreakdown />
```

Afficher :

- éclairage ;
- informatique ;
- électroménager ;
- cuisson ;
- équipements techniques ;
- batteries et onduleurs ;
- autres.

Pour chaque catégorie :

- puissance active ;
- gain sensible ;
- gain latent ;
- part du total ;
- charge de pointe.

---

## Charge de pointe

Créer :

```tsx
<PeakLoadAlert />
```

Identifier de manière indicative :

- équipement principal ;
- charge permanente élevée ;
- simultanéité prudente ;
- puissance anormalement élevée ;
- charge nocturne importante.

---

## Prévisualisation horaire

Créer éventuellement :

```tsx
<InternalLoadDailyChart />
```

Afficher sur 24 heures :

- éclairage ;
- équipements ;
- veille ;
- total sensible ;
- total latent.

Prévoir une alternative tabulaire.

---

## Mapping solver rapide

Payload minimal :

```json
{
  "equipment_sensible_gain_w": 1450,
  "equipment_latent_gain_w": 120,
  "lighting_sensible_gain_w": 300,
  "permanent_sensible_gain_w": 180,
  "design_internal_gain_w": 2050,
  "schedule": {}
}
```

Conserver si possible le détail par ligne.

---

## Mapping Honeybee/EnergyPlus

Le service de simulation doit pouvoir produire :

- `ElectricEquipment` ;
- `GasEquipment` si nécessaire ;
- `Lights` ;
- calendriers ;
- puissance absolue ;
- puissance par surface ;
- fraction latente ;
- fraction radiante ;
- fraction perdue ;
- fraction convective dérivée si nécessaire.

Créer une documentation explicite.

---

## Fraction perdue

Mapping possible :

```text
lost_fraction =
1 - zone_dissipation_fraction
```

Sous réserve du contrat exact EnergyPlus.

La somme des fractions doit être validée.

---

## Puissance absolue ou densité

Documenter le choix entre :

```text
design_level_w
watts_per_area
watts_per_person
```

La source de vérité Odoo peut rester la puissance absolue.

---

## Provenance

Utiliser :

```tsx
<DataSourceBadge />
```

Sources possibles :

```text
product_catalog
equipment_profile
usage_preset
manufacturer_data
measured
user_confirmed
estimated_reference
backend_default
missing_fallback
```

Afficher la provenance pour :

- puissance ;
- veille ;
- dissipation ;
- simultanéité ;
- fractions thermiques ;
- calendrier ;
- rendement ;
- éclairage.

---

## Score de confiance

Créer :

```tsx
<EquipmentConfidencePanel />
```

Composantes possibles :

```text
equipment_identification
nominal_power
average_power
standby_power
schedule
diversity_factor
zone_dissipation
sensible_latent_split
lighting
```

Exemple :

```text
Confiance globale : 82 %

Équipements identifiés : 95 %
Puissances : 90 %
Calendriers : 80 %
Simultanéité : 70 %
Dissipation thermique : 75 %
Éclairage : 85 %
```

---

## Données manquantes

Créer :

```tsx
<MissingEquipmentDataAlert />
```

Exemples :

- puissance absente ;
- simultanéité inconnue ;
- calendrier absent ;
- fraction dissipée absente ;
- partage sensible/latent absent ;
- équipement personnalisé non documenté ;
- veille inconnue.

Pour chaque donnée :

- indiquer si elle est bloquante ;
- proposer une valeur de référence ;
- demander confirmation ;
- réduire la confiance ;
- conserver la provenance.

---

## Équipement personnalisé

Créer :

```tsx
<CustomEquipmentForm />
```

Champs obligatoires :

- nom ;
- catégorie ;
- quantité ;
- puissance ;
- calendrier ;
- fraction dissipée ;
- fraction sensible ;
- fraction latente.

Champs facultatifs :

- fabricant ;
- référence ;
- commentaire ;
- documentation ;
- veille ;
- rendement ;
- localisation du rejet.

---

## Sauvegarde

Créer :

```ts
useSaveCoolingEquipmentSection()
```

Endpoint possible :

```text
PATCH /api/v1/greencube/cooling/studies/<id>
```

ou :

```text
PUT /api/v1/greencube/cooling/studies/<id>/equipment
```

Payload possible :

```json
{
  "equipment_lines": [
    {
      "product_id": 42,
      "product_variant_id": 65,
      "quantity": 4,
      "nominal_power_w": 90,
      "average_power_w": 60,
      "standby_power_w": 2,
      "load_factor": 1.0,
      "diversity_factor": 0.8,
      "zone_dissipation_fraction": 1.0,
      "sensible_fraction": 1.0,
      "latent_fraction": 0.0,
      "radiant_fraction": 0.3,
      "convective_fraction": 0.7,
      "schedule": {
        "mode": "follow_occupancy"
      }
    }
  ],
  "lighting": {
    "mode": "power_density",
    "power_density_w_m2": 6.0,
    "schedule": {
      "mode": "follow_occupancy"
    }
  },
  "version": "server-version"
}
```

Adapter au contrat réel.

---

## Invalidation

Une modification peut invalider :

- apports internes ;
- calcul rapide ;
- simulation EnergyPlus ;
- consommation estimée ;
- capacité recommandée ;
- rapport PDF.

Afficher :

```text
La modification des équipements, des puissances ou des calendriers rendra le résultat de refroidissement actuel obsolète.
```

---

## Formulaire React Hook Form

Créer :

```tsx
<EquipmentInternalLoadsForm />
```

Organisation :

```text
equipmentPreset
equipmentLines
lighting
permanentLoads
customEquipment
schedules
```

Utiliser :

- `useForm` ;
- `FormProvider` ;
- `useFieldArray` ;
- Zod ;
- dirty tracking ;
- reset contrôlé.

---

## Schéma Zod

Exemple :

```ts
const equipmentLineSchema = z.object({
  id: z.number().int().positive().optional(),
  productId: z.number().int().positive().nullable(),
  customName: z.string().max(120).nullable(),
  categoryCode: z.string().min(1),
  quantity: z.number().int().min(1).max(10000),
  nominalPowerW: z.number().min(0).max(1000000),
  averagePowerW: z.number().min(0).max(1000000).nullable(),
  standbyPowerW: z.number().min(0).max(1000000).nullable(),
  loadFactor: z.number().min(0).max(1),
  diversityFactor: z.number().min(0).max(1),
  zoneDissipationFraction: z.number().min(0).max(1),
  sensibleFraction: z.number().min(0).max(1),
  latentFraction: z.number().min(0).max(1),
  radiantFraction: z.number().min(0).max(1),
  convectiveFraction: z.number().min(0).max(1),
  isPermanentLoad: z.boolean(),
});
```

Compléter avec l’éclairage et les calendriers.

---

## Validations croisées

Utiliser `superRefine` pour vérifier :

- produit ou nom personnalisé présent ;
- puissance valide ;
- moyenne cohérente avec la nominale ;
- veille cohérente ;
- sensible + latent ≤ 1 ;
- radiant + convectif = 1 si requis ;
- calendrier valide ;
- équipement permanent correctement configuré ;
- puissance totale non aberrante ;
- preset compatible avec l’usage ;
- aucune ligne vide.

---

## Store temporaire

Ajouter uniquement :

```ts
interface CoolingEquipmentDraft {
  selectedCategory?: string;
  selectedPresetId?: number | null;
  activeEquipmentId?: string | number | null;
  hasUnconfirmedChanges: boolean;
}
```

Les données complètes restent dans React Hook Form et Odoo.

---

## Autosave

Autosave possible si :

- toutes les lignes sont valides ;
- les fractions sont cohérentes ;
- les calendriers sont valides ;
- aucune ligne personnalisée n’est incomplète ;
- aucune invalidation non confirmée n’est nécessaire.

Ne pas autosauvegarder :

- ligne partielle ;
- fractions incohérentes ;
- planning incomplet ;
- changement de preset non confirmé ;
- suppression massive non confirmée.

---

## Accessibilité

Respecter :

- recherche catalogue au clavier ;
- ajout sans souris ;
- labels ;
- fieldsets ;
- tableaux accessibles ;
- cartes lisibles ;
- erreurs associées ;
- focus lors de l’ajout et de la suppression ;
- annonces des recalculs ;
- graphiques avec alternative tabulaire ;
- couleurs non utilisées seules.

---

## Responsive

### Desktop

```text
Colonne gauche : catalogue et liste
Colonne droite : résumé thermique et paramètres
```

### Tablette

- catalogue repliable ;
- liste pleine largeur ;
- résumé sous les lignes.

### Mobile

- lignes en cartes ;
- catalogue dans un drawer ;
- paramètres avancés en accordéons ;
- récapitulatif sous le formulaire ;
- footer sticky.

---

## États de chargement

Prévoir :

- skeleton catalogue ;
- chargement des presets ;
- équipement introuvable ;
- produit archivé ;
- données thermiques partielles ;
- calcul de prévisualisation ;
- calendrier indisponible ;
- erreur catalogue.

---

## Gestion des erreurs

Codes possibles :

```text
EQUIPMENT_PRODUCT_NOT_FOUND
EQUIPMENT_PRODUCT_ARCHIVED
EQUIPMENT_PROFILE_VERSION_MISMATCH
INVALID_EQUIPMENT_QUANTITY
INVALID_NOMINAL_POWER
INVALID_AVERAGE_POWER
INVALID_STANDBY_POWER
INVALID_LOAD_FACTOR
INVALID_DIVERSITY_FACTOR
INVALID_DISSIPATION_FRACTION
INVALID_SENSIBLE_LATENT_SPLIT
INVALID_RADIANT_CONVECTIVE_SPLIT
INVALID_EQUIPMENT_SCHEDULE
INVALID_LIGHTING_CONFIGURATION
DUPLICATE_EQUIPMENT
MISSING_EQUIPMENT_DATA
CONFLICT
INVALID_STATE
ACCESS_DENIED
```

Pour chaque erreur :

- message compréhensible ;
- ligne concernée ;
- action ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires

Tester :

### Catalogue

- chargement ;
- recherche ;
- filtres ;
- pagination ;
- produit archivé ;
- données partielles.

### Équipements

- ajout ;
- suppression ;
- duplication ;
- quantité ;
- puissance ;
- veille ;
- simultanéité ;
- dissipation.

### Fractions

- sensible ;
- latent ;
- radiant ;
- convectif ;
- somme invalide.

### Éclairage

- luminaires ;
- densité ;
- profil catalogue ;
- calendrier.

### Calendrier

- suivi de l’occupation ;
- personnalisé ;
- permanent ;
- veille.

### Calculs

- puissance active ;
- gain sensible ;
- gain latent ;
- gain radiant ;
- gain convectif.

### Sauvegarde

- succès ;
- conflit ;
- invalidation ;
- lecture seule.

---

## Tests d’intégration

Tester :

1. chargement catalogue ;
2. ajout d’un équipement ;
3. modification de la quantité ;
4. modification de la puissance ;
5. ajout d’un calendrier ;
6. ajout d’une charge permanente ;
7. configuration de l’éclairage ;
8. ajout d’un équipement personnalisé ;
9. prévisualisation des gains ;
10. sauvegarde ;
11. réouverture ;
12. changement de preset ;
13. invalidation ;
14. conflit ;
15. étude validée ;
16. création d’une révision.

---

## Tests Playwright

Créer au minimum :

1. bureau avec ordinateurs et écrans ;
2. studio avec électroménager ;
3. local technique avec onduleur et batterie ;
4. serveur permanent 24/7 ;
5. éclairage par densité de puissance ;
6. équipement personnalisé ;
7. fraction thermique incohérente ;
8. puissance anormalement élevée ;
9. changement de preset avec invalidation ;
10. étude validée en lecture seule.

---

## Mock API

Créer des mocks pour :

- ordinateur portable ;
- écran ;
- imprimante ;
- routeur ;
- réfrigérateur ;
- four ;
- machine à café ;
- batterie ;
- onduleur ;
- serveur ;
- éclairage standard ;
- produit archivé ;
- puissance absente ;
- fraction thermique absente ;
- preset bureau ;
- preset studio ;
- preset local technique.

Les mocks doivent respecter l’OpenAPI réel.

---

## Composants à créer ou compléter

```text
CoolingEquipmentPage
InternalLoadSummaryCard
EquipmentCatalogSearch
EquipmentCatalogFilters
EquipmentCatalogResultCard
AddEquipmentDialog
EquipmentList
EquipmentRow
EquipmentCard
EquipmentQuantityField
NominalPowerField
StandbyPowerField
DiversityFactorField
ZoneDissipationFractionField
SensibleLatentSplitField
RadiantConvectiveSplitField
EquipmentHeatGainPreview
PermanentLoadsCard
LightingLoadCard
CookingEquipmentFields
BatteryInverterLoadFields
EquipmentScheduleCard
EquipmentScheduleEditor
EquipmentGroup
EquipmentPresetSelector
InternalGainBreakdown
PeakLoadAlert
InternalLoadDailyChart
EquipmentConfidencePanel
MissingEquipmentDataAlert
CustomEquipmentForm
EquipmentInternalLoadsForm
```

---

## Documentation

Créer :

```text
docs/cooling_equipment_internal_loads_screen.md
docs/cooling_equipment_energyplus_mapping.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

Mapping attendu :

```text
Catalogue équipements
→ GET /cooling/equipment-products

Presets
→ GET /cooling/equipment-presets

Sauvegarde équipements
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
- le catalogue vient d’Odoo ;
- aucun équipement n’est codé en dur ;
- les équipements peuvent être ajoutés ;
- les quantités et puissances sont validées ;
- les puissances de veille sont gérées ;
- les facteurs de charge sont gérés ;
- les facteurs de simultanéité sont gérés ;
- la dissipation dans la zone est gérée ;
- les charges sensibles et latentes sont distinguées ;
- les fractions radiantes et convectives sont distinguées ;
- les équipements permanents sont gérés ;
- l’éclairage est géré ;
- les équipements personnalisés sont gérés ;
- les calendriers sont gérés ;
- les presets sont versionnés ;
- le catalogue n’est jamais modifié ;
- les gains sont prévisualisés ;
- les apports par catégorie sont affichés ;
- la charge de pointe est identifiable ;
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

### Catalogue

- source ;
- filtres ;
- pagination ;
- versions ;
- presets.

### Équipements

- catégories ;
- puissances ;
- veille ;
- calendriers ;
- simultanéité ;
- dissipation.

### Éclairage

- modes ;
- densité ;
- profils ;
- calendriers.

### Gains thermiques

- sensible ;
- latent ;
- radiant ;
- convectif ;
- perdu ;
- calculs.

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

- catalogue ;
- formulaires ;
- re-renders ;
- bundle ;
- limites.

### Sécurité

- permissions ;
- stockage ;
- secrets ;
- logs ;
- documents ;
- données catalogue.

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
7. vérifier le catalogue ;
8. vérifier les presets ;
9. vérifier les quantités ;
10. vérifier les puissances ;
11. vérifier les veilles ;
12. vérifier les facteurs de charge ;
13. vérifier la simultanéité ;
14. vérifier la dissipation ;
15. vérifier le sensible ;
16. vérifier le latent ;
17. vérifier le radiant ;
18. vérifier le convectif ;
19. vérifier les calendriers ;
20. vérifier les charges permanentes ;
21. vérifier l’éclairage ;
22. vérifier les équipements personnalisés ;
23. vérifier les batteries et onduleurs ;
24. vérifier les équipements informatiques ;
25. vérifier les charges de pointe ;
26. vérifier la provenance ;
27. vérifier la confiance ;
28. vérifier les données manquantes ;
29. vérifier la sauvegarde ;
30. vérifier l’invalidation ;
31. vérifier les conflits ;
32. vérifier la lecture seule ;
33. vérifier la révision ;
34. vérifier l’accessibilité ;
35. vérifier le responsive ;
36. vérifier l’absence de secrets ;
37. vérifier que le catalogue n’a pas été modifié ;
38. vérifier qu’aucun fichier n’a été supprimé ;
39. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente uniquement l’écran Équipements, éclairage et apports internes.

Il ne finalise pas encore :

- la ventilation ;
- l’infiltration ;
- les consignes de confort ;
- le solver thermique ;
- les résultats ;
- la sélection de climatiseur.

Il doit fournir une description structurée, traçable et suffisamment précise des charges internes pour permettre leur intégration dans le calcul de refroidissement.
