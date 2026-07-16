# GC-COOLING-16 — Résultats et recommandation de puissance de refroidissement

## Objectif

Implémenter l’écran :

```text
8 — Résultats et recommandation de puissance
```

L’écran doit permettre de :

- consulter le statut du calcul ;
- suivre un calcul encore en cours ;
- consulter la puissance de refroidissement recommandée ;
- consulter la charge sensible ;
- consulter la charge latente ;
- consulter la charge totale ;
- consulter le ratio sensible `SHR` ;
- identifier le scénario dimensionnant ;
- comparer les scénarios climatiques ;
- visualiser la répartition des charges ;
- comparer MERCURE et EnergyPlus ;
- comprendre les écarts entre les moteurs ;
- consulter le niveau de confiance ;
- consulter les hypothèses et avertissements ;
- consulter les dépassements de confort ;
- consulter les recommandations d’optimisation ;
- relancer un calcul ;
- créer une révision avant toute modification ;
- préparer la future sélection d’un climatiseur ;
- exporter les données utiles ;
- conserver une traçabilité complète.

Odoo Community 18 reste la source de vérité.

Le frontend ne doit jamais recalculer ni modifier les résultats officiels. Il doit uniquement afficher et présenter les données retournées par le backend.

---

## Prérequis

Le lot suppose disponibles :

```text
GC-COOLING-13
→ étude vérifiée
→ snapshot immuable
→ statut ready

GC-COOLING-14
→ résultat MERCURE

GC-COOLING-15
→ résultat Honeybee/EnergyPlus
→ comparaison MERCURE / EnergyPlus
→ jobs et artefacts
```

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

- inspecter le socle frontend existant ;
- inspecter l’écran de revue GC-COOLING-13 ;
- inspecter le contrat MERCURE ;
- inspecter l’orchestration EnergyPlus ;
- vérifier les routes ;
- vérifier les modèles de résultats Odoo ;
- vérifier les statuts des jobs ;
- vérifier les endpoints de résultats ;
- vérifier les endpoints de comparaison ;
- vérifier les avertissements ;
- vérifier les hypothèses ;
- vérifier les artefacts ;
- vérifier la règle de recommandation finale ;
- vérifier les unités ;
- vérifier les règles d’arrondi ;
- vérifier les permissions ;
- vérifier le multi-société ;
- vérifier les feature flags ;
- vérifier les composants de graphiques ;
- vérifier l’accessibilité ;
- exécuter lint, TypeScript, tests et build ;
- ne supprimer aucun composant ;
- ne recalculer aucune charge dans le frontend ;
- ne modifier aucun résultat terminé ;
- ne jamais présenter un résultat provisoire comme officiel ;
- ne pas confondre puissance thermique, puissance électrique et énergie annuelle.

---

## Route

```text
/cooling/studies/:studyId/results
```

Routes secondaires possibles :

```text
/cooling/studies/:studyId/results/:resultId
/cooling/studies/:studyId/calculations/:jobId
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
CoolingResultGuard
```

---

## États de la page

Prévoir :

```text
not_started
queued
running
completed
completed_with_warnings
failed
cancelled
timed_out
stale
superseded
```

Chaque état doit disposer d’une présentation adaptée.

---

## Structure de la page

Créer :

```tsx
<CoolingResultsPage />
```

Structure recommandée :

```text
CoolingLayout
├── ResultsHeader
├── CalculationStatusBanner
├── MainRecommendationCard
├── GoverningScenarioCard
├── LoadSummaryCards
├── ScenarioComparisonSection
├── LoadBreakdownSection
├── MercureEnergyPlusComparison
├── ComfortPerformanceSection
├── ConfidenceAndWarningsSection
├── OptimizationRecommendations
├── TechnicalDetailsSection
├── CalculationHistorySection
└── ResultsActionFooter
```

---

## En-tête

Créer :

```tsx
<ResultsHeader />
```

Afficher :

- nom de l’étude ;
- modèle GreenCube ;
- localisation ;
- version de l’étude ;
- version du snapshot ;
- date du calcul ;
- moteur ou moteurs ;
- statut ;
- bouton Retour à l’étude ;
- bouton Nouvelle révision si autorisé.

---

## Statut du calcul

Créer :

```tsx
<CalculationStatusBanner />
```

États d’affichage :

```text
Calcul en attente de traitement
Simulation thermique en cours
Calcul terminé
Calcul terminé avec des points à vérifier
Le calcul n’a pas pu être finalisé
Ce résultat ne correspond plus à la version actuelle de l’étude
```

---

## Suivi du job

Créer :

```ts
useCoolingCalculationJob(jobId)
```

Afficher :

- statut ;
- étape ;
- progression ;
- message ;
- heure de lancement ;
- heartbeat ;
- moteur ;
- scénario en cours ;
- possibilité d’annulation si autorisée.

Le polling doit fonctionner uniquement pendant :

```text
queued
running
```

Il doit s’arrêter à la fin du job.

---

## Progression

Créer :

```tsx
<CalculationProgressCard />
```

Afficher :

- progression ;
- étape courante ;
- scénario courant ;
- moteur ;
- durée écoulée si fournie ;
- scénarios terminés ;
- nombre total de scénarios.

Ne pas inventer de temps restant.

---

## Échec du calcul

Créer :

```tsx
<CalculationFailurePanel />
```

Afficher :

- code d’erreur ;
- message compréhensible ;
- étape d’échec ;
- moteur ;
- scénario ;
- request ID ;
- action possible ;
- bouton Relancer ;
- bouton Utiliser MERCURE si EnergyPlus a échoué et qu’un résultat MERCURE existe.

Ne pas afficher de trace brute.

---

## Recommandation principale

Créer :

```tsx
<MainRecommendationCard />
```

Afficher en priorité :

```text
Puissance de refroidissement recommandée
```

Valeurs :

- puissance en kW ;
- puissance en W ;
- équivalent BTU/h ;
- charge brute ;
- marge ;
- puissance finale ;
- moteur retenu ;
- scénario dimensionnant ;
- confiance.

Exemple :

```text
Puissance recommandée : 3,5 kW

Charge calculée : 3,08 kW
Marge de dimensionnement : 14 %
Scénario dimensionnant : Canicule prolongée
Moteur retenu : EnergyPlus
Confiance : Élevée
```

---

## Capacité thermique

Afficher clairement :

```text
Puissance thermique de refroidissement
```

Ajouter une aide :

```text
Cette valeur correspond à la capacité thermique nécessaire. La consommation électrique dépendra du rendement du climatiseur sélectionné.
```

Ne pas présenter la capacité thermique comme une consommation électrique.

---

## Arrondi commercial

Si le backend fournit :

```text
raw_recommended_capacity_w
commercial_recommended_capacity_w
```

Afficher :

```text
Besoin calculé : 3,08 kW
Palier commercial recommandé : 3,5 kW
```

Le frontend ne doit jamais choisir le palier.

---

## Moteur retenu

Afficher les valeurs backend possibles :

```text
MERCURE
EnergyPlus
Maximum des deux
Validation ingénieur requise
MERCURE de secours
```

Créer :

```tsx
<SelectedEngineBadge />
```

---

## Scénario dimensionnant

Créer :

```tsx
<GoverningScenarioCard />
```

Afficher :

- code ;
- label ;
- température extérieure ;
- humidité ;
- consigne intérieure ;
- date ou période ;
- charge brute ;
- charge avec marge ;
- moteur ;
- facteur principal.

Scénarios :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Labels :

```text
Été de référence
Forte chaleur
Canicule prolongée
```

---

## Cartes de synthèse

Créer :

```tsx
<LoadSummaryCards />
```

Afficher :

```text
Charge sensible
Charge latente
Charge totale
Marge
Puissance recommandée
SHR
```

Exemple :

```text
Sensible : 2,72 kW
Latente : 0,36 kW
Total : 3,08 kW
Marge : 0,42 kW
Recommandée : 3,50 kW
SHR : 0,88
```

---

## Sensible Heat Ratio

Créer :

```tsx
<SensibleHeatRatioCard />
```

Afficher :

```text
SHR = charge sensible / charge totale
```

Explication :

```text
Un SHR élevé indique que le besoin provient principalement de la température. Un SHR plus faible indique une part d’humidité plus importante.
```

---

## Charge latente élevée

En cas de :

```text
HIGH_LATENT_LOAD
```

Afficher :

```text
La part d’humidité est importante. Le climatiseur sélectionné devra disposer d’une capacité de déshumidification adaptée.
```

---

## Comparaison des scénarios

Créer :

```tsx
<ScenarioComparisonSection />
<ScenarioResultCard />
<ScenarioComparisonTable />
<ScenarioLoadChart />
```

Pour chaque scénario, afficher :

- charge sensible ;
- charge latente ;
- charge totale ;
- marge ;
- recommandation ;
- température maximale ;
- heures de dépassement ;
- moteur ;
- confiance ;
- avertissements.

Colonnes recommandées :

```text
Scénario
Température extérieure
Humidité
Sensible
Latent
Total
Marge
Recommandé
Confiance
```

Le graphique doit disposer d’une alternative tabulaire accessible.

---

## Répartition des charges

Créer :

```tsx
<LoadBreakdownSection />
<LoadBreakdownChart />
<LoadBreakdownTable />
```

Catégories minimales :

```text
transmission
solar
occupants
equipment
lighting
ventilation
infiltration
openings
fan_heat
other
```

Détails possibles :

- murs ;
- toiture ;
- plancher ;
- portes ;
- vitrages ;
- ponts thermiques ;
- apports solaires ;
- occupants ;
- équipements ;
- éclairage ;
- ventilateurs ;
- ventilation ;
- infiltration ;
- ouvertures ;
- autres charges.

Afficher :

- puissance ;
- pourcentage du total.

---

## Contributions principales

Créer :

```tsx
<MainLoadDriversCard />
```

Afficher les trois premières contributions.

Exemple :

```text
1. Apports solaires ouest — 31 %
2. Équipements informatiques — 22 %
3. Ventilation — 16 %
```

---

## Navigation vers les données d’entrée

Pour chaque catégorie, proposer :

```text
Voir les données d’entrée
```

Le lien doit :

- ouvrir la section correspondante ;
- rester en lecture seule pour le résultat historique ;
- proposer une révision avant modification.

---

## Comparaison MERCURE / EnergyPlus

Créer :

```tsx
<MercureEnergyPlusComparison />
```

Afficher uniquement si les deux résultats existent.

Comparer :

- sensible ;
- latent ;
- total ;
- puissance recommandée ;
- scénario dimensionnant ;
- contribution dominante ;
- confiance.

Exemple :

```text
MERCURE : 3,32 kW
EnergyPlus : 3,08 kW
Écart : +0,24 kW, soit +7,8 %
Statut : cohérent
```

---

## Statut de comparaison

Valeurs :

```text
acceptable
warning
critical
not_comparable
```

Labels :

```text
Cohérent
Écart à surveiller
Écart important
Comparaison indisponible
```

Créer :

```tsx
<ComparisonStatusBadge />
```

---

## Explication des écarts

Créer :

```tsx
<ResultDifferenceExplanation />
```

Afficher les causes probables retournées par le backend :

- inertie thermique ;
- profils horaires ;
- pics non simultanés ;
- rayonnement dynamique ;
- ventilation nocturne ;
- humidité ;
- protections solaires dynamiques ;
- géométrie simplifiée ;
- température du sol ;
- construction équivalente.

Ne pas présenter une hypothèse comme une certitude.

---

## Écart critique

Si la comparaison est `critical`, afficher :

```text
Une revue technique est recommandée avant de sélectionner un équipement.
```

La sélection commerciale future doit pouvoir être désactivée.

---

## Résultat MERCURE seul

Si EnergyPlus n’est pas disponible :

- afficher MERCURE ;
- afficher sa version ;
- afficher ses limites ;
- signaler que la simulation dynamique n’a pas été exécutée.

---

## Résultat EnergyPlus seul

Si MERCURE n’est pas disponible :

- afficher EnergyPlus ;
- signaler l’absence de comparaison ;
- conserver les avertissements ;
- indiquer si le résultat est exploitable.

---

## Fallback MERCURE

Si EnergyPlus échoue :

```text
La simulation avancée n’a pas abouti. La recommandation affichée repose sur MERCURE.
```

Afficher :

- code d’échec ;
- confiance MERCURE ;
- option de relance ;
- option de revue technique.

---

## Performance de confort

Créer :

```tsx
<ComfortPerformanceSection />
<ComfortStatusBadge />
```

Afficher selon disponibilité :

- température intérieure maximale ;
- température opérative maximale ;
- humidité maximale ;
- heures au-dessus de la consigne ;
- heures au-dessus du maximum acceptable ;
- durée continue de dépassement ;
- date et heure du pic.

Statuts :

```text
maintained
partially_maintained
not_maintained
not_evaluated
```

Labels :

```text
Confort maintenu
Confort partiellement maintenu
Confort non maintenu
Non évalué
```

---

## Résilience canicule

Pour :

```text
prolonged_heatwave
```

Afficher :

- température maximale ;
- température moyenne ;
- heures de dépassement ;
- dépassement nocturne ;
- humidité ;
- maintien de la consigne ;
- statut de résilience.

---

## Courbes horaires

Créer si les séries sont disponibles :

```tsx
<IndoorTemperatureChart />
<IndoorHumidityChart />
```

Afficher :

- température extérieure ;
- température intérieure ;
- consigne ;
- température maximale acceptable ;
- humidité intérieure ;
- humidité extérieure ;
- seuil maximal.

Prévoir une alternative tabulaire.

Ne pas charger des milliers de points sans agrégation ou lazy loading.

---

## Période critique

Créer :

```tsx
<PeakPeriodCard />
```

Afficher :

- date ;
- heure ;
- scénario ;
- température extérieure ;
- humidité ;
- charge totale ;
- contributions principales ;
- occupation ;
- équipements ;
- ventilation.

---

## Énergie annuelle

Si disponible, afficher :

```text
annual_cooling_energy_kwh
```

Créer :

```tsx
<AnnualCoolingEnergyCard />
```

Libellé :

```text
Énergie thermique annuelle de refroidissement
```

Ne pas la présenter comme consommation électrique.

Si non simulée :

```text
L’énergie annuelle n’a pas été simulée pour ce calcul.
```

---

## Confiance globale

Créer :

```tsx
<ResultConfidencePanel />
```

Afficher :

- score global ;
- niveau ;
- score par moteur ;
- facteurs de baisse ;
- valeurs estimées ;
- simplifications ;
- date ;
- méthode.

Facteurs possibles :

- géométrie simplifiée ;
- construction équivalente ;
- infiltration estimée ;
- facteur solaire estimé ;
- équipements personnalisés ;
- météo synthétique ;
- ventilation naturelle simplifiée ;
- humidité non modélisée ;
- erreurs EnergyPlus tolérées.

---

## Hypothèses

Créer :

```tsx
<CalculationAssumptionsPanel />
```

Afficher :

- code ;
- valeur ;
- unité ;
- source ;
- version ;
- moteur ;
- impact ;
- confirmation initiale.

Les hypothèses doivent correspondre au snapshot.

---

## Avertissements

Créer :

```tsx
<ResultWarningsPanel />
<ResultWarningCard />
```

Pour chaque avertissement :

- code ;
- niveau ;
- message ;
- composante ;
- impact potentiel ;
- recommandation ;
- moteur ;
- scénario.

Niveaux :

```text
info
warning
high
critical
```

Ne pas dépendre uniquement de la couleur.

---

## Recommandations d’optimisation

Créer :

```tsx
<OptimizationRecommendations />
<OptimizationRecommendationCard />
```

Exemples :

- ajouter un store extérieur ;
- réduire le facteur solaire ;
- limiter les apports ouest ;
- améliorer l’étanchéité ;
- réduire les infiltrations ;
- activer la ventilation nocturne ;
- déplacer l’onduleur ;
- réduire les charges permanentes ;
- relever la consigne de 1 °C ;
- améliorer la récupération ;
- réduire la puissance d’éclairage.

Structure possible :

```ts
interface CoolingOptimizationRecommendation {
  code: string;
  title: string;
  description: string;
  category: string;
  impactLevel: "low" | "medium" | "high";
  estimatedReductionW?: number | null;
  estimatedReductionPercent?: number | null;
  sourceEngine: string;
  requiresRecalculation: boolean;
  targetSectionRoute?: string | null;
}
```

Afficher un impact chiffré uniquement s’il vient du backend.

---

## Action sur une recommandation

Bouton :

```text
Tester cette amélioration
```

Pour le MVP :

- créer une révision ;
- rediriger vers la section concernée ;
- ne pas modifier le snapshot historique ;
- ne pas modifier le résultat officiel.

Feature flag possible :

```text
enable_cooling_what_if
```

---

## Détails techniques

Créer :

```tsx
<TechnicalDetailsSection />
```

Afficher :

- moteur ;
- versions ;
- snapshot ;
- empreinte courte ;
- fichier météo ;
- mode de simulation ;
- pas de temps ;
- nombre de zones ;
- construction équivalente ou multicouche ;
- artefacts ;
- date ;
- durée.

---

## Traces de calcul

Créer :

```tsx
<CalculationTracePanel />
```

Visible uniquement pour les rôles autorisés.

Afficher :

- formule ;
- entrées ;
- unités ;
- résultat ;
- source ;
- hypothèse.

Ne pas exposer les chemins système ou informations sensibles.

---

## Artefacts

Créer :

```tsx
<SimulationArtifactsPanel />
```

Afficher pour les rôles autorisés :

- type ;
- nom ;
- taille ;
- checksum court ;
- date ;
- rétention ;
- téléchargement contrôlé.

Ne pas exposer de lien public permanent.

---

## Historique des calculs

Créer :

```tsx
<CalculationHistorySection />
<CalculationHistoryTable />
```

Afficher :

- date ;
- version d’étude ;
- snapshot ;
- moteur ;
- statut ;
- scénario dimensionnant ;
- puissance recommandée ;
- confiance ;
- auteur ;
- résultat actif ou obsolète.

Le backend doit fournir :

```text
is_current
is_stale
is_superseded
```

---

## Résultat obsolète

Afficher :

```text
Ce résultat correspond à une ancienne version de l’étude.
```

Actions possibles :

- consulter ;
- comparer ;
- créer une révision ;
- relancer le calcul.

Ne pas le présenter comme résultat actif.

---

## Comparaison de versions

Feature flag possible :

```text
enable_result_version_comparison
```

Créer éventuellement :

```tsx
<ResultVersionComparison />
```

Comparer :

- version d’étude ;
- puissance ;
- scénario ;
- charges principales ;
- confiance ;
- moteur ;
- date.

---

## Actions finales

Créer :

```tsx
<ResultsActionFooter />
```

Actions possibles :

```text
Retour à l’étude
Créer une révision
Relancer le calcul
Voir les détails techniques
Télécharger les données
Continuer vers la sélection d’équipement
```

Feature flag :

```text
enable_cooling_equipment_selection
```

Le bouton de sélection doit être désactivé si :

- résultat critique ;
- validation ingénieur requise ;
- résultat obsolète ;
- calcul en échec ;
- puissance absente ;
- confiance insuffisante.

---

## Relance du calcul

Créer :

```ts
useRerunCoolingCalculation()
```

La relance doit utiliser :

- le même snapshot ;
- un nouveau job ;
- un moteur sélectionné ;
- une clé d’idempotence ;
- les mêmes scénarios ou une sélection autorisée.

Ne pas modifier le résultat existant.

---

## Modification des entrées

Toute modification doit suivre :

```text
nouvelle révision
→ nouvelle validation
→ nouveau snapshot
→ nouveau calcul
```

Ne jamais relancer un calcul sur des données locales non sauvegardées.

---

## Endpoints

```text
GET /api/v1/greencube/cooling/calculations/<job_id>
GET /api/v1/greencube/cooling/results/<result_id>
GET /api/v1/greencube/cooling/studies/<study_id>/results
GET /api/v1/greencube/cooling/results/<result_id>/comparison
GET /api/v1/greencube/cooling/calculations/<job_id>/artifacts
POST /api/v1/greencube/cooling/studies/<study_id>/calculations
POST /api/v1/greencube/cooling/studies/<study_id>/revisions
```

---

## Schéma frontend principal

```ts
interface CoolingResultViewModel {
  id: number;
  studyId: number;
  snapshotId: number;
  snapshotVersion: string;
  status: string;
  isCurrent: boolean;
  isStale: boolean;
  engineDecision: CoolingEngineDecision;
  governingScenario: CoolingScenarioResult;
  scenarios: CoolingScenarioResult[];
  recommendation: CoolingCapacityRecommendation;
  comparison?: CoolingEngineComparison | null;
  comfort?: CoolingComfortResult | null;
  confidence: CoolingResultConfidence;
  assumptions: CoolingCalculationAssumption[];
  warnings: CoolingResultWarning[];
  recommendations: CoolingOptimizationRecommendation[];
  artifacts?: CoolingSimulationArtifact[];
  createdAt: string;
}
```

Adapter strictement à l’API réelle.

---

## Recommandation de capacité

```ts
interface CoolingCapacityRecommendation {
  rawCapacityW: number;
  marginW: number;
  marginFraction: number;
  recommendedCapacityW: number;
  commercialCapacityW?: number | null;
  recommendedCapacityKw: number;
  recommendedCapacityBtuH: number;
  sensibleLoadW: number;
  latentLoadW: number;
  totalLoadW: number;
  sensibleHeatRatio: number | null;
  marginReason: string;
}
```

---

## Résultat par scénario

```ts
interface CoolingScenarioResult {
  code: string;
  label: string;
  sensibleLoadW: number;
  latentLoadW: number;
  totalLoadW: number;
  marginW: number;
  recommendedCapacityW: number;
  peakTimestamp?: string | null;
  maxIndoorTemperatureC?: number | null;
  maxIndoorHumidityPercent?: number | null;
  hoursAboveSetpoint?: number | null;
  confidenceScore: number;
  breakdown: CoolingLoadBreakdownItem[];
  warnings: CoolingResultWarning[];
}
```

---

## Comparaison des moteurs

```ts
interface CoolingEngineComparison {
  mercureResultId: number;
  energyPlusResultId: number;
  mercureTotalW: number;
  energyPlusTotalW: number;
  absoluteDifferenceW: number;
  relativeDifferencePercent: number | null;
  status: "acceptable" | "warning" | "critical" | "not_comparable";
  explanations: string[];
  selectedEngine: string;
  decisionRule: string;
}
```

---

## Query hooks

Créer ou compléter :

```ts
useCoolingCalculationJob(jobId)
useCoolingResult(resultId)
useCoolingStudyResults(studyId)
useCoolingResultComparison(resultId)
useCoolingCalculationArtifacts(jobId)
useRerunCoolingCalculation()
```

Query keys :

```ts
coolingKeys.calculation(jobId)
coolingKeys.result(resultId)
coolingKeys.studyResults(studyId)
coolingKeys.resultComparison(resultId)
coolingKeys.calculationArtifacts(jobId)
```

---

## Polling et cache

Pendant un job actif :

- utiliser `refetchInterval` contrôlé ;
- arrêter après `completed`, `failed`, `cancelled` ou `timed_out` ;
- ralentir si la page passe en arrière-plan ;
- éviter plusieurs pollings pour le même job.

Cache recommandé :

- résultat terminé avec `staleTime` élevé ;
- job actif avec `staleTime` faible ;
- historique invalidé après nouveau calcul ;
- comparaison immuable ;
- artefacts chargés à la demande.

---

## Store temporaire

Ajouter uniquement :

```ts
interface CoolingResultsUiState {
  selectedScenarioCode?: string | null;
  selectedBreakdownCategory?: string | null;
  expandedSections: string[];
  selectedResultId?: number | null;
  showTechnicalDetails: boolean;
}
```

Les résultats métier restent dans Odoo.

---

## Accessibilité

Respecter :

- ordre de lecture logique ;
- statut annoncé ;
- graphiques avec tableaux alternatifs ;
- légendes explicites ;
- unités accessibles ;
- navigation clavier ;
- focus après fin de calcul ;
- focus sur l’erreur ;
- badges non dépendants uniquement de la couleur ;
- sections repliables accessibles ;
- explications pour SHR, sensible et latent.

---

## Responsive

### Desktop

```text
Colonne principale : recommandation, scénarios, répartitions
Colonne secondaire : confiance, alertes, recommandations
```

### Tablette

- cartes principales en deux colonnes ;
- graphiques pleine largeur.

### Mobile

- recommandation en premier ;
- cartes verticales ;
- scénarios en accordéons ;
- tableaux convertis en cartes ;
- détails techniques repliés ;
- footer sticky.

---

## Format des nombres

Créer :

```ts
formatCoolingPower()
formatCoolingEnergy()
formatTemperature()
formatPercentage()
formatDuration()
```

Règles :

- kW avec deux décimales au maximum ;
- W sans fausse précision ;
- pourcentages cohérents ;
- valeurs brutes conservées ;
- séparateur décimal français ;
- BTU/h comme valeur complémentaire ;
- fuseau explicite pour le pic.

---

## États de chargement

Prévoir :

- skeleton du résultat ;
- skeleton des graphiques ;
- job en attente ;
- job en cours ;
- comparaison en chargement ;
- artefacts en chargement ;
- historique en chargement ;
- résultat partiel ;
- résultat introuvable.

---

## Gestion des erreurs

Codes possibles :

```text
CALCULATION_JOB_NOT_FOUND
COOLING_RESULT_NOT_FOUND
COOLING_RESULT_NOT_READY
COOLING_RESULT_STALE
COOLING_RESULT_SUPERSEDED
COOLING_RESULT_INVALID
COOLING_COMPARISON_NOT_AVAILABLE
COOLING_ARTIFACT_ACCESS_DENIED
COOLING_CALCULATION_FAILED
COOLING_CALCULATION_TIMEOUT
COOLING_RERUN_NOT_ALLOWED
ENGINEER_REVIEW_REQUIRED
ACCESS_DENIED
```

Pour chaque erreur :

- message clair ;
- cause ;
- action ;
- moteur ;
- scénario si pertinent ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires

Tester :

### Recommandation

- W ;
- kW ;
- BTU/h ;
- marge ;
- palier commercial ;
- moteur retenu.

### Charges

- sensible ;
- latent ;
- total ;
- SHR ;
- total nul.

### Scénarios

- référence ;
- forte chaleur ;
- canicule ;
- scénario dimensionnant.

### Répartition

- catégories ;
- pourcentages ;
- valeur nulle ;
- données manquantes.

### Comparaison

- acceptable ;
- warning ;
- critical ;
- non comparable ;
- signe de l’écart.

### Confort

- température maximale ;
- humidité ;
- dépassements ;
- non évalué.

### Confiance

- élevée ;
- faible ;
- simplifications ;
- avertissements.

### Jobs

- queued ;
- running ;
- completed ;
- failed ;
- timed out ;
- cancelled.

---

## Tests d’intégration

Tester :

1. résultat MERCURE ;
2. résultat EnergyPlus ;
3. résultat BOTH ;
4. suivi d’un job ;
5. arrêt du polling ;
6. recommandation ;
7. comparaison des scénarios ;
8. répartition ;
9. comparaison des moteurs ;
10. avertissements ;
11. recommandations ;
12. détails techniques ;
13. historique ;
14. relance ;
15. résultat obsolète ;
16. lecture seule ;
17. accès aux artefacts ;
18. multi-société.

---

## Tests Playwright

Créer au minimum :

1. résultat MERCURE terminé ;
2. résultat EnergyPlus terminé ;
3. calcul BOTH cohérent ;
4. écart critique ;
5. EnergyPlus échoué avec fallback MERCURE ;
6. job en cours puis terminé ;
7. canicule avec dépassement ;
8. résultat obsolète ;
9. création d’une révision ;
10. utilisateur sans accès aux artefacts.

---

## Mock API

Créer des mocks pour :

- job queued ;
- job running ;
- job completed ;
- job failed ;
- job timed out ;
- résultat MERCURE ;
- résultat EnergyPlus ;
- résultat BOTH ;
- comparaison acceptable ;
- comparaison warning ;
- comparaison critical ;
- forte charge latente ;
- faible confiance ;
- canicule non maîtrisée ;
- artefacts protégés ;
- historique multi-versions ;
- résultat obsolète.

Les mocks doivent respecter l’OpenAPI réel.

---

## Composants à créer ou compléter

```text
CoolingResultsPage
ResultsHeader
CalculationStatusBanner
CalculationProgressCard
CalculationFailurePanel
MainRecommendationCard
SelectedEngineBadge
GoverningScenarioCard
LoadSummaryCards
SensibleHeatRatioCard
ScenarioComparisonSection
ScenarioResultCard
ScenarioComparisonTable
ScenarioLoadChart
LoadBreakdownSection
LoadBreakdownChart
LoadBreakdownTable
MainLoadDriversCard
MercureEnergyPlusComparison
ComparisonStatusBadge
ResultDifferenceExplanation
ComfortPerformanceSection
ComfortStatusBadge
IndoorTemperatureChart
IndoorHumidityChart
PeakPeriodCard
AnnualCoolingEnergyCard
ResultConfidencePanel
CalculationAssumptionsPanel
ResultWarningsPanel
ResultWarningCard
OptimizationRecommendations
OptimizationRecommendationCard
TechnicalDetailsSection
CalculationTracePanel
SimulationArtifactsPanel
CalculationHistorySection
CalculationHistoryTable
ResultVersionComparison
ResultsActionFooter
```

---

## Documentation

Créer :

```text
docs/cooling_results_screen.md
docs/cooling_results_view_model.md
docs/cooling_results_units.md
docs/cooling_results_accessibility.md
docs/cooling_results_error_states.md
docs/cooling_results_mercure_energyplus.md
docs/cooling_results_recommendations.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

---

## Critères d’acceptation

Le lot est accepté si :

- la route fonctionne ;
- les statuts de job sont gérés ;
- la progression est affichée ;
- les erreurs sont affichées ;
- le polling s’arrête ;
- la puissance recommandée est affichée ;
- W, kW et BTU/h sont affichés ;
- la charge brute est distinguée de la marge ;
- la capacité thermique est distinguée de la consommation électrique ;
- le scénario dimensionnant est affiché ;
- le moteur retenu est affiché ;
- sensible, latent, total et SHR sont affichés ;
- les scénarios sont comparés ;
- la répartition des charges est affichée ;
- les contributions principales sont affichées ;
- la comparaison MERCURE/EnergyPlus fonctionne ;
- les écarts et leurs causes sont affichés ;
- les écarts critiques sont signalés ;
- le fallback MERCURE est géré ;
- les températures et humidités sont affichées ;
- les dépassements de confort sont affichés ;
- la résilience canicule est affichée ;
- la confiance est affichée ;
- les hypothèses sont affichées ;
- les avertissements sont affichés ;
- les recommandations sont affichées ;
- les détails techniques sont accessibles ;
- les artefacts sont protégés ;
- l’historique est affiché ;
- les résultats obsolètes sont signalés ;
- les résultats restent en lecture seule ;
- la relance crée un nouveau job ;
- la révision fonctionne ;
- le frontend ne recalcule aucune charge ;
- les graphiques ont une alternative accessible ;
- le responsive fonctionne ;
- les tests passent ;
- TypeScript strict passe ;
- le lint passe ;
- le build passe ;
- le multi-société est respecté ;
- les permissions sont respectées ;
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
- polling ;
- feature flags.

### Résultat principal

- charge brute ;
- marge ;
- capacité recommandée ;
- palier commercial ;
- moteur ;
- scénario.

### Charges

- sensible ;
- latent ;
- total ;
- SHR ;
- répartition ;
- contributions principales.

### Scénarios

- valeurs ;
- comparaison ;
- scénario dimensionnant ;
- confort ;
- canicule.

### Comparaison des moteurs

- MERCURE ;
- EnergyPlus ;
- écarts ;
- seuils ;
- explications ;
- décision finale.

### Confiance et alertes

- score ;
- facteurs ;
- hypothèses ;
- avertissements ;
- restrictions.

### Recommandations

- règles ;
- impacts ;
- actions ;
- révision ;
- what-if.

### Historique

- versions ;
- résultat actif ;
- obsolescence ;
- comparaison de versions.

### API

Pour chaque appel :

- endpoint ;
- payload ;
- réponse ;
- erreurs ;
- permissions ;
- cache ;
- polling.

### Tests

- commandes ;
- résultats ;
- couverture ;
- tests non exécutés ;
- raisons.

### Performance

- taille des payloads ;
- nombre de points graphiques ;
- re-renders ;
- polling ;
- bundle ;
- limites.

### Accessibilité

- graphiques ;
- tableaux ;
- focus ;
- statuts ;
- unités ;
- clavier.

### Sécurité

- permissions ;
- artefacts ;
- liens temporaires ;
- logs ;
- données techniques ;
- multi-société.

### Patch

- diff ;
- patch réintégrable ;
- instructions ;
- migration ;
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
8. vérifier les statuts ;
9. vérifier le polling ;
10. vérifier les erreurs ;
11. vérifier la recommandation ;
12. vérifier W, kW et BTU/h ;
13. vérifier la marge ;
14. vérifier le scénario ;
15. vérifier le moteur ;
16. vérifier sensible, latent, total et SHR ;
17. vérifier les scénarios ;
18. vérifier les répartitions ;
19. vérifier les contributions ;
20. vérifier la comparaison MERCURE ;
21. vérifier la comparaison EnergyPlus ;
22. vérifier les écarts ;
23. vérifier les explications ;
24. vérifier le fallback ;
25. vérifier le confort ;
26. vérifier la température ;
27. vérifier l’humidité ;
28. vérifier les dépassements ;
29. vérifier la canicule ;
30. vérifier la confiance ;
31. vérifier les hypothèses ;
32. vérifier les avertissements ;
33. vérifier les recommandations ;
34. vérifier les détails techniques ;
35. vérifier les traces ;
36. vérifier les artefacts ;
37. vérifier l’historique ;
38. vérifier les résultats obsolètes ;
39. vérifier la relance ;
40. vérifier la révision ;
41. vérifier l’accessibilité ;
42. vérifier le responsive ;
43. vérifier les permissions ;
44. vérifier le multi-société ;
45. vérifier l’absence de secrets ;
46. vérifier qu’aucun résultat historique n’a été modifié ;
47. vérifier qu’aucun fichier n’a été supprimé ;
48. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente :

- le suivi des calculs ;
- l’affichage MERCURE ;
- l’affichage EnergyPlus ;
- la recommandation de puissance ;
- la comparaison des scénarios ;
- la comparaison des moteurs ;
- l’analyse du confort ;
- la confiance ;
- les avertissements ;
- les recommandations d’optimisation ;
- l’historique.

Il ne finalise pas encore :

- le catalogue commercial de climatiseurs ;
- la sélection précise d’un produit ;
- le calcul de consommation électrique d’un produit ;
- le calcul économique complet ;
- le devis Odoo ;
- le rapport PDF final.

Il doit fournir un résultat complet, compréhensible, explicable et exploitable pour guider la future sélection d’un système de refroidissement.
