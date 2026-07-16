# GC-COOLING-10 — Usage, occupation et profils horaires

## Objectif

Implémenter l’écran :

```text
4 — Usage, occupation et profils horaires
```

L’écran doit permettre de :

- définir l’usage principal du GreenCube ;
- sélectionner un profil d’usage depuis Odoo ;
- saisir le nombre habituel d’occupants ;
- saisir le nombre maximal d’occupants ;
- définir les jours et horaires d’occupation ;
- définir les périodes d’inoccupation ;
- indiquer une occupation nocturne ;
- sélectionner le niveau d’activité ;
- afficher les gains sensibles et latents ;
- gérer les usages intermittents ou exceptionnels ;
- afficher la provenance et le score de confiance ;
- sauvegarder les données dans Odoo ;
- fournir un format exploitable par le solver rapide ;
- fournir un format exploitable par Honeybee/EnergyPlus ;
- passer à l’étape Équipements et apports internes.

Odoo Community 18 reste la source de vérité.

Le frontend ne doit fournir qu’une prévisualisation. Les calculs définitifs doivent être recalculés côté backend.

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
- une orientation définie ;
- des vitrages et protections solaires ;
- les permissions et statuts d’étude ;
- la sauvegarde ;
- le verrouillage optimiste ;
- la gestion des révisions ;
- la provenance ;
- les scores de confiance.

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
- inspecter les modèles Odoo liés aux usages, calendriers et profils ;
- vérifier les profils horaires existants ;
- vérifier les unités des gains humains ;
- vérifier les niveaux d’activité ;
- vérifier le mapping Honeybee/EnergyPlus ;
- vérifier les règles de validation et d’invalidation ;
- vérifier les endpoints existants ;
- exécuter le lint ;
- exécuter TypeScript ;
- exécuter les tests ;
- exécuter le build ;
- ne supprimer aucun composant ;
- ne coder aucun profil d’usage en dur.

---

## Route

```text
/cooling/studies/:studyId/usage
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
<CoolingUsagePage />
```

Structure recommandée :

```text
CoolingLayout
├── Introduction
├── UsageProfileSelector
├── OccupancySummaryCard
├── OccupantCountCard
├── ActivityLevelCard
├── WeeklyScheduleEditor
├── SeasonalScheduleCard
├── NightOccupancyCard
├── ExceptionalUsageCard
├── HumanHeatGainPreview
├── ProvenanceAndConfidence
├── ValidationWarnings
└── CoolingFooter
```

---

## Profil d’usage

Créer :

```tsx
<UsageProfileSelector />
<UsageProfileCard />
```

Les profils doivent venir d’Odoo.

Exemples possibles, non codés en dur :

```text
studio_housing
office
meeting_room
classroom
shop
medical_room
technical_room
server_room
workshop
temporary_accommodation
custom
```

Afficher :

- nom ;
- description ;
- usage principal ;
- occupants indicatifs ;
- horaires indicatifs ;
- activité par défaut ;
- occupation nocturne ;
- source ;
- version.

---

## Chargement des profils

Créer :

```ts
useCoolingUsageProfiles()
```

Endpoint possible :

```text
GET /api/v1/greencube/cooling/usage-profiles
```

La réponse doit idéalement contenir :

- identifiant ;
- code ;
- nom ;
- description ;
- catégorie ;
- profil d’occupation ;
- activité par défaut ;
- gains sensibles ;
- gains latents ;
- jours de présence ;
- horaires ;
- occupation nocturne ;
- limites ;
- statut ;
- version ;
- provenance.

---

## Modes de configuration

Prévoir :

```text
profile
custom
```

Créer :

```tsx
<UsageConfigurationModeSelector />
```

### Mode profil

- charger les valeurs depuis Odoo ;
- préremplir les horaires ;
- préremplir l’activité ;
- préremplir les gains ;
- permettre les personnalisations autorisées ;
- conserver l’identifiant et la version.

### Mode personnalisé

- permettre la saisie complète ;
- demander davantage de données ;
- afficher les hypothèses ;
- réduire la confiance si les valeurs sont estimées.

### Changement de mode

- demander confirmation ;
- conserver éventuellement le brouillon ;
- ne pas perdre les horaires ;
- recalculer la prévisualisation ;
- invalider les résultats dépendants si nécessaire.

---

## Nombre d’occupants

Créer :

```tsx
<OccupantCountCard />
```

Champs :

```text
usual_occupants
maximum_occupants
minimum_occupants
design_occupants
```

Pour le MVP :

- nombre habituel ;
- nombre maximum.

Validation initiale :

```text
habituel : 0 à 500
maximum : 0 à 1000
```

Vérifier :

- entier ;
- valeur positive ou nulle ;
- maximum supérieur ou égal à l’habituel ;
- cohérence avec la surface ;
- cohérence avec le profil.

---

## Densité d’occupation

Prévisualisation :

```text
occupancy_density =
occupants / surface_utile
```

Afficher en :

```text
personnes/m²
```

ou :

```text
m²/personne
```

Ne pas présenter les seuils comme réglementaires sans source explicite.

---

## Occupation habituelle et maximale

Distinguer :

```text
occupation habituelle
occupation maximale ponctuelle
```

Le solver peut utiliser :

- l’habituelle pour l’énergie ;
- la maximale pour le pic ;
- un scénario spécifique selon le backend.

---

## Niveau d’activité

Créer :

```tsx
<ActivityLevelCard />
<ActivityLevelSelector />
```

Niveaux possibles :

```text
sleeping
seated_resting
seated_work
standing_light
light_activity
moderate_activity
heavy_activity
custom
```

Labels :

```text
Sommeil
Assis au repos
Travail assis
Debout, activité légère
Activité légère
Activité modérée
Activité soutenue
Personnalisé
```

Les valeurs doivent venir d’Odoo ou d’un référentiel backend.

---

## Valeurs métaboliques

Le backend peut fournir :

- `met` ;
- puissance totale par personne ;
- gain sensible ;
- gain latent ;
- fraction sensible ;
- fraction latente.

Exemple :

```text
Activité : travail assis
Gain sensible : 75 W/personne
Gain latent : 55 W/personne
```

Ne jamais coder ces valeurs en dur.

---

## Prévisualisation des gains humains

Créer :

```tsx
<HumanHeatGainPreview />
```

Formules indicatives :

```text
gain_sensible_total =
nombre_occupants
× gain_sensible_par_personne

gain_latent_total =
nombre_occupants
× gain_latent_par_personne
```

Afficher séparément :

- sensible ;
- latent ;
- total ;
- nombre d’occupants ;
- activité ;
- source.

Le backend doit recalculer.

---

## Occupation jour et nuit

Pour les usages résidentiels :

- activité de jour ;
- activité de nuit ;
- gains différents ;
- horaires distincts ;
- occupation prolongée.

Prévoir :

```text
day_activity
night_activity
```

---

## Profils multiples

Prévoir une architecture extensible pour :

```text
morning
day
evening
night
```

Pour le MVP, deux segments peuvent suffire :

```text
occupied
unoccupied
```

ou :

```text
day
night
```

---

## Calendrier hebdomadaire

Créer :

```tsx
<WeeklyScheduleEditor />
<SchedulePeriodEditor />
```

Le planning doit permettre de définir :

- jours actifs ;
- heure de début ;
- heure de fin ;
- nombre d’occupants ;
- activité ;
- fraction d’occupation.

Jours :

```text
monday
tuesday
wednesday
thursday
friday
saturday
sunday
```

---

## Format des horaires

Exemple structuré :

```json
{
  "monday": [
    {
      "start": "08:00",
      "end": "12:00",
      "occupancy_fraction": 0.8
    },
    {
      "start": "13:00",
      "end": "18:00",
      "occupancy_fraction": 1.0
    }
  ]
}
```

Ne pas stocker le planning en texte libre.

---

## Éditeur de périodes

Pour chaque période :

- début ;
- fin ;
- fraction d’occupation ;
- activité ;
- nombre d’occupants ;
- commentaire facultatif.

Fonctions :

- ajout ;
- suppression ;
- duplication ;
- copie vers plusieurs jours ;
- réinitialisation depuis le profil.

---

## Validation du planning

Vérifier :

- début antérieur à la fin ;
- absence de chevauchement ;
- fraction entre 0 et 1 ;
- nombre cohérent ;
- au moins une période si l’usage est occupé ;
- gestion du passage de minuit ;
- fuseau local de l’étude.

Créer :

```ts
validateWeeklySchedule()
```

---

## Passage de minuit

Exemple :

```text
22:00 → 06:00
```

Choisir une convention unique :

- période traversante ;
- ou découpage en deux segments.

Le backend doit normaliser.

---

## Occupation nocturne

Créer :

```tsx
<NightOccupancyCard />
```

Champs :

```text
night_occupancy_enabled
night_occupants
night_start_time
night_end_time
night_activity_level
```

Afficher :

```text
L’occupation nocturne influence la capacité du GreenCube à se refroidir pendant les nuits chaudes.
```

---

## Usage saisonnier

Créer :

```tsx
<SeasonalScheduleCard />
```

Modes :

```text
all_year
seasonal
custom_dates
```

Permettre :

- toute l’année ;
- certains mois ;
- saison estivale ;
- périodes fermées ;
- vacances ;
- usage événementiel.

---

## Périodes d’inoccupation

Permettre de représenter :

- vacances ;
- fermeture hebdomadaire ;
- fermeture saisonnière ;
- maintenance ;
- périodes sans occupation.

Pour le MVP :

- mois actifs ;
- jours actifs ;
- horaires hebdomadaires.

---

## Usage exceptionnel

Créer :

```tsx
<ExceptionalUsageCard />
```

Cas :

- réunion ;
- réception ;
- événement ;
- sur-occupation ;
- hébergement exceptionnel.

Champs :

- fréquence ;
- durée ;
- occupants ;
- activité ;
- inclusion dans le dimensionnement.

---

## Scénario de dimensionnement

Prévoir :

```text
usual
maximum
conservative
custom
```

Le backend doit décider du nombre d’occupants retenu pour chaque scénario climatique.

---

## Profils par scénario climatique

Le système doit pouvoir produire :

```text
reference_summer
hot_weather
prolonged_heatwave
```

Pour chaque scénario, le backend peut utiliser :

- occupation habituelle ;
- occupation maximale ;
- occupation nocturne ;
- calendrier spécifique.

---

## Mapping solver rapide

Payload minimal :

```json
{
  "usual_occupants": 4,
  "maximum_occupants": 6,
  "design_occupants": 6,
  "sensible_gain_w_per_person": 75,
  "latent_gain_w_per_person": 55,
  "schedule": {},
  "night_occupancy": {
    "enabled": true,
    "occupants": 2
  }
}
```

Le backend doit construire le payload final.

---

## Mapping Honeybee/EnergyPlus

Le service doit pouvoir produire :

- objet `People` ;
- calendrier d’occupation ;
- activité métabolique ;
- fraction radiante ;
- fraction sensible ;
- calendrier d’activité ;
- densité ou nombre absolu.

Ne pas supposer que Honeybee utilise directement les mêmes unités qu’Odoo.

---

## Nombre absolu ou densité

Documenter le choix entre :

```text
number_of_people
people_per_area
area_per_person
```

La source métier peut rester le nombre absolu.

Le convertisseur Honeybee peut calculer la densité.

---

## Fraction d’occupation

Valeur :

```text
0 à 1
```

Exemples :

```text
0 = absent
0,5 = occupation à 50 %
1 = occupation complète
```

Calcul possible :

```text
design_occupants × occupancy_fraction
```

---

## Provenance

Utiliser :

```tsx
<DataSourceBadge />
```

Sources possibles :

```text
catalog
usage_profile
user_confirmed
measured
estimated_reference
backend_default
missing_fallback
```

Afficher la provenance pour :

- profil ;
- occupants ;
- activité ;
- gains sensibles ;
- gains latents ;
- horaires ;
- occupation nocturne.

---

## Score de confiance

Créer :

```tsx
<UsageConfidencePanel />
```

Composantes possibles :

```text
usage_profile
usual_occupants
maximum_occupants
activity_level
weekly_schedule
night_occupancy
seasonal_schedule
```

Exemple :

```text
Confiance globale : 88 %

Usage : 100 %
Occupation habituelle : 90 %
Occupation maximale : 80 %
Activité : 95 %
Horaires : 85 %
Occupation nocturne : 75 %
```

---

## Données manquantes

Créer :

```tsx
<MissingUsageDataAlert />
```

Exemples :

- nombre maximal absent ;
- activité non définie ;
- horaires incomplets ;
- occupation nocturne inconnue ;
- gain latent absent ;
- profil non versionné.

Pour chaque donnée :

- indiquer si elle est bloquante ;
- proposer une valeur de référence ;
- demander confirmation ;
- conserver la provenance ;
- réduire la confiance.

---

## Résumé d’occupation

Créer :

```tsx
<OccupancySummaryCard />
```

Afficher :

- profil ;
- occupants habituels ;
- occupants maximum ;
- densité ;
- activité principale ;
- horaires ;
- occupation nocturne ;
- gains sensibles ;
- gains latents ;
- statut de complétude.

---

## Prévisualisation journalière

Créer éventuellement :

```tsx
<DailyOccupancyChart />
```

Afficher sur 24 heures :

- fraction d’occupation ;
- nombre de personnes ;
- gains sensibles ;
- gains latents.

Prévoir une alternative tabulaire accessible.

---

## Prévisualisation hebdomadaire

Créer éventuellement :

```tsx
<WeeklyOccupancyHeatmap />
```

Afficher :

- jours ;
- heures ;
- intensité d’occupation.

Cette vue reste complémentaire.

---

## Sauvegarde

Créer :

```ts
useSaveCoolingUsageSection()
```

Endpoint possible :

```text
PATCH /api/v1/greencube/cooling/studies/<id>
```

ou :

```text
PUT /api/v1/greencube/cooling/studies/<id>/usage
```

Payload possible :

```json
{
  "usage_mode": "profile",
  "usage_profile_id": 8,
  "usage_profile_version": "2.1",
  "usual_occupants": 4,
  "maximum_occupants": 6,
  "activity_level_code": "seated_work",
  "weekly_schedule": {
    "monday": [
      {
        "start": "08:00",
        "end": "18:00",
        "occupancy_fraction": 1.0
      }
    ]
  },
  "night_occupancy": {
    "enabled": false,
    "occupants": 0
  },
  "seasonal_schedule": {
    "mode": "all_year"
  },
  "version": "server-version"
}
```

Adapter au contrat réel.

---

## Invalidation

Une modification de l’usage peut invalider :

- apports internes ;
- résultat rapide ;
- simulation EnergyPlus ;
- consommation estimée ;
- capacité recommandée ;
- rapport PDF.

Afficher :

```text
La modification du nombre d’occupants, des horaires ou de l’activité rendra le résultat de refroidissement actuel obsolète.
```

---

## Formulaire React Hook Form

Créer :

```tsx
<UsageOccupationForm />
```

Organisation :

```text
usageMode
usageProfile
usualOccupants
maximumOccupants
activityLevel
weeklySchedule
nightOccupancy
seasonalSchedule
exceptionalUsage
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
const schedulePeriodSchema = z.object({
  start: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  end: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  occupancyFraction: z.number().min(0).max(1),
  occupants: z.number().int().min(0).optional(),
  activityLevelCode: z.string().optional(),
});

const usageSchema = z.object({
  usageMode: z.enum(["profile", "custom"]),
  usageProfileId: z.number().int().positive().nullable(),
  usageProfileVersion: z.string().nullable(),
  usualOccupants: z.number().int().min(0).max(500),
  maximumOccupants: z.number().int().min(0).max(1000),
  activityLevelCode: z.string().min(1),
});
```

Compléter avec le planning et l’occupation nocturne.

---

## Validations croisées

Utiliser `superRefine` pour vérifier :

- maximum supérieur ou égal à l’habituel ;
- planning sans chevauchement ;
- activité présente ;
- occupation nocturne cohérente ;
- nombre nocturne cohérent ;
- horaires valides ;
- profil requis en mode profil ;
- données custom requises ;
- densité non aberrante ;
- période saisonnière cohérente.

---

## Store temporaire

Ajouter seulement :

```ts
interface CoolingUsageDraft {
  usageMode: "profile" | "custom";
  selectedUsageProfileId?: number | null;
  activeScheduleDay?: string;
  hasUnconfirmedChanges: boolean;
}
```

Les données métier complètes restent dans React Hook Form et Odoo.

---

## Autosave

Autosave possible si :

- occupants valides ;
- activité définie ;
- planning valide ;
- aucun changement de mode en attente ;
- aucune exception partielle ;
- aucune invalidation non confirmée.

Ne pas autosauvegarder :

- planning avec chevauchement ;
- période incomplète ;
- nombre maximal incohérent ;
- occupation nocturne partielle ;
- changement de profil non confirmé.

---

## Comparaison profil / saisie

Créer éventuellement :

```tsx
<UsageProfileDifferencePanel />
```

Afficher :

- valeur du profil ;
- valeur modifiée ;
- écart ;
- provenance ;
- impact estimé.

---

## Accessibilité

Respecter :

- cartes utilisables au clavier ;
- planning éditable sans souris ;
- labels ;
- fieldsets ;
- légendes ;
- erreurs associées ;
- focus lors de l’ajout ;
- annonces de recalcul ;
- graphiques avec alternative tabulaire ;
- couleurs non utilisées seules.

---

## Responsive

### Desktop

```text
Colonne gauche : profil, occupants et activité
Colonne droite : planning et résumé
```

### Tablette

- cartes empilées partiellement ;
- planning sur toute la largeur.

### Mobile

- jours en accordéons ;
- périodes en cartes ;
- actions accessibles ;
- graphiques sous le formulaire ;
- footer sticky.

---

## États de chargement

Prévoir :

- skeleton profils ;
- chargement du planning ;
- profil introuvable ;
- version archivée ;
- données partielles ;
- calcul de prévisualisation ;
- erreur de référentiel.

---

## Gestion des erreurs

Codes possibles :

```text
USAGE_PROFILE_NOT_FOUND
USAGE_PROFILE_ARCHIVED
USAGE_PROFILE_VERSION_MISMATCH
INVALID_OCCUPANT_COUNT
INVALID_OCCUPANCY_DENSITY
INVALID_ACTIVITY_LEVEL
INVALID_WEEKLY_SCHEDULE
SCHEDULE_OVERLAP
INVALID_NIGHT_OCCUPANCY
INVALID_SEASONAL_SCHEDULE
MISSING_USAGE_DATA
CONFLICT
INVALID_STATE
ACCESS_DENIED
```

Pour chaque erreur :

- message clair ;
- champ ou période concernée ;
- action ;
- request ID ;
- aucune trace brute.

---

## Tests unitaires

Tester :

### Profils

- chargement ;
- recherche ;
- sélection ;
- profil archivé ;
- version différente.

### Occupants

- habituel ;
- maximum ;
- incohérence ;
- densité ;
- zéro occupant.

### Activité

- sélection ;
- gains ;
- activité nocturne ;
- activité personnalisée.

### Planning

- ajout ;
- suppression ;
- duplication ;
- copie vers plusieurs jours ;
- chevauchement ;
- passage de minuit ;
- fraction d’occupation.

### Occupation nocturne

- activée ;
- désactivée ;
- horaires ;
- occupants ;
- activité.

### Sauvegarde

- succès ;
- conflit ;
- invalidation ;
- lecture seule.

---

## Tests d’intégration

Tester :

1. chargement des profils ;
2. sélection d’un profil ;
3. préremplissage ;
4. modification des occupants ;
5. modification de l’activité ;
6. modification du planning ;
7. occupation nocturne ;
8. usage saisonnier ;
9. prévisualisation des gains ;
10. sauvegarde ;
11. réouverture ;
12. changement de profil ;
13. invalidation ;
14. conflit ;
15. étude validée ;
16. création d’une révision.

---

## Tests Playwright

Créer au minimum :

1. bureau standard ;
2. studio occupé jour et nuit ;
3. salle de réunion avec pics ;
4. local technique sans occupant permanent ;
5. occupation personnalisée avec plusieurs périodes ;
6. planning avec chevauchement ;
7. occupation maximale incohérente ;
8. occupation nocturne incomplète ;
9. changement de profil avec invalidation ;
10. étude validée en lecture seule.

---

## Mock API

Créer des mocks pour :

- bureau standard ;
- studio résidentiel ;
- salle de réunion ;
- commerce ;
- local technique ;
- serveur sans occupation ;
- usage saisonnier ;
- profil archivé ;
- profil sans gains latents ;
- planning incomplet ;
- version plus récente ;
- données partielles.

Les mocks doivent respecter l’OpenAPI réel.

---

## Composants à créer ou compléter

```text
CoolingUsagePage
UsageProfileSelector
UsageProfileCard
UsageConfigurationModeSelector
OccupancySummaryCard
OccupantCountCard
ActivityLevelCard
ActivityLevelSelector
WeeklyScheduleEditor
SchedulePeriodEditor
NightOccupancyCard
SeasonalScheduleCard
ExceptionalUsageCard
HumanHeatGainPreview
DailyOccupancyChart
WeeklyOccupancyHeatmap
UsageProfileDifferencePanel
UsageConfidencePanel
MissingUsageDataAlert
UsageOccupationForm
```

---

## Documentation

Créer :

```text
docs/cooling_usage_occupancy_screen.md
docs/cooling_usage_energyplus_mapping.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

Mapping attendu :

```text
Profils d’usage
→ GET /cooling/usage-profiles

Sauvegarde usage
→ PATCH /studies/<id>
ou endpoint dédié

Révision
→ POST /studies/<id>/revisions
```

Le mapping EnergyPlus doit contenir :

```text
champ Odoo
→ champ frontend
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
- les occupants habituels et maximum peuvent être saisis ;
- les incohérences sont détectées ;
- l’activité peut être sélectionnée ;
- les gains sensibles et latents sont affichés ;
- le planning hebdomadaire fonctionne ;
- les chevauchements sont détectés ;
- le passage de minuit est géré ;
- l’occupation nocturne fonctionne ;
- la saisonnalité fonctionne ;
- les usages exceptionnels sont représentables ;
- le scénario de dimensionnement est identifié ;
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

### Profils

- source ;
- versions ;
- valeurs par défaut ;
- personnalisations.

### Occupation

- nombres ;
- densités ;
- activités ;
- gains.

### Calendriers

- structure ;
- validation ;
- passage de minuit ;
- saisonnalité ;
- exceptions.

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
- planning ;
- re-renders ;
- bundle ;
- limites.

### Sécurité

- permissions ;
- stockage ;
- secrets ;
- logs ;
- données personnelles.

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
8. vérifier les versions ;
9. vérifier les occupants ;
10. vérifier les densités ;
11. vérifier les activités ;
12. vérifier les gains sensibles ;
13. vérifier les gains latents ;
14. vérifier le planning ;
15. vérifier les chevauchements ;
16. vérifier le passage de minuit ;
17. vérifier l’occupation nocturne ;
18. vérifier la saisonnalité ;
19. vérifier les usages exceptionnels ;
20. vérifier la prévisualisation ;
21. vérifier la provenance ;
22. vérifier la confiance ;
23. vérifier les données manquantes ;
24. vérifier la sauvegarde ;
25. vérifier l’invalidation ;
26. vérifier les conflits ;
27. vérifier la lecture seule ;
28. vérifier la révision ;
29. vérifier l’accessibilité ;
30. vérifier le responsive ;
31. vérifier l’absence de secrets ;
32. vérifier qu’aucun fichier n’a été supprimé ;
33. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## Limites du lot

Ce lot implémente uniquement l’écran Usage, occupation et profils horaires.

Il ne finalise pas encore :

- les équipements ;
- l’éclairage ;
- les batteries et onduleurs ;
- la ventilation ;
- l’infiltration ;
- le solver ;
- les résultats.

Il doit fournir un profil d’occupation suffisamment fiable et structuré pour permettre le calcul des gains sensibles et latents.
