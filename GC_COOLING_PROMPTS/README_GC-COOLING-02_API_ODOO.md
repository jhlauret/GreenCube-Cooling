# GC-COOLING-02 — API Odoo du configurateur GreenCube Cooling

## 1. Objet

Ce document définit le périmètre d’implémentation de l’API JSON versionnée du configurateur GreenCube Cooling.

Le backend repose sur **Odoo Community 18**, qui constitue la source de vérité métier. Le frontend React utilise cette API pour :

- consulter le catalogue thermique GreenCube ;
- créer et mettre à jour une étude ;
- sauvegarder progressivement les données des écrans ;
- récupérer le contexte climatique ;
- vérifier la complétude et la qualité des entrées ;
- déclencher le solver thermique ;
- consulter et valider les résultats ;
- créer des révisions ;
- générer un rapport PDF.

Le module métier principal est :

```text
greencube_cooling
```

Le préfixe obligatoire de l’API est :

```text
/api/v1/greencube/cooling
```

---

## 2. Principes d’architecture

### 2.1 Source de vérité

Odoo conserve :

- les modèles GreenCube ;
- les propriétés thermiques ;
- les études ;
- les hypothèses ;
- les données climatiques ;
- les versions du solver ;
- les résultats ;
- les révisions ;
- les rapports.

Le frontend React ne doit pas devenir une seconde base métier.

### 2.2 Contrôleurs légers

Les contrôleurs HTTP doivent uniquement :

1. authentifier la requête ;
2. valider les entrées ;
3. vérifier les droits ;
4. appeler un service métier ;
5. sérialiser la réponse ;
6. normaliser les erreurs.

La logique métier doit être placée dans des services Python testables.

### 2.3 Structure recommandée

```text
greencube_cooling/
├── controllers/
│   ├── __init__.py
│   ├── api_base.py
│   ├── api_catalog.py
│   ├── api_study.py
│   ├── api_climate.py
│   ├── api_calculation.py
│   └── api_report.py
├── services/
│   ├── __init__.py
│   ├── api_serializer.py
│   ├── api_validation.py
│   ├── study_service.py
│   ├── climate_service.py
│   ├── calculation_service.py
│   ├── confidence_service.py
│   └── idempotency_service.py
├── schemas/
│   ├── __init__.py
│   ├── common.py
│   ├── catalog.py
│   ├── study.py
│   ├── climate.py
│   └── calculation.py
├── tests/
│   ├── test_api_catalog.py
│   ├── test_api_study.py
│   ├── test_api_climate.py
│   ├── test_api_calculation.py
│   ├── test_api_security.py
│   ├── test_api_multicompany.py
│   └── test_api_idempotency.py
└── docs/
    └── openapi.yaml
```

Cette structure doit être adaptée aux conventions du dépôt existant.

---

## 3. Vérifications préalables

Avant toute modification :

1. inspecter le module `greencube_cooling` ;
2. vérifier les modèles et champs réellement disponibles ;
3. inspecter les contrôleurs existants ;
4. identifier les conventions d’authentification ;
5. identifier la stratégie CSRF ;
6. identifier la stratégie CORS ;
7. rechercher les API GreenCube ou Search & Select déjà présentes ;
8. exécuter les tests backend existants ;
9. ne supprimer aucun fichier ;
10. ne pas dupliquer un mécanisme d’authentification existant.

Le rapport préalable doit indiquer :

- les contrôleurs inspectés ;
- les modèles réutilisés ;
- la stratégie d’authentification retenue ;
- la stratégie CSRF ;
- la stratégie CORS ;
- les fichiers à créer ;
- les fichiers à modifier ;
- les incompatibilités détectées.

---

## 4. Convention générale des réponses

### 4.1 Succès

```json
{
  "data": {},
  "meta": {
    "request_id": "uuid",
    "api_version": "v1",
    "timestamp": "2026-07-15T10:00:00Z"
  }
}
```

### 4.2 Collection paginée

```json
{
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 0,
      "total_pages": 0
    }
  },
  "meta": {
    "request_id": "uuid",
    "api_version": "v1",
    "timestamp": "2026-07-15T10:00:00Z"
  }
}
```

### 4.3 Erreur

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Certaines données sont invalides.",
    "fields": {
      "target_temperature_c": [
        "La température doit être comprise entre 16 et 35 °C."
      ]
    },
    "request_id": "uuid"
  }
}
```

### 4.4 Codes d’erreur

- `AUTHENTICATION_REQUIRED`
- `ACCESS_DENIED`
- `RESOURCE_NOT_FOUND`
- `VALIDATION_ERROR`
- `CONFLICT`
- `INVALID_STATE`
- `IDEMPOTENCY_CONFLICT`
- `RATE_LIMIT_EXCEEDED`
- `CLIMATE_PROVIDER_UNAVAILABLE`
- `CLIMATE_DATA_PARTIAL`
- `CALCULATION_FAILED`
- `REPORT_GENERATION_FAILED`
- `INTERNAL_ERROR`

Aucune trace Python complète ne doit être retournée au frontend.

---

## 5. Codes HTTP

| Code | Utilisation |
|---|---|
| `200` | Lecture ou mise à jour réussie |
| `201` | Création réussie |
| `202` | Traitement asynchrone accepté |
| `204` | Succès sans contenu |
| `400` | Requête mal formée |
| `401` | Authentification requise |
| `403` | Accès refusé |
| `404` | Ressource introuvable ou inaccessible |
| `409` | Conflit métier ou de version |
| `422` | Données invalides |
| `429` | Limite de débit dépassée |
| `500` | Erreur interne |
| `502` | Erreur d’un fournisseur externe |
| `503` | Service temporairement indisponible |

---

## 6. Request ID et logs

Chaque requête doit :

1. lire le header `X-Request-ID` ;
2. générer un UUID s’il est absent ;
3. inclure cet identifiant dans les logs et la réponse ;
4. mesurer la durée de traitement ;
5. exclure les secrets des logs.

Exemple :

```json
{
  "request_id": "uuid",
  "route": "/api/v1/greencube/cooling/studies/42",
  "method": "PUT",
  "user_id": 7,
  "company_id": 1,
  "status_code": 200,
  "duration_ms": 84
}
```

Ne jamais logger :

- mots de passe ;
- cookies ;
- tokens ;
- clés API ;
- headers d’autorisation ;
- données personnelles inutiles.

---

## 7. Authentification

### 7.1 Priorité

Réutiliser le mécanisme d’authentification déjà présent :

- session Odoo ;
- jeton applicatif ;
- magic link ;
- BFF ;
- SSO.

Ne pas créer un second système d’identité sans nécessité.

### 7.2 Session Odoo

Appropriée aux utilisateurs internes.

### 7.3 Jeton applicatif court

Seulement si nécessaire pour un frontend séparé.

Le jeton doit :

- expirer ;
- être vérifié côté serveur ;
- identifier utilisateur et société ;
- être révocable ;
- ne jamais exposer de secret métier.

### 7.4 Routes éventuellement publiques

- `GET /models`
- `GET /models/<id>`
- `GET /reference-data/public`

Ces routes ne doivent exposer que les données catalogue strictement nécessaires.

Ne jamais rendre publics :

- les études ;
- les clients ;
- les résultats ;
- les paramètres internes du solver ;
- les notes internes ;
- les données climatiques brutes.

---

## 8. CSRF et CORS

### 8.1 CSRF

Avec session Odoo et cookies :

- conserver CSRF ;
- transmettre le token ;
- ne pas désactiver globalement la protection.

Avec un jeton `Authorization` sans cookie :

- documenter l’usage de `csrf=False` ;
- appliquer une authentification stricte.

### 8.2 CORS

Ne jamais utiliser `Access-Control-Allow-Origin: *` avec des credentials.

Configurer une liste blanche :

```text
greencube_cooling.allowed_frontend_origins
```

Exemples :

```text
https://greencube.example.com
https://app.search-select.example.com
```

Valider strictement :

- schéma ;
- hôte ;
- port ;
- absence de wildcard dangereux.

---

## 9. Sérialisation

Ne jamais retourner directement :

```python
record.read()
```

Créer des sérialiseurs explicites :

```python
serialize_thermal_specification(record)
serialize_study(record)
serialize_climate_context(record)
serialize_result(record)
```

Les sérialiseurs doivent :

- filtrer les champs ;
- utiliser ISO 8601 ;
- retourner des codes de sélection stables ;
- inclure les unités ;
- inclure la provenance ;
- respecter les droits ;
- masquer les données internes.

Exemple :

```json
{
  "value": 0.18,
  "unit": "W/m².K",
  "source": "catalog",
  "confirmed": true
}
```

---

## 10. Validation serveur

La validation Zod du frontend ne remplace jamais la validation Odoo.

### 10.1 Limites initiales

| Champ | Limites |
|---|---:|
| latitude | -90 à 90 |
| longitude | -180 à 180 |
| altitude | -500 à 9 000 m |
| température cible | 16 à 35 °C |
| humidité cible | 20 à 90 % |
| longueur | > 0 à 100 m |
| largeur | > 0 à 100 m |
| hauteur | > 0 à 20 m |
| occupants | 0 à 10 000 |
| débit d’air | 0 à 1 000 000 m³/h |
| puissance | 0 à 10 000 000 W |
| simultanéité | 0 à 100 % |
| facteur solaire | 0 à 1 |

Rejeter :

- champs inconnus ;
- types incorrects ;
- valeurs non finies ;
- identifiants négatifs ;
- coordonnées invalides ;
- chaînes excessivement longues ;
- incohérences métier.

---

## 11. Droits et multi-société

Chaque requête sur une étude doit vérifier :

1. l’existence de l’étude ;
2. le droit de lecture ;
3. la société autorisée ;
4. le rôle requis ;
5. la compatibilité du statut avec l’action.

Ne pas utiliser `sudo()` comme contournement global.

Les recherches doivent respecter :

```python
[("company_id", "in", env.companies.ids)]
```

Ne jamais faire confiance au `company_id` envoyé par le frontend.

---

## 12. Endpoints

### 12.1 Catalogue

#### `GET /models`

```text
GET /api/v1/greencube/cooling/models
```

Paramètres :

- `page`
- `page_size`
- `active`
- `standard_model`
- `usage_type`
- `search`
- `company_id`

`page_size` : minimum 1, maximum 100, défaut 20.

#### `GET /models/<id>`

Retourner :

- identification ;
- version ;
- dimensions ;
- enveloppe ;
- façades ;
- vitrages ;
- matériaux ;
- étanchéité ;
- inertie ;
- provenance ;
- verrouillage.

### 12.2 Référentiels

```text
GET /api/v1/greencube/cooling/reference-data
```

Retourner :

- usages ;
- niveaux d’activité ;
- niveaux de service ;
- environnements ;
- ventilations ;
- catégories d’équipement ;
- protections solaires ;
- orientations ;
- capacités commerciales ;
- profils par défaut.

### 12.3 Création d’étude

```text
POST /api/v1/greencube/cooling/studies
```

Payload :

```json
{
  "name": "GreenCube Mission",
  "thermal_specification_id": 12,
  "service_level": "enhanced",
  "target_temperature_c": 24,
  "target_humidity_percent": 50
}
```

### 12.4 Lecture d’étude

```text
GET /api/v1/greencube/cooling/studies/<id>
```

### 12.5 Mise à jour d’étude

```text
PUT /api/v1/greencube/cooling/studies/<id>
```

Payload par section :

```json
{
  "version": "2026-07-15T09:42:00Z",
  "sections": {
    "location": {},
    "model": {},
    "orientation": {},
    "occupancy": {},
    "equipment": [],
    "ventilation": {},
    "comfort": {}
  }
}
```

Le verrouillage optimiste doit empêcher les écrasements concurrents.

### 12.6 Validation des entrées

```text
POST /api/v1/greencube/cooling/studies/<id>/validate-inputs
```

Cette route ne lance pas le solver.

### 12.7 Création d’une révision

```text
POST /api/v1/greencube/cooling/studies/<id>/revision
```

### 12.8 Géocodage

```text
POST /api/v1/greencube/cooling/geocode
```

### 12.9 Contexte climatique

```text
POST /api/v1/greencube/cooling/studies/<id>/climate-context
```

### 12.10 Calcul

```text
POST /api/v1/greencube/cooling/studies/<id>/calculate
```

Header obligatoire :

```text
Idempotency-Key: <uuid>
```

### 12.11 Lecture du résultat

```text
GET /api/v1/greencube/cooling/studies/<id>/result
```

### 12.12 Validation du résultat

```text
POST /api/v1/greencube/cooling/studies/<id>/validate-result
```

### 12.13 Duplication

```text
POST /api/v1/greencube/cooling/studies/<id>/duplicate
```

### 12.14 Rapport PDF

```text
GET /api/v1/greencube/cooling/studies/<id>/report
```

---

## 13. Idempotence

Pour :

```text
study_id + idempotency_key + user_id
```

Même clé et même payload :

- retourner le résultat initial ;
- ne pas recalculer ;
- indiquer un rejeu idempotent.

Même clé et payload différent :

- retourner `409 IDEMPOTENCY_CONFLICT`.

Stocker :

- hash du payload ;
- date ;
- résultat ;
- utilisateur ;
- expiration éventuelle.

---

## 14. Rate limiting

| Route | Limite initiale |
|---|---:|
| géocodage | 30/minute/utilisateur |
| climat | 10/heure/étude |
| calcul | 10/heure/étude |
| rapport | 30/heure/utilisateur |

Retourner `429` et éventuellement `Retry-After`.

---

## 15. Protection SSRF

Le frontend ne doit jamais transmettre :

- URL externe ;
- hostname ;
- callback ;
- chemin de fichier ;
- commande ;
- expression de solver.

Les fournisseurs sont configurés côté serveur.

Appliquer :

- liste blanche ;
- HTTPS ;
- timeout ;
- taille de réponse limitée ;
- redirections limitées ;
- blocage des réseaux privés ;
- secrets absents des logs.

---

## 16. Documentation OpenAPI

Créer :

```text
docs/openapi.yaml
```

Documenter :

- routes ;
- authentification ;
- headers ;
- payloads ;
- réponses ;
- erreurs ;
- pagination ;
- idempotence ;
- unités ;
- sélections ;
- exemples.

La documentation doit refléter le code réellement implémenté.

---

## 17. Tests obligatoires

### Catalogue

- liste ;
- pagination ;
- filtres ;
- détail ;
- accès interdit ;
- multi-société.

### Études

- création ;
- lecture ;
- mise à jour ;
- sauvegarde par écran ;
- conflit de version ;
- verrouillage ;
- duplication ;
- révision.

### Climat

- géocodage ;
- coordonnées invalides ;
- cache ;
- cache ancien ;
- fournisseur indisponible ;
- données partielles ;
- rate limiting.

Aucun test ne doit appeler Internet.

### Calcul

- étude complète ;
- étude incomplète ;
- scénario absent ;
- idempotence ;
- conflit d’idempotence ;
- double requête ;
- erreur solver ;
- résultat immuable.

### Sécurité

- sans authentification ;
- droits insuffisants ;
- CORS interdit ;
- payload excessif ;
- champ inconnu ;
- tentative de changer la société ;
- tentative d’injecter une URL externe.

---

## 18. Fixtures de contrat

Créer :

```text
tests/fixtures/api/
```

Inclure :

- catalogue ;
- étude vide ;
- étude partielle ;
- étude complète ;
- contexte climatique ;
- validation ;
- résultat ;
- erreurs.

Ces fixtures peuvent être utilisées par les tests React.

---

## 19. Critères d’acceptation

L’implémentation est acceptable uniquement si :

1. toutes les routes sont versionnées ;
2. les réponses sont uniformes ;
3. les erreurs sont normalisées ;
4. aucun ORM brut n’est exposé ;
5. l’authentification est appliquée ;
6. le multi-société fonctionne ;
7. la création d’étude fonctionne ;
8. la sauvegarde par écran fonctionne ;
9. la complétude est calculée ;
10. le contexte climatique est enregistré ;
11. le calcul est idempotent ;
12. les résultats sont immuables ;
13. une étude validée est verrouillée ;
14. une révision peut être créée ;
15. les PDF sont protégés ;
16. l’OpenAPI correspond au code ;
17. les tests passent ;
18. aucun test ne dépend d’Internet ;
19. aucune clé API n’est exposée ;
20. aucun fichier n’est supprimé sans justification.

---

## 20. Rapport final attendu

Le livrable doit contenir :

- fichiers créés et modifiés ;
- routes et rôles requis ;
- stratégie d’authentification ;
- stratégie CSRF et CORS ;
- gestion multi-société ;
- rate limiting ;
- SSRF ;
- idempotence ;
- commandes exécutées ;
- résultats des tests ;
- limitations ;
- diff ;
- patch réintégrable ;
- instructions de rollback ;
- éventuelles étapes de migration.

---

## 21. Contrôle final

Avant conclusion :

1. exécuter les tests API ;
2. exécuter les tests modèles impactés ;
3. installer le module sur une base vierge ;
4. mettre à jour le module sur une base existante ;
5. vérifier les routes ;
6. vérifier les erreurs JSON ;
7. vérifier les ACL ;
8. vérifier les record rules ;
9. vérifier le multi-société ;
10. vérifier l’idempotence ;
11. vérifier le verrouillage optimiste ;
12. vérifier l’immutabilité ;
13. vérifier la protection PDF ;
14. vérifier l’absence d’appels Internet dans les tests ;
15. vérifier l’absence de secrets ;
16. vérifier la cohérence OpenAPI/code ;
17. vérifier qu’aucun fichier n’a été supprimé ;
18. ne jamais déclarer un test réussi sans l’avoir réellement exécuté.

---

## 22. Limites de ce lot

Ce lot implémente le contrat API et son infrastructure.

Le service climatique et le solver peuvent encore être représentés par des interfaces ou des mocks clairement identifiés tant que leurs lots respectifs ne sont pas implémentés.

L’API ne doit jamais produire de faux résultat métier présenté comme réel.
