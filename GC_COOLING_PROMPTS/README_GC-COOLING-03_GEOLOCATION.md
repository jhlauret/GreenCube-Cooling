# GC-COOLING-03 — Service de géocodage, altitude, fuseau horaire et contexte géographique

## 1. Objet

Ce document définit l’implémentation détaillée du service backend de géolocalisation du configurateur GreenCube Cooling.

Le module principal est :

```text
greencube_cooling
```

Le service doit permettre, à partir d’une adresse, d’un nom de lieu ou de coordonnées GPS, de déterminer :

- l’adresse normalisée ;
- la latitude ;
- la longitude ;
- l’altitude ;
- le fuseau horaire ;
- le pays ;
- la subdivision administrative ;
- la commune ;
- le code postal lorsque disponible ;
- une suggestion de type d’environnement ;
- un score de confiance ;
- la provenance et la date des données.

Ce service alimente l’écran :

```text
1 — Localisation et contexte climatique
```

Il ne doit pas encore récupérer l’historique météorologique ni exécuter le solver thermique.

## 2. Objectifs fonctionnels

### 2.1 Recherche par adresse

Entrée :

```text
137 rue d’Alésia, 75014 Paris, France
```

Sortie attendue :

- adresse normalisée ;
- latitude ;
- longitude ;
- altitude ;
- fuseau horaire ;
- pays ;
- région ;
- département ou canton ;
- commune ;
- code postal ;
- score de confiance.

### 2.2 Recherche par lieu

Entrée :

```text
Mission, Anniviers, Suisse
```

Le service doit pouvoir retourner plusieurs candidats lorsque le nom est ambigu.

### 2.3 Recherche par coordonnées

Entrée :

```json
{
  "latitude": 46.22,
  "longitude": 7.57
}
```

Le service doit effectuer un géocodage inverse et déterminer :

- le lieu le plus proche ;
- l’altitude ;
- le fuseau horaire ;
- les subdivisions géographiques ;
- le contexte environnemental suggéré.

### 2.4 Position issue du navigateur

Le frontend peut transmettre une position fournie par l’API de géolocalisation du navigateur.

Le backend doit :

- traiter cette position comme une saisie manuelle ;
- revalider les coordonnées ;
- ne pas considérer automatiquement l’altitude navigateur comme fiable ;
- conserver la provenance des données.

## 3. Vérifications préalables

Avant toute modification :

1. inspecter l’architecture du dépôt ;
2. vérifier les modèles Odoo existants ;
3. identifier les champs de localisation déjà présents ;
4. inspecter les services géographiques existants ;
5. rechercher les intégrations avec OpenStreetMap, Nominatim, Open-Meteo, Google Maps, Mapbox et GeoNames ;
6. identifier les conventions de configuration ;
7. inspecter les contrôleurs API ;
8. vérifier les mécanismes existants de cache, timeout, retries, rate limiting et logs ;
9. exécuter les tests existants ;
10. ne pas dupliquer un service existant s’il peut être étendu.

Le rapport préalable doit contenir :

- les services inspectés ;
- les fournisseurs disponibles ;
- les dépendances Python ;
- la stratégie retenue ;
- les fichiers à créer ;
- les fichiers à modifier ;
- les risques ;
- les limites.

## 4. Architecture du service

### 4.1 Interface de fournisseur

Créer une abstraction :

```python
class GeocodingProvider:
    def geocode_address(self, query, country_code=None, limit=5):
        raise NotImplementedError

    def reverse_geocode(self, latitude, longitude):
        raise NotImplementedError

    def resolve_altitude(self, latitude, longitude):
        raise NotImplementedError

    def resolve_timezone(self, latitude, longitude):
        raise NotImplementedError

    def healthcheck(self):
        raise NotImplementedError
```

### 4.2 Service orchestrateur

Créer un service métier :

```python
class GeolocationService:
    def resolve_from_address(self, payload):
        ...

    def resolve_from_coordinates(self, payload):
        ...

    def suggest_environment_type(self, resolved_location):
        ...

    def build_cache_key(self, payload):
        ...

    def normalize_result(self, provider_result):
        ...
```

Le contrôleur HTTP ne doit jamais appeler directement un fournisseur externe.

### 4.3 Structure recommandée

```text
greencube_cooling/
├── services/
│   ├── geolocation/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── provider_registry.py
│   │   ├── geolocation_service.py
│   │   ├── normalizer.py
│   │   ├── environment_classifier.py
│   │   ├── cache.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── nominatim_provider.py
│   │       ├── open_meteo_provider.py
│   │       └── mock_provider.py
├── models/
│   └── geolocation_cache.py
├── tests/
│   ├── test_geolocation_service.py
│   ├── test_geolocation_provider.py
│   ├── test_geolocation_cache.py
│   ├── test_environment_classifier.py
│   └── fixtures/
│       └── geolocation/
└── docs/
    └── geolocation.md
```

Adapter cette structure aux conventions réelles du dépôt.

## 5. Fournisseurs

### 5.1 Fournisseur de géocodage

Créer un paramètre système :

```text
greencube_cooling.geocoding_provider
```

Valeurs possibles :

```text
nominatim
open_meteo
custom
mock
```

Le fournisseur principal doit être configurable et non codé définitivement.

### 5.2 Fournisseur d’altitude

Créer une abstraction distincte :

```python
class ElevationProvider:
    def resolve_altitude(self, latitude, longitude):
        raise NotImplementedError
```

Paramètre :

```text
greencube_cooling.elevation_provider
```

### 5.3 Fournisseur de fuseau horaire

Créer :

```python
class TimezoneProvider:
    def resolve_timezone(self, latitude, longitude):
        raise NotImplementedError
```

Le fuseau doit être retourné au format IANA :

```text
Europe/Paris
Europe/Zurich
Europe/Lisbon
```

Ne jamais retourner uniquement un offset UTC.

### 5.4 Fallback

Prévoir une chaîne configurable :

```text
fournisseur principal
→ fournisseur secondaire
→ cache ancien
→ résultat partiel
```

Ne jamais inventer une coordonnée ou une altitude.

## 6. Configuration Odoo

Créer les paramètres :

```text
greencube_cooling.geocoding_provider
greencube_cooling.elevation_provider
greencube_cooling.timezone_provider
greencube_cooling.geocoding_timeout_seconds
greencube_cooling.geocoding_max_retries
greencube_cooling.geocoding_cache_ttl_days
greencube_cooling.geocoding_result_limit
greencube_cooling.allowed_geocoding_countries
greencube_cooling.geocoding_user_agent
```

Valeurs initiales recommandées :

```text
timeout : 8 secondes
retries : 2 maximum
cache TTL : 90 jours
nombre de résultats : 5
```

Les secrets doivent rester côté serveur, être masqués et ne jamais apparaître dans Git, les logs ou l’API.

## 7. Modèle de cache

Créer, si aucun modèle existant n’est réutilisable :

```python
_name = "greencube.geolocation.cache"
_description = "GreenCube Geolocation Cache"
_order = "write_date desc"
```

Champs principaux :

- `cache_key` ;
- `query_type` ;
- `normalized_query` ;
- `latitude` ;
- `longitude` ;
- `altitude_m` ;
- `timezone` ;
- `provider` ;
- `provider_version` ;
- `provider_reference` ;
- `result_json` ;
- `confidence_percent` ;
- `status` ;
- `retrieved_at` ;
- `expires_at` ;
- `last_used_at` ;
- `error_code` ;
- `error_message` ;
- `company_id`.

Statuts :

```text
available
partial
stale
failed
```

Contraintes :

- clé unique ;
- coordonnées valides ;
- confiance entre 0 et 100 ;
- expiration postérieure à la récupération.

## 8. Construction de la clé de cache

### Adresse

Inclure :

```text
provider
query_type
normalized_address
country_code
schema_version
```

### Coordonnées

Arrondir à cinq décimales et inclure :

```text
provider
latitude arrondie
longitude arrondie
schema_version
```

Créer :

```python
GEOLOCATION_SCHEMA_VERSION = "1"
```

## 9. Validation des entrées

### Adresse

Payload :

```json
{
  "address": "Route de Mission",
  "postal_code": "3961",
  "city": "Anniviers",
  "country_code": "CH",
  "limit": 5
}
```

Longueurs maximales :

```text
address : 255 caractères
city : 120 caractères
postal_code : 32 caractères
country_code : 2 caractères ISO
```

Rejeter les chaînes vides, trop longues, contenant du HTML, des caractères de contrôle ou une URL.

### Coordonnées

```text
latitude : -90 à 90
longitude : -180 à 180
```

Rejeter NaN, infini, chaîne non numérique et coordonnée manquante.

## 10. Format normalisé du résultat

```json
{
  "result_id": "provider-or-generated-id",
  "display_name": "Mission, 3961 Anniviers, Valais, Suisse",
  "normalized_address": {
    "street": null,
    "house_number": null,
    "postal_code": "3961",
    "city": "Anniviers",
    "municipality": "Anniviers",
    "county": null,
    "state": "Valais",
    "state_code": "VS",
    "country": "Suisse",
    "country_code": "CH"
  },
  "coordinates": {
    "latitude": 46.2263,
    "longitude": 7.1231,
    "precision": "locality"
  },
  "altitude": {
    "value_m": 1200,
    "source": "elevation_provider",
    "confidence_percent": 90
  },
  "timezone": {
    "iana": "Europe/Zurich",
    "source": "timezone_provider",
    "confidence_percent": 100
  },
  "environment": {
    "suggested_type": "mountain",
    "confidence_percent": 82,
    "reasons": ["Altitude supérieure à 800 m"]
  },
  "provider": {
    "name": "configured_provider",
    "version": null,
    "retrieved_at": "2026-07-15T10:00:00Z",
    "cache_used": false
  },
  "confidence_percent": 89,
  "warnings": []
}
```

## 11. Résultats multiples

Une recherche ambiguë doit retourner plusieurs candidats et demander une confirmation explicite.

Ne pas sélectionner automatiquement un résultat ambigu.

## 12. Altitude

L’altitude doit être calculée à partir des coordonnées finales.

Plage autorisée :

```text
-500 à 9000 m
```

Si absente :

- retourner `null` ;
- marquer le résultat `partial` ;
- réduire le score de confiance ;
- permettre une correction utilisateur.

Conserver séparément l’altitude fournisseur et l’altitude confirmée.

## 13. Fuseau horaire

Toujours retourner un fuseau IANA valide et le vérifier côté serveur.

## 14. Classification de l’environnement

Valeurs :

```text
dense_urban
suburban
rural
mountain
coastal
industrial
```

Créer un classificateur explicable retournant :

- la suggestion ;
- la confiance ;
- les raisons.

Seuils initiaux :

```text
montagne : altitude > 800 m
bord de mer : distance littorale < 10 km
```

Ces seuils doivent être configurables et les inférences faibles doivent être signalées.

## 15. Score de confiance

Pondération initiale :

```text
qualité du géocodage : 35 %
précision de la position : 20 %
qualité de l’altitude : 15 %
qualité du fuseau : 10 %
cohérence administrative : 10 %
absence d’ambiguïté : 10 %
```

Libellés :

```text
90–100 : excellente
75–89 : bonne
60–74 : moyenne
40–59 : faible
< 40 : insuffisante
```

## 16. Mise à jour de l’étude

Créer :

```python
study.action_confirm_geolocation(payload)
```

Cette méthode doit :

1. vérifier les droits ;
2. revalider le résultat ;
3. enregistrer les valeurs ;
4. conserver la provenance ;
5. tracer la modification ;
6. invalider le climat si les coordonnées changent ;
7. invalider le résultat si nécessaire ;
8. imposer une révision pour une étude calculée ou validée.

Une simple recherche ne doit pas modifier définitivement l’étude.

## 17. API

Endpoints :

```text
POST /api/v1/greencube/cooling/geocode
POST /api/v1/greencube/cooling/reverse-geocode
POST /api/v1/greencube/cooling/studies/<id>/confirm-location
```

Le backend doit revalider le résultat sélectionné et ne pas faire confiance à un objet librement modifié par le frontend.

## 18. Sécurité

Le frontend ne doit jamais fournir :

- une URL ;
- un domaine ;
- un fournisseur libre ;
- un callback ;
- un chemin local.

Les appels externes doivent utiliser :

- HTTPS ;
- timeout ;
- retries limités ;
- réponse limitée ;
- redirections contrôlées ;
- blocage des réseaux privés ;
- domaine autorisé.

Rate limits initiaux :

```text
30 recherches/minute/utilisateur
100 recherches/heure/utilisateur
10 confirmations/minute/étude
```

## 19. Timeout et retries

```text
timeout : 8 secondes
retries : 2 maximum
```

Retry uniquement sur timeout, 429, 502, 503 et 504, avec backoff limité et jitter.

## 20. Dégradation contrôlée

Statuts :

```text
available
partial
stale
failed
```

Ne jamais transformer un échec en valeur supposée.

## 21. Nettoyage du cache

Créer une tâche planifiée pour :

- supprimer les entrées expirées non utilisées ;
- conserver les entrées référencées ;
- purger les erreurs anciennes ;
- limiter la croissance du cache.

## 22. Tests

Aucun test ne doit appeler Internet.

Tester notamment :

- adresse complète ;
- lieu ambigu ;
- coordonnées valides et invalides ;
- altitude absente ou hors plage ;
- fuseaux Paris et Zurich ;
- cache hit, miss, expiré et stale ;
- timeout, 429 et erreurs fournisseur ;
- classification montagne, littoral, urbain, rural et industriel ;
- confirmation ;
- changement de localisation ;
- invalidation du climat ;
- droits et multi-société ;
- rate limiting ;
- tentative de résultat falsifié.

Créer les fixtures dans :

```text
tests/fixtures/geolocation/
```

## 23. Documentation

Créer :

```text
docs/geolocation.md
```

Documenter l’architecture, les fournisseurs, la configuration, le cache, la normalisation, l’altitude, le fuseau, la classification, l’API, les erreurs, les tests et l’ajout d’un fournisseur.

## 24. Observabilité

Mesurer :

- nombre de recherches ;
- taux de cache hit ;
- durée moyenne ;
- erreurs par fournisseur ;
- résultats partiels ;
- ambiguïtés ;
- confirmations ;
- corrections manuelles ;
- rate limiting.

Ne pas logger l’adresse complète par défaut.

## 25. Critères d’acceptation

Le lot est accepté si :

1. une adresse peut être géocodée ;
2. un géocodage inverse fonctionne ;
3. les ambiguïtés sont gérées ;
4. l’altitude est résolue ou déclarée manquante ;
5. le fuseau IANA est résolu ;
6. l’environnement est proposé avec confiance et raisons ;
7. la provenance est conservée ;
8. le cache fonctionne ;
9. les timeouts et retries sont contrôlés ;
10. aucune URL libre ni clé n’est exposée ;
11. la confirmation met à jour l’étude ;
12. le changement de localisation invalide le climat ;
13. une étude validée n’est pas modifiée directement ;
14. le multi-société fonctionne ;
15. les tests passent sans Internet ;
16. la documentation existe ;
17. aucun fichier n’est supprimé sans justification.

## 26. Rapport final attendu

Fournir :

- fichiers créés et modifiés ;
- fournisseurs retenus ;
- modèle de cache ;
- endpoints ;
- stratégie de sécurité ;
- commandes exécutées ;
- résultats des tests ;
- limitations ;
- patch réintégrable ;
- procédure d’application et de rollback.

## 27. Contrôle final

Avant conclusion :

1. exécuter les tests unitaires et API ;
2. installer le module sur une base vierge ;
3. mettre à jour une base existante ;
4. vérifier le cache et ses expirations ;
5. vérifier les résultats multiples ;
6. vérifier l’altitude et le fuseau ;
7. vérifier la classification ;
8. vérifier les droits et le multi-société ;
9. vérifier l’invalidation climatique ;
10. vérifier l’absence d’Internet dans les tests ;
11. vérifier l’absence de secrets et d’URL libre ;
12. vérifier qu’aucun fichier n’a été supprimé ;
13. ne jamais déclarer un test réussi sans l’avoir exécuté.

## 28. Limites de ce lot

Ce lot fournit une localisation fiable et auditée.

Il ne doit pas encore :

- récupérer l’historique des températures ;
- calculer les percentiles climatiques ;
- détecter les vagues de chaleur ;
- exécuter le solver ;
- recommander une puissance en BTU/h.
