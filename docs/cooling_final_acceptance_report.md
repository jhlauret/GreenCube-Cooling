# Rapport final de recette — GC-COOLING MVP (GC-COOLING-17)

Date d'exécution : 2026-07-24. Environnement : conteneurs Docker `gc_odoo` (image
`odoo:18.0-20260630`, `sleep infinity`, exécution via `docker exec`) et `gc_pg` (`postgres:15`), plus
environnement local Node 20.19.6 / npm 10.8.2 / Python 3 pour le worker et les suites Python pures.
Base de démonstration persistante : `gc_test_db` (jamais réinitialisée par ce lot).

## Synthèse

- Périmètre : consolidation finale des 18 lots GC-COOLING (06 à 18, plus vérification de non-régression
  de 01-05A/13/16 déjà livrés).
- Version module : `18.0.14.0.0` (inchangée — **aucune modification fonctionnelle** n'a été nécessaire
  dans ce lot ; voir section « Migrations »).
- **Décision : GO** (voir section Gate GO/NO-GO).
- P0 ouverts : 0. P1 ouverts sur le parcours principal : 0.
- Risques/limites principaux : absence de contrat OpenAPI versionné, absence de scripts/compose
  d'exploitation testés sur infra réelle (voir `docs/cooling_known_issues.md`, KI-03/KI-04/KI-05) —
  aucun n'affecte le parcours principal de pré-dimensionnement.

## Architecture (rappel, non modifiée par ce lot)

- Frontend React/TS/Vite (`frontend/`), interface de saisie/restitution, jamais source de vérité.
- Odoo 18 Community (`addons/greencube_cooling/`) : source de vérité métier (études, révisions,
  catalogue, scénarios, snapshots, résultats).
- MERCURE (`services/mercure/engine.py`) : cœur mathématique pur, sans accès ORM direct.
- Worker EnergyPlus (`energyplus_worker/worker.py`) : processus autonome, jamais dans le processus web
  Odoo ; claim atomique (`SELECT ... FOR UPDATE SKIP LOCKED`), cron de récupération des jobs bloqués.
- CI (`.github/workflows/ci.yml`) : jobs `frontend`, `python-pure`, `backend-odoo`.

## Commandes exécutées et résultats réels

### 1. Nettoyage des bases de test résiduelles

```
$ docker exec gc_pg psql -U odoo -d postgres -c "\l"
# 11 bases de test temporaires (gc_test_1784620989, gc_test_fresh_install, gc_test_gc16,
# gc_test_run1..3, gc_test_db2..4, gc_manual, gc_test_fresh_20260721) laissées par les lots
# précédents ont été DROPées. gc_test_db (démo persistante) conservée intacte.
```

### 2. Installation sur base vierge + suite complète (fresh-install)

```
$ docker exec gc_odoo odoo --addons-path=/mnt/extra-addons,/mnt/addons \
    --db_host=gc_pg --db_user=odoo --db_password=odoo \
    -d gc_test_fresh -i greencube_cooling \
    --test-enable --test-tags greencube_cooling --stop-after-init --log-level=test
```

Résultat réel (extrait des logs) :

```
odoo.tests.stats: greencube_cooling: 226 tests 19.77s 13081 queries
odoo.tests.result: 0 failed, 0 error(s) of 186 tests when loading database 'gc_test_fresh'
```

Base `gc_test_fresh` supprimée après coup.

### 3. Mise à jour d'une base existante (upgrade, sur la démo persistante `gc_test_db`)

```
$ docker exec gc_odoo odoo --addons-path=/mnt/extra-addons,/mnt/addons \
    --db_host=gc_pg --db_user=odoo --db_password=odoo \
    -d gc_test_db -u greencube_cooling \
    --test-enable --test-tags greencube_cooling --stop-after-init --log-level=test
```

Résultat réel :

```
odoo.tests.stats: greencube_cooling: 226 tests 19.72s 13081 queries
odoo.tests.result: 0 failed, 0 error(s) of 186 tests when loading database 'gc_test_db'
```

`gc_test_db` n'a subi aucune perte de données existantes (mise à jour de module standard Odoo, pas de
`--init` ni de suppression de base). Le comportement observé au passage (log `WARNING ... Historical
climate lookup failed for study ..., falling back`) est le fallback climatique attendu — les tests
bloquent volontairement les appels réseau sortants (`odoo.tests.common.requests`) ; ce n'est pas une
anomalie.

### 4. Worker EnergyPlus (processus autonome, hors Odoo)

```
$ python3 -m unittest energyplus_worker.test_worker -v
Ran 12 tests in 0.026s
OK
```

### 5. Suites Python pures (MERCURE, sérialisation, compatibilité, traducteur Honeybee)

```
$ cd addons/greencube_cooling
$ python3 tests/test_mercure_engine.py         # Ran 24 tests — OK
$ python3 tests/test_mercure_serialization.py  # Ran 3 tests — OK
$ python3 tests/test_compatibility.py          # Ran 12 tests — OK
$ python3 tests/test_honeybee_translator.py    # Ran 11 tests — OK
```

### 6. Frontend — lint, TypeScript strict, tests, build

```
$ cd frontend
$ npm run lint            # oxlint — 0 erreur
$ npx tsc -b --noEmit      # aucune sortie = 0 erreur
$ npm run test -- --run   # Test Files 10 passed (10) — Tests 99 passed (99)
$ npm run build           # tsc -b && vite build — succès, dist/ généré (308 kB JS, 20.6 kB CSS)
```

### 7. Dépendances

```
$ npm audit           # found 0 vulnerabilities
$ npm audit --omit=dev # found 0 vulnerabilities
```

`pip-audit` non exécuté : environnement Python « externally managed » sans `requirements.txt` propre au
module (le module s'exécute dans le runtime de l'image Odoo officielle `odoo:18.0-20260630`, déjà
maintenue en amont). Voir `docs/cooling_known_issues.md` KI-05.

### 8. Secrets

```
$ grep -rniE "(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9]{8,}" \
    --include="*.py" --include="*.ts" --include="*.tsx" --include="*.yml" --include="*.yaml" .
# aucune correspondance (hors node_modules/.git)
$ find . -iname "*.env*" -not -path "*/node_modules/*" -not -path "*/.git/*"
# frontend/.env.example uniquement (aucune valeur secrète réelle dedans)
```

## Tests obligatoires — statut

| Suite | Statut | Preuve |
|---|---|---|
| Lint frontend | PASS | `npm run lint` (oxlint, 0 erreur) |
| TypeScript strict | PASS | `npx tsc -b --noEmit`, aucune sortie |
| Tests frontend (Vitest) | PASS | 99/99, 10 fichiers |
| Build production frontend | PASS | `npm run build` réussi |
| Odoo — installation base vierge + tests | PASS | 0 failed, 0 error, 186 tests |
| Odoo — mise à jour base existante + tests | PASS | 0 failed, 0 error, 186 tests, `gc_test_db` intacte |
| Worker EnergyPlus (standalone) | PASS | 12/12 |
| MERCURE / sérialisation / compatibilité / Honeybee (Python pur) | PASS | 24+3+12+11 = 50/50 |
| `npm audit` | PASS | 0 vulnérabilité |
| `pip-audit` | NON EXÉCUTÉ (justifié) | KI-05 |
| Playwright (E2E navigateur) | NON EXÉCUTÉ | Aucun navigateur Playwright installé dans ce bac à sable headless ; le parcours principal est couvert côté backend par `test_http_api.py::test_full_wizard_flow_as_standard_user` (flux HTTP complet réel) et côté frontend par les tests de composants/store — voir Known issues pour la limite assumée |
| Docker Compose / scripts d'exploitation | NON PRODUIT (justifié) | KI-04 — aucune infra à tester réellement, refus de fabriquer un artefact non vérifié |

## Anomalies (classification P0-P3)

Voir `docs/cooling_known_issues.md` pour le détail complet. Résumé :

- P0 : 0
- P1 (parcours principal) : 0
- P2 : KI-03 (pas d'OpenAPI versionné), KI-04 (pas de scripts/compose d'exploitation testés sur infra
  réelle), KI-05 (pip-audit non exécutable)
- P3 : KI-01 (tri équipement côté client), KI-02 (moteur MERCURE TS non appelé en prod, gardé comme
  référence), KI-06 (comportement attendu, non une anomalie)

## Risques et limites

- Le parcours EnergyPlus réel (exécution du binaire) n'a jamais pu être exercé de bout en bout dans
  aucun environnement disponible pour cette campagne (aucun binaire EnergyPlus/Honeybee installé) — le
  chemin `EnergyPlusUnavailableError` est celui réellement exercé et rapporté honnêtement, jamais simulé
  comme un succès. Le fallback MERCURE fonctionne dans tous les cas.
- Aucune démonstration de déploiement VPS réel, sauvegarde/restauration réelle sur PostgreSQL/filestore,
  ni rollback réel n'a été faite dans ce lot — seule la procédure manuelle standard Odoo est documentée
  ci-dessous, non exécutée contre une cible de production.
- L'exécution CI GitHub Actions elle-même (déclenchement réel sur l'infrastructure Actions) n'a pas été
  vérifiée dans cette session (nécessiterait un `git push` vers le remote configuré) — seule
  l'équivalence locale via Docker (ce rapport) est une preuve directe.

## Procédure de validation manuelle (déploiement/sauvegarde/rollback — documentée, non exercée sur VPS réel)

1. Sauvegarde avant migration : `pg_dump -U odoo -d <db> -F c -f backup_<date>.dump` +
   sauvegarde du filestore Odoo (`~/.local/share/Odoo/filestore/<db>`).
2. Mise à jour : `odoo --addons-path=... -d <db> -u greencube_cooling --stop-after-init`
   (idempotent, revérifié dans ce rapport section 3 ci-dessus).
3. Vérification post-migration : rejouer `--test-enable --test-tags greencube_cooling` sur une copie de
   la base avant de la considérer valide en production.
4. Rollback module : restaurer le dump PostgreSQL pré-migration (`pg_restore -c -d <db>
   backup_<date>.dump`) et réinstaller la version précédente du code addon — aucune migration livrée
   dans cette campagne n'est destructive (voir `migrations/README.md`), donc un rollback de code sans
   restauration de dump reste possible tant qu'aucune donnée n'a été saisie avec les nouveaux champs.
5. Frontend : rollback = redéployer le `dist/` précédent (aucun état serveur côté frontend).
6. Worker EnergyPlus : processus indépendant, redémarrage sans impact sur Odoo (jobs restent `queued`
   et sont repris par le cron de récupération, `_requeue_stalled_energyplus_jobs`).

## Gate GO / NO-GO

| Critère | Statut |
|---|---|
| 0 P0 ouverts | ✅ |
| 0 P1 ouverts sur le parcours principal | ✅ |
| 0 vulnérabilité critique/élevée ouverte connue (npm audit) | ✅ |
| 0 secret exposé | ✅ |
| Migrations validées (fresh-install + upgrade réels) | ✅ |
| Rollback documenté | ✅ (procédure manuelle ci-dessus ; pas d'exercice réel sur VPS) |
| Smoke tests réussis | ✅ (flux HTTP complet du wizard rejoué dans `test_http_api.py`) |
| Parcours principal réussi | ✅ (étude → localisation/climat → modèle → orientation/vitrages →
  usage/occupation → équipements → ventilation/infiltration/confort → vérification → snapshot → MERCURE
  → résultats → révision, tous couverts par la suite Odoo 186 tests / 0 échec) |

**Décision : GO** pour le périmètre MVP tel que défini (pré-dimensionnement du besoin de refroidissement,
hors catalogue commercial complet/devis/facturation/rapport PDF définitif — explicitement hors périmètre
de ce lot). Les limites d'exploitation (KI-03/04/05) sont documentées et ne bloquent pas le parcours
principal ; elles sont recommandées comme premier chantier du prochain incrément.
