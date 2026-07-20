# Prompts détaillés de correction — GreenCube Cooling

**Base auditée :** `GreenCube_Cooling-18-07-2026.zip`  
**Référence :** audit fonctionnel du 20 juillet 2026  
**Usage :** prompts autonomes pour Codex ou agent de développement, à appliquer par lots et commits séparés.

## Ordre d’application

Commencer par `00_MASTER_ORDRE_APPLICATION.md`. Il définit trois vagues : stabilisation P0, fidélité métier P1, puis simulation/livraison.

## Fichiers

- `GC-COOLING-01_MODELE_ODOO_SECURITE_DONNEES.md` — Modèle Odoo, droits, propriété et migrations
- `GC-COOLING-02_API_CONTRATS_AUTH_CSRF.md` — API Odoo, contrats, authentification et protection des routes
- `GC-COOLING-03_GEOLOCALISATION_LOCATION_CANONIQUE.md` — Géolocalisation, altitude, fuseau et modèle Location
- `GC-COOLING-04_SERVICE_CLIMATIQUE.md` — Service climatique historique, scénarios et gouvernance des données
- `GC-COOLING-05A_SOCLE_HONEYBEE_ENERGYPLUS.md` — Socle initial Honeybee / EnergyPlus et adaptateur de modèle
- `GC-COOLING-06_FRONTEND_REACT_BUILD_SOURCE_VERITE.md` — Frontend React, build, état et source de vérité
- `GC-COOLING-07_UI_LOCALISATION_CLIMAT.md` — Écran localisation, climat et confirmation utilisateur
- `GC-COOLING-08_MODELES_GREEN_CUBE_THERMIQUE.md` — Modèles GreenCube et caractéristiques thermiques versionnées
- `GC-COOLING-09_ORIENTATION_VITRAGES_PROTECTIONS.md` — Orientation, vitrages et protections solaires physiques
- `GC-COOLING-10_USAGE_OCCUPATION.md` — Usage, occupation, calendrier et activité
- `GC-COOLING-11_EQUIPEMENTS_APPORTS_INTERNES.md` — Équipements, éclairage et apports internes
- `GC-COOLING-12_VENTILATION_CONFORT.md` — Ventilation, infiltration et confort
- `GC-COOLING-13_REVIEW_VALIDATION_SNAPSHOT_REVISION.md` — Vérification, score de confiance, snapshot et révision
- `GC-COOLING-14_MOTEUR_MERCURE_CANONIQUE.md` — Moteur MERCURE canonique, traçabilité et non-régression
- `GC-COOLING-15_ORCHESTRATION_ENERGYPLUS_WORKER.md` — Jobs, worker, artefacts et orchestration EnergyPlus
- `GC-COOLING-16_RESULTATS_RECOMMANDATION.md` — Résultats, job polling et recommandation de puissance
- `GC-COOLING-17_CONSOLIDATION_CI_RECETTE_DEPLOIEMENT.md` — Consolidation MVP, CI, recette et déploiement
- `GC-COOLING-18_SELECTION_EQUIPEMENT.md` — Sélection d'équipement, compatibilité et immuabilité commerciale

## Remarque

Ces prompts corrigent les écarts de l’audit. Ils ne remplacent pas les prompts historiques du ZIP : ils constituent une campagne de consolidation et de remédiation.


---

# MASTER — Application séquentielle des correctifs GreenCube Cooling

## Mission

Appliquer les prompts correctifs GC-COOLING-01 à GC-COOLING-18 au dépôt issu de `GreenCube_Cooling-18-07-2026.zip`, sans réécriture aveugle et sans masquer les défauts détectés lors de l'audit du 20 juillet 2026.

## Ordre recommandé

### Vague A — Stabilisation P0

1. GC-COOLING-06 — build frontend et source de vérité ;
2. GC-COOLING-02 — contrats API et sécurité des routes ;
3. GC-COOLING-01 — ACL, record rules et immuabilité ;
4. GC-COOLING-03 — géolocalisation et enum canonique ;
5. GC-COOLING-13 — validation, snapshot et révision ;
6. GC-COOLING-16 — job/résultat et suppression des recalculs automatiques.

### Vague B — Fidélité métier P1

7. GC-COOLING-08 — modèles GreenCube versionnés ;
8. GC-COOLING-09 — orientation, vitrages et protections ;
9. GC-COOLING-10 — usage et occupation ;
10. GC-COOLING-11 — apports internes ;
11. GC-COOLING-12 — ventilation et confort ;
12. GC-COOLING-04 — climat et scénarios ;
13. GC-COOLING-14 — MERCURE canonique ;
14. GC-COOLING-18 — sélection d'équipement.

### Vague C — Simulation et livraison

15. GC-COOLING-05A — adaptateur Honeybee ;
16. GC-COOLING-15 — worker EnergyPlus ;
17. GC-COOLING-07 — finition UX localisation/climat ;
18. GC-COOLING-17 — consolidation finale, CI et décision GO/NO-GO.

## Règles de séquencement

- Créer un commit ou patch séparé par prompt.
- Avant chaque prompt, rebaser l'état des tests et noter les échecs préexistants.
- Après chaque prompt, exécuter les tests ciblés et les tests de non-régression pertinents.
- Ne pas poursuivre vers la vague B tant que le frontend ne build pas, que l'utilisateur standard ne peut pas réaliser le flux et que le contrat calcul/job/résultat n'est pas corrigé.
- Ne pas activer EnergyPlus avant preuve d'une simulation réelle dans le worker.
- Chaque prompt doit laisser le dépôt dans un état cohérent et réversible.

## Critères globaux de GO MVP MERCURE

- `npm ci`, lint, typecheck, tests et build réussissent ;
- installation et upgrade Odoo réussissent sur une vraie instance ;
- utilisateur standard réalise le parcours complet sur sa société ;
- Odoo fournit la liste et le détail des études ;
- un clic de calcul crée au maximum un job idempotent ;
- job et résultat sont chargés selon le contrat canonique ;
- orientation, modèle, protections, occupation, équipements et ventilation affectent réellement le snapshot et le calcul ;
- snapshots, résultats et sélections validées sont immuables ;
- deux utilisateurs/deux sociétés sont isolés ;
- tests HTTP et Playwright sont exécutés en CI ;
- aucun P0 et aucun P1 du parcours MERCURE ne restent ouverts.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-01 — Modèle Odoo, droits, propriété et migrations

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Rendre le modèle Odoo fonctionnel pour un utilisateur standard tout en garantissant l'isolation par utilisateur et société, la cohérence des objets enfants et la sécurité des objets historiques. Le lot doit corriger les ACL et règles d'enregistrement sans ouvrir les référentiels administratifs ni fragiliser l'immuabilité des snapshots, résultats et sélections validées.

## Constat initial issu de l'audit

- Le rôle `User` peut créer une étude mais ne peut pas créer ou modifier `greencube.thermal.specification` et `greencube.thermal.facade`, alors que le wizard les écrit.
- Plusieurs sous-modèles et résultats disposent d'ACL globales sans règles de propriété complètes.
- Les modèles enfants doivent hériter de la sécurité de `study_id`.
- Le modèle canonique V2 est partiel et aucune migration n'est livrée.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/models/*.py`
- `addons/greencube_cooling/security/ir.model.access.csv`
- `addons/greencube_cooling/security/greencube_cooling_rules.xml`
- `addons/greencube_cooling/security/greencube_cooling_groups.xml`
- `addons/greencube_cooling/tests/`
- `addons/greencube_cooling/__manifest__.py`
- tout répertoire de migration existant ou à créer

## Travaux obligatoires

1. Cartographier tous les modèles et leurs relations avec `greencube.cooling.study`.
2. Définir la matrice de droits `User` / `Manager` pour chaque modèle : lecture, création, écriture, suppression.
3. Autoriser un utilisateur standard à créer et modifier uniquement les spécifications thermiques privées rattachées à ses propres études non verrouillées.
4. Conserver les modèles standards/canoniques administrables uniquement par les managers.
5. Ajouter des règles globales sur les profils d'occupation, apports internes, ventilation, protections, résultats, composants, sélections et autres enfants, en remontant vers `study_id.user_id` et `study_id.company_id`.
6. Vérifier le comportement multi-sociétés avec `allowed_company_ids` et éviter toute lecture croisée involontaire.
7. Bloquer explicitement `write()` et `unlink()` des snapshots et résultats terminés, sauf mécanisme interne strictement contrôlé au moment de la création.
8. Bloquer `write()` et `unlink()` d'une sélection d'équipement validée ; toute évolution doit créer une nouvelle sélection ou révision.
9. Revoir les `ondelete`, contraintes SQL et contraintes Python pour éviter les objets orphelins.
10. Ajouter une migration si les règles, champs, index ou relations changent. La migration doit être idempotente et documentée.
11. Ajouter des index sur les clés de recherche utilisées par l'API : étude, utilisateur, société, statut, snapshot, résultat actif.
12. Documenter la matrice des droits dans `docs/cooling_security_matrix.md`.

## Tests obligatoires

- Tests Odoo avec au minimum deux utilisateurs standards, un manager et deux sociétés.
- Un utilisateur A peut créer/modifier sa spécification privée et ses enfants sur une étude brouillon.
- L'utilisateur A ne peut ni lire ni modifier les objets de l'utilisateur B.
- Un utilisateur ne peut pas accéder aux objets d'une société non autorisée.
- Un manager peut gérer les modèles standards sans devenir propriétaire des études privées.
- Snapshot et résultat terminés sont non modifiables et non supprimables.
- Sélection validée non modifiable et non supprimable.
- Mise à niveau du module sur une base contenant des données de démonstration sans perte.
- Exécuter les `TransactionCase` existants et ajouter les cas manquants.

## Définition de terminé

- Le wizard complet est réalisable avec le groupe `User` sans `AccessError`.
- Toutes les ressources privées sont isolées par utilisateur et société.
- Aucun endpoint ne dépend d'une ACL trop permissive.
- Les objets historiques sont réellement immuables.
- Les migrations sont présentes, testées et documentées.
- Aucun P0 de sécurité des données n'est ouvert.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-02 — API Odoo, contrats, authentification et protection des routes

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Stabiliser l'API HTTP comme contrat canonique entre le frontend et Odoo. Corriger les divergences de schémas, les accès directs par identifiant, la gestion des erreurs, la stratégie session/CSRF/CORS et ajouter des tests HTTP reproductibles.

## Constat initial issu de l'audit

- `POST /studies/<id>/calculations` retourne un job minimal tandis que le frontend attend un résultat complet.
- Plusieurs endpoints adressent directement des lignes, jobs ou résultats par ID sans preuve explicite de propriété.
- Les routes mutatives utilisent `auth="user"`, cookie de session et `csrf=False`.
- Aucun test `HttpCase` n'est livré.
- Les erreurs d'accès ne sont pas toujours transformées en erreurs API cohérentes.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/controllers/api.py`
- modèles appelés par les contrôleurs
- `frontend/src/api/client.ts`
- `frontend/src/api/study.ts`
- reverse proxy, configuration Odoo et documentation de déploiement
- `addons/greencube_cooling/tests/`

## Travaux obligatoires

1. Inventorier toutes les routes, méthodes, paramètres, réponses, erreurs, droits et effets de bord.
2. Créer un contrat API versionné ou au minimum un document OpenAPI/JSON Schema aligné sur le code réel.
3. Normaliser les enveloppes de succès et d'erreur : `code`, `message`, `details`, `field_errors`, `request_id`.
4. Corriger le flux de calcul : `POST /studies/{id}/calculations` crée ou réutilise un job et renvoie `job_id`, `status`, `result_id` éventuel ; `GET /calculations/{job_id}` expose le statut ; `GET /results/{result_id}` expose le résultat canonique.
5. Réaliser toutes les vérifications de propriété et société avant lecture ou mutation d'une ressource adressée par identifiant.
6. Empêcher les IDOR sur équipement, ventilation, protection, job, résultat, composant et sélection.
7. Choisir et implémenter une stratégie de sécurité cohérente : même origine via reverse proxy de préférence, cookie sécurisé, CSRF actif ou jeton dédié, contrôle `Origin/Referer`, `SameSite`, `Secure` et CORS strict.
8. Ne jamais accepter `Access-Control-Allow-Origin: *` avec des credentials.
9. Capturer proprement `AccessError`, `ValidationError`, `UserError`, conflits de version et ressources absentes.
10. Ajouter une corrélation `request_id` dans les réponses et logs sans exposer de données sensibles.
11. Ajouter pagination, filtres et tri à la liste des études.
12. Documenter exemples de requêtes/réponses et codes HTTP.
13. Maintenir une compatibilité transitoire uniquement si elle est nécessaire et explicitement dépréciée.

## Tests obligatoires

- `HttpCase` ou tests HTTP équivalents exécutés sur une instance Odoo réelle.
- Cas nominal de création, mise à jour, validation, calcul, résultat et sélection.
- Test 401 sans session, 403 sur ressource d'autrui, 404 contrôlé, 409 sur version/verrouillage, 422 sur données invalides.
- Deux utilisateurs et deux sociétés pour chaque endpoint direct par ID.
- Test CSRF ou jeton de mutation selon la stratégie retenue.
- Test CORS depuis origine autorisée et refus depuis origine non autorisée.
- Test contrat JSON du job et du résultat.
- Test pagination et filtres.
- Aucun traceback serveur dans la réponse HTTP.

## Définition de terminé

- Le contrat frontend/backend est unique, versionné et testé.
- Le parcours job → résultat fonctionne réellement.
- Aucun accès croisé par simple changement d'identifiant.
- Les routes mutatives disposent d'une protection anti-CSRF/anti-origin adaptée.
- Les tests HTTP sont embarqués dans le dépôt et exécutables en CI.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-03 — Géolocalisation, altitude, fuseau et modèle Location

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Fiabiliser la résolution d'adresse et matérialiser une localisation canonique réutilisable, traçable et cohérente entre frontend et Odoo. Corriger les valeurs d'environnement urbain et les cas de coordonnées zéro.

## Constat initial issu de l'audit

- Le frontend utilise `urban_dense` alors qu'Odoo attend `dense_urban`.
- Les tests de vérité considèrent parfois latitude/longitude égales à zéro comme absentes.
- Il n'existe pas de modèle canonique Location séparé.
- La provenance, la date de résolution et le niveau de précision sont incomplets.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/services/geo.py`
- `addons/greencube_cooling/models/geo_cache.py`
- `addons/greencube_cooling/models/cooling_study.py`
- `addons/greencube_cooling/controllers/api.py`
- `frontend/src/api/geo.ts`
- `frontend/src/routes/steps/LocationStep.tsx`
- `frontend/src/types/study.ts`
- `frontend/src/sync/syncStudy.ts`

## Travaux obligatoires

1. Définir un modèle `greencube.location` ou documenter clairement pourquoi les champs restent dans l'étude pour le MVP.
2. Stocker adresse normalisée, pays, code postal, localité, latitude, longitude, altitude, fuseau IANA, fournisseur, précision, date de résolution et réponse source minimale/auditable.
3. Créer un enum canonique d'environnement : rural, suburban, urban, dense_urban, avec mapping rétrocompatible de `urban_dense`.
4. Accepter explicitement latitude ou longitude égales à zéro ; tester avec `is not None` plutôt que par vérité booléenne.
5. Valider plages latitude [-90, 90], longitude [-180, 180], altitude réaliste et fuseau IANA.
6. Définir la priorité entre saisie manuelle et géocodage, et conserver la provenance de chaque champ.
7. Gérer les résultats multiples, l'absence de résultat, les timeouts, le quota et le fallback sans inventer de données.
8. Introduire un cache avec clé normalisée, TTL, fournisseur, version et statut d'erreur.
9. Permettre la confirmation par l'utilisateur avant de figer la localisation.
10. Ne jamais envoyer l'adresse complète dans les logs applicatifs si elle n'est pas nécessaire.
11. Ajouter une migration de l'enum et des données existantes.
12. Documenter le contrat de géolocalisation et la politique de cache.

## Tests obligatoires

- Tests unitaires de normalisation et mapping d'enum.
- Tests latitude/longitude à 0, aux bornes et hors bornes.
- Tests résultat unique, multiple, vide, timeout et cache hit/miss.
- Test fuseau correct et fallback explicite.
- Test migration `urban_dense` vers `dense_urban`.
- Test utilisateur corrige manuellement une coordonnée avec provenance conservée.
- Test API empêchant l'accès à une localisation rattachée à une étude d'autrui.

## Définition de terminé

- Une seule représentation canonique de la localisation est utilisée par tous les lots.
- Les coordonnées zéro fonctionnent.
- L'enum urbain est aligné de bout en bout.
- La provenance et la précision sont visibles et persistées.
- Aucun géocodage silencieusement inventé.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-04 — Service climatique historique, scénarios et gouvernance des données

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Consolider le service climatique afin qu'il fournisse des jeux de données versionnés, reproductibles et explicitement qualifiés. Distinguer historique, année de référence, événement extrême et projection, sans présenter des données historiques comme des projections.

## Constat initial issu de l'audit

- Le service Open-Meteo et son cache sont une bonne base.
- L'interface affirme récupérer des projections climatiques alors que le service traite surtout l'historique.
- Le service est synchrone et le modèle canonique d'événement climatique manque.
- La gouvernance fournisseur, les versions et la fraîcheur sont incomplètes.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/services/climate.py`
- `addons/greencube_cooling/models/climate_dataset.py`
- `addons/greencube_cooling/models/climate_scenario.py`
- `addons/greencube_cooling/models/cooling_study.py`
- `addons/greencube_cooling/controllers/api.py`
- écrans localisation/review/résultats du frontend

## Travaux obligatoires

1. Définir les types de dataset : historical_observed, typical_year, design_day, extreme_event, projection.
2. Stocker fournisseur, endpoint, variables, période, fuseau, résolution, licence, version, date de récupération, checksum et qualité.
3. Créer ou documenter le modèle d'événement climatique et ses critères de sélection.
4. Produire des scénarios nommés et explicables : normal, chaud, extrême, avec règles traçables.
5. Ne pas appeler « projection » une extrapolation non issue d'un jeu de données prospectif reconnu.
6. Si de vraies projections sont activées, les isoler derrière un fournisseur/feature flag et stocker scénario climatique, horizon et modèle source.
7. Définir une politique de cache, reprise, timeout et circuit breaker.
8. Éviter de bloquer durablement le processus web ; prévoir un job si la collecte ou l'agrégation dépasse un temps acceptable.
9. Exposer au frontend la provenance, la période, la fraîcheur et les avertissements.
10. Définir les unités canoniques et conversions : température, humidité, rayonnement, vent.
11. Rendre le dataset immuable une fois associé à un snapshot de calcul.
12. Ajouter un mécanisme de réutilisation par localisation/période sans mélanger les sociétés ou droits.
13. Documenter les formules de sélection des design days et événements extrêmes.

## Tests obligatoires

- Tests de parsing et d'unités avec fixtures figées.
- Test reproductibilité du même dataset/checksum.
- Tests normal/chaud/extrême avec résultats déterministes.
- Test cache, timeout, fallback, données partielles et fournisseur indisponible.
- Test distinction historique/projection dans l'API et l'UI.
- Test immuabilité d'un dataset utilisé par un snapshot.
- Test changement de fournisseur ou version créant un nouveau dataset, pas une mutation silencieuse.

## Définition de terminé

- Chaque valeur climatique utilisée par un calcul est traçable.
- Les termes historique, scénario et projection sont utilisés correctement.
- Les scénarios sont reproductibles et testés.
- L'indisponibilité fournisseur produit un état explicite, jamais un faux succès.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-05A — Socle initial Honeybee / EnergyPlus et adaptateur de modèle

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Construire un socle réel mais limité pour convertir un snapshot GreenCube en modèle Honeybee/EnergyPlus validable, sans encore prétendre livrer toute l'orchestration de production. Le fonctionnement doit être strictement désactivé si les dépendances ou données nécessaires ne sont pas présentes.

## Constat initial issu de l'audit

- `services/energyplus.py` détecte les dépendances puis lève explicitement « not implemented ».
- Aucune traduction géométrique ni validation de modèle n'est disponible.
- EnergyPlus ne doit jamais être exécuté dans le processus web Odoo.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/services/energyplus.py`
- schémas/snapshots de calcul
- éventuels répertoires worker ou simulation à créer
- configuration/feature flags
- tests et fixtures

## Travaux obligatoires

1. Définir l'interface pure `build_honeybee_model(snapshot) -> model + diagnostics`.
2. Mapper géométrie, hauteur, orientation, façades, vitrages, constructions, infiltration, ventilation, occupation, éclairage, équipements et consignes.
3. Refuser explicitement toute géométrie incohérente ou donnée obligatoire absente.
4. Définir les approximations MVP et les restituer dans `diagnostics.assumptions`.
5. Produire un export Honeybee JSON déterministe et checksumé.
6. Implémenter un validateur sans lancer EnergyPlus dans Odoo.
7. Détecter versions Honeybee, Ladybug, OpenStudio et EnergyPlus ; vérifier une matrice de compatibilité.
8. Placer toutes les fonctionnalités derrière `GC_COOLING_ENERGYPLUS_ENABLED=false` par défaut.
9. Ne jamais installer dynamiquement de paquet depuis le code applicatif.
10. Préparer un contrat de job sérialisable pour le futur worker : snapshot_id, solver_version, weather_artifact, options.
11. Stocker uniquement les références d'artefacts dans Odoo, pas de gros fichiers en champ texte.
12. Ajouter une documentation des limites physiques du modèle MVP.

## Tests obligatoires

- Fixture minimale d'une pièce rectangulaire avec quatre façades et vitrages.
- Test déterminisme du JSON et du checksum.
- Test orientation/rotation.
- Test surfaces invalides, vitrages supérieurs à la façade et données manquantes.
- Test feature flag désactivé.
- Test dépendances absentes avec erreur explicite.
- Si l'environnement contient Honeybee, lancer la validation du modèle ; sinon ne pas déclarer ce test réussi.

## Définition de terminé

- Un snapshot valide peut être converti en modèle Honeybee sérialisé et validé.
- Odoo n'exécute aucune simulation EnergyPlus.
- Les approximations sont explicites.
- Le feature flag est désactivé par défaut.
- Aucune promesse de simulation complète n'est formulée à ce stade.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-06 — Frontend React, build, état et source de vérité

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Rendre le frontend compilable, testable et aligné sur Odoo comme source de vérité. Zustand doit devenir un cache de formulaire contrôlé, non la base primaire des études. Le lot doit aussi normaliser le client HTTP, la gestion d'état serveur et la validation des formulaires.

## Constat initial issu de l'audit

- Le build échoue car le client HTTP n'accepte pas `PUT` et `wallAreaM2` est inutilisé.
- La liste des études lit uniquement `localStorage`.
- Le bandeau « Enregistré » est toujours affiché.
- Aucun test de composant, d'intégration ou E2E.
- React Hook Form, Zod ou une vraie couche d'état serveur ne sont pas utilisés malgré les besoins.

## Fichiers et zones à inspecter en priorité

- `frontend/src/api/client.ts`
- `frontend/src/api/study.ts`
- `frontend/src/store/studyStore.ts`
- `frontend/src/sync/syncStudy.ts`
- `frontend/src/routes/StudiesListPage.tsx`
- `frontend/src/routes/StudyLayout.tsx`
- `frontend/src/components/layout/AppHeader.tsx`
- `frontend/package.json`, TypeScript, Vite, Vitest

## Travaux obligatoires

1. Corriger immédiatement le build TypeScript : méthode PUT, variable inutilisée et toute erreur révélée ensuite.
2. Définir des types API générés ou partagés à partir du contrat backend ; supprimer les castings optimistes.
3. Introduire une couche d'état serveur adaptée, par exemple TanStack Query, pour liste, détail, mutation, invalidation et reprise.
4. Charger les études depuis Odoo avec pagination ; le store local ne conserve qu'un brouillon non synchronisé et son statut.
5. Utiliser l'identifiant Odoo dans les routes. Permettre ouverture depuis un autre navigateur ou URL directe.
6. Implémenter un autosave contrôlé : debounce, état dirty/saving/saved/error/offline, `updated_at` ou version pour conflit optimiste.
7. N'afficher « Enregistré » qu'après confirmation backend.
8. Ne pas effacer un brouillon local tant que le backend n'a pas confirmé la sauvegarde.
9. Introduire validation Zod/formulaire sur tous les champs critiques avec messages français.
10. Gérer loading, empty, error, unauthorized, conflict et retry.
11. Supprimer le catalogue produit mock du parcours de production ou l'isoler explicitement derrière un mode démo.
12. Rendre le sélecteur de langue et l'aide fonctionnels ou les masquer.
13. Préserver le design existant et le fond blanc ; ne pas entreprendre de refonte visuelle non demandée.
14. Ajouter scripts `lint`, `typecheck`, `test`, `build` cohérents et sans avertissements bloquants.

## Tests obligatoires

- `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build` réussis.
- Tests de composant pour liste, création, chargement direct, autosave, erreur et conflit.
- Test que la suppression du localStorage ne supprime pas l'accès aux études Odoo.
- Test que « Enregistré » ne s'affiche pas avant réponse backend.
- Test réseau interrompu puis reprise.
- Test navigation directe vers une étude existante.
- Test aucune donnée mock utilisée en production.

## Définition de terminé

- Le frontend est reconstructible depuis les sources.
- Odoo est la source de vérité observable.
- Le statut de synchronisation est exact.
- Les erreurs et conflits sont traités sans perte silencieuse.
- Les tests frontend couvrent les flux critiques.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-07 — Écran localisation, climat et confirmation utilisateur

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Finaliser l'étape de localisation et de climat pour que l'utilisateur comprenne et confirme les données réellement utilisées. Ajouter les scénarios climatiques, la provenance et une carte uniquement si elle repose sur une implémentation réelle et accessible.

## Constat initial issu de l'audit

- La carte est absente.
- L'interface suggère des projections alors que les données sont historiques.
- Les scénarios ne sont ni visualisés ni confirmés.
- Les coordonnées ne sont que partiellement validées.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/LocationStep.tsx`
- `frontend/src/api/geo.ts`
- types et store d'étude
- endpoints de géolocalisation et climat
- composants UI partagés

## Travaux obligatoires

1. Organiser l'étape en trois états : recherche, confirmation de localisation, confirmation climatique.
2. Afficher adresse normalisée, coordonnées, altitude, fuseau, précision et fournisseur.
3. Permettre la correction manuelle des coordonnées avec avertissement et provenance `user_confirmed`.
4. Afficher clairement période et type des données climatiques.
5. Montrer les scénarios normal/chaud/extrême avec valeurs clés utilisées par le calcul.
6. Exiger une confirmation explicite des données estimées ou dégradées.
7. Si une carte est ajoutée, utiliser un composant léger, accessible et sans clé secrète dans le frontend ; sinon retirer toute promesse de carte.
8. Ne pas employer le terme projection sans dataset prospectif.
9. Ajouter validation bornes, messages d'erreur, état loading et retry.
10. Ajouter un lien depuis Review vers cette étape pour chaque problème de localisation/climat.
11. Rendre l'étape utilisable au clavier et sur mobile.
12. Sauvegarder uniquement après confirmation ou modification validée.

## Tests obligatoires

- Tests de recherche, résultat multiple, absence de résultat, correction manuelle et confirmation.
- Test coordonnées 0/0 et limites.
- Test fournisseur indisponible et état dégradé.
- Test affichage exact de la provenance et période.
- Test qu'une donnée non confirmée bloque Review si elle est obligatoire.
- Test navigation depuis une erreur Review vers le champ concerné.
- Test accessibilité de base et responsive.

## Définition de terminé

- L'utilisateur voit exactement quelles données seront utilisées.
- Les termes climatiques sont justes.
- Les données estimées sont confirmées.
- Aucune fonction de carte/projection fictive n'est affichée.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-08 — Modèles GreenCube et caractéristiques thermiques versionnées

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Rendre les choix Studio, Bureau, Habitat, Commerce et Personnalisé réellement fonctionnels en les branchant sur un catalogue Odoo versionné. Chaque modèle doit appliquer une géométrie, une enveloppe et une provenance déterministes, tout en permettant une personnalisation contrôlée.

## Constat initial issu de l'audit

- La sélection de modèle ne modifie que `modelCode` dans le frontend.
- `modelCode` n'est pas synchronisé au backend.
- Les dimensions et propriétés thermiques restent identiques.
- Le catalogue canonique Odoo n'est pas utilisé par l'interface.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/ModelStep.tsx`
- `frontend/src/types/study.ts`
- `frontend/src/sync/syncStudy.ts`
- `addons/greencube_cooling/models/thermal_specification.py`
- vues et données Odoo de modèles standards
- contrôleurs API

## Travaux obligatoires

1. Définir un modèle Odoo de template thermique versionné ou étendre proprement l'existant.
2. Pour chaque modèle, stocker code stable, version, statut actif, dimensions, hauteur, surfaces, U-values, composition, vitrage, toiture, plancher et hypothèses.
3. Exposer l'API de liste/détail des modèles actifs.
4. Charger le catalogue depuis Odoo dans le frontend, sans constante métier en dur.
5. À la sélection, appliquer les valeurs de la version choisie et conserver `template_id`, `template_version`, provenance et date.
6. Distinguer valeurs héritées, personnalisées et calculées.
7. Ne pas écraser silencieusement une personnalisation lors d'un rechargement du template.
8. Prévoir l'action « réappliquer le modèle » avec aperçu des changements.
9. Pour Personnalisé, rendre éditables les dimensions et propriétés requises avec validations physiques.
10. Synchroniser `modelCode` et version au backend.
11. Figer dans le snapshot les valeurs résolues, pas seulement la référence au template.
12. Prévoir une migration et des données de démonstration cohérentes.

## Tests obligatoires

- Test API catalogue et version.
- Test que Studio/Bureau/Habitat/Commerce produisent des valeurs distinctes.
- Test personnalisation d'une valeur héritée et persistance après rechargement.
- Test changement de version sans mutation rétroactive des anciennes études.
- Test snapshot contenant toutes les valeurs résolues.
- Test valeurs invalides : surface négative, vitrage incohérent, U-value hors plage.
- Test aucun modèle codé en dur utilisé en production.

## Définition de terminé

- Chaque carte modèle a un impact métier réel et vérifiable.
- Le catalogue Odoo est la source de vérité.
- Les versions historiques restent reproductibles.
- Les personnalisations sont visibles, traçables et non écrasées.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-09 — Orientation, vitrages et protections solaires physiques

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Rendre effectifs l'azimut principal, les surfaces vitrées et chaque type de protection solaire. Les données UI doivent se traduire sans perte en géométrie et paramètres physiques utilisés par le solver.

## Constat initial issu de l'audit

- L'orientation principale sélectionnée n'est pas transmise.
- Les façades restent nord/sud/est/ouest indépendamment de la rotation.
- Tous les types de protection sont réduits à `external_blind`.
- L'efficacité reste souvent sur une valeur moyenne non éditable.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/OrientationStep.tsx`
- `frontend/src/sync/syncStudy.ts`
- `frontend/src/types/study.ts`
- `addons/greencube_cooling/models/thermal_specification.py`
- `addons/greencube_cooling/models/shading.py`
- MERCURE et futur mapping EnergyPlus

## Travaux obligatoires

1. Définir l'azimut canonique en degrés, convention 0°=Nord, sens horaire, et mapper N/NE/E/SE/S/SO/O/NO.
2. Stocker l'orientation globale du bâtiment et les azimuts réels de chaque façade.
3. Choisir une seule approche : rotation des façades nominales ou saisie directe des azimuts, puis l'appliquer partout.
4. Valider surface de façade, surface vitrée, ratio vitré et cohérence géométrique.
5. Définir les types canoniques de protections : intérieur, extérieur, brise-soleil, casquette, végétation/ombrage externe.
6. Pour chaque type, définir facteur solaire/efficacité, géométrie éventuelle, calendrier, commande automatique/manuelle et provenance.
7. Permettre à l'utilisateur d'éditer les paramètres autorisés ; fournir des valeurs par défaut explicites par type.
8. Synchroniser par diff les protections ; supprimer côté backend une protection retirée dans l'UI.
9. Ne jamais convertir plusieurs types vers un seul type générique sans avertissement.
10. Inclure orientation et protections résolues dans le snapshot.
11. Rendre visibles dans les résultats les principaux gains solaires par façade.
12. Documenter les simplifications MERCURE et le mapping EnergyPlus.

## Tests obligatoires

- Tests rotation 0°, 45°, 90°, 180° et 270°.
- Test invariance contrôlée ou variation attendue des gains selon l'orientation.
- Test ratio vitré >100 % refusé.
- Test chaque type de protection produit un mapping distinct.
- Test suppression UI supprime/neutralise la protection backend.
- Test snapshot contient azimuts et paramètres de protections.
- Tests de non-régression des gains solaires MERCURE.

## Définition de terminé

- L'orientation choisie modifie réellement le calcul.
- Chaque protection visible possède un comportement métier distinct ou est explicitement signalée comme approximation.
- Aucun état supprimé côté UI ne reste actif dans Odoo.
- Les paramètres sont traçables dans le snapshot et les résultats.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-10 — Usage, occupation, calendrier et activité

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Transformer l'étape Usage/Occupation en profil exploitable par les moteurs, avec calendrier, jours, horaires, niveau d'activité et profils multiples si nécessaire. Éviter les valeurs décoratives ou figées.

## Constat initial issu de l'audit

- Usage, occupants et horaires existent partiellement.
- Jours d'occupation et activité ne sont pas réellement configurables.
- Le score et les apports ne reflètent pas toujours les données affichées.
- Le modèle canonique de profils multiples est incomplet.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/UsageStep.tsx`
- `frontend/src/types/study.ts`
- `frontend/src/sync/syncStudy.ts`
- `addons/greencube_cooling/models/occupancy_profile.py`
- modèles/snapshots/solveurs concernés

## Travaux obligatoires

1. Définir les usages canoniques et leurs valeurs par défaut sans empêcher la personnalisation.
2. Permettre configuration du nombre de personnes, densité éventuelle, niveau d'activité, chaleur sensible/latente, jours et horaires.
3. Supporter au minimum un calendrier hebdomadaire et des plages pouvant traverser minuit.
4. Valider chevauchements, horaires invalides et nombre d'occupants.
5. Si plusieurs zones ne sont pas supportées en MVP, documenter explicitement un profil global unique.
6. Conserver provenance et hypothèses par champ.
7. Synchroniser par upsert/diff plutôt que supprimer et recréer sans nécessité.
8. Inclure le profil résolu dans le snapshot.
9. Afficher sur Review le nombre d'heures occupées, le pic d'occupation et les hypothèses.
10. Faire apparaître dans les résultats la contribution sensible et latente des occupants.
11. Ajouter un modèle de données extensible aux profils multiples sans casser le MVP.
12. Définir la règle de changement d'usage sur une étude déjà calculée : nouvelle révision obligatoire.

## Tests obligatoires

- Tests profils résidentiel, bureau, commerce et inoccupé.
- Tests semaine/week-end, plage nocturne et horaires invalides.
- Test apports croissants avec occupants et activité.
- Test sensible/latent et unités.
- Test snapshot reproductible.
- Test modification après validation créant une révision.
- Test UI du calendrier au clavier et sur mobile.

## Définition de terminé

- Les paramètres d'occupation visibles sont tous utilisés ou explicitement signalés.
- Les apports sont traçables et testés.
- Le calendrier est cohérent de bout en bout.
- Une étude historique ne change pas silencieusement.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-11 — Équipements, éclairage et apports internes

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Remplacer le catalogue frontend figé et la synchronisation destructive par un catalogue Odoo, des lignes éditables et un calcul d'apports internes traçable. Préserver les identifiants et l'historique.

## Constat initial issu de l'audit

- Le catalogue est codé en dur dans `EquipmentStep.tsx`.
- Quantité, puissance, durée et simultanéité ne sont pas réellement éditables.
- La synchronisation supprime toutes les lignes backend puis les recrée.
- Cette stratégie casse l'audit, les identifiants et la concurrence.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/EquipmentStep.tsx`
- `frontend/src/api/mockCatalog.ts`
- `frontend/src/sync/syncStudy.ts`
- `addons/greencube_cooling/models/equipment_load.py`
- contrôleurs API et données Odoo

## Travaux obligatoires

1. Créer ou consolider un catalogue Odoo d'apports internes : catégorie, puissance nominale, fraction sensible/latente, facteur de veille, valeurs par défaut et version.
2. Exposer le catalogue par API paginée/recherchable.
3. Permettre ajout, modification et suppression de lignes avec quantité, puissance, durée, calendrier, simultanéité et provenance.
4. Utiliser des UUID/client IDs temporaires puis conserver les IDs Odoo après création.
5. Synchroniser par diff : create/update/delete ciblés, avec contrôle de version.
6. Ne plus supprimer/recréer toutes les lignes à chaque sauvegarde.
7. Séparer éclairage et équipements si leurs modèles physiques diffèrent.
8. Valider les unités et bornes.
9. Calculer et afficher la puissance installée, simultanée et énergie journalière indicative.
10. Figer les lignes résolues et le référentiel utilisé dans le snapshot.
11. Gérer la suppression concurrente ou modification externe par conflit explicite.
12. Retirer `mockCatalog` du build production ou le réserver aux tests/démo.

## Tests obligatoires

- Test CRUD ligne sans changement d'ID lors d'une simple modification.
- Test suppression ciblée d'une ligne.
- Test catalogue Odoo et recherche.
- Test puissance totale, simultanéité et fractions sensible/latente.
- Test quantité/power/durée à zéro, négatives et hors bornes.
- Test conflit de version.
- Test aucun appel au catalogue mock en production.
- Test snapshot conserve les valeurs même si le catalogue évolue.

## Définition de terminé

- Le catalogue métier vient d'Odoo.
- Toutes les valeurs visibles sont éditables et utilisées.
- La synchronisation est non destructive.
- L'historique d'un calcul reste reproductible après évolution du catalogue.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-12 — Ventilation, infiltration et confort

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Rendre les paramètres de ventilation, infiltration et confort explicites, cohérents en unités et réellement utilisés. Conserver les plages de consigne au lieu de les réduire silencieusement à une borne.

## Constat initial issu de l'audit

- Les plages `22-25` et `45-60` sont réduites à leur borne haute.
- Ouvertures de portes, aération, étanchéité textuelle et tolérance ne sont pas pleinement utilisées.
- Plusieurs données sont affichées mais cachées ou ignorées par le solver.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/ComfortStep.tsx`
- `frontend/src/types/study.ts`
- `frontend/src/sync/syncStudy.ts`
- `addons/greencube_cooling/models/ventilation_profile.py`
- MERCURE, snapshot et mapping EnergyPlus

## Travaux obligatoires

1. Définir les champs canoniques : ventilation type, débit, unité, horaires, récupération de chaleur, efficacité, infiltration ACH ou perméabilité, ouvertures, consigne min/max, humidité min/max et tolérance.
2. Ne pas convertir une plage en valeur unique sans règle explicite. Définir quelle valeur sert au dimensionnement et afficher cette règle.
3. Normaliser les unités et conversions dans une couche unique.
4. Mapper les niveaux textuels d'étanchéité vers des valeurs numériques documentées, tout en conservant la valeur source.
5. Gérer ventilation naturelle, mécanique simple/double flux et absence de ventilation.
6. Définir l'effet des ouvertures de portes/fenêtres ou les retirer du parcours tant qu'elles ne sont pas modélisées.
7. Calculer les apports sensible et latent de ventilation/infiltration.
8. Ajouter validations croisées : débit, volume, ACH, récupération, humidité et consignes.
9. Exposer les hypothèses dans Review et les contributions dans Results.
10. Figer toutes les valeurs résolues dans le snapshot.
11. Documenter les différences de traitement MERCURE/EnergyPlus.
12. Toute donnée non utilisée doit être signalée dans l'UI comme informative, pas présentée comme un paramètre de calcul.

## Tests obligatoires

- Tests conversions m³/h, L/s, ACH.
- Tests consigne min/max et humidité min/max conservées.
- Tests ventilation croissante → charge croissante, récupération → charge décroissante.
- Tests infiltration monotone.
- Tests valeurs incohérentes et bornes.
- Test snapshot et résultat détaillé.
- Test UI n'affiche aucun champ comme actif s'il n'est pas pris en compte.

## Définition de terminé

- Les plages ne sont plus tronquées silencieusement.
- Les unités sont canoniques et testées.
- Chaque champ est utilisé ou clairement marqué informatif.
- Les contributions ventilation/infiltration sont visibles dans les résultats.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-13 — Vérification, score de confiance, snapshot et révision

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Faire de Review une véritable porte de contrôle avant calcul : validation structurée, navigation vers les erreurs, confirmation des hypothèses, score pré-calcul distinct de la confiance solver, création de snapshot et gestion des révisions.

## Constat initial issu de l'audit

- Review affiche souvent 0 % avant calcul car il utilise `confidence_score` du solver.
- Le frontend attend `section` et des sévérités différentes de celles du backend.
- Les liens vers les champs fautifs manquent.
- Le cycle validation/révision existe côté Odoo mais n'est pas exposé.
- Le preview du snapshot et les conflits de version manquent.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/steps/ReviewStep.tsx`
- `frontend/src/api/study.ts`
- `frontend/src/types/study.ts`
- `addons/greencube_cooling/models/cooling_study.py`
- `addons/greencube_cooling/models/cooling_calculation_snapshot.py`
- contrôleurs API

## Travaux obligatoires

1. Définir un schéma de validation unique : `severity=error|warning|info`, `section_code`, `field_path`, `code`, `message`, `blocking`, `suggested_action`.
2. Aligner les types frontend sur ce schéma.
3. Calculer un score pré-calcul fondé sur complétude, provenance, fraîcheur, confirmations et avertissements ; le nommer distinctement de la confiance du solver.
4. Afficher séparément : complétude des données, qualité des données et confiance du résultat après calcul.
5. Ajouter un lien/action pour ouvrir l'étape et focaliser le champ concerné.
6. Exiger confirmation explicite des hypothèses bloquantes ou estimées selon la politique.
7. Afficher un aperçu lisible du snapshot avant lancement.
8. Créer le snapshot uniquement après validation réussie et action explicite de calcul.
9. Utiliser une version/ETag de l'étude pour refuser un snapshot sur données obsolètes.
10. Exposer validation d'étude, verrouillage, création de révision et historique dans le frontend.
11. Après validation, toute modification doit créer une révision, sans mutation de l'étude historique.
12. Afficher les différences entre révisions.
13. Garantir le checksum et l'immuabilité du snapshot.
14. Journaliser l'auteur et la date des confirmations sans stocker de données superflues.

## Tests obligatoires

- Tests schéma de validation backend/frontend.
- Test score pré-calcul non nul sur étude complète avant solver.
- Test erreur bloquante empêche le calcul.
- Test warning confirmable.
- Test navigation vers le champ fautif.
- Test conflit de version au moment du snapshot.
- Test checksum déterministe et snapshot immuable.
- Test étude validée verrouillée puis création de révision.
- Test diff de révisions.

## Définition de terminé

- Review reflète l'état réel des données.
- Le calcul ne part qu'après validation explicite.
- Les scores de complétude et confiance solver ne sont plus confondus.
- Les snapshots et révisions sont reproductibles et immuables.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-14 — Moteur MERCURE canonique, traçabilité et non-régression

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Conserver MERCURE comme moteur MVP canonique côté Python/Odoo, renforcer ses schémas, sa traçabilité et ses tests, et éviter que l'implémentation TypeScript parallèle devienne une seconde source de vérité divergente.

## Constat initial issu de l'audit

- MERCURE Python et TypeScript disposent de tests réussis.
- Deux implémentations parallèles créent un risque de divergence.
- Le frontend ne doit pas calculer un résultat métier canonique localement.
- Les champs ignorés ou approximés doivent être explicités.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/services/mercure/`
- `frontend/src/mercure/`
- mapping snapshot → input
- modèles solver version, résultat et composants
- tests Python/TypeScript

## Travaux obligatoires

1. Déclarer Python/Odoo comme implémentation canonique de production.
2. Définir un schéma d'entrée et de sortie versionné, avec unités et champs obligatoires.
3. Enregistrer version du solver, version du schéma, checksum d'entrée et paramètres.
4. Supprimer l'usage production du moteur TS ou le limiter à une estimation clairement non contractuelle.
5. Si le port TS est conservé, ajouter des tests de conformité sur les mêmes fixtures et tolérances numériques.
6. Centraliser les conversions et constantes ; éviter les valeurs magiques dupliquées.
7. Retourner un breakdown complet et stable : transmission, solaire, occupants, équipements, éclairage, ventilation, infiltration, latent, marges.
8. Lister dans le résultat les hypothèses, avertissements et champs ignorés.
9. Définir la méthode de capacité recommandée, marge et arrondi commercial.
10. Ajouter tests monotones et limites physiques.
11. Ajouter fixtures de référence versionnées et documentées.
12. Garantir qu'un même snapshot et une même version produisent le même résultat.
13. Ne pas recalculer ou modifier un résultat terminé.
14. Documenter les limites d'usage de MERCURE face à EnergyPlus.

## Tests obligatoires

- Tests unitaires Python existants et nouveaux.
- Tests déterminisme et checksum.
- Tests de conformité TS/Python si TS conservé.
- Tests monotones : surface, U-value, vitrage, température extérieure, occupants, équipements, infiltration.
- Tests unités et conversions.
- Golden fixtures avec tolérance explicitée.
- Test résultat terminé immuable.
- Test champs ignorés présents dans les diagnostics.

## Définition de terminé

- Une seule implémentation est canonique.
- Les entrées/sorties sont versionnées et reproductibles.
- Les contributions sont explicables.
- Le frontend ne peut pas substituer silencieusement un calcul local au résultat Odoo.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-15 — Jobs, worker, artefacts et orchestration EnergyPlus

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Implémenter l'orchestration asynchrone EnergyPlus hors du processus web Odoo : modèle de job, file d'attente, worker isolé, artefacts, statuts, reprise et sécurité. Ce lot ne doit être activé en production que si une simulation réelle est exécutée et vérifiée.

## Constat initial issu de l'audit

- Aucun modèle de job, worker, file Redis ou artefact n'existe.
- Le contrôleur présente actuellement le résultat comme un job déjà terminé.
- Aucun EPW/IDF/SQL/log n'est conservé.
- La comparaison MERCURE/EnergyPlus n'est pas disponible.

## Fichiers et zones à inspecter en priorité

- nouveau modèle `greencube.cooling.calculation.job`
- nouveau modèle `greencube.simulation.artifact`
- service/worker séparé à créer
- Docker/compose, Redis ou file choisie
- contrôleurs de job
- stockage objet ou volume d'artefacts
- tests d'intégration

## Travaux obligatoires

1. Créer le modèle de job avec moteur, snapshot, statut, progression, tentative, timestamps, erreur normalisée, result_id et idempotency_key.
2. Définir les statuts `queued`, `running`, `completed`, `failed`, `cancelled` et transitions autorisées.
3. Créer un worker séparé sans accès direct à PostgreSQL ; il consomme un payload signé/minimal et publie le résultat via une API/service contrôlé.
4. Choisir une file durable et documenter retry, backoff, dead-letter et concurrence.
5. Générer et stocker les artefacts : Honeybee JSON, EPW, IDF/OSM éventuel, stdout/stderr, SQL, résultats synthétiques, manifest/checksums.
6. Utiliser un stockage objet/volume avec références Odoo, politique de rétention et contrôle d'accès.
7. Vérifier versions et compatibilité des solveurs dans l'image worker.
8. Ajouter timeouts CPU/mémoire, sandbox, utilisateur non root et limites de ressources.
9. Ne jamais exécuter une commande construite depuis une entrée utilisateur non validée.
10. Implémenter idempotence par snapshot+engine+version+options.
11. Exposer polling API et éventuellement évènements ; le polling doit fonctionner sans websocket.
12. Créer le résultat Odoo uniquement après validation du manifeste et checksum.
13. Comparer MERCURE/EnergyPlus avec règle de tolérance et signaler les écarts.
14. Garder le feature flag désactivé jusqu'à réussite d'un test de simulation réelle.
15. Ajouter procédure d'exploitation, reprise et nettoyage des artefacts.

## Tests obligatoires

- Test transitions de job et transitions interdites.
- Test idempotence et double soumission.
- Test worker succès sur une simulation réelle minimale si dépendances présentes.
- Test timeout, crash, retry, échec permanent et dead-letter.
- Test artefacts/checksums et accès non autorisé.
- Test aucune connexion DB directe depuis le worker.
- Test limites de ressources et commande sûre.
- Test comparaison MERCURE/EnergyPlus.
- Test feature flag désactivé par défaut.
- Ne pas déclarer EnergyPlus livré sans preuve d'un run réel.

## Définition de terminé

- Les simulations sont réellement asynchrones et isolées.
- Les jobs sont observables, idempotents et récupérables.
- Les artefacts sont traçables et sécurisés.
- EnergyPlus reste désactivé si le test réel n'est pas démontré.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-16 — Résultats, job polling et recommandation de puissance

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Corriger l'écran Résultats et le flux de calcul afin qu'un seul calcul soit déclenché explicitement, suivi par job, puis affiché depuis un résultat canonique Odoo. Présenter les contributions, hypothèses, scénarios et capacité commerciale sans erreur de contrat.

## Constat initial issu de l'audit

- `ResultsPage` lance un calcul à chaque montage.
- Aucun `Idempotency-Key` n'est envoyé.
- Le frontend traite la réponse de job comme un résultat complet.
- React Strict Mode peut accentuer les doublons.
- La comparaison de moteurs et la consultation d'un résultat existant manquent.

## Fichiers et zones à inspecter en priorité

- `frontend/src/routes/ResultsPage.tsx`
- `frontend/src/api/study.ts`
- `frontend/src/routes/steps/ReviewStep.tsx`
- endpoints calculation/job/result
- modèles result/component/commercial capacity

## Travaux obligatoires

1. Déclencher le calcul uniquement depuis une action explicite de Review.
2. Générer une clé d'idempotence stable pour la soumission et la persister jusqu'à réponse.
3. Naviguer vers `/studies/{studyId}/calculations/{jobId}` ou route équivalente.
4. Poller le job avec backoff raisonnable et arrêt sur statut terminal.
5. Charger ensuite le résultat par `result_id` ; ne jamais supposer que le job contient tout le résultat.
6. En consultation, charger le résultat actif sans recalcul.
7. Gérer queued/running/completed/failed/cancelled, retry contrôlé et messages détaillés.
8. Aligner tous les types sur le schéma API réel.
9. Afficher capacité de base, marge, capacité recommandée W/kW/BTU/h et palier commercial.
10. Afficher breakdown, facteurs principaux, hypothèses, avertissements, qualité et solver version.
11. Afficher les scénarios et, si disponible, comparaison MERCURE/EnergyPlus avec écart expliqué.
12. Synchroniser le statut de l'étude dans la liste Odoo.
13. Garantir qu'un retour arrière ou refresh ne crée aucun nouveau calcul.
14. Rendre les erreurs accessibles et permettre retour vers Review.
15. Ajouter export JSON/CSV technique minimal si requis, sans prétendre livrer le PDF commercial final.

## Tests obligatoires

- Test un clic = un job.
- Test double clic, refresh, retour arrière et Strict Mode sans doublon.
- Test polling succès, échec, timeout et annulation.
- Test job terminé puis récupération du résultat.
- Test consultation d'un résultat existant sans POST.
- Test unités et capacité commerciale.
- Test affichage des avertissements et facteurs.
- Test contrat API avec fixtures réelles.
- Test responsive et accessibilité de la progression.

## Définition de terminé

- L'écran Résultats ne plante plus sur le contrat API.
- Aucun recalcul involontaire.
- Le job et le résultat sont des objets distincts correctement suivis.
- Les résultats sont explicables, reproductibles et consultables ultérieurement.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-17 — Consolidation MVP, CI, recette et déploiement

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Consolider l'ensemble des lots corrigés en une version MVP installable, testée, sécurisée et documentée. Ce prompt doit être appliqué après les prompts fonctionnels précédents et ne doit pas masquer les échecs par des mocks de livraison.

## Constat initial issu de l'audit

- Le build initial était cassé.
- Les tests couvrent surtout MERCURE, pas le parcours HTTP/React.
- Les documents Master V2, migrations, Docker/worker et preuves de recette sont incomplets.
- Le README contient des affirmations historiques non reproductibles depuis le ZIP.

## Fichiers et zones à inspecter en priorité

- dépôt complet
- CI GitHub Actions ou équivalent
- Docker/compose/reverse proxy
- README, docs, migrations
- tests Odoo, API, frontend, Playwright
- scripts de sauvegarde/rollback

## Travaux obligatoires

1. Établir `docs/cooling_v2_initial_state.md` et conserver les échecs initiaux.
2. Créer la matrice de traçabilité 01–18 avec preuves de code et tests.
3. Normaliser les versions de Python, Node, Odoo, PostgreSQL et dépendances.
4. Mettre en place une CI séparant lint, typecheck, tests frontend, build, tests Python, tests Odoo, tests HTTP et E2E.
5. Ajouter un environnement de test reproductible avec Odoo/PostgreSQL et données de test.
6. Ajouter Playwright pour le parcours : création → localisation → modèle → orientation → usage → équipements → confort → Review → calcul MERCURE → résultat → sélection → validation → révision.
7. Ajouter tests de sécurité deux utilisateurs/deux sociétés.
8. Ajouter migrations et test d'upgrade sur une copie de données.
9. Documenter reverse proxy même origine, cookies, CSRF, CORS et secrets.
10. Ajouter healthchecks pertinents sans exposer de détails sensibles.
11. Ajouter logs structurés et request/job IDs.
12. Préparer sauvegarde PostgreSQL, artefacts, configuration et procédure de restauration testée.
13. Préparer rollback applicatif et migration, avec limites explicites.
14. Mettre à jour le README uniquement avec des commandes réellement exécutées.
15. Éliminer les fichiers `__pycache__`, artefacts temporaires et secrets du livrable.
16. Produire un changelog, inventaire de fichiers et décision GO/NO-GO fondée sur les critères.
17. Ne pas activer EnergyPlus si les critères du lot 15 ne sont pas prouvés.

## Tests obligatoires

- Pipeline CI complet vert sur commit propre.
- Installation neuve du module Odoo.
- Upgrade depuis la version du ZIP.
- Build frontend reproductible.
- Tests HTTP et Playwright réels.
- Scan dépendances et secrets.
- Test sauvegarde/restauration.
- Test rollback documenté sur environnement de test.
- Test responsive et accessibilité minimale.
- Aucune affirmation de succès sans log ou rapport attaché.

## Définition de terminé

- Aucun P0 ouvert.
- Aucun P1 ouvert sur le parcours principal MERCURE.
- CI et recette sont reproductibles.
- Documentation et code sont alignés.
- Une décision GO/NO-GO argumentée est produite.
- EnergyPlus est clairement activé ou désactivé selon les preuves.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.


---

# GC-COOLING-18 — Sélection d'équipement, compatibilité et immuabilité commerciale

## Rôle

Tu es l'agent de développement principal chargé de corriger et consolider ce lot dans le dépôt GreenCube Cooling. Tu dois travailler directement sur l'existant, avec une approche de patch conservatrice et vérifiable.

## Objectif

Finaliser le parcours de sélection d'équipement à partir du résultat canonique, avec catalogue Odoo, règles de compatibilité versionnées, comparaison, justification et sélection validée immuable.

## Constat initial issu de l'audit

- Le catalogue et le moteur de compatibilité existent.
- La validation complète n'est pas exposée dans le frontend.
- `write()`/`unlink()` d'une sélection validée ne sont pas globalement bloqués.
- Le snapshot produit/prix et la comparaison sont incomplets.
- Le tri par `oversizing_ratio` doit être robuste aux valeurs absentes.

## Fichiers et zones à inspecter en priorité

- `addons/greencube_cooling/models/equipment_selection.py`
- `addons/greencube_cooling/models/product_template.py`
- `addons/greencube_cooling/services/compatibility.py`
- `addons/greencube_cooling/data/cooling_equipment_data.xml`
- `frontend/src/routes/EquipmentSelectionPage.tsx`
- `frontend/src/equipment/compatibility.ts`
- API associée

## Travaux obligatoires

1. Définir le catalogue Odoo canonique : capacités nominales et aux conditions, plage de fonctionnement, rendement, alimentation, bruit, fluide, dimensions, disponibilité, prix/version et source.
2. Définir les règles de compatibilité versionnées et leur explication.
3. Calculer les recommandations exclusivement côté backend à partir du résultat canonique et du contexte électrique/installation disponible.
4. Rendre le tri robuste aux valeurs absentes ; définir un ordre stable.
5. Exposer une comparaison de 2 à 4 équipements avec critères techniques et raisons de compatibilité/incompatibilité.
6. Permettre une sélection avec justification utilisateur et avertissements confirmés.
7. À validation, figer un snapshot complet des données produit, règle, prix/devise/date, capacité requise, solver et résultat source.
8. Interdire `write()` et `unlink()` sur une sélection validée.
9. Toute substitution crée une nouvelle sélection avec lien `supersedes_id`, sans modifier l'historique.
10. Gérer produit archivé ou prix changé sans altérer les anciennes sélections.
11. Ajouter une action frontend de validation et un écran d'historique.
12. Supprimer ou isoler le moteur de compatibilité frontend s'il peut diverger ; le backend reste canonique.
13. Ajouter permissions utilisateur/société et prévention IDOR.
14. Ne pas transformer la recommandation technique en devis/facture sans lot commercial séparé.

## Tests obligatoires

- Tests de compatibilité aux limites de capacité et température.
- Test données manquantes et tri stable.
- Test comparaison et explications.
- Test sélection validée immuable, suppression refusée et supersession.
- Test produit/prix modifié après validation sans effet historique.
- Test deux utilisateurs/deux sociétés.
- Test cohérence backend/frontend.
- Test snapshot de sélection complet et checksumé si prévu.
- Test parcours E2E résultat → sélection → validation → historique.

## Définition de terminé

- Les recommandations sont calculées côté Odoo et explicables.
- Une sélection validée est historiquement immuable.
- Les données produit/prix utilisées sont figées.
- La substitution conserve un chaînage d'audit complet.
- Aucun utilisateur ne peut voir ou modifier la sélection d'un autre.

## Règles d'exécution non négociables

- Commencer par inspecter le dépôt réel et établir un état initial. Ne jamais supposer qu'un fichier, modèle, route ou test existe.
- Ne pas réécrire le module complet. Préserver les composants fonctionnels existants et produire des modifications incrémentales.
- Ne supprimer, déplacer ou renommer aucun fichier sans justification explicite dans le rapport final. Avant toute suppression, rechercher ses imports, références XML, imports Python, routes et usages de build.
- Ne jamais modifier `frontend/dist` à la main. Le dossier doit être régénéré uniquement par le build du frontend.
- Odoo Community 18 est la source de vérité métier. Le frontend ne doit pas devenir la base primaire des études, résultats, catalogues ou prix.
- Respecter le multi-sociétés, la propriété par utilisateur, les règles d'enregistrement Odoo et l'immuabilité des objets historiques.
- Ne pas utiliser `sudo()` comme contournement général. Toute élévation doit être ciblée, justifiée, précédée d'une vérification d'accès et couverte par des tests.
- Toute modification de schéma doit disposer d'une stratégie de migration. Ne jamais casser les données existantes silencieusement.
- Ne déclarer aucun test, build, installation ou migration comme réussi sans l'avoir exécuté. Fournir la commande et le résultat réel.
- Si une dépendance externe manque, ne pas simuler un succès. Documenter le blocage et laisser la fonctionnalité derrière un feature flag sûr.
- Les erreurs doivent être structurées, compréhensibles par le frontend et ne jamais exposer de trace interne ou de secret.
- Maintenir la compatibilité avec Python/Odoo 18, React 18, TypeScript et Vite présents dans le dépôt, sauf décision explicitement documentée.

## Format obligatoire du compte rendu final

À la fin, fournir :

1. résumé des changements réellement réalisés ;
2. fichiers créés, modifiés, déplacés ou supprimés ;
3. décisions d'architecture ;
4. migrations et compatibilité ascendante ;
5. commandes exécutées ;
6. résultats exacts des tests, du typecheck, du lint et du build ;
7. anomalies restantes classées P0/P1/P2/P3 ;
8. risques et limites ;
9. procédure de validation manuelle ;
10. statut final `DONE`, `PARTIAL` ou `BLOCKED`, sans embellissement.
