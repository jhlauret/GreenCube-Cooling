# GC-COOLING-07 — Écran Localisation et contexte climatique

## 1. Objet

Ce document définit l’implémentation complète de l’écran :

```text
1 — Localisation et contexte climatique
```

Cet écran doit permettre à l’utilisateur de :

- rechercher une adresse ou un lieu ;
- utiliser sa position actuelle ;
- saisir des coordonnées manuelles ;
- sélectionner un résultat géographique ;
- vérifier la position sur une carte ;
- déplacer le marqueur si nécessaire ;
- confirmer ou corriger l’altitude ;
- consulter le fuseau horaire ;
- choisir ou corriger le type d’environnement ;
- consulter la provenance et le score de confiance ;
- confirmer la localisation dans Odoo ;
- déclencher l’analyse climatique ;
- visualiser les scénarios climatiques ;
- passer à l’étape suivante.

Odoo Community 18 reste la source de vérité.

---

## 2. Stack attendue

Le lot suppose disponibles :

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

Le socle GC-COOLING-06 doit normalement fournir :

- le layout ;
- le stepper ;
- le store ;
- le client API ;
- les composants partagés ;
- les guards ;
- les hooks génériques ;
- la gestion des permissions ;
- les statuts d’étude.

---

## 3. Vérifications préalables

Avant toute modification :

1. inspecter le socle frontend ;
2. vérifier les routes ;
3. vérifier le layout ;
4. vérifier le stepper ;
5. vérifier le store Zustand ;
6. vérifier TanStack Query ;
7. vérifier le client API ;
8. vérifier les composants partagés ;
9. vérifier les contrats réels du géocodage ;
10. vérifier le contrat du service climatique ;
11. vérifier la bibliothèque cartographique existante ;
12. vérifier les licences des fonds de carte ;
13. exécuter :
   - lint ;
   - TypeScript ;
   - tests ;
   - build ;
14. ne supprimer aucun composant ;
15. ne remplacer aucune bibliothèque existante sans justification.

Le rapport préalable doit contenir :

- composants réutilisés ;
- endpoints ;
- schémas ;
- bibliothèque cartographique ;
- fichiers à créer ;
- fichiers à modifier ;
- risques ;
- limites ;
- écarts entre API et frontend.

---

## 4. Route

Route principale :

```text
/cooling/studies/:studyId/location
```

Prévoir éventuellement une redirection depuis :

```text
/cooling/location
```

Guards recommandés :

```text
StudyRequiredGuard
StudyPermissionGuard
StudyEditableGuard
```

Pour une étude calculée ou validée :

- afficher en lecture seule ;
- proposer une révision si autorisée ;
- ne pas modifier directement la localisation.

---

## 5. Structure de la page

Créer :

```tsx
<CoolingLocationPage />
```

Structure recommandée :

```text
CoolingLayout
├── Introduction
├── SearchLocationCard
├── SearchResults
├── LocationMapCard
├── ConfirmedLocationCard
├── AltitudeAndEnvironmentCard
├── ClimateContextCard
├── WarningsAndConfidence
└── CoolingFooter
```

---

## 6. Texte introductif

Texte recommandé :

```text
Indiquez l’emplacement du GreenCube afin d’obtenir les conditions climatiques locales, l’altitude et les scénarios de chaleur nécessaires au dimensionnement du refroidissement.
```

L’utilisateur doit comprendre :

- pourquoi la localisation est nécessaire ;
- que l’altitude influence le climat ;
- que les coordonnées alimentent l’analyse climatique ;
- que la localisation doit être confirmée avant le calcul.

---

## 7. Modes de saisie

Prévoir trois modes :

```text
address
browser_location
manual_coordinates
```

Labels :

```text
Recherche par adresse
Position actuelle
Coordonnées manuelles
```

Créer :

```tsx
<LocationInputModeSelector />
```

Le mode actif doit être visible et accessible.

---

## 8. Recherche par adresse

Créer :

```tsx
<LocationSearchForm />
```

Champs possibles :

- adresse ou lieu ;
- code postal ;
- ville ;
- pays.

Exemples :

```text
Mission, Anniviers, Suisse
137 rue d’Alésia, Paris
```

Validation Zod :

- chaîne non vide ;
- longueur maximale ;
- absence de caractères de contrôle ;
- code pays valide ;
- limite de résultats valide.

Déclenchement recommandé :

- bouton Rechercher ;
- touche Entrée ;
- debounce uniquement si autocomplétion.

Ne pas appeler l’API à chaque frappe sans contrôle.

---

## 9. Hook de géocodage

Créer :

```ts
useGeocodeLocation()
```

Endpoint :

```text
POST /api/v1/greencube/cooling/geocode
```

Payload possible :

```json
{
  "address": "Mission",
  "city": "Anniviers",
  "country_code": "CH",
  "limit": 5
}
```

Le hook doit :

- normaliser les erreurs ;
- annuler les recherches obsolètes ;
- gérer le loading ;
- conserver le request ID ;
- retourner les candidats ;
- ne pas modifier l’étude.

---

## 10. Résultats de recherche

Créer :

```tsx
<LocationSearchResults />
<LocationSearchResultCard />
```

Afficher pour chaque résultat :

- nom complet ;
- commune ;
- région ;
- pays ;
- code postal ;
- précision ;
- score de confiance ;
- provenance ;
- bouton Sélectionner.

Ne pas sélectionner automatiquement un résultat ambigu.

Le résultat sélectionné doit :

- être visuellement distinct ;
- déplacer la carte ;
- charger altitude et fuseau ;
- charger l’environnement suggéré ;
- rester non confirmé jusqu’à l’action utilisateur.

---

## 11. Position actuelle

Créer :

```tsx
<UseCurrentLocationButton />
```

Utiliser :

```text
navigator.geolocation
```

Règles :

- appel uniquement après clic ;
- jamais automatiquement au chargement ;
- conserver latitude, longitude, précision et timestamp ;
- ne pas faire confiance à l’altitude navigateur ;
- appeler ensuite le géocodage inverse.

Gérer :

- permission accordée ;
- permission refusée ;
- position indisponible ;
- timeout ;
- précision faible ;
- navigateur incompatible.

---

## 12. Coordonnées manuelles

Créer :

```tsx
<ManualCoordinatesForm />
```

Champs :

- latitude ;
- longitude.

Validation :

```text
latitude : -90 à 90
longitude : -180 à 180
```

Prévoir :

- point ou virgule décimale ;
- normalisation ;
- messages d’erreur ;
- géocodage inverse après validation.

Ne pas sauvegarder directement sans validation backend.

---

## 13. Géocodage inverse

Endpoint :

```text
POST /api/v1/greencube/cooling/reverse-geocode
```

ou endpoint unifié existant.

Après réception des coordonnées :

- déterminer l’adresse ;
- déterminer l’altitude ;
- déterminer le fuseau ;
- déterminer l’environnement ;
- calculer la confiance ;
- afficher la provenance.

---

## 14. Carte

Utiliser la bibliothèque existante.

Si aucune bibliothèque n’existe, privilégier :

```text
Leaflet
React Leaflet
```

Créer :

```tsx
<LocationMap />
```

Fonctions minimales :

- point sélectionné ;
- centrage ;
- zoom adapté ;
- marqueur ;
- adresse ;
- déplacement du marqueur si modifiable.

Lors du déplacement :

1. mettre à jour les coordonnées temporaires ;
2. rendre la localisation non confirmée ;
3. lancer le géocodage inverse ;
4. recalculer altitude et fuseau ;
5. recalculer l’environnement ;
6. ne pas sauvegarder avant confirmation.

La page doit rester utilisable sans carte.

---

## 15. Fonds de carte

Documenter :

- fournisseur ;
- licence ;
- attribution ;
- limites ;
- politique de cache ;
- disponibilité.

L’attribution obligatoire doit rester visible.

Ne pas exposer une clé cartographique sans validation.

---

## 16. Résumé de localisation

Créer :

```tsx
<ConfirmedLocationSummary />
```

Afficher :

- adresse normalisée ;
- latitude ;
- longitude ;
- altitude ;
- fuseau ;
- commune ;
- région ;
- pays ;
- précision ;
- fournisseur ;
- date ;
- score de confiance.

Exemple :

```text
Mission, Anniviers, Valais, Suisse
46.226300, 7.123100
Altitude : 1 200 m
Fuseau : Europe/Zurich
Précision : localité
Confiance : 89 %
```

---

## 17. Altitude

Créer :

```tsx
<AltitudeField />
```

Afficher :

- altitude fournisseur ;
- source ;
- confiance ;
- résolution ;
- avertissement si absente.

Correction manuelle :

- explicite ;
- validée ;
- provenance `user_confirmed` ;
- valeur fournisseur conservée ;
- différence visible.

Plage :

```text
-500 à 9000 m
```

---

## 18. Fuseau horaire

Afficher un fuseau IANA :

```text
Europe/Paris
Europe/Zurich
Europe/Lisbon
```

Ne pas afficher uniquement un offset UTC.

Le fuseau doit rester en lecture seule sauf exception.

En cas d’échec :

- ne pas inventer de valeur ;
- afficher une erreur ;
- empêcher le climat si nécessaire.

---

## 19. Type d’environnement

Créer :

```tsx
<EnvironmentTypeSelector />
```

Valeurs :

```text
dense_urban
suburban
rural
mountain
coastal
industrial
```

Labels :

```text
Urbain dense
Périurbain
Rural
Montagne
Littoral
Industriel
```

Afficher :

- suggestion backend ;
- confiance ;
- raisons ;
- provenance.

L’utilisateur peut modifier la suggestion.

Conserver :

- suggestion initiale ;
- valeur retenue ;
- date ;
- utilisateur ;
- provenance.

---

## 20. Provenance des données

Utiliser :

```tsx
<DataSourceBadge />
```

Sources :

```text
api
browser
user_confirmed
manual
cache
stale_cache
estimated_reference
```

Afficher la provenance pour :

- adresse ;
- coordonnées ;
- altitude ;
- fuseau ;
- environnement ;
- climat.

---

## 21. Score de confiance

Créer :

```tsx
<LocationConfidencePanel />
```

Afficher :

- score global ;
- détail par composante ;
- avertissements ;
- actions d’amélioration.

Exemple :

```text
Confiance globale : 89 %

Adresse : 95 %
Coordonnées : 94 %
Altitude : 88 %
Fuseau : 100 %
Environnement : 82 %
```

Ce score ne doit pas être présenté comme une garantie.

---

## 22. Confirmation de localisation

Bouton principal :

```text
Confirmer cette localisation
```

Endpoint :

```text
POST /api/v1/greencube/cooling/studies/<id>/confirm-location
```

Payload :

```json
{
  "result_id": "provider-result-id",
  "normalized_result": {},
  "selected_environment_type": "mountain",
  "manual_altitude_m": null,
  "version": "server-version"
}
```

Après succès :

- mettre à jour l’étude ;
- mettre à jour le store ;
- invalider la query étude ;
- afficher Enregistré ;
- proposer ou déclencher le climat ;
- permettre de continuer.

En cas de conflit :

- ne pas écraser ;
- afficher un dialogue ;
- recharger l’étude.

---

## 23. Invalidation

Si la localisation change alors que l’étude possède déjà :

- un contexte climatique ;
- un calcul ;
- un résultat ;

afficher :

```text
La modification de la localisation rendra les données climatiques et le résultat actuels obsolètes.
```

Pour une étude validée :

- interdire la modification ;
- proposer une révision.

---

## 24. Contexte climatique

Créer :

```tsx
<ClimateContextCard />
```

États :

```text
Contexte climatique non récupéré
Contexte climatique disponible
```

Bouton :

```text
Analyser le climat local
```

Endpoint :

```text
POST /api/v1/greencube/cooling/studies/<id>/climate-context
```

Payload recommandé :

```json
{
  "force_refresh": false,
  "analysis": {
    "include_baseline": true,
    "include_13_years": true,
    "include_3_years": true,
    "include_12_months": true,
    "include_9_months": true,
    "include_3_summers": true,
    "include_current_summer": true
  }
}
```

---

## 25. Hooks climatiques

Créer :

```ts
useCoolingClimateContext(studyId)
useRequestCoolingClimateContext()
```

Gérer :

```text
idle
pending
success
partial
stale
failed
```

Prévoir :

- polling si nécessaire ;
- annulation ;
- timeout ;
- reprise ;
- cache.

---

## 26. Progression climatique

Créer :

```tsx
<ClimateAnalysisProgress />
```

Étapes possibles :

```text
Préparation de la période
Récupération des données
Contrôle qualité
Analyse des extrêmes
Construction des scénarios
Finalisation
```

Ne pas simuler une progression si le backend ne fournit aucun état réel.

---

## 27. Synthèse climatique

Afficher :

- période analysée ;
- fournisseur ;
- qualité ;
- température de référence ;
- température forte chaleur ;
- température canicule prolongée ;
- minimum nocturne critique ;
- jours ou heures très chauds ;
- séquence maximale ;
- signal récent ;
- date ;
- cache utilisé.

Exemple :

```text
Période analysée : 2013–2026
Qualité des données : 94 %

Été de référence : 31,8 °C
Forte chaleur : 36,2 °C
Canicule prolongée : 40,1 °C
Minimum nocturne critique : 25,2 °C

Signal récent : fort
```

---

## 28. Scénarios climatiques

Créer :

```tsx
<ClimateScenarioCards />
```

Cartes :

```text
Été de référence
Forte chaleur
Canicule prolongée
```

Afficher :

- température extérieure ;
- minimum nocturne ;
- humidité ;
- rayonnement ;
- vent ;
- durée ;
- confiance ;
- provenance.

Prévoir :

```text
Voir les détails climatiques
```

---

## 29. Signal climatique récent

Créer :

```tsx
<RecentClimateSignal />
```

Niveaux :

```text
Faible
Modéré
Fort
Très fort
```

Afficher :

- niveau ;
- score ;
- anomalies principales ;
- avertissement méthodologique.

Texte recommandé :

```text
Le signal récent complète l’historique local. Il ne constitue pas à lui seul une projection climatique à long terme.
```

---

## 30. Données partielles et anciennes

### `partial`

- afficher les données disponibles ;
- expliquer les données manquantes ;
- réduire la confiance ;
- permettre de continuer si autorisé.

### `stale`

- afficher la date ;
- indiquer l’usage d’un ancien cache ;
- proposer un rafraîchissement ;
- ne pas masquer l’état.

---

## 31. Rafraîchissement

Bouton :

```text
Actualiser les données climatiques
```

Payload :

```json
{
  "force_refresh": true
}
```

Respecter le rate limiting backend.

---

## 32. Schéma Zod

Exemple :

```ts
const locationSchema = z.object({
  resultId: z.string().min(1),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  altitudeM: z.number().min(-500).max(9000).nullable(),
  timezone: z.string().min(1),
  environmentType: z.enum([
    "dense_urban",
    "suburban",
    "rural",
    "mountain",
    "coastal",
    "industrial",
  ]),
  locationConfirmed: z.literal(true),
});
```

Adapter au contrat réel.

---

## 33. Store local

Ajouter uniquement un draft temporaire :

```ts
interface CoolingLocationDraft {
  inputMode: "address" | "browser_location" | "manual_coordinates";
  searchQuery?: string;
  selectedResultId?: string;
  selectedCandidate?: NormalizedLocationCandidate;
  manualAltitudeM?: number | null;
  selectedEnvironmentType?: EnvironmentType;
  hasUnconfirmedChanges: boolean;
}
```

Après confirmation :

- la version serveur devient prioritaire ;
- nettoyer le draft ;
- conserver uniquement l’état d’interface nécessaire.

---

## 34. Autosave

La recherche ne doit pas sauvegarder automatiquement l’étude.

La confirmation doit rester explicite.

L’autosave peut conserver seulement :

- le mode de saisie ;
- la requête ;
- le candidat temporaire ;
- des données locales non sensibles.

---

## 35. Accessibilité

Exigences :

- labels associés ;
- résultats navigables au clavier ;
- annonce du nombre de résultats ;
- focus sur les erreurs ;
- alternative textuelle à la carte ;
- aria-live ;
- boutons explicites ;
- sélection possible sans carte.

---

## 36. Responsive

### Desktop

```text
Colonne gauche : recherche et résultats
Colonne droite : carte
Sous-section : altitude, environnement et climat
```

### Tablette

- deux colonnes compactes ;
- ou carte sous la recherche.

### Mobile

- recherche ;
- résultats ;
- carte ;
- confirmation ;
- climat ;
- footer sticky.

---

## 37. États de chargement

Prévoir des skeletons pour :

- résultats ;
- carte ;
- altitude ;
- environnement ;
- climat ;
- scénarios.

Ne pas utiliser un spinner global unique.

---

## 38. Gestion des erreurs

Codes à traiter :

```text
VALIDATION_ERROR
GEOCODING_NO_RESULT
GEOCODING_AMBIGUOUS
GEOLOCATION_PERMISSION_DENIED
GEOLOCATION_UNAVAILABLE
GEOLOCATION_TIMEOUT
ALTITUDE_UNAVAILABLE
TIMEZONE_UNAVAILABLE
CLIMATE_PROVIDER_UNAVAILABLE
CLIMATE_DATA_PARTIAL
CLIMATE_DATA_STALE
RATE_LIMIT_EXCEEDED
CONFLICT
ACCESS_DENIED
```

Pour chaque erreur :

- message compréhensible ;
- action possible ;
- request ID ;
- aucune trace brute.

---

## 39. Composants à créer ou compléter

```text
CoolingLocationPage
LocationInputModeSelector
LocationSearchForm
LocationSearchResults
LocationSearchResultCard
UseCurrentLocationButton
ManualCoordinatesForm
LocationMap
ConfirmedLocationSummary
AltitudeField
EnvironmentTypeSelector
LocationConfidencePanel
ClimateContextCard
ClimateAnalysisProgress
ClimateScenarioCards
RecentClimateSignal
```

---

## 40. Tests unitaires

Tester :

### Recherche

- saisie valide ;
- saisie vide ;
- loading ;
- aucun résultat ;
- résultats multiples ;
- sélection.

### Position actuelle

- autorisation ;
- refus ;
- timeout ;
- précision faible ;
- navigateur incompatible.

### Coordonnées

- latitude valide ;
- longitude valide ;
- valeurs invalides ;
- virgule décimale.

### Carte

- marqueur ;
- déplacement ;
- fallback.

### Altitude

- valeur API ;
- correction ;
- valeur absente ;
- valeur hors plage.

### Environnement

- suggestion ;
- modification ;
- provenance.

### Confirmation

- succès ;
- conflit ;
- erreur ;
- étude verrouillée.

### Climat

- disponible ;
- partiel ;
- stale ;
- erreur ;
- rafraîchissement.

---

## 41. Tests d’intégration

Tester :

1. recherche d’adresse ;
2. sélection ;
3. mise à jour de la carte ;
4. altitude ;
5. environnement ;
6. confirmation ;
7. sauvegarde Odoo ;
8. climat ;
9. scénarios ;
10. changement de localisation ;
11. invalidation ;
12. conflit ;
13. étude validée ;
14. absence de carte ;
15. fournisseur indisponible.

---

## 42. Tests Playwright

Créer au minimum :

1. adresse précise ;
2. recherche ambiguë ;
3. refus de position ;
4. saisie manuelle ;
5. déplacement du marqueur ;
6. correction d’altitude ;
7. modification de l’environnement ;
8. climat réussi ;
9. climat partiel ;
10. cache ancien ;
11. lecture seule.

---

## 43. Mock API

Créer des mocks pour :

- Paris ;
- Mission en Valais ;
- Porto ;
- résultat ambigu ;
- altitude absente ;
- fuseau absent ;
- environnement montagne ;
- environnement littoral ;
- climat disponible ;
- climat partiel ;
- climat stale ;
- fournisseur indisponible.

Les mocks doivent respecter l’OpenAPI réel.

---

## 44. Documentation

Créer :

```text
docs/cooling_location_screen.md
```

Compléter :

```text
docs/cooling_frontend_api_mapping.md
```

Mapping :

```text
Recherche
→ POST /geocode

Position
→ POST /reverse-geocode

Confirmation
→ POST /studies/<id>/confirm-location

Climat
→ POST /studies/<id>/climate-context

Lecture climat
→ endpoint réel de lecture
```

---

## 45. Critères d’acceptation

Le lot est accepté si :

1. la route fonctionne ;
2. l’étude est chargée ;
3. la recherche fonctionne ;
4. les résultats multiples sont gérés ;
5. la position actuelle fonctionne ;
6. le refus est géré ;
7. les coordonnées manuelles fonctionnent ;
8. le géocodage inverse fonctionne ;
9. la carte affiche le point ;
10. la page fonctionne sans carte ;
11. le déplacement du marqueur fonctionne ;
12. l’altitude est affichée ;
13. l’altitude peut être corrigée ;
14. le fuseau IANA est affiché ;
15. l’environnement est suggéré ;
16. l’environnement peut être modifié ;
17. la provenance est visible ;
18. la confiance est visible ;
19. la confirmation met à jour Odoo ;
20. les conflits sont gérés ;
21. la modification invalide le climat ;
22. le contexte climatique peut être lancé ;
23. les scénarios sont visibles ;
24. les données partielles sont gérées ;
25. les données stale sont identifiées ;
26. les permissions sont respectées ;
27. l’étude validée est en lecture seule ;
28. l’accessibilité est assurée ;
29. le responsive fonctionne ;
30. les tests passent ;
31. TypeScript strict passe ;
32. le lint passe ;
33. le build passe ;
34. aucune clé n’est exposée ;
35. aucun fichier n’est supprimé.

---

## 46. Rapport final attendu

### Architecture

- page ;
- composants ;
- hooks ;
- store ;
- carte ;
- API.

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

### Carte

- bibliothèque ;
- fournisseur ;
- licence ;
- attribution ;
- fallback.

### Accessibilité

- clavier ;
- focus ;
- alternative carte ;
- erreurs ;
- annonces.

### Tests

- commandes ;
- résultats ;
- couverture ;
- tests non exécutés ;
- raisons.

### Performance

- requêtes ;
- carte ;
- bundle ;
- cache ;
- limitations.

### Sécurité

- géolocalisation ;
- secrets ;
- URLs ;
- stockage local ;
- logs.

### Patch

- diff ;
- patch réintégrable ;
- instructions ;
- rollback.

---

## 47. Contrôle final

Avant conclusion :

1. lancer le lint ;
2. lancer TypeScript strict ;
3. lancer les tests unitaires ;
4. lancer les tests d’intégration ;
5. lancer Playwright ;
6. construire le frontend ;
7. vérifier la recherche ;
8. vérifier les résultats multiples ;
9. vérifier la position actuelle ;
10. vérifier le refus ;
11. vérifier les coordonnées manuelles ;
12. vérifier le géocodage inverse ;
13. vérifier la carte ;
14. vérifier le fallback sans carte ;
15. vérifier l’altitude ;
16. vérifier l’environnement ;
17. vérifier la confirmation ;
18. vérifier l’invalidation ;
19. vérifier le climat ;
20. vérifier les scénarios ;
21. vérifier `partial` ;
22. vérifier `stale` ;
23. vérifier les permissions ;
24. vérifier l’accessibilité ;
25. vérifier le responsive ;
26. vérifier l’absence de secrets ;
27. vérifier qu’aucun fichier n’a été supprimé ;
28. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## 48. Limites du lot

Ce lot implémente uniquement l’écran Localisation et contexte climatique.

Il ne finalise pas :

- la sélection du modèle GreenCube ;
- la géométrie détaillée ;
- les vitrages ;
- l’occupation ;
- les équipements ;
- la ventilation ;
- le solver ;
- le résultat final.

Il doit fournir une localisation confirmée et un contexte climatique suffisamment fiable pour permettre l’étape suivante.
