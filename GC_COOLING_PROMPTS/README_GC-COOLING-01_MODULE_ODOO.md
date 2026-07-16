# GC-COOLING-01 — Module Odoo Community 18 et modèle de données

## 1. Objet

Ce document définit l’implémentation détaillée du module Odoo Community 18 :

```text
greencube_cooling
```

Ce module constitue la **source de vérité métier** du configurateur GreenCube Cooling.

Il doit permettre de :

- décrire les modèles GreenCube ;
- stocker leurs propriétés thermiques ;
- créer et versionner des études de refroidissement ;
- enregistrer les données d’usage, d’occupation, d’équipement et de ventilation ;
- conserver les données climatiques utilisées ;
- stocker les versions du solver ;
- enregistrer les résultats et leurs composantes ;
- gérer les révisions ;
- assurer l’auditabilité et le multi-société.

Le frontend React ne doit pas devenir une seconde base métier.

---

## 2. Principes directeurs

### 2.1 Odoo comme source de vérité

Odoo doit stocker :

- les spécifications GreenCube ;
- les variantes techniques ;
- les études ;
- les entrées calculatoires ;
- les scénarios climatiques ;
- les résultats ;
- les révisions ;
- les versions du solver ;
- les paramètres administrables.

### 2.2 Immutabilité

Les éléments suivants doivent être auditables :

- une étude validée ;
- un résultat calculé ;
- une version du solver ;
- une version de spécification thermique utilisée.

Il est interdit de :

- modifier silencieusement un résultat ;
- écraser une étude validée ;
- réutiliser un résultat avec de nouvelles entrées ;
- modifier une spécification déjà utilisée dans une étude validée ;
- modifier rétroactivement une version du solver.

Toute évolution majeure doit produire une nouvelle version ou une nouvelle révision.

### 2.3 Provenance des données

Chaque donnée calculatoire doit pouvoir indiquer sa provenance.

Valeurs recommandées :

```text
catalog
api
user_confirmed
estimated_reference
estimated_manual
missing_fallback
```

---

## 3. Vérifications préalables

Avant toute modification :

1. inspecter l’arborescence du dépôt ;
2. identifier les modules Odoo existants ;
3. rechercher les modèles liés à GreenCube ;
4. rechercher les extensions de `product.template` ;
5. identifier les modèles liés au catalogue, au bâtiment, à l’énergie, au CRM et aux ventes ;
6. identifier les conventions Python, XML, sécurité et tests ;
7. vérifier la version exacte d’Odoo ;
8. exécuter les tests Odoo existants ;
9. ne supprimer aucun fichier ;
10. ne pas dupliquer un modèle métier existant s’il peut être étendu.

Le rapport préalable doit contenir :

- les modules inspectés ;
- les modèles réutilisables ;
- les dépendances retenues ;
- les fichiers à créer ;
- les fichiers à modifier ;
- les risques de migration ;
- les éventuels conflits.

---

## 4. Dépendances

Dépendances minimales envisagées :

```python
"depends": [
    "base",
    "mail",
    "product",
    "contacts",
]
```

Ajouter uniquement si nécessaire :

```python
"crm",
"sale_management",
```

Préférence d’architecture :

- `greencube_cooling` pour le cœur métier ;
- `greencube_cooling_crm` pour CRM ;
- `greencube_cooling_sale` pour Sales.

Le module cœur ne doit pas être couplé inutilement au CRM ou aux ventes.

---

## 5. Structure recommandée

```text
greencube_cooling/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── thermal_specification.py
│   ├── thermal_facade.py
│   ├── material_layer.py
│   ├── cooling_study.py
│   ├── occupancy_profile.py
│   ├── equipment_load.py
│   ├── ventilation_profile.py
│   ├── shading.py
│   ├── climate_dataset.py
│   ├── climate_scenario.py
│   ├── solver_version.py
│   ├── cooling_result.py
│   ├── cooling_result_component.py
│   ├── default_profile.py
│   └── commercial_capacity.py
├── security/
│   ├── greencube_cooling_groups.xml
│   ├── ir.model.access.csv
│   └── greencube_cooling_rules.xml
├── views/
│   ├── thermal_specification_views.xml
│   ├── cooling_study_views.xml
│   ├── climate_views.xml
│   ├── solver_views.xml
│   ├── default_profile_views.xml
│   ├── commercial_capacity_views.xml
│   └── greencube_cooling_menus.xml
├── data/
│   ├── sequence_data.xml
│   ├── solver_version_data.xml
│   ├── default_profile_data.xml
│   └── commercial_capacity_data.xml
├── demo/
│   └── greencube_cooling_demo.xml
├── tests/
│   ├── __init__.py
│   ├── common.py
│   ├── test_thermal_specification.py
│   ├── test_cooling_study.py
│   ├── test_revisions.py
│   ├── test_security.py
│   └── test_multicompany.py
├── migrations/
│   └── <version>/
│       ├── pre-migration.py
│       └── post-migration.py
└── README.md
```

Adapter cette structure aux conventions du dépôt réel.

---

## 6. Modèle `greencube.thermal.specification`

```python
_name = "greencube.thermal.specification"
_description = "GreenCube Thermal Specification"
_inherit = ["mail.thread", "mail.activity.mixin"]
_order = "name, version desc"
```

### 6.1 Champs

```python
name = fields.Char(required=True, tracking=True)
code = fields.Char(required=True, index=True, tracking=True)
active = fields.Boolean(default=True)
version = fields.Char(required=True, tracking=True)
valid_from = fields.Date()
valid_to = fields.Date()

product_template_id = fields.Many2one(
    "product.template",
    ondelete="restrict",
    index=True,
)

standard_model = fields.Boolean(default=True)

length_m = fields.Float(required=True, digits=(12, 3))
width_m = fields.Float(required=True, digits=(12, 3))
height_m = fields.Float(required=True, digits=(12, 3))

floor_area_m2 = fields.Float(
    compute="_compute_geometry",
    store=True,
    digits=(12, 3),
)

internal_volume_m3 = fields.Float(
    compute="_compute_geometry",
    store=True,
    digits=(12, 3),
)

wall_u_value = fields.Float(required=True, digits=(12, 4))
roof_u_value = fields.Float(required=True, digits=(12, 4))
floor_u_value = fields.Float(required=True, digits=(12, 4))

airtightness_n50 = fields.Float(digits=(12, 3))

thermal_mass_level = fields.Selection(
    [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ],
    required=True,
    default="medium",
)

thermal_bridge_factor = fields.Float(default=0.05, digits=(12, 4))
default_infiltration_ach = fields.Float(default=0.5, digits=(12, 3))

company_id = fields.Many2one(
    "res.company",
    required=True,
    default=lambda self: self.env.company,
    index=True,
)

notes = fields.Html()

facade_ids = fields.One2many(
    "greencube.thermal.facade",
    "thermal_specification_id",
)

material_layer_ids = fields.One2many(
    "greencube.material.layer",
    "thermal_specification_id",
)

study_count = fields.Integer(compute="_compute_study_count")
```

### 6.2 Contraintes

Contraintes SQL :

- unicité de `code`, `version`, `company_id` ;
- dimensions strictement positives ;
- valeurs U strictement positives ;
- `valid_to >= valid_from`.

Contraintes Python :

- valeurs U physiquement cohérentes ;
- `airtightness_n50 > 0` si renseignée ;
- `thermal_bridge_factor` entre 0 et 1 ;
- `default_infiltration_ach >= 0` ;
- cohérence des surfaces ;
- présence d’au moins une façade si compatible avec les données existantes.

Plages initiales recommandées :

```text
U-value : > 0 et <= 10 W/m².K
airtightness_n50 : > 0 et <= 50
thermal_bridge_factor : 0 à 1
infiltration_ach : 0 à 20
```

### 6.3 Verrouillage

Si une spécification est utilisée dans une étude validée, interdire la modification des champs calculatoires :

- dimensions ;
- valeurs U ;
- étanchéité ;
- inertie ;
- ponts thermiques ;
- infiltration ;
- façades ;
- couches de matériaux.

Autoriser :

- l’archivage ;
- les notes non calculatoires ;
- la création d’une nouvelle version.

Créer une action :

```text
Créer une nouvelle version
```

---

## 7. Modèle `greencube.thermal.facade`

```python
_name = "greencube.thermal.facade"
_description = "GreenCube Thermal Facade"
_order = "sequence, id"
```

### 7.1 Champs

```python
thermal_specification_id = fields.Many2one(
    "greencube.thermal.specification",
    required=True,
    ondelete="cascade",
    index=True,
)

orientation = fields.Selection(
    [
        ("north", "North"),
        ("north_east", "North-East"),
        ("east", "East"),
        ("south_east", "South-East"),
        ("south", "South"),
        ("south_west", "South-West"),
        ("west", "West"),
        ("north_west", "North-West"),
    ],
    required=True,
)

gross_area_m2 = fields.Float(required=True, digits=(12, 3))

opaque_area_m2 = fields.Float(
    compute="_compute_areas",
    store=True,
    digits=(12, 3),
)

glazing_area_m2 = fields.Float(default=0, digits=(12, 3))
window_u_value = fields.Float(digits=(12, 4))
solar_factor_g = fields.Float(digits=(12, 4))
visible_transmittance = fields.Float(digits=(12, 4))

default_shading_type = fields.Selection(
    [
        ("none", "None"),
        ("internal_blind", "Internal blind"),
        ("external_blind", "External blind"),
        ("brise_soleil", "Brise-soleil"),
        ("overhang", "Overhang"),
        ("natural", "Natural shading"),
        ("building", "Neighbouring building"),
        ("mountain", "Mountain mask"),
    ],
    default="none",
)

default_shading_factor = fields.Float(default=1.0, digits=(12, 4))
facade_code = fields.Char()
sequence = fields.Integer(default=10)
```

### 7.2 Règles

- `opaque_area_m2 = gross_area_m2 - glazing_area_m2` ;
- aucune surface négative ;
- vitrage inférieur ou égal à la surface brute ;
- facteur solaire entre 0 et 1 ;
- transmittance visible entre 0 et 1 ;
- facteur d’ombrage entre 0 et 1 ;
- valeur U obligatoire si vitrage > 0 ;
- facteur solaire obligatoire si vitrage > 0.

Créer une contrainte d’unicité sur :

```text
thermal_specification_id + orientation
```

sauf justification documentée d’un découpage multiple par orientation.

---

## 8. Modèle `greencube.material.layer`

```python
_name = "greencube.material.layer"
_description = "GreenCube Material Layer"
_order = "element_type, sequence, id"
```

### 8.1 Champs

- spécification thermique ;
- type d’élément ;
- matériau ;
- épaisseur ;
- conductivité ;
- densité ;
- capacité thermique massique ;
- résistance à la vapeur ;
- ordre.

Types :

```text
wall
roof
floor
internal_partition
```

### 8.2 Contraintes

- épaisseur > 0 ;
- conductivité > 0 ;
- densité > 0 ;
- capacité thermique > 0 ;
- ordre positif.

### 8.3 Champs calculés facultatifs

Résistance thermique :

```text
R = épaisseur en mètres / conductivité
```

Capacité thermique surfacique :

```text
C_surface = épaisseur × densité × capacité thermique
```

Ne pas calculer automatiquement une valeur U globale non documentée.

---

## 9. Modèle `greencube.cooling.study`

```python
_name = "greencube.cooling.study"
_description = "GreenCube Cooling Study"
_inherit = ["mail.thread", "mail.activity.mixin"]
_order = "create_date desc"
```

### 9.1 Champs

- nom ;
- référence ;
- partenaire ;
- responsable ;
- société ;
- statut ;
- révision ;
- étude parente ;
- étude racine ;
- spécification thermique ;
- géométrie standard ou personnalisée ;
- adresse ;
- ville ;
- code postal ;
- pays ;
- latitude ;
- longitude ;
- altitude ;
- fuseau horaire ;
- environnement ;
- température cible ;
- humidité cible ;
- niveau de service ;
- confiance ;
- date de calcul ;
- date de validation ;
- validateur ;
- snapshot d’entrée JSON ;
- dernier résultat ;
- nombre de résultats ;
- notes.

### 9.2 Statuts

```text
draft
incomplete
ready
calculating
calculated
validated
failed
archived
```

### 9.3 Niveaux de service

```text
standard
enhanced
heatwave_resilience
```

### 9.4 Environnements

```text
dense_urban
suburban
rural
mountain
coastal
industrial
```

### 9.5 Référence

Exemple :

```text
GCC/2026/00001
```

Révision :

```text
GCC/2026/00001-R02
```

La stratégie exacte doit être documentée.

### 9.6 Règles métier

Une étude :

- est modifiable en brouillon ;
- peut être incomplète ;
- devient prête lorsque les données minimales sont présentes ;
- passe à `calculating` pendant le solver ;
- passe à `calculated` lorsqu’un résultat existe ;
- est validable uniquement par un technicien ou manager ;
- n’est plus modifiable directement une fois validée ;
- doit créer une révision si une entrée calculatoire change après validation.

### 9.7 Révision

Créer :

```python
action_create_revision()
```

La méthode doit :

1. vérifier les droits ;
2. dupliquer l’étude ;
3. incrémenter la révision ;
4. conserver le lien source ;
5. conserver la racine ;
6. repasser en brouillon ;
7. effacer les champs de validation ;
8. ne pas copier les résultats actifs ;
9. copier les sous-lignes utiles ;
10. préserver l’audit.

### 9.8 Snapshot

`input_snapshot_json` doit être alimenté uniquement au moment du calcul.

Il doit contenir :

- étude ;
- révision ;
- spécification thermique ;
- version de spécification ;
- façades ;
- matériaux utiles ;
- occupation ;
- équipements ;
- ventilation ;
- ombrage ;
- climat ;
- consignes ;
- provenance ;
- date ;
- société ;
- version du schéma.

---

## 10. Modèle `greencube.cooling.occupancy.profile`

### 10.1 Champs

- étude ;
- type d’usage ;
- occupants habituels ;
- occupants maximum ;
- niveau d’activité ;
- jours d’usage ;
- heure de début ;
- heure de fin ;
- occupation nocturne ;
- chaleur sensible par personne ;
- chaleur latente par personne ;
- provenance.

### 10.2 Types d’usage

```text
office
housing
meeting_room
retail
workshop
medical
server_room
other
```

### 10.3 Activité

```text
rest
seated
light
moderate
high
```

### 10.4 Contraintes

- occupants >= 0 ;
- maximum >= habituels ;
- horaires entre 0 et 24 ;
- charges par personne positives ;
- valeurs par défaut marquées comme estimées.

---

## 11. Modèle `greencube.cooling.equipment.load`

### 11.1 Champs

- étude ;
- produit Odoo ;
- nom ;
- catégorie ;
- quantité ;
- puissance unitaire ;
- heures d’utilisation ;
- simultanéité ;
- facteur de dissipation ;
- fonctionnement permanent ;
- provenance ;
- notes ;
- charge thermique calculée.

### 11.2 Formule

```text
thermal_load_w =
quantity
× unit_power_w
× simultaneity_percent / 100
× heat_dissipation_factor
```

### 11.3 Catégories

```text
it
lighting
appliance
kitchen
network
battery
inverter
medical
machine
other
```

### 11.4 Contraintes

- quantité positive ;
- puissance >= 0 ;
- durée entre 0 et 24 ;
- simultanéité entre 0 et 100 ;
- dissipation entre 0 et 1.

---

## 12. Modèle `greencube.cooling.ventilation.profile`

### 12.1 Champs

- étude ;
- type ;
- débit ;
- renouvellements par heure ;
- rendement de récupération ;
- ouvertures de portes ;
- ouvertures de fenêtres ;
- étanchéité ;
- infiltration ;
- provenance.

### 12.2 Types

```text
natural
single_flow
double_flow
dedicated_mechanical
```

### 12.3 Fréquences

```text
rare
occasional
frequent
continuous
```

### 12.4 Contraintes

- débit >= 0 ;
- ACH >= 0 ;
- récupération entre 0 et 100 ;
- étanchéité positive si renseignée ;
- infiltration >= 0.

---

## 13. Modèle `greencube.cooling.shading`

### 13.1 Champs

- étude ;
- orientation ;
- type ;
- efficacité ;
- heure de début ;
- heure de fin ;
- automatique ;
- confirmé ;
- provenance.

### 13.2 Contraintes

- efficacité entre 0 et 100 ;
- horaires entre 0 et 24 ;
- cohérence début-fin.

---

## 14. Modèle `greencube.cooling.climate.dataset`

### 14.1 Rôle

Stocker les métadonnées climatiques et les synthèses.

### 14.2 Champs

- étude ;
- fournisseur ;
- version fournisseur ;
- date de récupération ;
- coordonnées ;
- altitude ;
- période ;
- résolution ;
- pièce jointe brute éventuelle ;
- résumé JSON ;
- clé de cache ;
- expiration ;
- statut ;
- erreur technique ;
- confiance.

### 14.3 Statuts

```text
pending
available
partial
stale
failed
```

### 14.4 Sécurité

Ne pas stocker :

- clés API ;
- headers d’authentification ;
- URLs signées sensibles ;
- secrets dans les erreurs.

---

## 15. Modèle `greencube.cooling.climate.scenario`

### 15.1 Scénarios

```text
reference_summer
hot_weather
prolonged_heatwave
```

### 15.2 Champs

- étude ;
- dataset ;
- type ;
- température extérieure ;
- température nocturne ;
- humidité ;
- rayonnement ;
- vent ;
- durée ;
- confiance ;
- provenance ;
- données détaillées JSON.

Créer une contrainte d’unicité :

```text
study_id + scenario_type
```

ou versionner explicitement les scénarios si plusieurs exécutions doivent être conservées.

---

## 16. Modèle `greencube.cooling.solver.version`

### 16.1 Champs

- nom ;
- code ;
- version ;
- actif ;
- description des formules ;
- coefficients JSON ;
- dates de validité ;
- checksum ;
- notes ;
- société ;
- statut.

### 16.2 Statuts

```text
draft
active
retired
```

### 16.3 Règles

- une seule version active par code et société ;
- une version utilisée ne peut pas être supprimée ;
- ses coefficients ne peuvent plus être modifiés ;
- toute évolution crée une nouvelle version ;
- checksum calculé à partir des paramètres utiles.

---

## 17. Modèle `greencube.cooling.result`

### 17.1 Immutabilité

Un résultat est immuable après création.

Seuls peuvent évoluer :

- notes non calculatoires ;
- archivage ;
- liens documentaires.

### 17.2 Champs

- étude ;
- version du solver ;
- statut ;
- puissance calculée ;
- puissance recommandée ;
- BTU/h ;
- capacité commerciale ;
- marge ;
- confiance ;
- charge dominante ;
- résumé scénarios JSON ;
- avertissements JSON ;
- recommandations JSON ;
- snapshot de calcul JSON ;
- date ;
- durée ;
- clé d’idempotence ;
- checksum des entrées.

### 17.3 Statuts

```text
success
partial
failed
superseded
```

Créer une contrainte d’unicité sur l’idempotency key lorsqu’elle existe.

---

## 18. Modèle `greencube.cooling.result.component`

### 18.1 Champs

- résultat ;
- scénario ;
- composante ;
- puissance W ;
- pourcentage ;
- formule ;
- entrées JSON ;
- ordre.

### 18.2 Types

```text
wall
roof
floor
window_conduction
solar
ventilation
infiltration
occupants_sensible
occupants_latent
equipment
lighting
safety_margin
```

### 18.3 Contraintes

- puissance >= 0 ;
- pourcentage entre 0 et 100 ;
- somme contrôlée avec tolérance ;
- résultat parent obligatoire.

---

## 19. Modèle `greencube.cooling.default.profile`

### 19.1 Champs

- nom ;
- usage ;
- actif ;
- occupants habituels ;
- occupants maximum ;
- activité ;
- température ;
- humidité ;
- débit d’air ;
- infiltration ;
- équipements W/m² ;
- éclairage W/m² ;
- niveau de service ;
- société.

### 19.2 Profils initiaux

- bureau ;
- logement ;
- salle de réunion ;
- commerce ;
- atelier ;
- cabinet médical ;
- salle informatique.

Ces données sont indicatives et non certifiées tant qu’elles ne sont pas validées.

---

## 20. Modèle `greencube.cooling.commercial.capacity`

### 20.1 Champs

- nom ;
- capacité BTU/h ;
- capacité kW ;
- actif ;
- charge minimale ;
- charge maximale ;
- ordre ;
- société.

### 20.2 Capacités initiales

```text
7 000 BTU/h
9 000 BTU/h
12 000 BTU/h
18 000 BTU/h
24 000 BTU/h
30 000 BTU/h
36 000 BTU/h
```

Conversion :

```text
1 kW = 3412.142 BTU/h
```

Éviter toute divergence entre les champs.

---

## 21. Vues Odoo

## 21.1 Spécifications thermiques

Vue liste :

- code ;
- nom ;
- version ;
- produit ;
- surface ;
- volume ;
- actif ;
- société.

Vue formulaire, onglets :

1. Général
2. Géométrie
3. Enveloppe
4. Façades et vitrages
5. Matériaux
6. Utilisation
7. Notes

Ajouter :

- bouton nouvelle version ;
- smart button études ;
- indication de verrouillage.

## 21.2 Études

Vue liste ou kanban :

- référence ;
- nom ;
- client ;
- modèle ;
- statut ;
- révision ;
- confiance ;
- puissance recommandée ;
- responsable ;
- date.

Vue formulaire, onglets :

1. Projet
2. Localisation
3. GreenCube
4. Occupation
5. Équipements
6. Ventilation
7. Ombrage
8. Climat
9. Résultats
10. Audit

Actions :

- vérifier la complétude ;
- créer une révision ;
- archiver ;
- valider si autorisé.

Ne pas simuler de faux résultat si le solver n’est pas encore implémenté.

---

## 22. Menus

```text
GreenCube Cooling
├── Études
│   ├── Toutes les études
│   ├── Mes études
│   ├── À compléter
│   ├── Calculées
│   └── Validées
├── Catalogue thermique
│   ├── Spécifications GreenCube
│   └── Matériaux
├── Climat
│   ├── Jeux de données
│   └── Scénarios
└── Configuration
    ├── Profils d’usage
    ├── Capacités commerciales
    └── Versions du solver
```

Les menus de configuration sont réservés aux managers.

---

## 23. Groupes et droits

## 23.1 Utilisateur

Groupe :

```text
group_greencube_cooling_user
```

Peut :

- créer ses études ;
- modifier ses études non validées ;
- consulter ses résultats ;
- consulter le catalogue actif.

Ne peut pas :

- modifier les spécifications ;
- modifier le solver ;
- valider ;
- consulter une autre société.

## 23.2 Technicien

Groupe :

```text
group_greencube_cooling_technician
```

Hérite de l’utilisateur.

Peut :

- consulter les études de sa société ;
- compléter les données ;
- calculer ;
- valider ;
- créer une révision.

## 23.3 Manager

Groupe :

```text
group_greencube_cooling_manager
```

Hérite du technicien.

Peut :

- gérer les spécifications ;
- gérer les profils ;
- gérer les capacités ;
- gérer les versions du solver ;
- consulter toutes les études de sa société.

## 23.4 Multi-société

Record rules :

```python
company_id in company_ids
```

Tester avec au moins deux sociétés.

---

## 24. Chatter et audit

Tracer les champs critiques :

- statut ;
- modèle GreenCube ;
- température cible ;
- niveau de service ;
- confiance ;
- validation ;
- responsable ;
- version ;
- dates de validité.

Créer des activités pour :

- étude incomplète ;
- étude prête ;
- climat en échec ;
- résultat à contrôler.

Éviter un chatter trop bruité.

---

## 25. Données initiales et démonstration

### 25.1 Données initiales

Créer :

- séquence ;
- capacités commerciales ;
- groupes ;
- menus ;
- version initiale du solver clairement marquée ;
- profils nécessaires.

### 25.2 Données de démonstration

Créer séparément :

- GreenCube Studio ;
- GreenCube Bureau ;
- GreenCube Habitat ;
- GreenCube Commerce ;
- profils d’usage ;
- exemple d’étude.

Ne jamais présenter une valeur fictive comme certifiée.

---

## 26. Migration

Si des modèles similaires existent :

1. ne pas créer de doublons ;
2. proposer un mapping ;
3. utiliser héritage ou champs liés ;
4. conserver les identifiants ;
5. créer une migration.

Les migrations doivent :

- être idempotentes ;
- journaliser les changements ;
- ne supprimer aucune donnée ;
- détecter les ambiguïtés ;
- échouer explicitement en cas d’incertitude.

---

## 27. Tests obligatoires

## 27.1 Spécifications

Tester :

- surface ;
- volume ;
- dimensions négatives ;
- valeur U invalide ;
- vitrage supérieur à la façade ;
- facteur solaire invalide ;
- duplication de version ;
- verrouillage après validation.

## 27.2 Études

Tester :

- création ;
- référence ;
- statuts ;
- complétude ;
- verrouillage ;
- révision ;
- copie des sous-lignes ;
- absence de copie du résultat actif ;
- conservation de la racine.

## 27.3 Équipements

Tester :

- calcul ;
- simultanéité ;
- dissipation ;
- données invalides.

## 27.4 Ventilation

Tester :

- rendement > 100 ;
- débit négatif ;
- profil valide.

## 27.5 Résultats

Tester :

- immutabilité ;
- idempotence ;
- checksum ;
- composantes ;
- lien étude-résultat.

## 27.6 Sécurité

Tester :

- utilisateur ;
- technicien ;
- manager ;
- autre société ;
- configuration ;
- validation interdite.

## 27.7 Installation

Tester :

- base vide ;
- mise à jour ;
- données initiales ;
- absence de doublons.

---

## 28. Critères d’acceptation

Le module est accepté uniquement si :

1. il s’installe sur Odoo Community 18 ;
2. il se met à jour sans erreur ;
3. les modèles respectent les droits ;
4. les vues s’ouvrent ;
5. les contraintes fonctionnent ;
6. une étude peut être créée ;
7. l’occupation peut être enregistrée ;
8. les équipements peuvent être enregistrés ;
9. la ventilation peut être enregistrée ;
10. l’ombrage peut être enregistré ;
11. une étude validée est verrouillée ;
12. une révision peut être créée ;
13. les spécifications utilisées sont verrouillées ;
14. les capacités sont chargées ;
15. les profils sont administrables ;
16. le multi-société fonctionne ;
17. tous les tests ajoutés passent ;
18. aucun test existant n’est cassé sans justification ;
19. aucun fichier n’est supprimé ;
20. les données fictives sont identifiées.

---

## 29. Rapport final attendu

### Fichiers

- fichiers créés ;
- fichiers modifiés ;
- fichiers non modifiés ;
- fichiers supprimés, normalement aucun.

### Commandes

- installation ;
- mise à jour ;
- tests ;
- lint ;
- vérifications.

### Résultats

- succès ;
- échecs ;
- limitations ;
- tests non exécutés ;
- raisons.

### Décisions

- modèles réutilisés ;
- modèles créés ;
- versionnement ;
- révisions ;
- multi-société ;
- immutabilité ;
- dépendances.

### Limitations

- solver non encore implémenté ;
- API non encore implémentée ;
- données techniques à valider ;
- intégrations différées.

### Patch

- diff ;
- patch réintégrable ;
- application ;
- rollback ;
- migration.

---

## 30. Contrôle final

Avant conclusion :

1. exécuter les tests du module ;
2. exécuter les tests impactés ;
3. installer sur une base vierge ;
4. mettre à jour une base existante ;
5. vérifier les vues ;
6. vérifier les groupes ;
7. vérifier les record rules ;
8. vérifier le multi-société ;
9. vérifier les contraintes ;
10. vérifier les révisions ;
11. vérifier l’absence de suppression ;
12. vérifier l’absence de secret ;
13. vérifier l’identification des données de démonstration ;
14. vérifier l’absence de dépendance inutile au CRM ;
15. ne jamais déclarer un test réussi sans l’avoir exécuté.

---

## 31. Limites de ce lot

Ce lot implémente :

- le modèle de données ;
- les droits ;
- les vues ;
- les règles métier ;
- le versionnement ;
- les révisions ;
- les structures nécessaires au climat et au solver.

Il n’implémente pas encore nécessairement :

- l’API JSON complète ;
- le service climatique ;
- le solver thermique ;
- le PDF final ;
- l’intégration CRM/Sales.

Ces éléments doivent être traités dans les lots suivants.
