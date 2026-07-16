# GreenCube Cooling — module Odoo Community 18

## Périmètre livré dans ce lot

- **Modèles** : `greencube.thermal.specification` (+ `greencube.thermal.facade`), `greencube.cooling.study`
  (avec statuts, révisions, snapshot, verrouillage après validation), `occupancy.profile`, `equipment.load`,
  `ventilation.profile`, `shading`, `climate.scenario`, `solver.version`, `result` (+ `result.component`,
  immuables), `equipment.selection`, `commercial.capacity`, et une extension de `product.template` pour le
  catalogue équipement (réutilisation d'Odoo, pas de nouveau catalogue produit).
- **Sécurité** : 4 groupes (`user`, `technician`, `manager`, `admin`), ACL par modèle, règles multi-société
  (`company_id in company_ids`) et règle "un utilisateur ne voit que ses études".
- **Vues** : liste/formulaire pour les études et les spécifications thermiques, menus.
- **Moteur MERCURE** : portage Python 1:1 de `frontend/src/mercure/engine.ts`, indépendant de l'ORM
  (`services/mercure/`), appelé de façon synchrone par `cooling_study.action_calculate()`.
- **Moteur de compatibilité équipement** : portage Python de `frontend/src/equipment/compatibility.ts`
  (`services/compatibility.py`).
- **API JSON** (`controllers/api.py`) : études (CRUD), révisions, validation, snapshot, calcul (MERCURE
  synchrone), résultats, catalogue équipement, recommandations et sélection d'équipement — endpoints alignés
  sur `README_GC-COOLING-MASTER.md`, avec le format d'erreur standard (`error.code/message/field/section/action/request_id`).

## Ce qui a été réellement vérifié

- `python3 -c "ast.parse(...)"` sur tous les fichiers `.py` du module : **aucune erreur de syntaxe**.
- `python3 -c "xml.etree.ElementTree.parse(...)"` sur tous les fichiers `.xml` : **tous bien formés**.
- `python3 tests/test_mercure_engine.py` — **13 tests unittest passent**, y compris les propriétés
  monotones exigées par le prompt MERCURE (plus de vitrage n'abaisse jamais le solaire, plus d'occupants
  n'abaisse jamais les gains, une meilleure récupération n'augmente jamais la charge de ventilation, etc.).
  Ce module ne dépend pas d'Odoo — il tourne avec le seul interpréteur Python standard.
- `python3 tests/test_compatibility.py` — **5 tests unittest passent** sur le moteur de compatibilité produit.

## Ce qui n'a PAS pu être vérifié dans cet environnement

Aucun runtime Odoo (ni `odoo-bin`, ni PostgreSQL, ni `pip`) n'est disponible dans cet environnement
d'exécution. En conséquence, **je n'ai pas pu prouver** :

- que le module s'installe sur une base Odoo 18 vierge ;
- que les vues s'ouvrent sans erreur de rendu ;
- que les contraintes SQL/Python s'exécutent correctement via l'ORM réel ;
- que les `ir.model.access.csv` / record rules produisent les permissions attendues ;
- que les routes JSON répondent correctement à de vraies requêtes HTTP authentifiées ;
- que les migrations et la mise à jour d'une base existante fonctionnent.

Le code a été écrit en suivant strictement les conventions Odoo 18 (nouvelle syntaxe `invisible="..."` dans
les vues, `@api.model_create_multi`, etc.), mais **ceci reste non exécuté** tant qu'une vraie instance Odoo
n'est pas disponible. Avant toute mise en production, il faut :

1. installer le module sur une base vierge (`odoo-bin -i greencube_cooling`) et vérifier le code retour ;
2. lancer `odoo-bin -i greencube_cooling --test-enable --stop-after-init` pour exécuter `tests/` sous le
   TransactionCase d'Odoo (le contenu actuel n'a que des tests purs Python ; il faudra ajouter des
   `TransactionCase` couvrant la création d'étude, les révisions, le verrouillage post-validation, et le
   multi-société, comme l'exige `README_GC-COOLING-01_MODULE_ODOO.md` §27) ;
3. tester une mise à jour (`-u greencube_cooling`) sur une base contenant déjà des données ;
4. tester les routes API avec un vrai client HTTP authentifié.

## Limitations connues de ce lot

- **Climat (GC-COOLING-03/04)** non implémenté : `_build_climate_scenarios()` dans `cooling_study.py`
  reproduit la même heuristique que le mock frontend (température de base selon l'altitude/l'environnement)
  plutôt que d'interroger un vrai service climatique. À remplacer par le lot climat quand il sera livré.
- **Snapshot** (`action_create_snapshot`) construit un hash simplifié et ne persiste pas encore de modèle
  `greencube.cooling.calculation.snapshot` dédié — le payload JSON est stocké directement sur l'étude.
  Une vraie table de snapshot immuable est nécessaire pour GC-COOLING-13.
- **Honeybee / EnergyPlus** non implémenté : seul MERCURE est câblé. `greencube.cooling.calculation.job`
  n'existe pas encore en tant que modèle séparé — le contrôleur traite le résultat MERCURE comme un job
  toujours `completed` de façon synchrone (acceptable pour MERCURE seul, insuffisant pour EnergyPlus qui
  doit être asynchrone et isolé du process web).
- **`greencube.material.layer`** (couches de matériaux détaillées) non implémenté — hors périmètre MVP.
- **`greencube.cooling.climate.dataset`** non implémenté — seul `climate.scenario` existe.
- **CRM/Sales, devis, facturation** : explicitement hors périmètre, conformément aux limites du Master Prompt.
- **Frontend non branché sur cette API** : le frontend React construit précédemment utilise encore un store
  Zustand mocké (`localStorage`) ; le remplacer par de vrais appels à `/api/v1/greencube/cooling/...` est la
  prochaine étape d'intégration.
- **Aucune donnée de démonstration** n'a été créée (`demo/greencube_cooling_demo.xml` absent) — à ajouter
  avant une recette utilisateur.

## Prochaines étapes suggérées

1. Faire tourner ce module sur une vraie instance Odoo 18 pour lever les limitations ci-dessus.
2. Écrire les tests Odoo `TransactionCase` (§27 du prompt GC-COOLING-01).
3. Brancher le frontend React sur cette API (remplacer `store/studyStore.ts` mock par TanStack Query + fetch).
4. Traiter GC-COOLING-03/04 (géolocalisation, climat) pour remplacer l'heuristique de scénarios climatiques.
