# Matrice de sécurité — GreenCube Cooling

Référence : `security/ir.model.access.csv` (ACL par modèle/groupe) et
`security/greencube_cooling_rules.xml` (`ir.rule`, propriété par
enregistrement). Ce document décrit l'état après le lot de stabilisation
du 2026-07-20 (suite à `Audit_fonctionnel_GreenCube_Cooling_18-07-2026.md`,
prompts P0-03/P0-05/GC-COOLING-01), **mis à jour le 2026-07-21** lors de
l'exécution formelle du prompt GC-COOLING-01 (module version `18.0.5.0.0`).

## Correctifs du 2026-07-21 (GC-COOLING-01)

Trouvés en relisant `greencube_cooling_rules.xml` règle par règle contre la
matrice ci-dessous (donc avant toute exécution réelle des tests) :

1. **Manager bloqué sur le catalogue standard.** `rule_thermal_specification_user_owns_private`
   et son miroir `rule_thermal_facade_user_owns_private` sont scopées au
   groupe `group_greencube_cooling_user`, et un Manager est aussi membre de
   ce groupe (via `implied_ids`). Comme ces règles excluent explicitement
   `standard_model=True`, c'était la SEULE règle non globale octroyant
   write/create/unlink sur ces deux modèles pour un Manager : un Manager
   n'avait donc en pratique aucun moyen d'éditer un modèle GreenCube
   standard (`standard_model=True`), malgré une ACL manager `1,1,1,1` —
   contredisant GC-COOLING-01 pt 4. Ajout de
   `rule_thermal_specification_manager_full` et
   `rule_thermal_facade_manager_full` (groupe manager, domaine
   `company_id in company_ids`, sans restriction sur `standard_model`).
2. **`greencube.cooling.commercial.capacity` sans cloisonnement société.**
   Aucun `ir.rule` n'existait pour ce modèle : un Manager de la société A
   pouvait lire/modifier/supprimer un palier de capacité `company_id`
   appartenant à la société B. Ajout de `rule_commercial_capacity_company`
   (règle globale, `company_id = False OR company_id in company_ids`, pour
   préserver les paliers globaux non rattachés à une société).
3. **`greencube.cooling.solver.version.unlink()` non gardé.** `write()`
   bloquait déjà la modification de `coefficients_json` une fois la
   version utilisée par un résultat (`is_used`), mais `unlink()` n'était
   pas surchargé : une version utilisée pouvait être supprimée, cassant
   `result.solver_version_id` et l'auditabilité, contredisant GC-COOLING-01
   §16.3 ("une version utilisée ne peut pas être supprimée"). `unlink()`
   lève désormais `UserError` si `is_used`.
4. **Domaine de propriété des spécifications privées non borné à la
   société.** `rule_thermal_specification_user_owns_private` (et son
   miroir façade) autorisait l'édition d'une spécification privée
   **pas encore rattachée à une étude** (`study_ids = False`) par
   n'importe quel User de n'importe quelle société — l'ancrage société
   n'existait qu'indirectement, une fois la spécification liée à une étude
   de son propriétaire. Ajout explicite de `('company_id', 'in',
   company_ids)` en tête du domaine des deux règles.
5. **Index manquants sur les clés de recherche de l'API** (GC-COOLING-01
   pt 11) : `greencube.cooling.study.user_id`, `.state`, et
   `greencube.cooling.equipment.selection.result_id` n'étaient pas
   indexés alors que l'API filtre dessus (`/studies?status=...`, liste
   "mes études", résolution de sélection par résultat). `index=True`
   ajouté aux trois champs — changement purement additif, aucun script de
   migration nécessaire (voir `migrations/README.md` : Odoo crée l'index
   via `_auto_init` au prochain `-u`).

Aucun de ces cinq points n'était couvert par un test avant ce lot ; les
tests correspondants ont été ajoutés dans
`tests/test_cooling_study.py::TestCoolingStudySecurity` (voir §"Tests
ajoutés" en bas de ce document) et **exécutés réellement** contre
l'instance Docker `gc_odoo`/`gc_pg` (voir le rapport final de session pour
la commande et la sortie).

Non couvert par ce document : ce n'est pas une preuve d'exécution à elle
seule pour les sections écrites le 2026-07-20. Les `ir.rule`/ACL ci-dessous
ont été relus statiquement (XML/CSV valides,
lecture du code) mais **pas rejoués sur une instance Odoo réelle** dans cet
environnement (aucun Odoo installé ici — voir `README.md`). La procédure de
validation manuelle en bas de ce document doit être exécutée avant toute
recette.

## Groupes

`group_greencube_cooling_user` ⊂ `group_greencube_cooling_technician` ⊂
`group_greencube_cooling_manager` ⊂ `group_greencube_cooling_admin`
(hiérarchie par `implied_ids` — un Manager a donc automatiquement tous les
droits d'un Technician, qui a tous les droits d'un User).

- **User** : opère ses propres études de bout en bout (créer, saisir,
  calculer, sélectionner un équipement).
- **Technician** : voit et modifie toutes les études de sa société, pas
  seulement les siennes (support, revue).
- **Manager** : en plus, administre les référentiels (modèles thermiques
  standards, capacités commerciales, versions du solveur).
- **Admin** : hérite de tout, réservé à la configuration du module.

## Matrice par modèle

| Modèle | Lecture User | Écriture/Création User | Suppression User | Portée `ir.rule` |
|---|---|---|---|---|
| `greencube.cooling.study` | ✅ (ses études) | ✅ (ses études) | ❌ | `study.user_id = user.id` (OR technicien: toute la société) ; global : `company_id in company_ids` |
| `greencube.thermal.specification` | ✅ (société) | ✅ **uniquement si** `standard_model=False` et rattachée à une de ses études (ou pas encore rattachée) | ❌ (unlink réservé, voir note) | Lecture : `company_id in company_ids`. Écriture/création/unlink : `standard_model=False AND (study_ids=False OR study_ids.user_id=user.id)` |
| `greencube.thermal.facade` | ✅ (société) | ✅ **uniquement** si la spécification parente est privée et sienne | ✅ (même condition) | Miroir de la règle ci-dessus via `thermal_specification_id.*` |
| `greencube.cooling.occupancy.profile` | ✅ (ses études) | ✅ (ses études) | ✅ (ses études) | `study_id.user_id = user.id` (OR technicien société) ; global société |
| `greencube.cooling.equipment.load` | idem | idem | idem | idem, via `study_id` |
| `greencube.cooling.ventilation.profile` | idem | idem | idem | idem, via `study_id` |
| `greencube.cooling.shading` | idem | idem | idem | idem, via `study_id` |
| `greencube.cooling.result` | ✅ (ses études) | ❌ (immuable, voir note) | ❌ (immuable) | `study_id.user_id = user.id` (OR technicien société) ; global société |
| `greencube.cooling.result.component` | ✅ (ses études, via résultat) | ❌ | ❌ | `result_id.study_id.user_id = user.id` (OR technicien) ; global société |
| `greencube.cooling.calculation.snapshot` | ✅ (ses études) | ❌ (immuable, voir note) | ❌ | `study_id.user_id = user.id` (OR technicien société) ; global société — **corrigé dans le lot simulation (2026-07-20)** : ne portait auparavant qu'une règle société, sans propriété par utilisateur (oubli du balayage P0-05 initial) |
| `greencube.cooling.equipment.selection` | ✅ (société) | ✅ tant que `state != 'validated'` | ❌ si `state == 'validated'` | ACL société existante ; immuabilité au niveau `write()`/`unlink()` (voir note) |
| `greencube.cooling.calculation.job` | ✅ (ses études) | ❌ (User ; write=1 en ACL mais verrouillé une fois `completed`/`failed` sauf `energyplus_processing_status`) | ❌ | `study_id.user_id = user.id` (OR technicien société) ; global société |
| `greencube.cooling.simulation.artifact` | ✅ (ses études, via job) | ❌ (immuable) | ❌ | `job_id.study_id.user_id = user.id` (OR technicien société) ; global société |
| `greencube.cooling.climate.scenario`, `.solver.version`, `.commercial.capacity` | ✅ (lecture seule) | ❌ (Manager uniquement) | ❌ | Référentiels : gérés par Manager, jamais par User |
| `greencube.cooling.geo.cache`, `.climate.dataset` | ✅ | ✅ (cache technique, pas de donnée métier privée) | ❌ | Pas de portée par étude : ce sont des caches partagés par coordonnées, pas des objets appartenant à un utilisateur |

**Note — immuabilité au niveau `write()`/`unlink()` (pas seulement ACL) :**
`greencube.cooling.calculation.snapshot`, `greencube.cooling.result`,
`greencube.cooling.equipment.selection` (état `validated`),
`greencube.cooling.calculation.job` (une fois `completed`/`failed`, sauf
son propre champ `energyplus_processing_status`) et
`greencube.cooling.simulation.artifact` (toujours) surchargent
`write()`/`unlink()` pour lever un `UserError` sur toute tentative de
mutation en dehors de la seule transition d'état interne autorisée
(`state -> superseded`). Ceci est **indépendant** des ACL/`ir.rule` : même
un Manager avec tous les droits ACL ne peut pas modifier un résultat ou un
snapshot déjà créé, ni un équipement validé, par ce chemin. C'est la
garantie d'immuabilité demandée par GC-COOLING-01 pt 7/8.

**Bug corrigé dans le lot simulation (2026-07-20) :** l'ACL de
`greencube.cooling.result` et `greencube.cooling.result.component` pour le
groupe User interdisait `create` (`perm_create=0`), alors que
`action_calculate()` crée ces enregistrements sans `sudo()`. Un utilisateur
standard appelant `POST /calculations` aurait donc dû échouer avec une
`AccessError` — non détecté plus tôt car les tests `TransactionCase`
existants appellent cette méthode via `.sudo()` (`test_plain_user_cannot_validate`),
masquant le problème. `perm_create` est passé à `1` pour les deux ; `write`
et `unlink` restent à `0` (protégés de toute façon par les surcharges
Python ci-dessus, et aucun code n'écrit `state=superseded` sur un résultat
en tant qu'utilisateur simple aujourd'hui).

## Contrôleur HTTP

Toutes les routes de `controllers/api.py` sont décorées `@_guarded` : une
`AccessError` (violation d'`ir.rule`) ou `MissingError` (enregistrement
supprimé entre temps) levée par l'ORM est convertie en réponse JSON
standard (`COOLING_ACCESS_DENIED` / `COOLING_NOT_FOUND`) au lieu de la page
d'erreur HTML par défaut d'Odoo. Les endpoints qui adressent une
sous-ressource par id direct (`PATCH/DELETE /equipment-loads/<id>`,
`GET /results/<id>`, `GET /calculations/<id>`, ...) reposent entièrement
sur ces `ir.rule` pour empêcher l'IDOR : il n'y a pas de vérification de
propriété dupliquée dans le contrôleur, par choix (single source of truth
= les règles ORM, pas une vérification ad hoc par route qui pourrait
diverger).

## Procédure de validation manuelle (à exécuter sur une vraie instance Odoo)

1. Créer deux sociétés `A` et `B`, deux utilisateurs standards
   `user_a` (société A) et `user_b` (société B), un technicien
   `tech_a` (société A) et un manager `mgr`.
2. `user_a` crée une étude, une spécification thermique privée, un profil
   d'occupation, une ligne d'équipement. Vérifier qu'aucune `AccessError`
   n'apparaît (ce que l'audit appelait "le rôle User n'est pas
   fonctionnel").
3. `user_b` tente de lire/modifier/supprimer chacun de ces enregistrements
   par id direct (`GET/PATCH/DELETE`). Attendu : `403 COOLING_ACCESS_DENIED`
   partout, jamais de traceback ni de données exposées.
4. `tech_a` doit voir et pouvoir modifier l'étude de `user_a` (même
   société) mais pas une étude de la société B.
5. `user_a` calcule sa cooling study, obtient un résultat, puis tente
   `PATCH`/`unlink` direct sur `greencube.cooling.result`,
   `greencube.cooling.calculation.snapshot` : attendu `UserError`
   (immutabilité), pas seulement un refus ACL.
6. `user_a` sélectionne un équipement, le fait passer à `state=validated`
   (flux métier existant), puis tente de le modifier/supprimer : attendu
   `UserError`.
7. `mgr` doit pouvoir créer/modifier une `greencube.thermal.specification`
   avec `standard_model=True` (catalogue) ; `user_a` doit échouer sur la
   même opération mais réussir à créer sa propre spécification privée.
8. Exécuter les `TransactionCase` existants dans `tests/` et les compléter
   avec les scénarios 1 à 7 ci-dessus s'ils manquent.

## Tests ajoutés (GC-COOLING-01, 2026-07-21)

Dans `tests/test_cooling_study.py::TestCoolingStudySecurity` :

- `test_user_can_create_and_modify_own_private_spec_and_children` : le
  wizard complet (étude + spécification privée + façade + occupation) est
  réalisable par un simple User sans `AccessError`.
- `test_manager_cannot_create_private_spec_shortcut_but_can_edit_catalog` :
  confirme le correctif §1 ci-dessus (Manager édite le catalogue standard ;
  User échoue dessus).
- `test_user_a_cannot_read_or_write_user_a2_child_objects` : isolation par
  propriétaire **au sein de la même société** (pas seulement inter-société)
  sur étude, profil d'occupation et ligne d'équipement.
- `test_manager_can_manage_company_studies_without_becoming_owner` :
  le Manager agit sur une étude privée sans que `user_id` change.
- `test_manager_cannot_access_company_b_objects` : le Manager reste borné
  à ses propres sociétés.
- `test_validated_equipment_selection_is_immutable` : `write()`/`unlink()`
  sur une sélection `state=validated` lèvent `UserError`.
- `test_used_solver_version_cannot_be_deleted` : confirme le correctif §3.

Ces tests s'ajoutent à ceux déjà présents (immuabilité résultat/snapshot,
verrouillage de spécification utilisée, révision, multi-société de base).
Procédure d'exécution réelle et résultat : voir le rapport final de
session (recherche `GC-COOLING-01` dans l'historique git).

## Limites connues

- Les modèles de cache (`geo.cache`, `climate.dataset`) ne sont pas
  cloisonnés par société : deux sociétés partagent le même cache
  météo/géocodage pour les mêmes coordonnées. C'est un choix assumé (ce
  sont des données publiques, pas des données métier privées), mais à
  documenter explicitement si une société souhaite un cloisonnement strict.
- Aucune migration de schéma n'a été nécessaire pour ce lot : seuls des
  `ir.rule`/ACL et des méthodes `write()`/`unlink()` ont changé, pas de
  champ ni de table.
