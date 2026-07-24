# Inventaire des routes — GreenCube Cooling API

Référence : `addons/greencube_cooling/controllers/api.py` (base
`/api/v1/greencube/cooling`, `auth="user"`, `csrf=False` partout — voir la
stratégie same-origin dans le `README.md` du module et
`docs/cooling_security_matrix.md`). Ce n'est pas une spécification OpenAPI
formelle (aucune génération automatique n'est en place) : c'est un
inventaire tenu à la main, à mettre à jour à chaque route ajoutée ou
modifiée (GC-COOLING-02 pt 1/2).

Toutes les routes renvoient l'enveloppe standard :

```json
// succès
{ "data": <payload> }

// erreur
{
  "error": {
    "code": "COOLING_XXX",
    "message": "...",
    "field": null,
    "section": null,
    "action": null,
    "request_id": "req-..."
  }
}
```

`AccessError`/`MissingError` de l'ORM sont interceptées par le décorateur
`@_guarded` (appliqué à toutes les routes) et retournées respectivement en
`403 COOLING_ACCESS_DENIED` / `404 COOLING_NOT_FOUND`.

## Études

| Méthode | Route | Effet | Codes d'erreur notables |
|---|---|---|---|
| GET | `/studies?limit&offset&search` | Liste paginée des études visibles (`ir.rule`) | — |
| POST | `/studies` | Crée une étude vide | — |
| GET | `/studies/<id>` | Détail d'une étude | 404 |
| PATCH | `/studies/<id>` | Met à jour les champs de premier niveau (localisation, confort...). Supporte `If-Match` (comparé à `write_date`) | 404, 409 `COOLING_STUDY_VERSION_CONFLICT`, 409 `COOLING_STUDY_LOCKED` |
| POST | `/studies/<id>/revisions` | Crée une révision d'une étude verrouillée | 404, 422 |
| POST | `/studies/<id>/validate` | Valide/verrouille une étude calculée | 404, 422 |
| GET | `/studies/<id>/validation` | Rapport de validation structuré + `completeness_score`/`confidence_score` | 404 |
| POST | `/studies/<id>/assumptions/confirm` | Confirme en masse les hypothèses non mesurées | 404, 422 |

## Géolocalisation

| Méthode | Route | Effet |
|---|---|---|
| GET | `/geocode?query` | Recherche d'adresse (Open-Meteo geocoding, cache) |
| GET | `/geo-context?latitude&longitude` | Altitude, fuseau, contexte (cache 30 j) |

## Sous-ressources d'étude

| Méthode | Route | Effet | Notes |
|---|---|---|---|
| GET/PUT | `/studies/<id>/thermal-specification` | Spécification thermique + façades (remplacement complet des façades au PUT) | PUT force un fork privé si la spec est `standard_model=True` ou partagée |
| GET/PUT | `/studies/<id>/occupancy-profile` | Profil d'occupation (unique par étude) | 409 `INVALID_STATE` si l'étude est `validated` (créer une révision) |
| GET/PUT | `/studies/<id>/ventilation-profile` | Profil de ventilation (unique par étude) | |
| GET/PUT | `/studies/<id>/shading` | Protections solaires (remplacement complet de la liste au PUT) | |
| GET/POST | `/studies/<id>/equipment-loads` | Liste / création d'une ligne d'apport interne | |
| PATCH/DELETE | `/equipment-loads/<line_id>` | Modifie / supprime une ligne par id direct | Protégé uniquement par `ir.rule` (pas de re-vérification de propriété dans le contrôleur — voir `docs/cooling_security_matrix.md`) |
| GET | `/equipment-load-catalog` | Catalogue Odoo des apports internes de référence (ordinateur, écran, éclairage LED, électroménager, batterie, onduleur, ...) proposés par l'écran Équipements | `product.template` où `is_internal_load_equipment=True` — jamais codé en dur côté frontend (GC-COOLING-11) |

### Orientation, vitrages, protections → simplifications MERCURE (GC-COOLING-09)

- **Azimut canonique** : convention `0°=Nord`, sens horaire (`N`, `NE`, `E`,
  `SE`, `S`, `SO`, `O`, `NO` = `0/45/90/135/180/225/270/315°`). Le frontend
  ne stocke qu'une orientation cardinale (`CardinalDirection`) et fait
  pivoter ses 4 emplacements de façade fixes (`north/south/east/west` =
  slots UI « avant/droite/arrière/gauche », pas des points cardinaux figés)
  via `rotatedOrientation()` (`frontend/src/sync/syncStudy.ts`) avant de les
  envoyer comme `orientation` réelle de chaque `greencube.thermal.facade`.
  Le backend ne recalcule pas les azimuts : il fait confiance à
  l'orientation déjà résolue par le frontend, mais reste l'autorité pour la
  cohérence géométrique (`glazing_area_m2 <= gross_area_m2`, façade unique
  par orientation).
- **Protections solaires** : chaque type (`internal_blind`,
  `external_blind`, `brise_soleil`, `overhang`, `natural`, `building`,
  `mountain`) a un `efficiency_percent` propre — plus aucune conversion
  générique vers `external_blind`. Le calcul MERCURE lui-même ne lit
  toutefois que `greencube.thermal.facade.default_shading_factor` (un
  facteur constant par façade, sans variation horaire) : les enregistrements
  `greencube.cooling.shading` (`shading_ids`) portent la donnée plus riche
  (type, créneau `start_hour`/`end_hour`, `automatic`, `confirmed`,
  provenance) utilisée pour la validation/l'audit et copiée lors d'une
  révision, mais **n'alimentent pas encore directement le moteur physique**
  — c'est la simplification MVP assumée ici (une seule protection
  dominante par façade, sans calendrier dynamique dans le calcul rapide).
  Une future intégration EnergyPlus/Honeybee est le point d'extension
  naturel pour un calendrier de protection réellement dynamique.
- **Gains solaires par façade** : `GET /results/<id>` expose
  `solar_gain_by_facade` (`facade`, `area_m2`, `radiation_wm2`,
  `solar_factor`, `protection_factor`, `gain_w`), une décomposition
  informative de l'entrée agrégée `solar_glazing` de `breakdown` — jamais
  additionnée par-dessus le total déjà présent dans `breakdown`/
  `total_load_w`.

### Usage, occupation et calendrier hebdomadaire (GC-COOLING-10)

- **Calendrier structuré, pas de texte libre** : `active_monday` ..
  `active_sunday` (booléens) sont la source de vérité du calendrier
  hebdomadaire. `usage_days` (`Char`, ex. `"Mon-Fri"`) est conservé en
  lecture seule pour compatibilité d'affichage mais n'est plus écrit par le
  frontend ni lu par le moteur MERCURE.
- **Passage de minuit** : `start_hour`/`end_hour` sont des heures `0..24`.
  Si `end_hour < start_hour`, la plage traverse minuit et la durée
  occupée est `(24 - start_hour) + end_hour` ; si égaux, la durée est `0`
  (profil inoccupé, ex. local technique). `crosses_midnight` et
  `daily_occupied_hours` sont des champs calculés exposés en lecture.
- **`occupancy_fraction`** (calculé, `daily_occupied_hours / 24`) est
  désormais ce que `cooling_study.py`'s `_build_mercure_input()` envoie
  dans `Occupancy.occupancy_fraction` — auparavant figé à `1.0`, ce qui
  rendait les horaires/jours sans aucun effet sur les gains sensibles/
  latents calculés. Simplification volontairement identique à celle déjà
  utilisée pour `equipment_load.usage_hours_per_day / 24` et
  `lighting_usage_fraction` (moyenne journalière en régime permanent) —
  ne factorise pas le nombre de jours actifs par semaine, par cohérence
  avec ces deux autres composantes qui n'ont pas non plus de notion de
  variation hebdomadaire.
- **Bornes** : `usual_occupants` 0–500, `maximum_occupants` 0–1000
  (`api_validation.FIELD_LIMITS`, mêmes bornes en contrainte modèle), et
  `maximum_occupants >= usual_occupants`.
- **Profil unique par étude** : `occupancy_profile_ids` est un `One2many`
  (extensible à un futur modèle multi-zone) mais seul le premier
  enregistrement (`[:1]`) est jamais lu — MVP à profil global unique,
  documenté explicitement plutôt que silencieusement supposé.
- **Verrouillage** : `greencube.cooling.occupancy.profile.write()`/
  `.unlink()` refusent toute modification (hors `provenance`) une fois
  l'étude `validated`, miroir du verrou `greencube.cooling.study.write()`
  qui ne couvrait jamais ce sous-modèle — créer une révision à la place.
- **Mapping Honeybee/EnergyPlus** : `services/mercure/honeybee_translator.py`
  ne consomme que `occupancy_schedule_fraction` (un nombre unique par
  scénario climatique, pas un horaire complet 8760h) — les champs
  `active_<weekday>`/`start_hour`/`end_hour` du modèle Odoo n'alimentent
  pas encore un vrai calendrier Honeybee `People`/`ScheduleRuleset` heure
  par heure ; c'est une simplification MVP documentée, pas un mapping
  perdu.

### Équipements, éclairage et apports internes (GC-COOLING-11)

- **Catalogue jamais codé en dur** : la liste des apports internes de
  référence proposés par l'écran Équipements (ordinateur portable, écran,
  imprimante, serveur, éclairage LED, machine à café, réseau, batterie,
  onduleur) vient exclusivement de `GET /equipment-load-catalog`
  (`product.template` où `is_internal_load_equipment=True`). Avant cette
  version, ce catalogue était une constante TypeScript
  (`frontend/src/equipment/internalLoadsCatalog.ts`) — sans lien avec
  Odoo, non versionnable, non corrigeable sans déploiement frontend.
- **Liaison catalogue → ligne d'étude** : à l'ajout, `product_id` (déjà un
  champ existant sur `greencube.cooling.equipment.load`) est désormais
  effectivement transmis par le frontend ; une ligne rechargée est
  reliée à sa carte catalogue par `product_id` (identité fiable), avec un
  repli sur la correspondance par nom pour les lignes historiques créées
  avant ce changement.
- **Catégories** : `equipment_load.category` (`it`, `lighting`,
  `appliance`, `kitchen`, `network`, `battery`, `inverter`, `medical`,
  `machine`, `other`) est la référence ; le type frontend
  `EquipmentItem.category` a été élargi pour correspondre exactement
  (auparavant limité à 5 valeurs, `battery`/`inverter` étaient repliés
  sur `other`).
- **Mapping solver rapide (MERCURE)** : `cooling_study.py`'s
  `_build_mercure_input()` calcule déjà `operating_fraction` depuis
  `usage_hours_per_day / 24` (simplification en moyenne journalière,
  cohérente avec `lighting_usage_fraction`/`occupancy_fraction`, GC-
  COOLING-10) et un partage sensible/latent grossier
  (`category == "other"` → 20 % latent, sinon 100 % sensible) — inchangé
  par ce lot ; un partage sensible/latent/radiant/convectif par ligne
  (README_GC-COOLING-11) reste une limite connue du MVP, pas un mapping
  perdu.
- **Mapping Honeybee/EnergyPlus** : `services/mercure/honeybee_translator.py`
  dérive `ElectricEquipment`/`Lights` depuis `EquipmentLoad`/`Lighting`
  (`operating_fraction`, `fraction_dissipated_in_zone` comme fraction
  perdue = `1 - fraction_dissipated_in_zone`) ; aucune fraction
  radiante/convective distincte n'est encore modélisée séparément.

## Snapshot, calcul, résultats

| Méthode | Route | Effet | Codes d'erreur notables |
|---|---|---|---|
| POST | `/studies/<id>/snapshots` | Fige un snapshot immuable (hash SHA-256) | 404, 422 `COOLING_STUDY_INCOMPLETE` |
| POST | `/studies/<id>/calculations` | Crée/relance un calcul. Body : `{engine?: quick_solver\|energyplus\|both}`. Header `Idempotency-Key` recommandé. Renvoie l'enveloppe de **job**, pas le résultat complet | 404, 422 `COOLING_CALCULATION_FAILED` |
| GET | `/calculations/<job_id>` | Statut d'un `greencube.cooling.calculation.job` réel (`queued\|running\|completed\|failed`) | 404 `COOLING_JOB_NOT_FOUND` |
| GET | `/results/<result_id>` | Résultat complet (`recommended_capacity_w`, `breakdown`, `warnings`, ...) | 404 `COOLING_RESULT_NOT_FOUND` |
| GET | `/studies/<id>/results` | Historique des résultats d'une étude | 404 |

**Contrat job → résultat (GC-COOLING-02 pt4/GC-COOLING-16) :** le client
doit toujours suivre `POST /calculations` → `job.result_id` →
`GET /results/<result_id>`, jamais supposer que la réponse de
`POST /calculations` contient le résultat complet. C'est le contrat que le
frontend (`frontend/src/api/study.ts`) suit depuis le lot de stabilisation
du 2026-07-20.

**Depuis le lot simulation (2026-07-20) :** `job_id` est désormais l'id d'un
vrai `greencube.cooling.calculation.job` (GC-COOLING-15 pt.1), plus l'id du
résultat réutilisé comme identifiant de job. MERCURE (`quick_solver`) reste
synchrone dans le process web (c'est un calcul rapide, pas de raison de
l'isoler). Si `engine` inclut `energyplus`, la réponse porte aussi
`energyplus_processing_status` : `not_requested` / `disabled` (flag
`GC_COOLING_ENERGYPLUS_ENABLED` désactivé, par défaut) /
`translation_failed` / `queued_for_worker` (traduction Honeybee réussie,
stockée comme `simulation.artifact`, simulation EnergyPlus elle-même
laissée à un cron désactivé par défaut — jamais exécutée dans la requête
HTTP) / `simulation_unavailable` / `simulation_failed` /
`simulation_completed`. En pratique cet état reste toujours
`disabled`/`translation_failed`/`queued_for_worker` puis
`simulation_unavailable` aujourd'hui : ni honeybee-energy/ladybug ni le
binaire EnergyPlus ne sont installés dans un déploiement cible actuel de ce
MVP — voir `services/energyplus.py` et le README du module.

## Équipement

| Méthode | Route | Effet |
|---|---|---|
| GET | `/equipment-catalog` | Catalogue Odoo des équipements de refroidissement |
| POST | `/studies/<id>/equipment-recommendations` | Recommandations de compatibilité pour le résultat actif |
| GET | `/studies/<id>/equipment-selections` | Historique des sélections |
| POST | `/studies/<id>/equipment-selections` | Crée une sélection (supersède la précédente si `state=selected`, jamais si `state=validated` — voir immutabilité dans `docs/cooling_security_matrix.md`) |

## Ce qui manque encore par rapport à GC-COOLING-02

- Pas de spécification OpenAPI/JSON Schema générée automatiquement à
  partir du code (ce document est maintenu à la main).
- Pas de tests `HttpCase` livrés dans ce dépôt — les codes 401/403/404/409/
  422 listés ci-dessus sont documentés depuis la lecture du code, pas
  vérifiés par une requête HTTP réelle dans cet environnement (pas d'Odoo
  installé ici, voir `README.md`).
- Pas de tri (`order`) exposé sur `GET /studies`, seulement pagination et
  recherche par nom.
- Pas de corrélation `request_id` entre la réponse HTTP et les logs
  serveur (le `request_id` est généré par requête mais pas propagé dans le
  logger Odoo).
