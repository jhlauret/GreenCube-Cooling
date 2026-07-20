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
| GET/PUT | `/studies/<id>/occupancy-profile` | Profil d'occupation (unique par étude) | |
| GET/PUT | `/studies/<id>/ventilation-profile` | Profil de ventilation (unique par étude) | |
| GET/PUT | `/studies/<id>/shading` | Protections solaires (remplacement complet de la liste au PUT) | |
| GET/POST | `/studies/<id>/equipment-loads` | Liste / création d'une ligne d'apport interne | |
| PATCH/DELETE | `/equipment-loads/<line_id>` | Modifie / supprime une ligne par id direct | Protégé uniquement par `ir.rule` (pas de re-vérification de propriété dans le contrôleur — voir `docs/cooling_security_matrix.md`) |

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
