# GC-COOLING-06 — Socle frontend React du configurateur GreenCube Cooling

## 1. Objet

Ce document définit l’implémentation du socle frontend du configurateur GreenCube Cooling.

Le frontend doit permettre de :

- créer une étude ;
- saisir progressivement les données nécessaires ;
- naviguer entre les étapes ;
- sauvegarder les réponses dans Odoo ;
- restaurer une étude existante ;
- gérer les droits et statuts ;
- déclencher les services climatiques et le calcul ;
- afficher les résultats.

Odoo Community 18 reste la source de vérité métier.

Le frontend ne doit pas devenir une seconde base permanente pour :

- les modèles GreenCube ;
- les propriétés thermiques ;
- les études ;
- les données climatiques ;
- les résultats ;
- les permissions ;
- les versions du solver.

---

## 2. Stack technique

Utiliser ou conserver :

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

Ne pas remplacer une bibliothèque existante sans justification.

---

## 3. Vérifications préalables

Avant toute modification :

1. inspecter l’arborescence frontend ;
2. identifier les versions installées ;
3. identifier le routeur ;
4. identifier le state management ;
5. identifier le client API ;
6. identifier les composants UI réutilisables ;
7. identifier le système d’authentification ;
8. identifier la persistance locale ;
9. identifier les tests existants ;
10. exécuter :
   - installation des dépendances ;
   - lint ;
   - TypeScript ;
   - tests ;
   - build ;
11. noter les erreurs existantes ;
12. ne supprimer aucun fichier ;
13. ne modifier aucune route publique sans analyser ses consommateurs.

Le rapport préalable doit contenir :

- architecture actuelle ;
- architecture cible ;
- composants réutilisables ;
- hooks existants ;
- routes existantes ;
- client API existant ;
- fichiers à créer ;
- fichiers à modifier ;
- risques de régression ;
- stratégie de migration.

---

## 4. Parcours fonctionnel

Le socle doit supporter les écrans suivants :

```text
1. Localisation et contexte climatique
2. Modèle GreenCube
3. Orientation et vitrages
4. Usage et occupation
5. Équipements et apports internes
6. Ventilation et confort
7. Vérification avant calcul
8. Résultat
```

Fonctions transverses :

- navigation par étapes ;
- validation ;
- sauvegarde progressive ;
- autosave ;
- restauration ;
- gestion des erreurs ;
- gestion des conflits ;
- permissions ;
- révisions ;
- verrouillage des études ;
- gestion des chargements ;
- responsive ;
- accessibilité.

---

## 5. Architecture frontend

Séparer clairement :

```text
Interface utilisateur
→ formulaires
→ hooks métier
→ store temporaire
→ client API
→ Odoo
```

Éviter :

- appels API directs dans les composants ;
- logique métier complexe dans les pages ;
- calcul thermique dans le navigateur ;
- store utilisé comme base permanente ;
- schémas dupliqués.

---

## 6. Structure recommandée

```text
src/
├── app/
│   ├── router.tsx
│   ├── providers.tsx
│   ├── query-client.ts
│   └── app-shell.tsx
├── features/
│   └── cooling/
│       ├── api/
│       │   ├── cooling-api.ts
│       │   ├── cooling-query-keys.ts
│       │   └── cooling-api.types.ts
│       ├── components/
│       │   ├── CoolingLayout.tsx
│       │   ├── CoolingStepper.tsx
│       │   ├── CoolingFooter.tsx
│       │   ├── SaveStatus.tsx
│       │   ├── DataSourceBadge.tsx
│       │   ├── ConfidenceBadge.tsx
│       │   ├── PermissionGuard.tsx
│       │   ├── SectionCard.tsx
│       │   └── ErrorSummary.tsx
│       ├── hooks/
│       │   ├── useCoolingStudy.ts
│       │   ├── useCoolingNavigation.ts
│       │   ├── useAutosave.ts
│       │   ├── useStudyPermissions.ts
│       │   ├── useOptimisticVersion.ts
│       │   └── useUnsavedChanges.ts
│       ├── schemas/
│       │   ├── location.schema.ts
│       │   ├── model.schema.ts
│       │   ├── orientation.schema.ts
│       │   ├── usage.schema.ts
│       │   ├── equipment.schema.ts
│       │   ├── comfort.schema.ts
│       │   └── review.schema.ts
│       ├── store/
│       │   ├── cooling-store.ts
│       │   ├── cooling-store.types.ts
│       │   └── cooling-store.migrations.ts
│       ├── pages/
│       │   ├── CoolingLocationPage.tsx
│       │   ├── CoolingModelPage.tsx
│       │   ├── CoolingOrientationPage.tsx
│       │   ├── CoolingUsagePage.tsx
│       │   ├── CoolingEquipmentPage.tsx
│       │   ├── CoolingComfortPage.tsx
│       │   ├── CoolingReviewPage.tsx
│       │   └── CoolingResultPage.tsx
│       ├── utils/
│       │   ├── units.ts
│       │   ├── provenance.ts
│       │   ├── study-status.ts
│       │   └── route-guards.ts
│       └── index.ts
├── shared/
└── tests/
```

Adapter cette structure à l’existant.

---

## 7. Charte graphique

Respecter :

- fond blanc ;
- typographie noire ;
- accent vert GreenCube ;
- liserés verts fins ;
- cartes blanches ;
- bordures gris clair ;
- ombres discrètes ;
- interface lean ;
- espaces généreux ;
- desktop prioritaire ;
- responsive ensuite.

Centraliser les tokens :

```text
background
surface
text-primary
text-secondary
border
accent-green
accent-green-soft
error
warning
success
focus
```

Prévoir les états :

- normal ;
- hover ;
- focus ;
- actif ;
- sélectionné ;
- désactivé ;
- erreur ;
- avertissement ;
- succès ;
- chargement.

---

## 8. Routes

Convention recommandée :

```text
/cooling/studies/:studyId/location
/cooling/studies/:studyId/model
/cooling/studies/:studyId/orientation
/cooling/studies/:studyId/usage
/cooling/studies/:studyId/equipment
/cooling/studies/:studyId/comfort
/cooling/studies/:studyId/review
/cooling/studies/:studyId/result
```

Prévoir éventuellement :

```text
/cooling/start
```

Inclure l’identifiant d’étude dans l’URL facilite :

- la reprise ;
- la navigation directe ;
- le partage interne ;
- la gestion des révisions ;
- la restauration.

---

## 9. Guards de routes

Créer des guards pour :

- étude absente ;
- étude inaccessible ;
- étape non autorisée ;
- étude validée ;
- étude archivée ;
- résultat absent ;
- permissions insuffisantes ;
- session expirée.

Exemples :

```text
StudyRequiredGuard
StudyEditableGuard
StudyCalculatedGuard
StudyPermissionGuard
```

Une étude validée doit être en lecture seule.

---

## 10. Layout partagé

Créer :

```tsx
<CoolingLayout />
```

Le layout contient :

- logo GreenCube ;
- titre ;
- référence de l’étude ;
- révision ;
- statut ;
- indicateur de sauvegarde ;
- bouton Aide ;
- langue ;
- stepper ;
- contenu ;
- navigation inférieure.

Header recommandé :

```text
GreenCube
Configurateur de besoin de refroidissement
Étude GCC/2026/00042 — Révision 1
```

Footer :

- Retour ;
- Enregistrer ;
- Continuer ;
- Calculer sur l’étape finale ;
- état des modifications.

Le bouton Continuer doit :

1. valider ;
2. sauvegarder ;
3. attendre le succès ;
4. naviguer.

---

## 11. Stepper

Créer :

```tsx
<CoolingStepper />
```

Étapes :

```text
1 Localisation
2 GreenCube
3 Orientation
4 Usage
5 Équipements
6 Confort
7 Vérification
```

États possibles :

- future ;
- active ;
- visitée ;
- complète ;
- incomplète ;
- erreur ;
- verrouillée.

Autoriser :

- retour vers une étape précédente ;
- accès à une étape déjà visitée ;
- blocage d’une étape si un prérequis manque.

---

## 12. Store Zustand

Le store sert uniquement aux données temporaires.

Contenu autorisé :

- étude courante ;
- référence ;
- révision ;
- statut ;
- étape courante ;
- version serveur ;
- modifications non sauvegardées ;
- statut de sauvegarde ;
- erreurs locales ;
- permissions ;
- dernière synchronisation ;
- moteur sélectionné.

Exemple :

```ts
type SaveStatus =
  | "idle"
  | "dirty"
  | "saving"
  | "saved"
  | "error"
  | "conflict";

interface CoolingStoreState {
  studyId: number | null;
  reference: string | null;
  revision: number | null;
  status: string | null;
  currentStep: CoolingStep;
  serverVersion: string | null;
  saveStatus: SaveStatus;
  lastSavedAt: string | null;
  pendingSections: Partial<CoolingStudySections>;
  permissions: CoolingPermissions | null;
  errors: Record<string, string[]>;
}
```

Le store ne doit pas être la source permanente des données métier.

---

## 13. Persistance locale

Utiliser la persistance locale uniquement pour récupérer une saisie non sauvegardée.

Exigences :

- schéma versionné ;
- expiration ;
- aucun token sensible ;
- données personnelles limitées ;
- migration du store ;
- nettoyage après sauvegarde ou changement d’utilisateur.

Créer :

```text
cooling-store-schema-version
```

Supprimer les données locales :

- après sauvegarde complète ;
- après validation ;
- après archivage ;
- après expiration ;
- après déconnexion ;
- en cas de schéma incompatible.

---

## 14. TanStack Query

Utiliser TanStack Query pour les données serveur.

Query keys :

```ts
export const coolingQueryKeys = {
  all: ["cooling"] as const,
  models: () => [...coolingQueryKeys.all, "models"] as const,
  model: (id: number) => [...coolingQueryKeys.models(), id] as const,
  study: (id: number) => [...coolingQueryKeys.all, "study", id] as const,
  climate: (id: number) => [...coolingQueryKeys.study(id), "climate"] as const,
  result: (id: number) => [...coolingQueryKeys.study(id), "result"] as const,
};
```

Hooks de lecture :

- `useCoolingModels`
- `useCoolingModel`
- `useCoolingStudy`
- `useCoolingReferenceData`
- `useCoolingClimate`
- `useCoolingResult`

Mutations :

- `useCreateCoolingStudy`
- `useUpdateCoolingStudy`
- `useValidateCoolingInputs`
- `useCreateCoolingRevision`
- `useRequestClimateContext`
- `useCalculateCoolingStudy`
- `useValidateCoolingResult`
- `useDuplicateCoolingStudy`

---

## 15. Client API

Créer un client typé unique.

Fonctions minimales :

```text
getCoolingModels
getCoolingModel
getCoolingReferenceData
createCoolingStudy
getCoolingStudy
updateCoolingStudy
validateCoolingInputs
createCoolingRevision
requestClimateContext
calculateCoolingStudy
getCoolingResult
validateCoolingResult
duplicateCoolingStudy
getCoolingReport
```

Headers :

```text
Content-Type
Accept
X-Request-ID
Idempotency-Key
If-Match
CSRF token
Authorization
```

Prévoir :

- timeout ;
- annulation ;
- erreurs normalisées ;
- session expirée ;
- requêtes obsolètes annulées.

---

## 16. Gestion des erreurs

Créer :

```ts
interface ApiError {
  code: string;
  message: string;
  fields?: Record<string, string[]>;
  requestId?: string;
  status?: number;
}
```

Codes à gérer :

```text
AUTHENTICATION_REQUIRED
ACCESS_DENIED
RESOURCE_NOT_FOUND
VALIDATION_ERROR
CONFLICT
INVALID_STATE
IDEMPOTENCY_CONFLICT
RATE_LIMIT_EXCEEDED
CLIMATE_PROVIDER_UNAVAILABLE
CALCULATION_FAILED
INTERNAL_ERROR
```

Afficher :

- message global ;
- erreurs de champs ;
- request ID ;
- bouton Réessayer ;
- bouton Recharger ;
- bouton Créer une révision si nécessaire.

Ne jamais afficher une trace brute.

---

## 17. Verrouillage optimiste

Le frontend doit transmettre :

- `write_date` ;
- `version` ;
- ou `If-Match`.

En cas de conflit `409` :

1. ne pas écraser ;
2. afficher un dialogue ;
3. proposer de recharger ;
4. permettre de comparer ;
5. abandonner ou reprendre explicitement.

État store :

```text
saveStatus = conflict
```

---

## 18. Formulaires

Chaque écran utilise :

- React Hook Form ;
- Zod ;
- validation au blur ;
- validation à la soumission ;
- dirty tracking ;
- reset contrôlé ;
- erreurs accessibles.

Ne pas appeler `reset()` à chaque rendu.

Dériver les types depuis Zod :

```ts
type LocationFormValues = z.infer<typeof locationSchema>;
```

---

## 19. Schémas Zod

### Localisation

- adresse ;
- ville ;
- pays ;
- latitude ;
- longitude ;
- altitude ;
- environnement ;
- confirmation.

### Modèle

- modèle catalogue ;
- mode personnalisé ;
- dimensions ;
- surface ;
- volume ;
- valeurs U ;
- vitrage.

### Orientation

- orientation ;
- surfaces vitrées ;
- facteurs solaires ;
- ombrage ;
- façades.

### Usage

- type d’usage ;
- occupants ;
- horaires ;
- activité ;
- occupation nocturne.

### Équipements

- quantité ;
- puissance ;
- simultanéité ;
- durée ;
- dissipation.

### Confort

- ventilation ;
- débit ;
- infiltration ;
- température cible ;
- humidité ;
- niveau de service.

### Vérification

- sections complètes ;
- hypothèses acceptées ;
- données manquantes ;
- erreurs bloquantes.

---

## 20. Provenance des données

Créer :

```tsx
<DataSourceBadge source="catalog" />
```

Sources :

```text
catalog
api
user_confirmed
estimated_reference
estimated_manual
missing_fallback
```

Afficher la provenance pour :

- valeurs U ;
- altitude ;
- facteur solaire ;
- débit d’air ;
- occupation ;
- équipements ;
- climat.

---

## 21. Score de confiance

Créer :

```tsx
<ConfidenceBadge value={86} />
```

Afficher :

- score ;
- libellé ;
- explication ;
- catégories faibles ;
- actions d’amélioration.

Ce score mesure la qualité des entrées et non une précision scientifique garantie.

---

## 22. Autosave

Créer :

```ts
useAutosave()
```

Comportement :

- détecter les changements ;
- attendre un debounce ;
- sauvegarder la section courante ;
- ne pas sauvegarder si invalide ;
- gérer l’annulation ;
- gérer les conflits ;
- éviter les doublons.

Valeur recommandée :

```text
800 à 1500 ms
```

États :

```text
Modifications non enregistrées
Enregistrement…
Enregistré
Échec de l’enregistrement
Conflit de version
Hors connexion
```

Ne pas perdre les données lors d’un changement de page.

---

## 23. Réseau instable

Le MVP doit :

- détecter l’absence de réseau ;
- conserver temporairement les modifications ;
- ne pas afficher un faux statut enregistré ;
- retenter après reconnexion ;
- informer l’utilisateur.

Ne pas lancer automatiquement un calcul après une reconnexion prolongée.

---

## 24. Permissions

Respecter les permissions API :

```json
{
  "can_edit": true,
  "can_calculate": false,
  "can_validate": false,
  "can_create_revision": false
}
```

Créer :

```tsx
<PermissionGuard permission="can_validate">
  ...
</PermissionGuard>
```

Le backend reste l’autorité finale.

---

## 25. Statuts d’étude

### `draft`

- modifiable ;
- sauvegardable.

### `incomplete`

- modifiable ;
- données manquantes visibles.

### `ready`

- modifiable ;
- calculable.

### `calculating`

- modifications verrouillées ;
- progression affichée.

### `calculated`

- résultat disponible ;
- modification via révision.

### `validated`

- lecture seule ;
- révision possible.

### `archived`

- lecture seule.

### `failed`

- erreur visible ;
- relance contrôlée.

Créer une fonction centralisée :

```ts
getStudyCapabilities(status, permissions)
```

---

## 26. Création d’étude

Flux :

1. charger les référentiels ;
2. créer l’étude dans Odoo ;
3. récupérer l’identifiant ;
4. initialiser le store ;
5. naviguer vers la localisation.

Ne pas maintenir une étude complète uniquement côté navigateur.

---

## 27. Restauration d’étude

À l’ouverture :

```text
/cooling/studies/:studyId/*
```

Le frontend doit :

1. charger l’étude ;
2. charger les permissions ;
3. charger les référentiels ;
4. mettre à jour le store ;
5. restaurer les données locales compatibles ;
6. comparer la version locale et serveur ;
7. signaler les conflits.

---

## 28. Navigation

Créer :

```ts
useCoolingNavigation()
```

Fonctions :

```text
goToNextStep
goToPreviousStep
goToStep
canAccessStep
getNextStep
getPreviousStep
```

Avant de continuer :

1. valider ;
2. sauvegarder ;
3. attendre la réponse ;
4. naviguer.

---

## 29. Internationalisation

Réutiliser l’infrastructure i18n existante.

Prévoir :

- français ;
- compatibilité future avec l’anglais.

Les codes API ne doivent jamais être traduits.

---

## 30. Accessibilité

Respecter :

- labels ;
- associations `for/id` ;
- focus visible ;
- navigation clavier ;
- aria ;
- contraste ;
- erreurs associées ;
- live regions ;
- tableaux accessibles ;
- boutons explicites.

Le parcours doit fonctionner sans souris.

---

## 31. Responsive

Ordre de priorité :

```text
desktop
→ tablette
→ mobile
```

Sur mobile :

- stepper compact ;
- colonnes empilées ;
- footer accessible ;
- cartes adaptatives ;
- tableaux réorganisés ;
- actions visibles.

---

## 32. Performance

Appliquer :

- lazy loading ;
- code splitting ;
- cache Query ;
- déduplication ;
- chargement différé ;
- images optimisées ;
- sélecteurs Zustand ciblés ;
- limitation des re-renders.

Mesurer :

- bundle ;
- temps de chargement ;
- nombre de requêtes ;
- fréquence autosave ;
- temps de rendu.

---

## 33. Sécurité frontend

Interdictions :

- aucune clé météo ;
- aucun token serveur ;
- aucun secret Odoo ;
- aucune URL interne sensible ;
- aucune permission uniquement côté client ;
- aucune donnée sensible dans les logs ;
- aucun HTML non nettoyé.

Appliquer :

- échappement React ;
- validation Zod ;
- nettoyage au logout ;
- stockage sécurisé des tokens ;
- CSP si disponible.

---

## 34. Composants partagés

Créer ou réutiliser :

```text
CoolingLayout
CoolingStepper
CoolingFooter
SaveStatus
DataSourceBadge
ConfidenceBadge
SectionCard
ErrorSummary
LoadingState
EmptyState
PermissionGuard
StudyStatusBadge
FormField
NumberField
UnitField
```

Ils doivent être :

- typés ;
- testés ;
- accessibles ;
- réutilisables.

---

## 35. Gestion des unités

Créer :

```text
units.ts
```

Unités :

- m ;
- m² ;
- m³ ;
- °C ;
- % ;
- W ;
- kW ;
- BTU/h ;
- m³/h ;
- ACH ;
- W/m².K ;
- W/m².

Les conversions doivent être centralisées.

---

## 36. Feature flags

Prévoir :

```text
enable_energyplus
enable_annual_simulation
enable_anonymous_study
enable_pdf_export
enable_crm_link
enable_product_selection
```

Les fonctions non prêtes doivent rester masquées.

---

## 37. Tests unitaires

Tester :

### Layout

- header ;
- statut ;
- stepper ;
- footer.

### Store

- initialisation ;
- dirty ;
- sauvegarde ;
- conflit ;
- restauration ;
- migration.

### API

- succès ;
- erreur ;
- timeout ;
- annulation ;
- session expirée.

### Formulaires

- valeurs ;
- validation ;
- reset ;
- dirty tracking.

### Navigation

- suite ;
- retour ;
- blocage ;
- route directe.

### Permissions

- lecture seule ;
- validation ;
- révision ;
- action interdite.

---

## 38. Tests d’intégration

Tester :

1. création ;
2. chargement ;
3. sauvegarde localisation ;
4. navigation ;
5. sauvegarde partielle ;
6. erreur API ;
7. conflit ;
8. restauration ;
9. étude validée ;
10. révision ;
11. session expirée ;
12. hors connexion ;
13. reconnexion ;
14. calcul en cours ;
15. résultat disponible.

---

## 39. Tests Playwright

Créer au minimum :

1. Studio complet ;
2. étude partielle ;
3. retour vers une étape ;
4. autosave ;
5. conflit de version ;
6. étude validée ;
7. création d’une révision ;
8. erreur climatique ;
9. calcul en cours ;
10. résultat.

---

## 40. Mock API

Le mock doit refléter le contrat réel :

- catalogue ;
- étude ;
- permissions ;
- climat ;
- validation ;
- calcul ;
- résultat ;
- erreurs.

Éviter tout contrat mock divergent de l’OpenAPI.

---

## 41. TypeScript strict

Activer ou conserver :

```json
{
  "strict": true,
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true
}
```

Éviter :

- `any` ;
- assertions non justifiées ;
- types dupliqués ;
- réponses API non validées.

---

## 42. Documentation

Créer :

```text
docs/cooling_frontend.md
docs/cooling_frontend_api_mapping.md
```

Documenter :

- architecture ;
- routes ;
- store ;
- queries ;
- API ;
- formulaires ;
- autosave ;
- permissions ;
- statuts ;
- provenance ;
- confiance ;
- erreurs ;
- tests ;
- feature flags ;
- limites.

Mapper :

```text
écran
→ formulaire
→ endpoint
→ modèle Odoo
→ statut
```

---

## 43. Critères d’acceptation

Le lot est accepté si :

1. les routes existent ;
2. le layout fonctionne ;
3. le stepper fonctionne ;
4. le store est typé ;
5. le store n’est pas la source permanente ;
6. Query gère les données serveur ;
7. le client API est centralisé ;
8. les erreurs sont normalisées ;
9. les conflits sont gérés ;
10. l’autosave fonctionne ;
11. les formulaires utilisent RHF ;
12. les formulaires utilisent Zod ;
13. les permissions sont respectées ;
14. les statuts sont gérés ;
15. une étude peut être créée ;
16. une étude peut être restaurée ;
17. les modifications locales sont protégées ;
18. l’accessibilité est assurée ;
19. le desktop est cohérent ;
20. le responsive fonctionne ;
21. les tests passent ;
22. le build passe ;
23. TypeScript strict passe ;
24. le lint passe ;
25. aucun secret n’est exposé ;
26. aucun fichier n’est supprimé ;
27. la documentation est fournie ;
28. les fonctions non prêtes sont masquées.

---

## 44. Rapport final attendu

### Architecture

- structure ;
- composants ;
- hooks ;
- store ;
- API ;
- routes.

### Fichiers

- créés ;
- modifiés ;
- non modifiés ;
- supprimés, normalement aucun.

### API

- hook ;
- endpoint ;
- payload ;
- réponse ;
- erreurs.

### Store

- état ;
- persistance ;
- migration ;
- nettoyage.

### Tests

- commandes ;
- résultats ;
- couverture ;
- tests non exécutés ;
- raisons.

### Performance

- bundle ;
- chargement ;
- requêtes ;
- autosave ;
- limites.

### Sécurité

- secrets ;
- tokens ;
- stockage local ;
- logs ;
- permissions.

### Patch

- diff ;
- patch réintégrable ;
- application ;
- rollback.

---

## 45. Contrôle final

Avant conclusion :

1. installer les dépendances ;
2. lancer le lint ;
3. lancer TypeScript strict ;
4. lancer les tests unitaires ;
5. lancer les tests d’intégration ;
6. lancer Playwright ;
7. construire le frontend ;
8. vérifier les routes ;
9. vérifier le store ;
10. vérifier l’autosave ;
11. vérifier les conflits ;
12. vérifier les permissions ;
13. vérifier les statuts ;
14. vérifier l’accessibilité ;
15. vérifier le responsive ;
16. vérifier l’absence de secrets ;
17. vérifier l’absence de `any` injustifié ;
18. vérifier l’absence de calcul thermique dans le navigateur ;
19. vérifier qu’aucun fichier n’a été supprimé ;
20. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## 46. Limites du lot

Ce lot implémente le socle frontend.

Il ne finalise pas nécessairement :

- chaque écran métier ;
- la carte interactive ;
- les graphiques de résultats ;
- la simulation EnergyPlus ;
- le PDF ;
- le CRM ;
- la sélection produit.

Il doit fournir une architecture stable permettant d’implémenter les écrans suivants sans réécriture du socle.
