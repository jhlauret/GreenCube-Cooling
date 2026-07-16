# GC-COOLING-13 — Vérification et synthèse avant calcul

## Objectif

Implémenter l’écran :

```text
7 — Vérification et synthèse avant calcul
```

Cet écran constitue la barrière qualité avant le lancement du solver.

Il doit permettre de :

- visualiser la synthèse complète de l’étude ;
- vérifier la complétude de chaque section ;
- identifier les erreurs bloquantes ;
- identifier les avertissements ;
- consulter les hypothèses ;
- consulter les valeurs estimées et les valeurs par défaut ;
- consulter les provenances ;
- consulter les versions des référentiels ;
- afficher le score de confiance global ;
- afficher les scores de confiance par section ;
- afficher les trois scénarios climatiques ;
- identifier le scénario probablement dimensionnant ;
- revenir directement vers une section à corriger ;
- confirmer les hypothèses non mesurées ;
- accepter les valeurs de référence ;
- vérifier les données envoyées au solver ;
- créer un snapshot de calcul immuable ;
- faire passer l’étude au statut `ready` ;
- préparer le lancement du calcul rapide ou d’EnergyPlus.

Odoo Community 18 reste la source de vérité.

Le frontend ne doit jamais déclarer une étude prête uniquement à partir de validations locales. La validation définitive doit être réalisée côté backend.

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
- une géométrie ;
- une enveloppe thermique ;
- une orientation ;
- des vitrages et protections solaires ;
- un profil d’usage ;
- un profil d’occupation ;
- des équipements et charges internes ;
- une ventilation ;
- une infiltration ;
- des consignes de confort ;
- les permissions et statuts ;
- la provenance des données ;
- les scores de confiance ;
- le verrouillage optimiste ;
- la gestion des révisions ;
- les règles d’invalidation.

---

## Vérifications préalables

Avant toute modification :

- inspecter les écrans précédents ;
- vérifier la route et le stepper ;
- vérifier le store Zustand ;
- vérifier le client API ;
- vérifier les query keys ;
- vérifier les composants partagés ;
- inspecter les modèles Odoo de validation, hypothèses, scénarios, snapshots et résultats ;
- vérifier les statuts d’étude ;
- vérifier les transitions autorisées ;
- vérifier les endpoints de validation ;
- vérifier les endpoints de création de snapshot ;
- vérifier les codes d’erreur ;
- vérifier les règles de provenance ;
- vérifier les règles de score de confiance ;
- vérifier les règles d’invalidation ;
- vérifier le payload du solver ;
- vérifier le mapping Honeybee/EnergyPlus ;
- exécuter lint, TypeScript, tests et build ;
- ne supprimer aucun composant ;
- ne dupliquer aucune règle métier critique dans le frontend ;
- ne jamais passer une étude à `ready` sans confirmation serveur ;
- ne jamais lancer un calcul depuis un état incomplet.

---

## Route

```text
/cooling/studies/:studyId/review
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
StudyReviewGuard
```

Pour une étude calculée ou validée :

- afficher la synthèse en lecture seule ;
- afficher le snapshot utilisé ;
- permettre une révision si autorisée ;
- interdire la modification directe.

---

## Structure de la page

Créer :

```tsx
<CoolingReviewPage />
```

Structure recommandée :

```text
CoolingLayout
├── ReviewHeader
├── StudyReadinessBanner
├── SectionCompletionOverview
├── BlockingIssuesPanel
├── WarningIssuesPanel
├── AssumptionsPanel
├── DataProvenancePanel
├── ConfidenceOverview
├── ClimateScenarioSummary
├── CalculationInputSummary
├── SnapshotPreview
├── FinalConfirmationPanel
└── CoolingFooter
```

---

## Statuts de préparation

Prévoir un statut de préparation distinct du statut principal si nécessaire :

```text
not_started
incomplete
needs_review
ready
invalid
stale
```

Ne pas confondre :

- complétude ;
- validation ;
- calcul ;
- statut métier de l’étude.

---

## Statuts métier

Consommer les statuts réels du backend.

Exemple possible :

```text
draft
in_progress
ready
queued
running
calculated
validated
archived
```

Ne pas coder ces statuts sans vérifier Odoo.

---

## Bannière de préparation

Créer :

```tsx
<StudyReadinessBanner />
```

États possibles :

```text
Étude incomplète
Corrections nécessaires
Hypothèses à confirmer
Prête pour calcul
Résultat obsolète
Étude calculée
```

Afficher :

- statut ;
- nombre d’erreurs ;
- nombre d’avertissements ;
- nombre d’hypothèses ;
- confiance globale ;
- dernière validation ;
- dernière modification.

---

## Synthèse par section

Créer :

```tsx
<SectionCompletionOverview />
<ReviewSectionCard />
```

Sections minimales :

```text
location
model
orientation
usage
equipment
comfort
```

Afficher pour chaque section :

- nom ;
- statut ;
- pourcentage de complétude ;
- score de confiance ;
- nombre d’erreurs ;
- nombre d’avertissements ;
- nombre de valeurs estimées ;
- dernière modification ;
- bouton Corriger ;
- bouton Consulter.

---

## États de section

Valeurs possibles :

```text
complete
incomplete
warning
blocked
stale
not_applicable
```

Le backend doit retourner l’état officiel.

---

## Navigation vers les corrections

Chaque problème doit fournir :

```text
section_code
field_path
route
anchor
```

Créer :

```tsx
<FixIssueLink />
```

Le clic doit :

- ouvrir la bonne route ;
- cibler la bonne section ;
- conserver le contexte ;
- mettre en évidence le champ concerné ;
- permettre un retour vers la revue.

---

## Validation serveur

Créer :

```ts
useValidateCoolingStudy()
```

Endpoint possible :

```text
POST /api/v1/greencube/cooling/studies/<id>/validate
```

ou :

```text
GET /api/v1/greencube/cooling/studies/<id>/validation
```

Le backend doit vérifier :

- présence des données ;
- cohérence des unités ;
- cohérence géométrique ;
- cohérence des surfaces ;
- cohérence des puissances ;
- cohérence des débits ;
- cohérence des scénarios ;
- compatibilité solver ;
- compatibilité Honeybee/EnergyPlus ;
- absence de double comptage ;
- versions des référentiels ;
- permissions ;
- état de l’étude.

---

## Structure d’un problème

Exemple :

```ts
interface CoolingValidationIssue {
  id: string;
  code: string;
  severity: "error" | "warning" | "info";
  blocking: boolean;
  sectionCode: string;
  fieldPath?: string | null;
  title: string;
  message: string;
  remediation?: string | null;
  route?: string | null;
  anchor?: string | null;
  source?: string | null;
  acknowledged?: boolean;
}
```

Adapter au contrat réel.

---

## Erreurs bloquantes

Créer :

```tsx
<BlockingIssuesPanel />
<ValidationIssueCard />
```

Exemples :

- localisation absente ;
- modèle absent ;
- géométrie invalide ;
- surface vitrée supérieure à la façade ;
- nombre maximal d’occupants incohérent ;
- équipement sans puissance ;
- débit de ventilation invalide ;
- consigne absente ;
- scénario climatique indisponible ;
- référentiel introuvable ;
- payload solver incomplet.

Une erreur bloquante doit empêcher le passage à `ready`.

---

## Avertissements

Créer :

```tsx
<WarningIssuesPanel />
```

Exemples :

- `n50` estimé ;
- facteur solaire par défaut ;
- simultanéité estimée ;
- masque extérieur absent ;
- occupation nocturne supposée ;
- profil catalogue ancien ;
- confiance faible ;
- valeur inhabituelle mais techniquement valide.

---

## Informations non bloquantes

Créer éventuellement :

```tsx
<InformationIssuesPanel />
```

Exemples :

- version plus récente disponible ;
- EnergyPlus désactivé ;
- scénario économique absent ;
- justificatif absent.

---

## Hypothèses

Créer :

```tsx
<AssumptionsPanel />
<AssumptionCard />
```

Une hypothèse doit contenir :

```text
code
label
value
unit
source
version
reason
confidence
blocking_confirmation
confirmed
confirmed_by
confirmed_at
```

---

## Types d’hypothèses

Prévoir :

```text
catalog_default
reference_value
user_estimate
backend_fallback
derived_value
conversion_assumption
solver_assumption
```

Distinguer clairement :

- valeur mesurée ;
- valeur catalogue ;
- valeur estimée ;
- valeur dérivée ;
- valeur par défaut.

---

## Confirmation des hypothèses

Créer :

```tsx
<AssumptionConfirmationControl />
```

Certaines hypothèses peuvent nécessiter :

- une confirmation simple ;
- une justification ;
- un rôle spécifique ;
- aucune action.

Ne pas utiliser uniquement une case globale.

---

## Confirmation en masse

Créer éventuellement :

```tsx
<ConfirmAllNonBlockingAssumptions />
```

L’action doit :

- exclure les hypothèses bloquantes ;
- afficher le nombre d’éléments ;
- demander confirmation ;
- conserver l’utilisateur ;
- conserver la date ;
- conserver la version.

---

## Provenance globale

Créer :

```tsx
<DataProvenancePanel />
<ProvenanceSummary />
```

Catégories possibles :

```text
measured
manufacturer_data
product_catalog
usage_profile
climate_source
user_confirmed
estimated_reference
backend_default
missing_fallback
derived
```

Afficher :

- nombre de valeurs par provenance ;
- impact sur la confiance ;
- sections concernées ;
- accès au détail.

---

## Versions des référentiels

Créer :

```tsx
<ReferenceVersionSummary />
```

Afficher les versions utilisées pour :

- climat ;
- modèle GreenCube ;
- spécification thermique ;
- vitrages ;
- profils d’usage ;
- gains humains ;
- équipements ;
- ventilation ;
- étanchéité ;
- confort ;
- solver ;
- mapping EnergyPlus.

Ne pas mettre automatiquement les versions à jour.

---

## Référentiel plus récent

Créer :

```tsx
<ReferenceUpdateNotice />
```

Si une version plus récente existe :

- afficher l’information ;
- ne pas l’appliquer silencieusement ;
- proposer une mise à jour explicite ;
- expliquer les invalidations ;
- demander confirmation ;
- créer une révision si nécessaire.

---

## Score de confiance global

Créer :

```tsx
<ConfidenceOverview />
<GlobalConfidenceGauge />
```

Le score doit venir du backend.

Afficher :

- score global ;
- niveau qualitatif ;
- score par section ;
- principaux facteurs de réduction ;
- nombre de valeurs estimées ;
- nombre de valeurs manquantes ;
- date du calcul.

---

## Niveaux de confiance

Valeurs possibles :

```text
very_low
low
medium
high
very_high
```

Labels :

```text
Très faible
Faible
Moyenne
Élevée
Très élevée
```

Les seuils doivent venir du backend ou d’une configuration partagée.

---

## Facteurs de baisse

Créer :

```tsx
<ConfidenceDriversPanel />
```

Exemples :

- infiltration estimée ;
- orientation non mesurée ;
- facteur solaire par défaut ;
- équipements personnalisés ;
- masque extérieur absent ;
- planning approximatif.

Afficher les facteurs principaux.

---

## Synthèse climatique

Créer :

```tsx
<ClimateScenarioSummary />
<ScenarioReviewCard />
```

Scénarios :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Pour chaque scénario, afficher :

- nom ;
- source climatique ;
- période ou fichier météo ;
- température extérieure ;
- humidité ;
- rayonnement ;
- vent ;
- durée ;
- statut ;
- confiance ;
- version.

---

## Scénario dimensionnant pressenti

Afficher si fourni par le backend :

```text
expected_governing_scenario
```

Libellé :

```text
Scénario probablement dimensionnant
```

Ne pas le présenter comme un résultat définitif.

---

## Synthèse des données de calcul

Créer :

```tsx
<CalculationInputSummary />
```

Familles :

```text
géométrie
transmission
apports solaires
occupants
équipements
éclairage
ventilation
infiltration
consignes
```

Pour chaque famille :

- valeur principale ;
- unité ;
- provenance ;
- confiance ;
- statut ;
- accès au détail.

---

## Résumé géométrique

Afficher :

- modèle ;
- dimensions ;
- surface ;
- volume ;
- surfaces de façades ;
- surface vitrée ;
- ratio vitré ;
- orientation.

---

## Résumé enveloppe

Afficher :

- U murs ;
- U toiture ;
- U plancher ;
- U vitrage ;
- facteur solaire ;
- étanchéité ;
- ponts thermiques ;
- provenance.

---

## Résumé usage

Afficher :

- usage ;
- occupants habituels ;
- occupants maximum ;
- activité ;
- planning ;
- occupation nocturne ;
- gains sensibles ;
- gains latents.

---

## Résumé équipements

Afficher :

- puissance installée ;
- puissance active de pointe ;
- charge sensible ;
- charge latente ;
- éclairage ;
- charge permanente ;
- catégorie principale.

---

## Résumé ventilation et confort

Afficher :

- système ;
- débit ;
- ACH ;
- récupération ;
- infiltration ;
- `n50` ;
- ouverture nocturne ;
- consigne jour ;
- consigne nuit ;
- humidité maximale ;
- niveau de résilience.

---

## Valeurs aberrantes

Créer :

```tsx
<OutlierReviewPanel />
```

Exemples :

- densité d’occupation élevée ;
- puissance par m² élevée ;
- débit très élevé ;
- consigne très basse ;
- ratio vitré extrême ;
- infiltration extrême ;
- récupération incohérente ;
- facteur solaire inhabituel.

Une valeur aberrante peut être valide, mais doit être confirmée.

---

## Écarts entre sections

Le backend doit vérifier :

- surface ouvrable supérieure à la surface vitrée ;
- ventilation par personne sans occupants ;
- éclairage par m² sans surface ;
- occupation nocturne sans consigne nocturne ;
- récupération active avec ventilation naturelle ;
- baie supprimée mais protection conservée ;
- modèle modifié après calcul des façades.

---

## Données obsolètes

Créer :

```tsx
<StaleDataPanel />
```

Exemples :

- orientation modifiée après calcul solaire ;
- modèle modifié après saisie des vitrages ;
- usage modifié après création des équipements ;
- volume modifié après conversion ACH ;
- consigne modifiée après prévisualisation.

Une donnée obsolète doit être recalculée ou reconfirmée.

---

## Snapshot de calcul

Créer un snapshot immuable contenant :

- identifiant d’étude ;
- version d’étude ;
- date ;
- utilisateur ;
- société ;
- modèles et variantes ;
- versions de référentiels ;
- données consolidées ;
- hypothèses confirmées ;
- scénarios ;
- moteur demandé ;
- version du solver ;
- hash ou empreinte ;
- statut.

---

## Aperçu du snapshot

Créer :

```tsx
<SnapshotPreview />
```

Afficher :

- version ;
- date ;
- nombre de sections ;
- nombre d’hypothèses ;
- scénarios ;
- moteur ;
- empreinte courte ;
- état.

---

## Création du snapshot

Créer :

```ts
useCreateCoolingCalculationSnapshot()
```

Endpoint possible :

```text
POST /api/v1/greencube/cooling/studies/<id>/snapshots
```

Payload possible :

```json
{
  "study_version": "server-version",
  "confirmed_assumption_ids": [
    "assumption-1",
    "assumption-2"
  ],
  "scenario_codes": [
    "reference_summer",
    "hot_weather",
    "prolonged_heatwave"
  ],
  "requested_engines": [
    "quick_solver"
  ]
}
```

Le backend doit :

- revérifier l’étude ;
- refuser si elle est incomplète ;
- figer les données ;
- calculer une empreinte ;
- créer le snapshot ;
- retourner le statut.

---

## Idempotence

Utiliser :

```text
Idempotency-Key
```

Éviter les doublons causés par :

- double clic ;
- retry réseau ;
- retour arrière ;
- rafraîchissement.

---

## Passage au statut ready

Créer :

```ts
useMarkCoolingStudyReady()
```

Endpoint possible :

```text
POST /api/v1/greencube/cooling/studies/<id>/ready
```

ou transition incluse dans la création du snapshot.

Le backend doit :

- vérifier les permissions ;
- vérifier la version ;
- vérifier les erreurs ;
- vérifier les hypothèses ;
- créer ou lier le snapshot ;
- passer l’étude à `ready`.

---

## Confirmation finale

Créer :

```tsx
<FinalConfirmationPanel />
<ReadyForCalculationDialog />
```

Texte recommandé :

```text
En lançant la préparation du calcul, les données actuelles seront figées dans un snapshot. Toute modification ultérieure nécessitera une nouvelle révision et un nouveau calcul.
```

Afficher :

- erreurs : 0 ;
- avertissements ;
- hypothèses confirmées ;
- confiance ;
- scénarios ;
- moteur prévu ;
- version d’étude.

---

## Conditions d’activation

Le bouton :

```text
Préparer le calcul
```

doit être désactivé si :

- une erreur bloquante existe ;
- une hypothèse obligatoire n’est pas confirmée ;
- l’étude est obsolète ;
- une validation serveur est en cours ;
- une sauvegarde est en attente ;
- une version est en conflit ;
- l’utilisateur n’a pas la permission.

---

## États du bouton

Prévoir :

```text
Vérifier l’étude
Corriger les erreurs
Confirmer les hypothèses
Préparer le calcul
Étude prête
Calcul en cours
```

---

## Choix du moteur

Créer :

```tsx
<CalculationEngineSelector />
```

Moteurs possibles :

```text
quick_solver
energyplus
both
```

Pour le MVP :

- `quick_solver` obligatoire ;
- `energyplus` derrière un feature flag ;
- `both` si disponible.

Feature flag :

```text
enable_energyplus_calculation
```

---

## Sélection des scénarios

Créer :

```tsx
<ScenarioSelectionPanel />
```

Scénarios minimaux :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Le backend peut imposer les trois.

---

## Prévisualisation du payload solver

Créer éventuellement :

```tsx
<SolverPayloadPreview />
```

Réserver cette vue :

- aux administrateurs ;
- aux développeurs ;
- au mode debug.

Feature flag :

```text
enable_solver_payload_preview
```

---

## Validation du payload solver

Le backend doit vérifier la présence de :

- climat ;
- géométrie ;
- enveloppe ;
- vitrages ;
- apports solaires ;
- occupants ;
- équipements ;
- ventilation ;
- infiltration ;
- consignes ;
- scénarios ;
- versions.

---

## Sauvegardes en attente

Créer :

```tsx
<PendingSaveNotice />
```

Avant validation :

- finaliser les sauvegardes ;
- invalider les queries ;
- recharger l’étude ;
- relancer la validation serveur.

Ne pas créer un snapshot depuis un état local non sauvegardé.

---

## Conflit de version

Créer :

```tsx
<StudyVersionConflictDialog />
```

En cas de conflit :

- bloquer la préparation ;
- recharger les données ;
- afficher les changements ;
- permettre une fusion uniquement si le workflow existe ;
- ne jamais écraser silencieusement.

---

## Révision

Pour une étude déjà calculée ou validée :

- proposer une nouvelle révision ;
- copier les données compatibles ;
- conserver le lien avec le snapshot précédent ;
- invalider les anciens résultats pour la nouvelle révision ;
- conserver l’historique.

Réutiliser :

```tsx
<CreateRevisionDialog />
```

---

## Confirmation des hypothèses

Créer :

```ts
useConfirmCoolingAssumptions()
```

Endpoint possible :

```text
POST /api/v1/greencube/cooling/studies/<id>/assumptions/confirm
```

Payload possible :

```json
{
  "assumption_ids": [
    "assumption-1",
    "assumption-2"
  ],
  "comment": "Hypothèses vérifiées avec le porteur de projet.",
  "version": "server-version"
}
```

Conserver :

- utilisateur ;
- date ;
- commentaire ;
- version.

---

## Audit trail

Auditer :

- validation ;
- confirmation d’hypothèse ;
- acceptation d’une valeur estimée ;
- création du snapshot ;
- passage à `ready` ;
- création de révision ;
- lancement de calcul.

---

## Query hooks

Créer ou compléter :

```ts
useCoolingStudyReview(studyId)
useValidateCoolingStudy()
useConfirmCoolingAssumptions()
useCreateCoolingCalculationSnapshot()
useMarkCoolingStudyReady()
```

Query keys recommandées :

```ts
coolingKeys.study(studyId)
coolingKeys.review(studyId)
coolingKeys.validation(studyId)
coolingKeys.snapshots(studyId)
```

---

## Actualisation de la validation

Relancer la validation :

- à l’ouverture ;
- après une sauvegarde ;
- après confirmation d’une hypothèse ;
- après retour d’une autre section ;
- avant création du snapshot ;
- après résolution d’un conflit.

Éviter les boucles de validation.

---

## Cache TanStack Query

Règles recommandées :

- review avec faible `staleTime` ;
- validation explicitement invalidée ;
- snapshot immuable ;
- étude invalidée après transition ;
- pas de cache persistant non chiffré contenant des données sensibles.

---

## Store temporaire

Ajouter uniquement :

```ts
interface CoolingReviewDraft {
  expandedSectionCodes: string[];
  selectedIssueId?: string | null;
  selectedScenarioCodes: string[];
  selectedEngine: "quick_solver" | "energyplus" | "both";
  hasPendingConfirmations: boolean;
}
```

Les données métier restent dans Odoo.

---

## Formulaire limité

L’écran de revue n’est pas un formulaire métier global.

React Hook Form peut être utilisé uniquement pour :

- les confirmations ;
- le commentaire ;
- les scénarios ;
- le choix du moteur.

Ne pas recopier toute l’étude dans un formulaire local.

---

## Schéma Zod

Exemple :

```ts
const prepareCalculationSchema = z.object({
  confirmedAssumptionIds: z.array(z.string()),
  scenarioCodes: z.array(
    z.enum([
      "reference_summer",
      "hot_weather",
      "prolonged_heatwave",
    ])
  ).min(1),
  engine: z.enum([
    "quick_solver",
    "energyplus",
    "both",
  ]),
  confirmationComment: z.string().max(1000).optional(),
  studyVersion: z.string().min(1),
});
```

---

## Accessibilité

Respecter :

- ordre de lecture logique ;
- navigation clavier ;
- liens de correction accessibles ;
- panneaux d’erreurs annoncés ;
- statut global annoncé ;
- badges non dépendants uniquement de la couleur ;
- accordéons accessibles ;
- résumé textuel des graphiques ;
- focus sur le premier problème bloquant ;
- dialogue final accessible.

---

## Responsive

### Desktop

```text
Colonne gauche : complétude, erreurs et hypothèses
Colonne droite : synthèse, scénarios et confiance
```

### Tablette

- cartes empilées ;
- synthèse en deux colonnes si possible.

### Mobile

- sections en accordéons ;
- cartes compactes ;
- bouton de correction visible ;
- scénarios sous forme de cartes ;
- footer sticky ;
- action finale pleine largeur.

---

## États de chargement

Prévoir :

- skeleton synthèse ;
- validation en cours ;
- confirmation en cours ;
- création du snapshot ;
- transition vers `ready` ;
- problème de version ;
- étude introuvable ;
- validation indisponible ;
- données partielles.

---

## Gestion des erreurs

Codes possibles :

```text
STUDY_NOT_FOUND
STUDY_NOT_EDITABLE
STUDY_INCOMPLETE
STUDY_VALIDATION_FAILED
BLOCKING_ISSUES_PRESENT
UNCONFIRMED_ASSUMPTIONS
STALE_STUDY_DATA
INVALID_SCENARIO_SELECTION
CALCULATION_ENGINE_UNAVAILABLE
SNAPSHOT_ALREADY_EXISTS
SNAPSHOT_CREATION_FAILED
STUDY_VERSION_CONFLICT
INVALID_STATE_TRANSITION
ACCESS_DENIED
```

Pour chaque erreur :

- message clair ;
- cause ;
- action ;
- section concernée ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires

Tester :

### Complétude

- section complète ;
- section incomplète ;
- section bloquée ;
- section obsolète ;
- section non applicable.

### Problèmes

- erreur bloquante ;
- avertissement ;
- information ;
- lien de correction ;
- champ inconnu.

### Hypothèses

- confirmation ;
- confirmation obligatoire ;
- confirmation en masse ;
- justification ;
- hypothèse déjà confirmée.

### Confiance

- score global ;
- scores par section ;
- facteur de réduction ;
- niveau qualitatif.

### Scénarios

- trois scénarios ;
- sélection ;
- moteur indisponible ;
- scénario obligatoire.

### Snapshot

- création ;
- idempotence ;
- conflit ;
- étude incomplète ;
- version incorrecte.

### Transition

- passage à `ready` ;
- transition interdite ;
- lecture seule ;
- révision.

---

## Tests d’intégration

Tester :

1. chargement de la revue ;
2. affichage des sections ;
3. affichage des erreurs ;
4. navigation vers une correction ;
5. retour à la revue ;
6. relance de validation ;
7. confirmation d’une hypothèse ;
8. confirmation en masse ;
9. affichage des versions ;
10. affichage de la confiance ;
11. sélection des scénarios ;
12. sélection du moteur ;
13. création du snapshot ;
14. passage à `ready` ;
15. conflit de version ;
16. étude obsolète ;
17. étude déjà calculée ;
18. création d’une révision.

---

## Tests Playwright

Créer au minimum :

1. étude complète et préparation réussie ;
2. erreur bloquante sur la géométrie ;
3. hypothèse d’infiltration à confirmer ;
4. avertissements non bloquants ;
5. confiance globale faible ;
6. référentiel plus récent disponible ;
7. conflit de version avant snapshot ;
8. double clic sur Préparer le calcul ;
9. étude calculée en lecture seule ;
10. création d’une nouvelle révision.

---

## Mock API

Créer des mocks pour :

- étude complète ;
- étude incomplète ;
- géométrie bloquante ;
- hypothèses à confirmer ;
- confiance élevée ;
- confiance faible ;
- données obsolètes ;
- référentiel ancien ;
- moteur EnergyPlus indisponible ;
- snapshot existant ;
- conflit de version ;
- transition interdite ;
- validation serveur indisponible.

Les mocks doivent respecter l’OpenAPI réel.

---

## Composants à créer ou compléter

```text
CoolingReviewPage
ReviewHeader
StudyReadinessBanner
SectionCompletionOverview
ReviewSectionCard
BlockingIssuesPanel
WarningIssuesPanel
InformationIssuesPanel
ValidationIssueCard
FixIssueLink
AssumptionsPanel
AssumptionCard
AssumptionConfirmationControl
ConfirmAllNonBlockingAssumptions
DataProvenancePanel
ProvenanceSummary
ReferenceVersionSummary
ReferenceUpdateNotice
ConfidenceOverview
GlobalConfidenceGauge
ConfidenceDriversPanel
ClimateScenarioSummary
ScenarioReviewCard
ScenarioSelectionPanel
CalculationInputSummary
OutlierReviewPanel
StaleDataPanel
SnapshotPreview
CalculationEngineSelector
SolverPayloadPreview
PendingSaveNotice
FinalConfirmationPanel
ReadyForCalculationDialog
StudyVersionConflictDialog
```

---

## Documentation

Créer :

```text
docs/cooling_review_before_calculation.md
docs/cooling_validation_rules.md
docs/cooling_calculation_snapshot.md
docs/cooling_section_dependency_matrix.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

Mapping attendu :

```text
Revue étude
→ GET /studies/<id>/review

Validation
→ POST /studies/<id>/validate

Confirmation hypothèses
→ POST /studies/<id>/assumptions/confirm

Création snapshot
→ POST /studies/<id>/snapshots

Passage à ready
→ POST /studies/<id>/ready

Révision
→ POST /studies/<id>/revisions
```

La matrice de dépendance doit suivre :

```text
section modifiée
→ sections invalidées
→ résultats invalidés
→ confirmation nécessaire
```

---

## Critères d’acceptation

Le lot est accepté si :

- la route fonctionne ;
- l’étude est chargée ;
- les sections sont synthétisées ;
- la complétude est affichée ;
- les erreurs bloquantes sont affichées ;
- les avertissements sont affichés ;
- les informations non bloquantes sont affichées ;
- les liens de correction fonctionnent ;
- les hypothèses sont affichées ;
- les hypothèses obligatoires peuvent être confirmées ;
- les confirmations sont auditées ;
- les provenances sont visibles ;
- les versions des référentiels sont visibles ;
- les versions plus récentes sont signalées ;
- la confiance globale est affichée ;
- les scores par section sont affichés ;
- les facteurs de baisse sont visibles ;
- les scénarios climatiques sont affichés ;
- les scénarios peuvent être sélectionnés si autorisé ;
- le moteur peut être sélectionné si autorisé ;
- le payload est validé côté serveur ;
- les données obsolètes sont détectées ;
- les valeurs aberrantes sont signalées ;
- les écarts entre sections sont détectés ;
- les sauvegardes en attente empêchent le snapshot ;
- les conflits de version sont gérés ;
- le snapshot est créé côté serveur ;
- le snapshot est immuable ;
- l’idempotence est assurée ;
- l’étude passe à `ready` uniquement côté serveur ;
- une étude incomplète ne peut pas passer à `ready` ;
- une étude calculée est en lecture seule ;
- la création d’une révision fonctionne ;
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
- queries ;
- mutations.

### Validation

- règles ;
- sévérités ;
- erreurs ;
- avertissements ;
- informations ;
- dépendances croisées.

### Hypothèses

- types ;
- confirmations ;
- audit ;
- valeurs par défaut ;
- provenances.

### Confiance

- score global ;
- scores par section ;
- facteurs de réduction ;
- seuils.

### Scénarios

- scénarios disponibles ;
- sélection ;
- moteur ;
- disponibilité.

### Snapshot

- structure ;
- idempotence ;
- empreinte ;
- version ;
- immuabilité ;
- transition `ready`.

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
- permissions ;
- tests.

### Tests

- commandes ;
- résultats ;
- couverture ;
- tests non exécutés ;
- raisons.

### Performance

- nombre de requêtes ;
- validation ;
- re-renders ;
- bundle ;
- limites.

### Sécurité

- permissions ;
- audit ;
- versioning ;
- idempotence ;
- données sensibles ;
- logs.

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
7. vérifier la route ;
8. vérifier les sections ;
9. vérifier la complétude ;
10. vérifier les erreurs ;
11. vérifier les avertissements ;
12. vérifier les informations ;
13. vérifier les liens de correction ;
14. vérifier les hypothèses ;
15. vérifier les confirmations ;
16. vérifier l’audit ;
17. vérifier les provenances ;
18. vérifier les versions ;
19. vérifier la confiance ;
20. vérifier les scénarios ;
21. vérifier le moteur ;
22. vérifier les données obsolètes ;
23. vérifier les valeurs aberrantes ;
24. vérifier les dépendances croisées ;
25. vérifier les sauvegardes en attente ;
26. vérifier les conflits de version ;
27. vérifier la validation serveur ;
28. vérifier la création du snapshot ;
29. vérifier l’idempotence ;
30. vérifier l’immuabilité ;
31. vérifier la transition `ready` ;
32. vérifier l’étude calculée ;
33. vérifier la révision ;
34. vérifier l’accessibilité ;
35. vérifier le responsive ;
36. vérifier l’absence de secrets ;
37. vérifier qu’aucun fichier n’a été supprimé ;
38. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente uniquement l’écran Vérification et synthèse avant calcul.

Il ne finalise pas encore :

- le solver thermique rapide ;
- l’orchestration des jobs EnergyPlus ;
- l’écran de résultats ;
- la recommandation finale de puissance ;
- la sélection d’un climatiseur.

Il doit garantir qu’aucun calcul n’est lancé sur une étude incomplète, incohérente, obsolète ou insuffisamment confirmée.
