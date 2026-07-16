# GC-COOLING-09 — Orientation, vitrages et protections solaires

## Objectif

Implémenter l’écran :

```text
3 — Orientation, vitrages et protections solaires
```

L’écran doit permettre de :

- définir l’orientation réelle du GreenCube ;
- visualiser les façades ;
- saisir ou confirmer les surfaces vitrées ;
- sélectionner les vitrages ;
- renseigner le coefficient U ;
- renseigner le facteur solaire ;
- positionner les ouvertures ;
- renseigner les protections solaires ;
- renseigner les masques extérieurs ;
- vérifier les incohérences géométriques ;
- calculer les surfaces opaques nettes ;
- prévisualiser les apports solaires ;
- afficher la provenance et la confiance ;
- sauvegarder les données dans Odoo ;
- passer à l’étape Usage et occupation.

Odoo Community 18 reste la source de vérité.

Les calculs frontend servent uniquement à la prévisualisation. Les calculs thermiques définitifs doivent être réalisés côté backend ou par EnergyPlus.

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
- un modèle GreenCube sélectionné ;
- une géométrie validée ;
- les surfaces brutes des façades ;
- les caractéristiques thermiques de l’enveloppe ;
- les permissions et statuts d’étude ;
- le système de sauvegarde ;
- le verrouillage optimiste ;
- la gestion des révisions.

---

## Vérifications préalables

Avant toute modification :

- inspecter les écrans précédents ;
- vérifier la route ;
- vérifier le layout et le stepper ;
- vérifier le store Zustand ;
- vérifier le client API ;
- vérifier les query keys ;
- vérifier les composants de formulaire ;
- inspecter les modèles Odoo liés aux façades, ouvertures, vitrages et protections ;
- vérifier la convention d’orientation ;
- vérifier les unités ;
- vérifier les facteurs solaires stockés ;
- vérifier si les ouvertures sont stockées individuellement ou agrégées ;
- vérifier les endpoints existants ;
- vérifier les règles d’invalidation ;
- vérifier les données utilisées par Honeybee/EnergyPlus ;
- exécuter le lint ;
- exécuter TypeScript ;
- exécuter les tests ;
- exécuter le build ;
- ne supprimer aucun composant ;
- ne coder aucun vitrage ou protection en dur.

---

## Route

```text
/cooling/studies/:studyId/orientation
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
StudyEditableGuard
```

Prérequis :

- étude existante ;
- localisation confirmée ;
- modèle sélectionné ;
- géométrie disponible.

Pour une étude calculée ou validée :

- afficher en lecture seule ;
- proposer une révision ;
- interdire la modification directe.

---

## Structure de la page

Créer :

```tsx
<CoolingOrientationPage />
```

Structure recommandée :

```text
CoolingLayout
├── Introduction
├── BuildingOrientationCard
├── OrientationCompass
├── FacadeTabs
├── ApertureSummaryCard
├── GlazingPerformanceCard
├── ShadingProtectionCard
├── ExternalObstructionCard
├── SolarGainPreviewCard
├── GeometryWarnings
├── ProvenanceAndConfidence
└── CoolingFooter
```

---

## Convention d’orientation

Utiliser :

```text
0° = nord
90° = est
180° = sud
270° = ouest
```

Créer :

```ts
normalizeOrientationDegrees(value: number): number
```

La valeur doit rester entre :

```text
0 inclus et 360 exclu
```

La convention doit être confirmée avec :

- Odoo ;
- Honeybee ;
- EnergyPlus ;
- la géométrie du modèle.

---

## Orientation principale

Créer :

```tsx
<BuildingOrientationCard />
<OrientationCompass />
<OrientationSelector />
```

Modes de saisie :

- valeur numérique ;
- points cardinaux ;
- sélection graphique ;
- orientation issue du catalogue ;
- orientation issue d’un plan ;
- aide via carte.

Champs :

```text
orientation_deg
orientation_source
orientation_confirmed
```

Sources possibles :

```text
catalog
plan
map
user_confirmed
estimated
```

---

## Points cardinaux

Correspondances :

```text
Nord : 0°
Nord-Est : 45°
Est : 90°
Sud-Est : 135°
Sud : 180°
Sud-Ouest : 225°
Ouest : 270°
Nord-Ouest : 315°
```

La valeur numérique reste la valeur interne.

---

## Façades

Créer :

```tsx
<FacadeTabs />
<FacadePanel />
<FacadeSummary />
```

Afficher pour chaque façade :

- nom ;
- orientation réelle ;
- largeur ;
- hauteur ;
- surface brute ;
- surface de portes ;
- surface vitrée ;
- surface opaque nette ;
- pourcentage vitré ;
- avertissements.

---

## Calcul des azimuts

Pour une géométrie rectangulaire simple :

```text
façade principale = orientation_deg
façade droite = orientation_deg + 90°
façade arrière = orientation_deg + 180°
façade gauche = orientation_deg + 270°
```

Normaliser modulo 360.

Le backend doit recalculer.

---

## Structure des façades

Type possible :

```ts
interface CoolingFacadeDraft {
  facadeId?: number;
  facadeCode: string;
  azimuthDeg: number;
  grossAreaM2: number;
  opaqueDoorAreaM2: number;
  glazingAreaM2: number;
  netOpaqueAreaM2: number;
  glazingRatioPercent: number;
  apertures: CoolingApertureDraft[];
}
```

Les valeurs calculées doivent être séparées des valeurs saisies.

---

## Ouvertures vitrées

Créer :

```tsx
<ApertureEditor />
<ApertureList />
<ApertureCard />
```

Pour chaque ouverture :

- identifiant ;
- nom ;
- façade ;
- type ;
- largeur ;
- hauteur ;
- surface ;
- position ;
- hauteur d’allège ;
- coefficient U ;
- facteur solaire ;
- transmission visible ;
- protection ;
- provenance ;
- confiance.

Types possibles :

```text
window
glazed_door
fixed_glazing
rooflight
other
```

---

## Modes de saisie

Prévoir :

```text
aggregated
detailed
```

Créer :

```tsx
<ApertureInputModeSelector />
```

### Mode agrégé

Saisir :

- surface vitrée totale par façade ;
- vitrage principal ;
- protection globale.

### Mode détaillé

Saisir chaque ouverture individuellement.

Adapté à :

- EnergyPlus ;
- géométrie avancée ;
- projets très vitrés ;
- vitrages différents sur une même façade.

---

## Conversion entre modes

### Agrégé vers détaillé

- proposer une ouverture représentative ;
- conserver la surface totale ;
- marquer la géométrie comme estimée ;
- demander confirmation.

### Détaillé vers agrégé

- sommer les ouvertures ;
- avertir de la perte de détail ;
- ne rien supprimer sans confirmation.

---

## Validation géométrique

Vérifier :

- largeur positive ;
- hauteur positive ;
- surface positive ;
- cohérence largeur × hauteur ;
- surface vitrée totale inférieure ou égale à la façade ;
- position dans les limites ;
- hauteur d’allège valide ;
- absence de chevauchement si pris en charge ;
- aucune ouverture hors paroi.

Créer :

```ts
validateApertureGeometry()
```

Le backend reste l’autorité finale.

---

## Ratio vitré

Calcul :

```text
glazing_ratio_percent =
surface_vitree / surface_brute_facade × 100
```

Repères indicatifs :

```text
0 à 20 % : faible
20 à 40 % : modéré
40 à 60 % : élevé
plus de 60 % : très élevé
```

Ces niveaux ne doivent pas être présentés comme des normes.

---

## Surface opaque nette

Calcul :

```text
surface_opaque_nette =
surface_brute
- surface_vitree
- surface_portes_opaques
```

La valeur ne doit jamais être négative.

En cas d’erreur :

- bloquer la sauvegarde ;
- identifier la façade ;
- afficher un message clair.

---

## Catalogue de vitrages

Créer :

```ts
useCoolingGlazingProducts()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/glazing-products
```

Les vitrages doivent venir d’Odoo.

Données possibles :

- identifiant ;
- nom ;
- code ;
- type ;
- coefficient U ;
- facteur solaire ;
- transmission visible ;
- épaisseur ;
- composition ;
- statut ;
- version ;
- fabricant ;
- documentation.

Ne jamais coder les vitrages en dur.

---

## Sélecteur de vitrage

Créer :

```tsx
<GlazingTypeSelector />
```

Afficher :

- nom ;
- code ;
- double ou triple vitrage ;
- coefficient U ;
- facteur solaire ;
- transmission visible ;
- provenance ;
- version.

---

## Coefficient U du vitrage

Créer :

```tsx
<GlazingUValueField />
```

Unité :

```text
W/m².K
```

Plage indicative :

```text
0,3 à 6,0 W/m².K
```

Ne pas confondre :

- `Ug` du vitrage ;
- `Uw` de la fenêtre complète ;
- `Uf` du cadre.

Le contrat API doit préciser la valeur réellement utilisée.

---

## Facteur solaire

Créer :

```tsx
<SolarFactorField />
```

Unité interne recommandée :

```text
valeur décimale de 0 à 1
```

Exemple :

```text
0,42
```

Créer :

```ts
formatSolarFactor(value: number): string
```

Ne pas afficher `42` sans préciser qu’il s’agit de 42 %.

---

## g-value et SHGC

Créer :

```ts
mapGlazingSolarProperty()
```

Toute conversion doit :

- être centralisée ;
- être documentée ;
- conserver la valeur source ;
- conserver le type source ;
- afficher l’approximation.

---

## Cadres de fenêtres

Si disponible, renseigner :

- matériau ;
- largeur ;
- fraction de cadre ;
- coefficient `Uf` ;
- pont thermique de bord.

Pour le MVP, choisir une seule méthode :

```text
cadre inclus dans Uw
```

ou :

```text
cadre modélisé séparément
```

Ne pas appliquer les deux.

---

## Transmission visible

Champ facultatif :

```text
visible_transmittance
```

Plage :

```text
0 à 1
```

Cette valeur ne doit pas bloquer le calcul de refroidissement si elle est absente.

---

## Protections solaires

Créer :

```tsx
<ShadingProtectionCard />
<ShadingTypeSelector />
```

Types possibles :

```text
none
interior_blind
interior_curtain
exterior_blind
roller_shutter
awning
overhang
vertical_fin
pergola
fixed_screen
vegetation
other
```

Distinguer explicitement :

```text
Protection intérieure
Protection extérieure
```

---

## Protections fixes

Créer :

```tsx
<FixedShadingGeometryForm />
```

Saisir :

- profondeur ;
- largeur ;
- hauteur ;
- distance par rapport à la baie ;
- angle ;
- débord gauche ;
- débord droit.

Exemples :

- auvent ;
- casquette ;
- brise-soleil ;
- lame verticale ;
- pergola.

---

## Protections mobiles

Créer :

```tsx
<DynamicShadingControlForm />
```

Saisir :

- type ;
- intérieur ou extérieur ;
- état par défaut ;
- calendrier ;
- seuil d’activation ;
- contrôle manuel ou automatique ;
- coefficient de réduction.

Modes possibles :

```text
always_open
always_closed
manual_schedule
solar_threshold
temperature_threshold
backend_default
```

---

## Calendrier des protections

Proposer :

```text
Toujours actif en été
Actif en journée
Automatique selon rayonnement
Personnalisé
```

Le calendrier doit être structuré et non stocké comme texte libre.

---

## Coefficient de réduction solaire

Plage :

```text
0 à 1
```

Exemple :

```text
0,30 = 70 % d’apports solaires bloqués
```

Conserver :

- valeur ;
- source ;
- méthode ;
- version ;
- confiance.

---

## Masques extérieurs

Créer :

```tsx
<ExternalObstructionCard />
<ExternalObstructionEditor />
```

Types :

```text
nearby_building
wall
tree
terrain
canopy
balcony
other
```

Pour chaque masque :

- orientation ;
- distance ;
- hauteur ;
- largeur angulaire ;
- opacité ;
- saisonnalité ;
- provenance.

---

## Végétation

Pour un arbre ou une végétation :

- type générique ;
- distance ;
- hauteur ;
- largeur ;
- feuillage permanent ou caduc ;
- période feuillue ;
- densité approximative.

Ne pas considérer automatiquement la végétation comme opaque.

---

## Terrain et relief

Pour les sites montagneux :

- permettre un masque de relief ;
- ne pas le déduire uniquement de l’altitude ;
- conserver la provenance ;
- prévoir une future intégration avec un modèle numérique de terrain.

Pour le MVP, un masque angulaire simplifié est acceptable.

---

## Toiture vitrée

Créer si nécessaire :

```tsx
<RoofApertureSection />
```

Cas concernés :

- lanterneau ;
- puits de lumière ;
- toiture vitrée.

Les apports de toiture doivent être séparés de ceux des façades verticales.

---

## Aperçu graphique

Créer éventuellement :

```tsx
<FacadeGlazingPreview />
```

Afficher :

- bâtiment simplifié ;
- orientation ;
- vitrages ;
- protections ;
- façade active.

L’aperçu reste illustratif.

---

## Prévisualisation des apports solaires

Créer :

```tsx
<SolarGainPreviewCard />
```

Formule simplifiée :

```text
Q_solaire =
surface_vitree
× rayonnement_scenario
× facteur_solaire
× facteur_protection
× facteur_masque
```

Le calcul doit :

- utiliser un scénario climatique ;
- afficher l’unité W ;
- afficher les hypothèses ;
- être identifié comme prévisualisation ;
- ne pas remplacer le backend.

---

## Scénarios de prévisualisation

Permettre :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Afficher par façade :

- rayonnement ;
- apport brut ;
- réduction par vitrage ;
- réduction par protection ;
- apport net estimé.

---

## Répartition des apports

Afficher un tableau accessible :

| Façade | Surface vitrée | Facteur solaire | Protection | Apport estimé |
|---|---:|---:|---:|---:|
| Nord | 1,5 m² | 0,42 | Aucune | 180 W |
| Est | 3,0 m² | 0,42 | Store extérieur | 420 W |
| Sud | 4,5 m² | 0,38 | Casquette | 610 W |
| Ouest | 5,0 m² | 0,42 | Aucune | 1 320 W |

---

## Façade critique

Créer :

```tsx
<CriticalFacadeAlert />
```

Le frontend peut identifier de manière indicative :

- la façade avec le plus d’apports ;
- un ratio vitré élevé ;
- un facteur solaire élevé ;
- une absence de protection ;
- une baie ouest critique.

---

## Données manquantes

Créer :

```tsx
<MissingGlazingDataAlert />
```

Exemples :

- facteur solaire absent ;
- coefficient U absent ;
- surface vitrée incohérente ;
- protection non caractérisée ;
- orientation non confirmée ;
- masque incomplet.

Pour chaque donnée :

- indiquer si elle est bloquante ;
- proposer une valeur de référence ;
- demander confirmation ;
- réduire la confiance ;
- conserver la provenance.

---

## Valeurs de référence

Le backend peut proposer :

- vitrage standard ;
- facteur solaire standard ;
- coefficient U standard ;
- réduction de store ;
- absence de masque.

Afficher :

- source ;
- version ;
- date ;
- confiance ;
- caractère estimé.

---

## Provenance

Utiliser :

```tsx
<DataSourceBadge />
```

Sources possibles :

```text
catalog
plan
user_confirmed
measured
estimated_reference
backend_default
missing_fallback
```

Afficher la provenance pour :

- orientation ;
- surface vitrée ;
- vitrage ;
- coefficient U ;
- facteur solaire ;
- protection ;
- masque.

---

## Score de confiance

Créer :

```tsx
<OrientationGlazingConfidencePanel />
```

Composantes possibles :

```text
orientation
surface_glazing
glazing_type
solar_factor
u_value
shading
external_masks
```

Exemple :

```text
Confiance globale : 84 %

Orientation : 100 %
Surfaces vitrées : 90 %
Type de vitrage : 95 %
Facteur solaire : 95 %
Protections : 70 %
Masques extérieurs : 45 %
```

---

## Sauvegarde

Créer :

```ts
useSaveCoolingOrientationSection()
```

Endpoint possible :

```text
PATCH /api/v1/greencube/cooling/studies/<id>
```

ou :

```text
PUT /api/v1/greencube/cooling/studies/<id>/orientation
```

Payload possible :

```json
{
  "orientation_deg": 225,
  "orientation_source": "user_confirmed",
  "facades": [
    {
      "facade_code": "front",
      "azimuth_deg": 225,
      "gross_area_m2": 16.2,
      "opaque_door_area_m2": 2.1,
      "apertures": [
        {
          "name": "Baie principale",
          "type": "fixed_glazing",
          "width_m": 3.0,
          "height_m": 2.1,
          "area_m2": 6.3,
          "glazing_product_id": 17,
          "u_value_w_m2k": 1.1,
          "solar_factor": 0.42,
          "shading": {
            "type": "exterior_blind",
            "control_mode": "solar_threshold"
          }
        }
      ]
    }
  ],
  "version": "server-version"
}
```

Adapter au contrat réel.

---

## Invalidation

Une modification peut invalider :

- apports solaires ;
- calcul rapide ;
- simulation EnergyPlus ;
- capacité recommandée ;
- rapport PDF.

Afficher :

```text
La modification de l’orientation, des vitrages ou des protections rendra le résultat de refroidissement actuel obsolète.
```

---

## Formulaire React Hook Form

Créer :

```tsx
<OrientationGlazingForm />
```

Organisation :

```text
orientation
facades
apertureInputMode
apertures
glazingProducts
shading
externalObstructions
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
const apertureSchema = z.object({
  id: z.number().int().positive().optional(),
  name: z.string().min(1).max(120),
  type: z.enum([
    "window",
    "glazed_door",
    "fixed_glazing",
    "rooflight",
    "other",
  ]),
  widthM: z.number().positive(),
  heightM: z.number().positive(),
  areaM2: z.number().positive(),
  glazingProductId: z.number().int().positive().nullable(),
  uValueWM2K: z.number().min(0.3).max(6),
  solarFactor: z.number().min(0).max(1),
});

const facadeSchema = z.object({
  facadeCode: z.string().min(1),
  azimuthDeg: z.number().min(0).lt(360),
  grossAreaM2: z.number().positive(),
  opaqueDoorAreaM2: z.number().min(0),
  apertures: z.array(apertureSchema),
});

const orientationSchema = z.object({
  orientationDeg: z.number().min(0).lt(360),
  orientationSource: z.enum([
    "catalog",
    "plan",
    "map",
    "user_confirmed",
    "estimated",
  ]),
  facades: z.array(facadeSchema).min(1),
});
```

Compléter avec les protections et masques.

---

## Validations croisées

Utiliser `superRefine` pour vérifier :

- somme des ouvertures inférieure ou égale à la façade ;
- surface opaque nette positive ;
- cohérence largeur × hauteur ;
- vitrage requis ;
- facteur solaire requis ;
- protection compatible ;
- masque valide ;
- orientation confirmée ;
- façade unique ;
- azimut cohérent.

---

## Store temporaire

Ajouter uniquement :

```ts
interface CoolingOrientationDraft {
  orientationDeg?: number;
  orientationSource?: string;
  activeFacadeCode?: string;
  apertureInputMode: "aggregated" | "detailed";
  hasUnconfirmedChanges: boolean;
}
```

Les données complètes doivent rester dans React Hook Form et Odoo.

---

## Autosave

Autosave possible si :

- orientation valide ;
- surfaces cohérentes ;
- ouvertures complètes ;
- aucun changement de mode en attente ;
- aucune invalidation non confirmée.

Ne pas autosauvegarder :

- ouverture partielle ;
- façade incohérente ;
- conversion de mode non confirmée ;
- changement invalidant non confirmé.

---

## Comparaison avant/après protection

Créer éventuellement :

```tsx
<ShadingImpactComparison />
```

Afficher :

- apport sans protection ;
- apport avec protection ;
- réduction en W ;
- réduction en %.

Cette comparaison reste indicative.

---

## Accessibilité

Respecter :

- orientation utilisable au clavier ;
- tabs accessibles ;
- formulaires structurés ;
- tableaux lisibles ;
- légendes ;
- erreurs associées ;
- focus lors de l’ajout ;
- annonces de recalcul ;
- alternative textuelle à la visualisation ;
- couleurs non utilisées seules.

---

## Responsive

### Desktop

```text
Colonne gauche : orientation et façades
Colonne droite : résumé et prévisualisation solaire
```

### Tablette

- façades en onglets ;
- résumé sous le formulaire.

### Mobile

- orientation compacte ;
- façades en accordéons ;
- ouvertures en cartes ;
- tableaux simplifiés ;
- prévisualisation sous le formulaire ;
- footer sticky.

---

## États de chargement

Prévoir :

- skeleton façades ;
- skeleton catalogue vitrage ;
- chargement de variante ;
- prévisualisation ;
- aperçu indisponible ;
- données partielles.

---

## Gestion des erreurs

Codes possibles :

```text
ORIENTATION_REQUIRED
INVALID_ORIENTATION
FACADE_NOT_FOUND
INVALID_FACADE_AREA
APERTURE_OUT_OF_BOUNDS
APERTURE_OVERLAP
GLAZING_AREA_EXCEEDS_FACADE
GLAZING_PRODUCT_NOT_FOUND
INVALID_GLAZING_U_VALUE
INVALID_SOLAR_FACTOR
INVALID_SHADING_CONFIGURATION
INVALID_EXTERNAL_OBSTRUCTION
MISSING_GLAZING_DATA
CONFLICT
INVALID_STATE
ACCESS_DENIED
```

Pour chaque erreur :

- message clair ;
- façade ou ouverture concernée ;
- action ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires

Tester :

### Orientation

- degrés valides ;
- normalisation ;
- points cardinaux ;
- rotation ;
- source.

### Façades

- surface brute ;
- azimut ;
- surface opaque ;
- ratio vitré ;
- valeur négative.

### Ouvertures

- ajout ;
- suppression ;
- dimensions ;
- surface ;
- dépassement ;
- chevauchement si pris en charge.

### Vitrages

- sélection catalogue ;
- U ;
- facteur solaire ;
- valeur manquante ;
- vitrage archivé.

### Protections

- aucune ;
- intérieure ;
- extérieure ;
- fixe ;
- mobile ;
- calendrier.

### Masques

- bâtiment ;
- arbre ;
- relief ;
- données incomplètes.

### Sauvegarde

- succès ;
- conflit ;
- invalidation ;
- lecture seule.

---

## Tests d’intégration

Tester :

1. chargement des façades ;
2. saisie orientation ;
3. sélection de façade ;
4. ajout d’une baie ;
5. sélection d’un vitrage ;
6. ajout d’une protection ;
7. calcul de surface opaque ;
8. prévisualisation solaire ;
9. sauvegarde ;
10. réouverture ;
11. passage agrégé vers détaillé ;
12. dépassement de façade ;
13. données manquantes ;
14. changement d’orientation ;
15. invalidation ;
16. étude validée ;
17. création d’une révision.

---

## Tests Playwright

Créer au minimum :

1. orientation sud-ouest avec vitrages catalogue ;
2. baie ouest importante sans protection ;
3. ajout d’un store extérieur ;
4. ajout d’une casquette fixe ;
5. configuration agrégée ;
6. configuration détaillée ;
7. surface vitrée supérieure à la façade ;
8. facteur solaire manquant ;
9. changement d’orientation avec invalidation ;
10. étude validée en lecture seule.

---

## Mock API

Créer des mocks pour :

- GreenCube standard ;
- façade ouest très vitrée ;
- double vitrage standard ;
- vitrage contrôle solaire ;
- triple vitrage ;
- store intérieur ;
- store extérieur ;
- casquette ;
- arbre caduc ;
- bâtiment voisin ;
- facteur solaire absent ;
- vitrage archivé ;
- données partielles.

Les mocks doivent respecter l’OpenAPI réel.

---

## Composants à créer ou compléter

```text
CoolingOrientationPage
BuildingOrientationCard
OrientationCompass
OrientationSelector
OrientationMapAssist
FacadeTabs
FacadePanel
FacadeSummary
ApertureInputModeSelector
ApertureEditor
ApertureList
ApertureCard
GlazingTypeSelector
GlazingUValueField
SolarFactorField
ShadingProtectionCard
ShadingTypeSelector
FixedShadingGeometryForm
DynamicShadingControlForm
ExternalObstructionCard
ExternalObstructionEditor
RoofApertureSection
FacadeGlazingPreview
SolarGainPreviewCard
CriticalFacadeAlert
MissingGlazingDataAlert
OrientationGlazingConfidencePanel
ShadingImpactComparison
OrientationGlazingForm
```

---

## Documentation

Créer :

```text
docs/cooling_orientation_glazing_screen.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

Mapping attendu :

```text
Façades
→ endpoint réel de lecture étude/modèle

Catalogue vitrages
→ GET /cooling/glazing-products

Sauvegarde orientation
→ PATCH /studies/<id>
ou endpoint dédié

Révision
→ POST /studies/<id>/revisions
```

---

## Critères d’acceptation

Le lot est accepté si :

- la route fonctionne ;
- les prérequis sont contrôlés ;
- l’orientation peut être saisie ;
- la convention est centralisée ;
- les façades sont affichées ;
- les azimuts sont calculés ;
- les surfaces brutes sont disponibles ;
- les ouvertures peuvent être saisies ;
- les modes agrégé et détaillé fonctionnent ;
- le catalogue de vitrages vient d’Odoo ;
- aucun vitrage n’est codé en dur ;
- les coefficients U sont validés ;
- les facteurs solaires sont validés ;
- la distinction g-value/SHGC est tracée ;
- les protections intérieures et extérieures sont distinguées ;
- les protections fixes sont configurables ;
- les protections mobiles sont configurables ;
- les masques extérieurs sont configurables ;
- la surface vitrée ne dépasse pas la façade ;
- la surface opaque nette est calculée ;
- le ratio vitré est calculé ;
- la prévisualisation solaire fonctionne ;
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
- prévisualisation.

### Orientation

- convention ;
- calculs ;
- sources ;
- validations.

### Façades et ouvertures

- structure ;
- surfaces ;
- ratios ;
- validations ;
- limites.

### Vitrages

- catalogue ;
- coefficient U ;
- facteur solaire ;
- versions ;
- provenance.

### Protections et masques

- types ;
- géométrie ;
- calendriers ;
- hypothèses.

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
- prévisualisation ;
- bundle ;
- re-renders ;
- limites.

### Sécurité

- permissions ;
- stockage ;
- secrets ;
- logs ;
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
7. vérifier l’orientation ;
8. vérifier les azimuts ;
9. vérifier les façades ;
10. vérifier les surfaces ;
11. vérifier les ouvertures ;
12. vérifier le mode agrégé ;
13. vérifier le mode détaillé ;
14. vérifier le catalogue de vitrages ;
15. vérifier les valeurs U ;
16. vérifier les facteurs solaires ;
17. vérifier les protections ;
18. vérifier les masques ;
19. vérifier la toiture vitrée ;
20. vérifier les ratios ;
21. vérifier la surface opaque ;
22. vérifier la prévisualisation ;
23. vérifier la provenance ;
24. vérifier la confiance ;
25. vérifier les données manquantes ;
26. vérifier la sauvegarde ;
27. vérifier l’invalidation ;
28. vérifier les conflits ;
29. vérifier la lecture seule ;
30. vérifier la révision ;
31. vérifier l’accessibilité ;
32. vérifier le responsive ;
33. vérifier l’absence de secrets ;
34. vérifier qu’aucun fichier n’a été supprimé ;
35. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente uniquement l’écran Orientation, vitrages et protections solaires.

Il ne finalise pas encore :

- les profils d’occupation ;
- les apports humains ;
- les équipements ;
- la ventilation ;
- l’infiltration détaillée ;
- le solver ;
- le résultat final.

Il doit fournir une description suffisamment fiable des orientations, vitrages et protections pour permettre le calcul des apports solaires dans les étapes suivantes.
