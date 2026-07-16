# GC-COOLING-08 — Modèle GreenCube et caractéristiques thermiques

## Objectif

Implémenter l’écran :

```text
2 — Modèle GreenCube et caractéristiques thermiques
```

L’écran doit permettre de :

- sélectionner un modèle GreenCube depuis Odoo ;
- sélectionner une variante ;
- afficher les dimensions ;
- afficher la surface et le volume ;
- consulter les caractéristiques thermiques ;
- choisir entre un modèle catalogue et une configuration personnalisée ;
- saisir des dimensions personnalisées ;
- renseigner des valeurs U ;
- renseigner des couches de matériaux ;
- afficher les surfaces calculées ;
- identifier les données manquantes ou estimées ;
- afficher la provenance et le score de confiance ;
- enregistrer la section dans Odoo ;
- passer à l’étape Orientation et vitrages.

Odoo Community 18 reste la source de vérité.

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

## Vérifications préalables

Avant toute modification :

- inspecter le socle frontend ;
- inspecter l’écran Localisation ;
- vérifier les routes ;
- vérifier le layout ;
- vérifier le stepper ;
- vérifier le store Zustand ;
- vérifier le client API ;
- vérifier les query keys ;
- vérifier les composants partagés ;
- inspecter les modèles Odoo réels ;
- vérifier les endpoints catalogue ;
- vérifier les endpoints de spécification thermique ;
- vérifier les unités ;
- vérifier les versions de spécification ;
- vérifier la provenance et la confiance ;
- exécuter le lint ;
- exécuter TypeScript ;
- exécuter les tests ;
- exécuter le build ;
- ne supprimer aucun fichier ;
- ne coder aucun modèle GreenCube en dur.

---

## Route

```text
/cooling/studies/:studyId/model
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
<CoolingModelPage />
```

Structure recommandée :

```text
CoolingLayout
├── Introduction
├── ModelSelectionMode
├── CatalogModelSelector
├── SelectedModelSummary
├── VariantSelector
├── GeometryCard
├── EnvelopePerformanceCard
├── MaterialLayersCard
├── SurfaceCalculationCard
├── ProvenanceAndConfidence
├── ValidationWarnings
└── CoolingFooter
```

---

## Modes de configuration

Prévoir deux modes :

```text
catalog
custom
```

Labels :

```text
Modèle GreenCube du catalogue
Configuration personnalisée
```

Créer :

```tsx
<ModelConfigurationModeSelector />
```

### Mode catalogue

- charger les modèles depuis Odoo ;
- afficher uniquement les modèles actifs ;
- permettre les filtres ;
- charger la variante ;
- charger la spécification thermique ;
- verrouiller les données catalogue ;
- conserver la version utilisée.

### Mode personnalisé

- saisir les dimensions ;
- saisir les valeurs U ou les couches ;
- calculer les surfaces ;
- afficher les hypothèses ;
- réduire la confiance si les données sont incomplètes.

### Changement de mode

- demander confirmation si des données existent ;
- expliquer les conséquences ;
- éviter toute perte silencieuse ;
- conserver un brouillon temporaire si utile ;
- invalider les données dépendantes si nécessaire.

---

## Chargement du catalogue

Créer :

```ts
useCoolingModels()
```

Endpoint attendu :

```text
GET /api/v1/greencube/cooling/models
```

La réponse doit idéalement contenir :

- identifiant ;
- nom ;
- code ;
- catégorie ;
- image ;
- dimensions ;
- surface ;
- volume ;
- statut ;
- variantes ;
- version thermique ;
- disponibilité.

Ne jamais coder en dur les modèles GreenCube.

---

## Sélecteur de modèle

Créer :

```tsx
<CatalogModelSelector />
<ModelCatalogFilters />
<ModelCard />
```

Fonctions :

- recherche ;
- filtre par catégorie ;
- filtre par surface ;
- filtre par usage ;
- filtre par disponibilité ;
- tri ;
- sélection.

Afficher :

- nom ;
- code ;
- surface ;
- dimensions ;
- image ;
- statut ;
- description ;
- disponibilité de la spécification thermique.

---

## Modèle sélectionné

Créer :

```tsx
<SelectedModelSummary />
```

Afficher :

- modèle ;
- code ;
- version ;
- variante ;
- dimensions intérieures ;
- dimensions extérieures si disponibles ;
- surface utile ;
- volume intérieur ;
- source ;
- date de mise à jour ;
- confiance ;
- statut de spécification.

---

## Variantes et versions

Créer :

```tsx
<ModelVariantSelector />
<ThermalSpecificationVersionNotice />
```

Conserver :

```text
model_id
variant_id
thermal_specification_id
thermal_specification_version
```

Règles :

- ne jamais fusionner deux variantes silencieusement ;
- conserver la version utilisée dans l’étude ;
- ne pas mettre à jour automatiquement une ancienne étude ;
- afficher si une version plus récente existe ;
- permettre une mise à jour explicite ;
- expliquer l’impact potentiel.

---

## Géométrie

Créer :

```tsx
<GeometryCard />
```

Champs :

- longueur intérieure ;
- largeur intérieure ;
- hauteur intérieure ;
- surface au sol ;
- volume intérieur ;
- périmètre ;
- surface de toiture ;
- surface de plancher ;
- surface brute des façades.

### Calculs de prévisualisation

```text
surface_sol = longueur × largeur
volume = longueur × largeur × hauteur
périmètre = 2 × (longueur + largeur)
surface_toiture = surface_sol
surface_facades_brutes = périmètre × hauteur
```

Le backend doit recalculer et valider.

### Validation indicative

```text
longueur : 1 à 50 m
largeur : 1 à 50 m
hauteur : 2 à 10 m
surface : 4 à 1 000 m²
volume : 8 à 10 000 m³
```

Vérifier :

- nombres finis ;
- valeurs positives ;
- cohérence surface et volume ;
- absence de dimensions nulles ;
- compatibilité avec le mode choisi.

Pour le MVP, privilégier une géométrie parallélépipédique.

Feature flag possible :

```text
enable_custom_complex_geometry
```

---

## Enveloppe thermique

Créer :

```tsx
<EnvelopePerformanceCard />
<UValueField />
```

Afficher ou saisir :

- valeur U des murs ;
- valeur U de la toiture ;
- valeur U du plancher ;
- valeur U des portes ;
- ponts thermiques ;
- niveau d’isolation ;
- provenance ;
- confiance.

Unité :

```text
W/m².K
```

Champs principaux :

```text
wall_u_value
roof_u_value
floor_u_value
door_u_value
```

Plage indicative :

```text
0,05 à 6,00 W/m².K
```

Toute valeur hors plage doit être refusée ou explicitement confirmée.

---

## Modes de définition de l’enveloppe

Prévoir :

```text
u_values
material_layers
```

### Mode valeurs U

- rapide ;
- simple ;
- adapté au pré-dimensionnement ;
- confiance inférieure pour l’inertie.

### Mode couches

- plus précis ;
- compatible avec EnergyPlus ;
- permet de représenter l’inertie ;
- demande davantage de données.

---

## Couches de matériaux

Créer :

```tsx
<MaterialLayersCard />
<MaterialLayerTable />
<CalculatedUValuePreview />
```

Pour chaque couche :

- ordre ;
- nom ;
- matériau ;
- épaisseur ;
- conductivité ;
- densité ;
- capacité thermique ;
- résistance thermique ;
- provenance.

Calcul de prévisualisation :

```text
R_couche = épaisseur / conductivité
R_total = somme des résistances
U_estimé = 1 / R_total
```

Le backend doit recalculer et gérer :

- résistances superficielles ;
- ponts thermiques ;
- cohérence des unités ;
- valeur finale retenue.

---

## Ponts thermiques

Créer :

```tsx
<ThermalBridgeAdjustment />
```

Modes possibles :

```text
none
percentage_adjustment
global_linear_value
backend_default
```

Pour le MVP :

```text
backend_default
percentage_adjustment
```

Afficher :

- correction ;
- provenance ;
- justification ;
- impact estimé.

---

## Surfaces et façades

Créer :

```tsx
<SurfaceCalculationCard />
<FacadeSummary />
```

Afficher :

- surface de plancher ;
- surface de toiture ;
- surface brute des façades ;
- surface de portes ;
- future surface vitrée ;
- surface opaque nette provisoire.

Pour une géométrie rectangulaire :

```text
nord/sud = longueur × hauteur
est/ouest = largeur × hauteur
```

Les vitrages détaillés seront saisis à l’étape suivante.

---

## Inertie et étanchéité

Créer :

```tsx
<AirtightnessSummary />
```

Afficher si disponible :

- niveau d’inertie ;
- `n50` ;
- ACH ;
- classe d’étanchéité ;
- débit de fuite.

Ne pas inventer une inertie si les couches sont absentes.

---

## Provenance et confiance

Utiliser :

```tsx
<DataSourceBadge />
<ModelConfidencePanel />
<MissingThermalDataAlert />
```

Provenances possibles :

```text
Catalogue Odoo
Modifié par l’utilisateur
Estimation référentielle
Valeur par défaut
Donnée manquante
```

Afficher la provenance pour :

- dimensions ;
- valeurs U ;
- matériaux ;
- ponts thermiques ;
- étanchéité.

Score de confiance possible :

```text
Modèle
Dimensions
Valeurs U
Couches de matériaux
Étanchéité
Ponts thermiques
```

---

## Données manquantes et valeurs de référence

Pour chaque donnée manquante :

- indiquer si elle est bloquante ;
- proposer une valeur de référence si autorisée ;
- demander confirmation ;
- conserver la provenance ;
- réduire la confiance.

Exemple :

```text
Valeur proposée : 0,22 W/m².K
Source : Référentiel GreenCube — Enveloppe standard v2
```

Ne jamais présenter une valeur référentielle comme une mesure réelle.

---

## Personnalisation d’un modèle catalogue

Le catalogue Odoo ne doit jamais être modifié depuis cet écran.

Si une personnalisation est autorisée :

- créer une copie liée à l’étude ;
- conserver les valeurs d’origine ;
- afficher « Modifié pour cette étude » ;
- enregistrer les écarts ;
- utiliser une provenance explicite.

---

## Sauvegarde

Créer :

```ts
useSaveCoolingModelSection()
```

Endpoint possible :

```text
PATCH /api/v1/greencube/cooling/studies/<id>
```

ou :

```text
PUT /api/v1/greencube/cooling/studies/<id>/model
```

Payload possible :

```json
{
  "configuration_mode": "catalog",
  "model_id": 12,
  "variant_id": 4,
  "thermal_specification_id": 31,
  "thermal_specification_version": "3.2",
  "geometry": {
    "length_m": 6.0,
    "width_m": 5.0,
    "height_m": 2.7
  },
  "envelope": {
    "wall_u_value": 0.18,
    "roof_u_value": 0.15,
    "floor_u_value": 0.20
  },
  "version": "server-version"
}
```

Le hook doit :

- valider ;
- transmettre la version ;
- gérer les conflits ;
- invalider la query étude ;
- mettre à jour le store ;
- conserver le request ID.

---

## Invalidation et révision

Une modification du modèle peut invalider :

- orientation et vitrages ;
- surfaces des façades ;
- ventilation ;
- résultat ;
- simulation EnergyPlus ;
- capacité recommandée.

Afficher :

```text
La modification du modèle ou de ses dimensions rendra certaines données des étapes suivantes obsolètes.
```

Pour une étude calculée ou validée :

- créer une nouvelle révision ;
- copier les données compatibles ;
- invalider les résultats ;
- revenir à l’étape Modèle.

Créer :

```tsx
<CreateRevisionDialog />
```

---

## Formulaire et validation

Créer :

```tsx
<ModelConfigurationForm />
```

Organisation :

```text
configurationMode
catalogSelection
variantSelection
geometry
envelope
materialLayers
thermalBridges
airtightness
```

Utiliser :

- React Hook Form ;
- Zod ;
- `FormProvider` si nécessaire ;
- `useFieldArray` pour les couches ;
- dirty tracking ;
- reset contrôlé.

Utiliser une union discriminée Zod entre :

```text
catalog
custom
```

Ajouter des validations croisées avec `superRefine`.

---

## Store temporaire et autosave

Draft autorisé :

```ts
interface CoolingModelDraft {
  configurationMode: "catalog" | "custom";
  selectedModelId?: number;
  selectedVariantId?: number | null;
  customGeometry?: {
    lengthM: number;
    widthM: number;
    heightM: number;
  };
  envelopeMode?: "u_values" | "material_layers";
  hasUnconfirmedChanges: boolean;
}
```

Autosave autorisé uniquement si :

- formulaire valide ;
- modèle sélectionné ;
- données obligatoires présentes ;
- aucun changement invalidant non confirmé.

---

## Comparaison et aperçu

Options recommandées :

```tsx
<ModelComparisonDrawer />
<GreenCubeGeometryPreview />
```

Feature flag :

```text
enable_model_comparison
```

Comparer :

- surface ;
- volume ;
- valeurs U ;
- inertie ;
- étanchéité ;
- confiance.

L’aperçu géométrique reste illustratif.

---

## Unités

Utiliser `units.ts` pour :

```text
m
m²
m³
W/m².K
mm
W/m.K
kg/m³
J/kg.K
```

---

## Accessibilité et responsive

Respecter :

- navigation clavier ;
- cartes sélectionnables ;
- labels ;
- groupes de champs ;
- tableaux accessibles ;
- focus ;
- erreurs associées ;
- textes alternatifs.

### Desktop

```text
Colonne gauche : sélection et configuration
Colonne droite : résumé technique et aperçu
```

### Mobile

- filtres repliables ;
- cartes empilées ;
- tableaux en accordéons ;
- footer sticky.

---

## Gestion des erreurs

Codes possibles :

```text
MODEL_NOT_FOUND
MODEL_ARCHIVED
VARIANT_NOT_FOUND
VARIANT_NOT_COMPATIBLE
THERMAL_SPECIFICATION_NOT_FOUND
THERMAL_SPECIFICATION_OUTDATED
INVALID_GEOMETRY
INVALID_U_VALUE
INVALID_MATERIAL_LAYER
MISSING_THERMAL_DATA
CONFLICT
INVALID_STATE
ACCESS_DENIED
```

Pour chaque erreur :

- message clair ;
- champ concerné ;
- action ;
- request ID ;
- aucune trace brute.

---

## Tests

### Tests unitaires

Tester :

- catalogue ;
- recherche ;
- filtres ;
- sélection ;
- variantes ;
- versions ;
- géométrie ;
- surfaces ;
- volume ;
- valeurs U ;
- couches ;
- calcul R/U ;
- provenance ;
- sauvegarde ;
- conflits ;
- lecture seule.

### Tests d’intégration

Tester :

1. chargement catalogue ;
2. sélection modèle ;
3. chargement spécification ;
4. sélection variante ;
5. sauvegarde ;
6. réouverture ;
7. mode personnalisé ;
8. calcul géométrique ;
9. valeurs U ;
10. couches ;
11. donnée manquante ;
12. valeur référentielle ;
13. changement de modèle ;
14. invalidation ;
15. conflit ;
16. étude validée ;
17. révision.

### Tests Playwright

Créer au minimum :

1. modèle catalogue standard ;
2. variante renforcée ;
3. comparaison de modèles ;
4. configuration personnalisée avec valeurs U ;
5. configuration personnalisée avec couches ;
6. erreur de dimension ;
7. valeur U manquante ;
8. changement avec invalidation ;
9. étude validée ;
10. création d’une révision.

---

## Composants à créer ou compléter

```text
CoolingModelPage
ModelConfigurationModeSelector
CatalogModelSelector
ModelCatalogFilters
ModelCard
SelectedModelSummary
ModelVariantSelector
ThermalSpecificationVersionNotice
GeometryCard
EnvelopePerformanceCard
UValueField
MaterialLayersCard
MaterialLayerTable
CalculatedUValuePreview
ThermalBridgeAdjustment
SurfaceCalculationCard
FacadeSummary
AirtightnessSummary
ModelConfidencePanel
MissingThermalDataAlert
ModelConfigurationForm
ModelComparisonDrawer
GreenCubeGeometryPreview
```

---

## Documentation

Créer :

```text
docs/cooling_model_screen.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

---

## Critères d’acceptation

Le lot est accepté si :

- la route fonctionne ;
- l’étude est chargée ;
- le catalogue provient d’Odoo ;
- aucun modèle n’est codé en dur ;
- la recherche et les filtres fonctionnent ;
- les modèles et variantes sont sélectionnables ;
- la version thermique est conservée ;
- les dimensions, surfaces et volumes sont calculés ;
- les valeurs U et couches sont gérées ;
- le mode personnalisé fonctionne ;
- les valeurs aberrantes sont rejetées ;
- les données manquantes sont identifiées ;
- les valeurs de référence sont tracées ;
- la provenance et la confiance sont visibles ;
- la sauvegarde met à jour Odoo ;
- le catalogue n’est jamais modifié ;
- les personnalisations restent liées à l’étude ;
- les conflits et invalidations sont gérés ;
- la révision fonctionne ;
- l’accessibilité et le responsive fonctionnent ;
- les tests passent ;
- TypeScript strict, le lint et le build passent ;
- aucun secret n’est exposé ;
- aucun fichier n’est supprimé.

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
8. vérifier les variantes et versions ;
9. vérifier la géométrie ;
10. vérifier les surfaces et volumes ;
11. vérifier les valeurs U et couches ;
12. vérifier les ponts thermiques ;
13. vérifier l’étanchéité ;
14. vérifier les valeurs de référence ;
15. vérifier la provenance et la confiance ;
16. vérifier la sauvegarde ;
17. vérifier l’invalidation et les conflits ;
18. vérifier la lecture seule et la révision ;
19. vérifier l’accessibilité et le responsive ;
20. vérifier que le catalogue n’a pas été modifié ;
21. vérifier qu’aucun fichier n’a été supprimé ;
22. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot ne finalise pas encore :

- l’orientation ;
- les vitrages détaillés ;
- les protections solaires ;
- l’occupation ;
- les équipements ;
- la ventilation ;
- le solver ;
- les résultats.

Il doit fournir une géométrie et une enveloppe suffisamment fiables pour permettre l’étape suivante.
