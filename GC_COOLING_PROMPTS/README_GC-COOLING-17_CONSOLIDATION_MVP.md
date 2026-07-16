# GC-COOLING-17 — Consolidation finale du MVP, recette, sécurité et livraison

## Objectif

Consolider l’ensemble de GreenCube Cooling en une version MVP :

```text
fonctionnelle
testée
sécurisée
documentée
installable
réversible
observable
maintenable
livrable sur VPS
```

Le lot doit :

- vérifier l’intégration complète de tous les lots ;
- corriger les ruptures de contrat ;
- supprimer les incohérences ;
- finaliser les migrations Odoo ;
- finaliser les droits et règles multi-sociétés ;
- exécuter la recette fonctionnelle ;
- exécuter la recette technique ;
- exécuter les tests de sécurité ;
- finaliser le packaging ;
- finaliser les scripts de déploiement ;
- finaliser les procédures de sauvegarde et de rollback ;
- produire un patch réintégrable ;
- produire la documentation finale ;
- préparer la mise en production.

Odoo Community 18 reste la source de vérité métier.

Aucune réussite de test, installation, sauvegarde, restauration ou déploiement ne doit être déclarée sans exécution réelle et preuve vérifiable.

---

## Périmètre consolidé

Le lot finalise les éléments suivants :

```text
GC-COOLING-06
→ socle frontend et architecture

GC-COOLING-07 à GC-COOLING-12
→ écrans de configuration

GC-COOLING-13
→ vérification et snapshot

GC-COOLING-14
→ moteur MERCURE

GC-COOLING-15
→ Honeybee / EnergyPlus

GC-COOLING-16
→ résultats et recommandation
```

Le parcours cible est :

```text
Création d’une étude
→ localisation et climat
→ modèle GreenCube
→ orientation et vitrages
→ usage et occupation
→ équipements et charges internes
→ ventilation, infiltration et confort
→ vérification
→ snapshot immuable
→ calcul MERCURE
→ simulation EnergyPlus si activée
→ comparaison
→ recommandation de puissance
→ historique et révision
```

---

## Hors périmètre

Ce lot ne finalise pas :

- le catalogue commercial complet de climatiseurs ;
- le devis complet ;
- la facturation ;
- le rapport PDF commercial définitif ;
- l’analyse économique complète ;
- les fonctionnalités futures derrière feature flags.

Aucune nouvelle fonctionnalité métier majeure ne doit être ajoutée.

---

## Priorisation des anomalies

Classer les problèmes selon :

```text
P0 — bloquant sécurité, données ou parcours principal
P1 — bloquant fonctionnel important
P2 — anomalie significative avec contournement
P3 — amélioration non bloquante
```

Le MVP ne peut pas être livré avec :

- un P0 ouvert ;
- un P1 ouvert sur le parcours principal ;
- une migration non testée ;
- une faille critique ou élevée non traitée ;
- une perte de données connue ;
- un secret exposé ;
- un test critique non exécuté sans justification.

---

## Vérifications préalables

Avant toute modification :

- inspecter l’arborescence complète ;
- identifier les modules GreenCube Cooling ;
- identifier les branches, patches et lots appliqués ;
- inspecter les modèles Odoo ;
- inspecter les migrations ;
- inspecter les contrôleurs et endpoints ;
- inspecter le frontend React ;
- inspecter OpenAPI ;
- inspecter les workers ;
- inspecter MERCURE ;
- inspecter Honeybee/EnergyPlus ;
- inspecter les images Docker ;
- inspecter Nginx ou le reverse proxy ;
- inspecter les variables d’environnement ;
- inspecter les scripts de déploiement ;
- inspecter les tests ;
- inspecter les healthchecks ;
- inspecter les logs ;
- inspecter les ACL ;
- inspecter les règles multi-sociétés ;
- inspecter les feature flags ;
- inspecter la rétention ;
- inspecter les sauvegardes ;
- inspecter le rollback ;
- vérifier l’absence de suppressions injustifiées ;
- exécuter les commandes de diagnostic ;
- établir un état initial avant modification.

---

## Matrice de traçabilité

Créer :

```text
docs/cooling_requirements_traceability_matrix.md
```

Pour chaque exigence de GC-COOLING-06 à GC-COOLING-16, indiquer :

```text
identifiant
lot source
exigence
implémentation
fichier
endpoint
test
statut
écart
justification
```

Statuts :

```text
implemented
partially_implemented
not_implemented
not_applicable
blocked
```

Ne jamais déclarer une exigence implémentée sans code ou test associé.

---

## Inventaire fonctionnel final

Vérifier :

```text
Étude
Localisation
Climat
Modèle
Orientation
Vitrages
Protections solaires
Usage
Occupation
Équipements
Éclairage
Ventilation
Infiltration
Confort
Vérification
Snapshot
MERCURE
EnergyPlus
Résultats
Historique
Révision
```

Pour chaque étape :

- route ;
- permissions ;
- chargement ;
- sauvegarde ;
- validation ;
- erreurs ;
- provenance ;
- confiance ;
- responsive ;
- accessibilité ;
- tests.

---

## Parcours utilisateur de recette

Automatiser autant que possible :

1. créer une étude ;
2. renseigner la localisation ;
3. récupérer le climat ;
4. sélectionner un modèle ;
5. configurer orientation, vitrages et protections ;
6. configurer usage et occupation ;
7. configurer équipements et éclairage ;
8. configurer ventilation, infiltration et confort ;
9. ouvrir la revue ;
10. corriger les erreurs ;
11. confirmer les hypothèses ;
12. créer le snapshot ;
13. lancer MERCURE ;
14. lancer EnergyPlus si activé ;
15. consulter les résultats ;
16. comparer les moteurs ;
17. créer une révision.

Compléter l’automatisation par une recette manuelle documentée.

---

## Routes à vérifier

```text
/cooling/studies
/cooling/studies/new
/cooling/studies/:studyId
/cooling/studies/:studyId/location
/cooling/studies/:studyId/model
/cooling/studies/:studyId/orientation
/cooling/studies/:studyId/usage
/cooling/studies/:studyId/equipment
/cooling/studies/:studyId/comfort
/cooling/studies/:studyId/review
/cooling/studies/:studyId/results
```

Tester :

- route inconnue ;
- étude inconnue ;
- accès interdit ;
- étude archivée ;
- résultat obsolète ;
- retour arrière ;
- deep link ;
- rafraîchissement direct ;
- navigation mobile.

---

## Stepper final

Le stepper doit afficher :

- étapes terminées ;
- étapes incomplètes ;
- étapes en erreur ;
- étape courante ;
- résultat disponible ;
- étude obsolète.

Le statut doit venir du backend.

---

## Modèles Odoo à consolider

```text
greencube.cooling.study
greencube.cooling.study.revision
greencube.cooling.scenario
greencube.cooling.assumption
greencube.cooling.validation.issue
greencube.cooling.calculation.snapshot
greencube.cooling.calculation.job
greencube.cooling.result
greencube.cooling.result.scenario
greencube.cooling.result.line
greencube.cooling.result.comparison
greencube.cooling.simulation.artifact
```

Vérifier :

- contraintes SQL ;
- contraintes Python ;
- index ;
- relations ;
- suppressions ;
- archivage ;
- readonly ;
- calculs ;
- multi-société ;
- historique ;
- performances.

---

## Sources de vérité

Garantir :

```text
Odoo = source de vérité métier
snapshot = source immuable du calcul
résultat = immuable
frontend = interface et cache temporaire
worker = exécution technique
stockage objet = artefacts techniques
```

---

## Statuts

### Étude

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

### Préparation

```text
not_started
incomplete
needs_review
ready
invalid
stale
```

### Job

```text
queued
running
completed
failed
cancelled
timed_out
superseded
```

### Résultat

```text
current
stale
superseded
invalid
```

Adapter aux statuts réellement présents.

---

## Machine à états

Créer :

```text
docs/cooling_state_machine.md
```

Documenter :

- états ;
- transitions ;
- rôles ;
- préconditions ;
- effets ;
- invalidations ;
- audit ;
- erreurs.

Exemple :

```text
in_progress
→ ready
si validation réussie et snapshot créé

ready
→ queued
si calcul lancé

running
→ calculated
si résultat produit

calculated
→ in_progress
uniquement via nouvelle révision
```

---

## Migrations Odoo

Vérifier :

- installation sur base vierge ;
- mise à jour d’une base existante ;
- création des champs ;
- création des index ;
- création des contraintes ;
- création des référentiels ;
- maintien des données existantes ;
- idempotence ;
- rollback documenté.

Créer si nécessaire :

```text
migrations/<version>/pre-migration.py
migrations/<version>/post-migration.py
```

Ne jamais altérer une migration déjà livrée sans raison historique valide.

---

## Données de démonstration

Prévoir :

```text
GreenCube Studio standard
Bureau vitré ouest
Local technique
Studio canicule
GreenCube performant
Étude à faible confiance
```

Les données doivent être :

- optionnelles ;
- non sensibles ;
- multi-sociétés ;
- clairement identifiées ;
- adaptées à la recette.

---

## Référentiels initiaux

Vérifier :

- scénarios climatiques ;
- profils de confort ;
- profils de ventilation ;
- profils d’étanchéité ;
- profils d’usage ;
- facteurs de confiance ;
- marges ;
- seuils ;
- moteurs ;
- versions ;
- feature flags.

Chaque entrée doit avoir :

- code stable ;
- version ;
- statut ;
- source ;
- date ;
- société si nécessaire.

---

## Consolidation API

Vérifier les endpoints liés à :

```text
études
révisions
localisation
climat
modèles
vitrages
usage
équipements
ventilation
validation
hypothèses
snapshots
calculs
résultats
comparaisons
artefacts
```

Pour chaque endpoint :

- méthode ;
- authentification ;
- autorisation ;
- validation ;
- contrat ;
- code HTTP ;
- erreur structurée ;
- idempotence ;
- pagination ;
- filtres ;
- request ID ;
- multi-société ;
- tests.

---

## Contrat OpenAPI

Créer ou compléter :

```text
openapi/cooling.yaml
```

Inclure :

- schémas ;
- enums ;
- exemples ;
- erreurs ;
- permissions ;
- pagination ;
- idempotence ;
- statuts ;
- unités.

Le frontend doit utiliser des types générés ou strictement alignés.

---

## Erreur API standard

Exemple :

```json
{
  "error": {
    "code": "STUDY_VERSION_CONFLICT",
    "message": "L’étude a été modifiée.",
    "field": null,
    "section": "review",
    "action": "reload",
    "request_id": "req-..."
  }
}
```

Ne pas exposer :

- stack trace ;
- SQL ;
- chemin système ;
- secret ;
- détail interne inutile.

---

## Verrouillage optimiste

Vérifier l’utilisation de :

```text
version
etag
updated_at
```

ou équivalent.

Tester :

- deux onglets ;
- deux utilisateurs ;
- sauvegarde simultanée ;
- snapshot pendant modification ;
- relance sur ancienne version ;
- confirmation concurrente.

Aucun écrasement silencieux ne doit être possible.

---

## Idempotence

Vérifier :

- création de snapshot ;
- confirmation d’hypothèse ;
- lancement de calcul ;
- relance ;
- annulation ;
- création de révision si nécessaire.

Utiliser :

```text
Idempotency-Key
```

Tester :

- double clic ;
- retry ;
- timeout client ;
- réponse perdue ;
- rechargement.

---

## Consolidation MERCURE

Vérifier :

- fonctions pures ;
- unités ;
- constantes ;
- psychrométrie ;
- transmission ;
- solaire ;
- occupants ;
- équipements ;
- ventilation ;
- infiltration ;
- marges ;
- recommandations ;
- version ;
- trace ;
- résultats ;
- non-régression.

Le cœur mathématique ne doit pas accéder à l’ORM.

---

## Consolidation Honeybee / EnergyPlus

Vérifier :

- feature flag ;
- versions ;
- image Docker ;
- géométrie ;
- constructions ;
- ouvertures ;
- calendriers ;
- charges ;
- météo ;
- isolation ;
- timeout ;
- heartbeat ;
- parsing ;
- artefacts ;
- comparaison MERCURE ;
- nettoyage ;
- non-régression.

EnergyPlus ne doit jamais s’exécuter dans le processus web Odoo.

---

## Gestion des artefacts

Vérifier :

- types ;
- stockage ;
- checksum ;
- taille ;
- permissions ;
- rétention ;
- nettoyage ;
- accès temporaire ;
- multi-société.

Aucun artefact ne doit disposer d’une URL publique permanente.

---

## Consolidation frontend

Vérifier :

- routes ;
- guards ;
- layout ;
- stepper ;
- composants partagés ;
- query hooks ;
- store ;
- formulaires ;
- validations ;
- autosave ;
- polling ;
- cache ;
- erreurs ;
- skeletons ;
- responsive ;
- accessibilité.

Éliminer :

- logique métier dupliquée ;
- référentiels codés en dur ;
- types divergents ;
- composants morts ;
- effets inutiles ;
- polling en double ;
- requêtes non annulées ;
- erreurs silencieuses.

---

## Design final

Respecter :

```text
fond blanc
typographie noire
accents verts
interface lean
navigation claire
hiérarchie forte
```

Vérifier la cohérence des :

- boutons ;
- cartes ;
- formulaires ;
- alertes ;
- badges ;
- stepper ;
- graphiques ;
- tableaux ;
- dialogues ;
- états vides ;
- états d’erreur.

---

## Responsive

Tester au minimum :

```text
360 × 800
390 × 844
768 × 1024
1024 × 768
1366 × 768
1440 × 900
1920 × 1080
```

Vérifier :

- débordements ;
- footer sticky ;
- tableaux ;
- graphiques ;
- accordéons ;
- dialogues ;
- clavier virtuel ;
- orientation mobile ;
- zones cliquables.

---

## Accessibilité

Viser les bonnes pratiques WCAG 2.1 AA.

Vérifier :

- navigation clavier ;
- focus visible ;
- ordre du focus ;
- labels ;
- erreurs associées ;
- contraste ;
- lecteurs d’écran ;
- tableaux ;
- alternatives aux graphiques ;
- dialogues ;
- accordéons ;
- annonces de statut ;
- formulaires ;
- unités ;
- zoom à 200 %.

Créer :

```text
docs/cooling_accessibility_audit.md
```

---

## Internationalisation

Même si le MVP est français :

- centraliser les textes ;
- localiser nombres et dates ;
- gérer les unités ;
- gérer les pluriels ;
- structurer les erreurs ;
- préparer une architecture i18n.

---

## Performance frontend

Mesurer :

- bundle ;
- chargement ;
- requêtes ;
- re-renders ;
- poids des graphiques ;
- payloads ;
- polling ;
- cache ;
- lazy loading.

Optimiser :

- code splitting ;
- chargement différé ;
- pagination ;
- agrégation des séries ;
- invalidation ciblée ;
- mémorisation justifiée.

---

## Performance backend

Mesurer :

- temps de réponse ;
- requêtes SQL ;
- N+1 ;
- index ;
- sérialisation ;
- taille des snapshots ;
- durée MERCURE ;
- durée EnergyPlus ;
- persistance ;
- historique.

---

## Charge et concurrence

Tester :

- plusieurs études ;
- plusieurs utilisateurs ;
- plusieurs sociétés ;
- MERCURE simultané ;
- EnergyPlus limité ;
- file pleine ;
- worker arrêté ;
- reprise ;
- timeout ;
- annulation ;
- historique volumineux.

Respecter :

```text
max_concurrent_energyplus_jobs
```

---

## Sécurité — authentification

Vérifier :

- aucune route privée publique ;
- session ou token valide ;
- expiration ;
- révocation ;
- CORS ;
- CSRF si applicable ;
- cookies sécurisés ;
- headers ;
- absence de token dans les logs ou URLs.

---

## Sécurité — autorisation

Tester les rôles :

```text
cooling_user
cooling_engineer
cooling_manager
cooling_admin
```

Vérifier :

- lecture ;
- modification ;
- snapshot ;
- calcul ;
- artefacts ;
- traces ;
- configuration ;
- validation ;
- révision ;
- archivage ;
- accès inter-sociétés interdit.

---

## Sécurité — entrées

Vérifier :

- Zod côté frontend ;
- validation backend indépendante ;
- limites numériques ;
- limites de texte ;
- noms de fichiers ;
- payloads surdimensionnés ;
- injections ;
- caractères spéciaux ;
- NaN et infinis ;
- dates invalides ;
- enums inconnues.

---

## Sécurité — fichiers

Vérifier :

- path traversal ;
- extensions ;
- MIME ;
- taille ;
- checksum ;
- téléchargement contrôlé ;
- URL temporaire ;
- stockage privé ;
- nettoyage ;
- rétention.

---

## Sécurité — EnergyPlus

Vérifier :

- utilisateur non root ;
- `shell=False` ;
- commandes en liste blanche ;
- chemins serveur ;
- réseau désactivé si possible ;
- limites CPU ;
- limites mémoire ;
- timeout ;
- filesystem temporaire ;
- nettoyage ;
- aucun secret dans l’image.

---

## Sécurité — secrets

Analyser :

- dépôt Git ;
- historique si accessible ;
- `.env` ;
- Dockerfiles ;
- CI ;
- logs ;
- fixtures ;
- tests ;
- documentation.

Ne jamais livrer :

- mot de passe ;
- clé API ;
- token ;
- certificat privé ;
- credential Odoo ;
- URL signée permanente.

---

## Sécurité — dépendances

Exécuter si disponibles :

```text
npm audit
pip-audit
scanner d’image Docker
scanner de dépendances
```

Classer :

```text
critical
high
medium
low
```

Traiter les vulnérabilités critiques et élevées ou documenter précisément le blocage.

---

## Headers de sécurité

Vérifier :

```text
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
Strict-Transport-Security
frame-ancestors
```

---

## Logs

Les logs peuvent contenir :

```text
request_id
study_id
job_id
snapshot_id
company_id
status
duration
error_code
```

Ils ne doivent pas contenir :

- secret ;
- token ;
- payload sensible complet ;
- données personnelles inutiles ;
- fichier météo complet ;
- SQL brut en production.

---

## Audit trail

Auditer :

- création ;
- modification ;
- validation ;
- confirmation ;
- snapshot ;
- lancement ;
- annulation ;
- résultat ;
- révision ;
- accès aux artefacts ;
- validation ingénieur ;
- archivage.

Conserver :

- utilisateur ;
- société ;
- date ;
- action ;
- objet ;
- version ;
- request ID.

---

## Sauvegarde

Documenter et tester :

- PostgreSQL ;
- filestore Odoo ;
- stockage objet ;
- configuration ;
- fichiers météo ;
- paramètres moteurs ;
- métadonnées des artefacts.

Créer :

```text
docs/cooling_backup_restore.md
```

---

## Restauration

Tester en environnement non productif :

- études ;
- snapshots ;
- résultats ;
- comparaisons ;
- artefacts ;
- pièces jointes ;
- permissions ;
- paramètres ;
- historique des jobs.

---

## Déploiement VPS

Architecture possible :

```text
Nginx
Frontend React
Odoo 18 Community
PostgreSQL
Redis ou file existante
Worker Cooling
Worker EnergyPlus
MinIO ou stockage existant
```

Adapter à l’existant.

---

## Docker Compose

Créer ou compléter :

```text
docker-compose.yml
docker-compose.production.yml
```

Services possibles :

```text
nginx
frontend
odoo
postgres
redis
cooling-worker
simulation-worker
minio
```

Ne pas ajouter de service inutile.

---

## Variables d’environnement

Créer :

```text
.env.example
```

Documenter pour chaque variable :

```text
nom
obligatoire
valeur par défaut
description
secret ou non
service concerné
```

Exemples :

```text
ODOO_DB_HOST
ODOO_DB_USER
ODOO_DB_PASSWORD
REDIS_URL
COOLING_STORAGE_ENDPOINT
COOLING_STORAGE_BUCKET
ENERGYPLUS_ENABLED
ENERGYPLUS_VERSION
MAX_CONCURRENT_ENERGYPLUS_JOBS
SIMULATION_TIMEOUT_SECONDS
```

Ne jamais placer de vraie valeur secrète dans `.env.example`.

---

## Scripts

Créer ou compléter :

```text
scripts/install.sh
scripts/update.sh
scripts/rollback.sh
scripts/healthcheck.sh
scripts/backup.sh
scripts/restore.sh
scripts/smoke_test_cooling.sh
```

Les scripts doivent :

- utiliser `set -euo pipefail` si Bash ;
- vérifier les prérequis ;
- afficher des erreurs claires ;
- ne pas exposer de secret ;
- être idempotents autant que possible ;
- produire des logs utiles.

---

## Documentation de déploiement

Créer :

```text
docs/cooling_deployment_vps.md
```

Documenter :

1. prérequis ;
2. DNS ;
3. TLS ;
4. variables ;
5. volumes ;
6. base ;
7. migrations ;
8. build frontend ;
9. démarrage ;
10. healthchecks ;
11. smoke tests ;
12. supervision ;
13. sauvegarde ;
14. rollback.

---

## TLS et reverse proxy

Vérifier :

- HTTPS ;
- renouvellement certificat ;
- redirection HTTP ;
- HSTS si approprié ;
- cookies sécurisés ;
- taille des requêtes ;
- timeouts ;
- compression ;
- cache statique ;
- routage frontend ;
- routage API ;
- limitation de débit ;
- healthchecks.

EnergyPlus doit rester asynchrone, sans timeout web très long.

---

## Healthchecks

Créer ou compléter :

```text
/health
/health/deep
```

Vérifier :

- frontend ;
- Odoo ;
- PostgreSQL ;
- worker ;
- file ;
- stockage ;
- MERCURE ;
- EnergyPlus ;
- écriture temporaire.

Distinguer si possible :

```text
liveness
readiness
```

---

## Monitoring

Prévoir :

- disponibilité ;
- erreurs ;
- temps de réponse ;
- longueur de file ;
- jobs bloqués ;
- durée MERCURE ;
- durée EnergyPlus ;
- espace disque ;
- taille du stockage ;
- erreurs de sauvegarde ;
- erreurs worker.

---

## Alertes opérationnelles

Documenter :

```text
API indisponible
base indisponible
worker arrêté
heartbeat absent
file pleine
stockage presque plein
simulation en échec
sauvegarde en échec
certificat proche d’expiration
```

---

## CI

Pipeline recommandé :

```text
lint frontend
TypeScript
tests frontend
build frontend
lint Python
format check Python
type check Python
tests Python
tests Odoo
tests API
tests sécurité
build images
smoke tests
```

Un gate critique doit bloquer la livraison.

---

## CD

Vérifier :

- environnement ;
- approbation ;
- backup avant migration ;
- migrations ;
- healthchecks ;
- smoke tests ;
- rollback ;
- journal de déploiement.

Ne pas déployer automatiquement en production sans instruction explicite.

---

## Versionnement

Version MVP :

```text
GC-COOLING MVP 1.0.0
```

Conserver les versions de :

- module Odoo ;
- frontend ;
- API ;
- MERCURE ;
- méthode de calcul ;
- EnergyPlus ;
- Honeybee ;
- image Docker ;
- migrations.

---

## Changelog et release notes

Créer :

```text
CHANGELOG_GC_COOLING.md
docs/releases/GC_COOLING_MVP_1.0.0.md
```

Sections du changelog :

```text
Added
Changed
Fixed
Security
Deprecated
Removed
Known limitations
```

Les release notes doivent inclure :

- périmètre ;
- fonctionnalités ;
- prérequis ;
- migrations ;
- paramètres ;
- feature flags ;
- limites ;
- risques ;
- rollback ;
- tests exécutés ;
- anomalies connues.

---

## Smoke tests

Créer :

```text
scripts/smoke_test_cooling.sh
```

Vérifier :

- connexion ;
- création ou lecture d’une étude de test ;
- validation ;
- snapshot ;
- MERCURE ;
- lecture du résultat ;
- accès frontend ;
- healthchecks.

Prévoir un test EnergyPlus minimal séparé :

- géométrie simple ;
- EPW de référence ;
- un scénario ;
- timeout ;
- sortie attendue ;
- nettoyage.

---

## Tests frontend

Exécuter :

```text
lint
TypeScript strict
Vitest
Testing Library
Playwright
build production
```

Fournir les commandes et résultats réels.

---

## Tests backend

Exécuter :

```text
lint Python
format check
type check
tests unitaires
tests Odoo
tests API
tests migrations
tests multi-sociétés
```

---

## Tests MERCURE

Exécuter :

- conversions ;
- transmission ;
- solaire ;
- occupants ;
- équipements ;
- ventilation ;
- infiltration ;
- psychrométrie ;
- marges ;
- non-régression ;
- propriétés.

---

## Tests EnergyPlus

Exécuter :

- construction modèle ;
- validation météo ;
- runner ;
- timeout ;
- parsing ;
- artefacts ;
- comparaison ;
- job ;
- annulation ;
- non-régression.

---

## Parcours Playwright

Créer au minimum :

1. Studio standard jusqu’au résultat MERCURE ;
2. calcul BOTH et comparaison ;
3. erreur bloquante empêchant le snapshot ;
4. confirmation d’hypothèse ;
5. conflit entre deux onglets ;
6. révision d’un résultat historique ;
7. échec EnergyPlus avec fallback MERCURE ;
8. accès inter-sociétés interdit ;
9. parcours mobile ;
10. résultat obsolète après révision.

---

## Recette métier

Créer :

```text
docs/cooling_user_acceptance_test.md
```

Pour chaque cas :

- préconditions ;
- données ;
- étapes ;
- résultat attendu ;
- résultat observé ;
- preuve ;
- statut ;
- anomalie associée.

---

## Jeux de données de recette

Préparer :

- Studio standard ;
- Bureau vitré ouest ;
- Local technique ;
- Canicule prolongée ;
- GreenCube performant ;
- Données incomplètes ;
- Faible confiance ;
- Forte charge latente ;
- Multi-société ;
- Révision.

---

## Non-régression

Créer ou compléter :

```text
tests/fixtures/cooling_snapshots/
tests/fixtures/cooling_results/
```

Conserver :

- snapshot ;
- version ;
- résultat MERCURE ;
- résultat EnergyPlus normalisé ;
- tolérance ;
- justification des écarts.

---

## Tests visuels

Si disponibles, créer des références pour :

- page étude ;
- écran revue ;
- écran résultats ;
- mobile ;
- erreurs ;
- chargement.

Éviter des tests trop fragiles.

---

## Tests de panne

Tester :

- PostgreSQL indisponible ;
- Redis indisponible ;
- worker absent ;
- stockage indisponible ;
- météo absente ;
- EnergyPlus indisponible ;
- disque plein simulé si possible ;
- timeout ;
- processus tué ;
- réponse API interrompue.

Le système doit échouer proprement et rester récupérable.

---

## Jobs bloqués

Créer une commande :

```text
cooling_recover_stalled_jobs
```

Elle doit :

- détecter les heartbeats expirés ;
- vérifier le worker ;
- marquer ou relancer ;
- éviter les doublons ;
- conserver l’audit.

---

## Commandes d’administration

Créer si nécessaire :

```text
revalider une étude
reconstruire un snapshot de test
relancer un job
annuler un job
nettoyer les artefacts expirés
vérifier les checksums
recalculer la confiance
inspecter les versions
```

Ces actions doivent être protégées par rôle.

---

## Politique de rétention

Finaliser la politique pour :

- logs ;
- jobs ;
- artefacts ;
- fichiers intermédiaires ;
- résultats ;
- snapshots ;
- audits ;
- données de démonstration.

Les résultats et snapshots métier ne doivent pas être supprimés arbitrairement.

---

## Documentation utilisateur

Créer :

```text
docs/cooling_user_guide.md
```

Inclure :

- création d’étude ;
- étapes ;
- valeurs estimées ;
- confiance ;
- calcul ;
- résultats ;
- sensible et latent ;
- scénario dimensionnant ;
- révision ;
- avertissements ;
- limites.

---

## Documentation administrateur

Créer :

```text
docs/cooling_odoo_admin_guide.md
```

Inclure :

- groupes ;
- profils ;
- référentiels ;
- moteurs ;
- marges ;
- seuils ;
- feature flags ;
- météo ;
- jobs ;
- artefacts ;
- rétention ;
- audit.

---

## Documentation développeur

Créer :

```text
docs/cooling_developer_guide.md
```

Inclure :

- architecture ;
- installation ;
- modèles ;
- API ;
- frontend ;
- MERCURE ;
- EnergyPlus ;
- tests ;
- migrations ;
- conventions ;
- extensions.

---

## Documentation d’exploitation

Créer :

```text
docs/cooling_operations_runbook.md
```

Inclure :

- démarrage ;
- arrêt ;
- déploiement ;
- rollback ;
- sauvegarde ;
- restauration ;
- workers ;
- file ;
- stockage ;
- healthchecks ;
- incidents ;
- logs ;
- métriques ;
- nettoyage.

---

## Guide de dépannage

Créer :

```text
docs/cooling_troubleshooting.md
```

Cas :

- étude bloquée ;
- snapshot impossible ;
- MERCURE en erreur ;
- EnergyPlus en erreur ;
- job bloqué ;
- météo absente ;
- artefact inaccessible ;
- résultat obsolète ;
- conflit de version ;
- accès interdit ;
- migration échouée.

---

## Compatibilité

Documenter :

- navigateurs ;
- Node ;
- Python ;
- Odoo 18 ;
- PostgreSQL ;
- EnergyPlus ;
- Honeybee ;
- OS ;
- Docker ;
- architecture CPU si pertinente.

---

## Packaging final

Produire une structure adaptée au dépôt :

```text
GC_COOLING_MVP_1.0.0/
├── addons/
├── frontend/
├── workers/
├── deployment/
├── scripts/
├── docs/
├── openapi/
├── migrations/
├── tests/
├── CHANGELOG_GC_COOLING.md
├── README.md
└── MANIFEST.txt
```

---

## Manifest

Créer :

```text
MANIFEST_GC_COOLING_MVP_1.0.0.txt
```

Inclure :

- fichiers ;
- checksums ;
- version ;
- date ;
- dépendances ;
- migrations ;
- scripts ;
- exclusions.

---

## Patch réintégrable

Produire :

```text
PATCH_GC_COOLING_MVP_1.0.0.diff
PATCH_GC_COOLING_MVP_1.0.0_README.md
```

Le patch doit :

- rester limité au périmètre GreenCube Cooling ;
- éviter les fichiers générés inutiles ;
- éviter le reformatage global ;
- éviter les suppressions ;
- documenter les conflits ;
- fournir l’ordre d’application ;
- inclure les migrations ;
- inclure les tests ;
- inclure le rollback.

---

## Instructions du patch

Le README du patch doit contenir :

1. prérequis ;
2. branche de destination ;
3. sauvegarde ;
4. application ;
5. résolution des conflits ;
6. dépendances ;
7. migrations ;
8. build ;
9. tests ;
10. smoke tests ;
11. rollback.

Ne pas livrer un simple ZIP à écraser sans diff, manifest et procédure.

---

## Rollback

Documenter le rollback pour :

- frontend ;
- module Odoo ;
- migrations ;
- worker ;
- image EnergyPlus ;
- configuration ;
- base ;
- stockage.

Préciser les opérations non réversibles.

---

## Known issues

Créer :

```text
docs/cooling_known_issues.md
```

Pour chaque anomalie :

- identifiant ;
- gravité ;
- description ;
- impact ;
- contournement ;
- lot futur ;
- décision de livraison.

---

## Feature flags finaux

Recenser :

```text
enable_energyplus_calculation
enable_annual_energyplus_simulation
enable_advanced_natural_ventilation
enable_solver_payload_preview
enable_cooling_what_if
enable_result_version_comparison
enable_cooling_equipment_selection
```

Pour chaque flag :

- valeur par défaut ;
- environnement ;
- dépendance ;
- risque ;
- comportement désactivé ;
- test.

Une fonctionnalité désactivée ne doit pas casser le parcours principal.

---

## Recette de production

Avant livraison, exécuter :

1. installation sur base vierge ;
2. mise à jour d’une base existante ;
3. build production ;
4. démarrage complet ;
5. healthchecks ;
6. smoke tests ;
7. parcours Studio standard ;
8. calcul MERCURE ;
9. calcul EnergyPlus si activé ;
10. comparaison ;
11. révision ;
12. sauvegarde ;
13. restauration ;
14. rollback de test.

---

## Gate GO / NO-GO

La mise en production est autorisée uniquement si :

```text
0 P0 ouverts
0 P1 ouverts sur le parcours principal
0 vulnérabilité critique ouverte
0 secret exposé
migrations validées
backup validé
rollback documenté
smoke tests réussis
parcours principal réussi
```

Sinon, la décision doit être :

```text
NO-GO
```

---

## Rapport final de recette

Créer :

```text
docs/cooling_final_acceptance_report.md
```

Inclure :

- environnement ;
- versions ;
- date ;
- tests ;
- résultats ;
- anomalies ;
- preuves ;
- couverture ;
- risques ;
- décision GO/NO-GO.

Pour chaque commande :

- commande ;
- environnement ;
- code retour ;
- durée ;
- résumé ;
- fichier de log si disponible.

---

## Critères d’acceptation fonctionnels

Le lot est accepté si :

- une étude peut être créée ;
- toutes les étapes peuvent être renseignées ;
- les données sont sauvegardées ;
- les conflits sont gérés ;
- la validation serveur fonctionne ;
- les erreurs bloquantes empêchent le snapshot ;
- les hypothèses peuvent être confirmées ;
- le snapshot est créé ;
- le snapshot est immuable ;
- MERCURE fonctionne ;
- EnergyPlus fonctionne si activé ;
- le fallback MERCURE fonctionne ;
- les résultats sont affichés ;
- les scénarios sont comparés ;
- la recommandation est affichée ;
- la confiance est affichée ;
- les avertissements sont affichés ;
- les résultats sont immuables ;
- les révisions fonctionnent ;
- l’historique fonctionne ;
- les résultats obsolètes sont signalés ;
- le multi-société fonctionne ;
- les permissions fonctionnent ;
- les feature flags fonctionnent.

---

## Critères d’acceptation techniques

Le lot est accepté si :

- TypeScript strict passe ;
- le lint frontend passe ;
- le build frontend passe ;
- les tests frontend passent ;
- Playwright passe ;
- le lint Python passe ;
- le formatage Python passe ;
- le contrôle de types Python passe ;
- les tests Python passent ;
- les tests Odoo passent ;
- les tests API passent ;
- les migrations passent ;
- les tests MERCURE passent ;
- les tests EnergyPlus passent si activé ;
- les tests de non-régression passent ;
- les smoke tests passent ;
- les healthchecks passent ;
- l’image Docker est construite ;
- l’installation vierge fonctionne ;
- la mise à jour fonctionne ;
- la sauvegarde est testée ;
- la restauration est testée ;
- le rollback est documenté ;
- aucune suppression injustifiée n’existe.

---

## Critères d’acceptation sécurité

Le lot est accepté si :

- aucune route privée n’est publique ;
- les permissions sont testées ;
- le multi-société est testé ;
- les fichiers sont protégés ;
- EnergyPlus est isolé ;
- aucun `shell=True` dangereux n’est utilisé ;
- les secrets sont absents ;
- les logs ne contiennent pas de secrets ;
- les dépendances critiques sont corrigées ;
- les headers sont vérifiés ;
- les entrées sont validées ;
- les erreurs internes ne sont pas exposées ;
- les téléchargements sont contrôlés ;
- les URLs temporaires expirent ;
- les sauvegardes sont protégées.

---

## Critères d’acceptation exploitation

Le lot est accepté si :

- la documentation de déploiement existe ;
- les variables sont documentées ;
- les scripts existent ;
- les healthchecks existent ;
- le monitoring est défini ;
- les alertes sont définies ;
- la sauvegarde est documentée ;
- la restauration est documentée ;
- le rollback est documenté ;
- le runbook existe ;
- le troubleshooting existe ;
- la rétention est définie ;
- les jobs bloqués peuvent être récupérés ;
- le nettoyage fonctionne.

---

## Rapport final attendu

### Synthèse

- périmètre ;
- version ;
- GO/NO-GO ;
- P0 ;
- P1 ;
- risques ;
- limites.

### Architecture

- frontend ;
- Odoo ;
- API ;
- MERCURE ;
- EnergyPlus ;
- workers ;
- stockage ;
- reverse proxy ;
- flux.

### Fonctionnel

- parcours ;
- étapes ;
- résultats ;
- révisions ;
- historique ;
- feature flags.

### Modèles Odoo

- modèles ;
- contraintes ;
- index ;
- ACL ;
- multi-société ;
- migrations.

### API

Pour chaque endpoint :

- statut ;
- contrat ;
- sécurité ;
- idempotence ;
- test.

### Tests

- commandes ;
- résultats ;
- couverture ;
- échecs ;
- tests non exécutés ;
- raisons ;
- preuves.

### Sécurité

- authentification ;
- autorisation ;
- secrets ;
- dépendances ;
- fichiers ;
- isolation ;
- logs ;
- vulnérabilités.

### Performance

- frontend ;
- API ;
- MERCURE ;
- EnergyPlus ;
- base ;
- concurrence ;
- limites.

### Déploiement

- services ;
- variables ;
- scripts ;
- migrations ;
- healthchecks ;
- smoke tests ;
- sauvegarde ;
- restauration ;
- rollback.

### Documentation

- utilisateur ;
- administrateur ;
- développeur ;
- exploitation ;
- dépannage ;
- release notes ;
- changelog.

### Livraison

- fichiers ;
- manifest ;
- checksums ;
- patch ;
- instructions ;
- exclusions.

### Anomalies

- ouvertes ;
- fermées ;
- contournements ;
- décisions.

---

## Livrables obligatoires

Produire au minimum :

```text
README_GC_COOLING_MVP.md
CHANGELOG_GC_COOLING.md
MANIFEST_GC_COOLING_MVP_1.0.0.txt
PATCH_GC_COOLING_MVP_1.0.0.diff
PATCH_GC_COOLING_MVP_1.0.0_README.md
docs/cooling_requirements_traceability_matrix.md
docs/cooling_state_machine.md
docs/cooling_accessibility_audit.md
docs/cooling_backup_restore.md
docs/cooling_deployment_vps.md
docs/cooling_user_acceptance_test.md
docs/cooling_user_guide.md
docs/cooling_odoo_admin_guide.md
docs/cooling_developer_guide.md
docs/cooling_operations_runbook.md
docs/cooling_troubleshooting.md
docs/cooling_known_issues.md
docs/cooling_final_acceptance_report.md
docs/releases/GC_COOLING_MVP_1.0.0.md
.env.example
scripts/install.sh
scripts/update.sh
scripts/rollback.sh
scripts/healthcheck.sh
scripts/backup.sh
scripts/restore.sh
scripts/smoke_test_cooling.sh
```

Adapter les chemins à la structure réelle sans créer de doublons inutiles.

---

## Contrôle final

Avant conclusion :

1. vérifier l’arborescence ;
2. vérifier la matrice de traçabilité ;
3. vérifier les routes ;
4. vérifier le stepper ;
5. vérifier les modèles ;
6. vérifier les statuts ;
7. vérifier les transitions ;
8. vérifier les migrations ;
9. vérifier les référentiels ;
10. vérifier les API ;
11. vérifier OpenAPI ;
12. vérifier les erreurs ;
13. vérifier les conflits ;
14. vérifier l’idempotence ;
15. vérifier MERCURE ;
16. vérifier EnergyPlus ;
17. vérifier les artefacts ;
18. vérifier le frontend ;
19. vérifier le design ;
20. vérifier le responsive ;
21. vérifier l’accessibilité ;
22. vérifier les performances ;
23. vérifier la charge ;
24. vérifier l’authentification ;
25. vérifier les permissions ;
26. vérifier le multi-société ;
27. vérifier les entrées ;
28. vérifier les fichiers ;
29. vérifier l’isolation ;
30. vérifier les secrets ;
31. vérifier les dépendances ;
32. vérifier les headers ;
33. vérifier les logs ;
34. vérifier l’audit ;
35. vérifier la sauvegarde ;
36. vérifier la restauration ;
37. vérifier Docker Compose ;
38. vérifier les variables ;
39. vérifier les scripts ;
40. vérifier TLS ;
41. vérifier Nginx ;
42. vérifier les healthchecks ;
43. vérifier le monitoring ;
44. vérifier la CI ;
45. vérifier le versionnement ;
46. vérifier le changelog ;
47. vérifier les smoke tests ;
48. vérifier les tests frontend ;
49. vérifier les tests backend ;
50. vérifier les tests MERCURE ;
51. vérifier les tests EnergyPlus ;
52. vérifier Playwright ;
53. vérifier la recette métier ;
54. vérifier la non-régression ;
55. vérifier les tests de panne ;
56. vérifier les jobs bloqués ;
57. vérifier la rétention ;
58. vérifier la documentation ;
59. vérifier le packaging ;
60. vérifier le manifest ;
61. vérifier le patch ;
62. vérifier les instructions ;
63. vérifier le rollback ;
64. vérifier les known issues ;
65. vérifier les feature flags ;
66. exécuter la recette de production ;
67. déterminer GO ou NO-GO ;
68. vérifier qu’aucun ancien résultat n’a été modifié ;
69. vérifier qu’aucun fichier n’a été supprimé sans justification ;
70. ne jamais déclarer un test, une migration, une sauvegarde, une restauration ou un déploiement réussi sans l’avoir réellement exécuté.

---

## Limites du lot

Ce lot finalise le MVP technique de GreenCube Cooling.

Il ne doit pas ajouter silencieusement :

- un catalogue commercial complet ;
- un devis ;
- une facturation ;
- une sélection produit avancée ;
- une étude réglementaire officielle ;
- une promesse de conformité réglementaire ;
- une automatisation de production non validée.

Le résultat attendu est une application MVP consolidée, testée, sécurisée, documentée et livrable, avec un parcours complet de pré-dimensionnement du besoin de refroidissement d’un GreenCube.
