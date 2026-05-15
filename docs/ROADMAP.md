# Roadmap V1

Cette roadmap sert de sequence d'execution. Chaque etape doit etre verifiee, committee et poussee avant de passer a la suivante.

## Etape 0 - Documentation Initiale

Objectif :

- poser le README principal ;
- decrire l'architecture ;
- cadrer la roadmap ;
- documenter le futur README design.

Verification :

- relire les documents ;
- verifier les liens internes ;
- verifier l'etat git ;
- pousser sur GitHub.

## Etape 1 - Base Backend

Objectif :

- creer `requirements.txt` ;
- creer `config.yaml` ;
- creer la structure `backend/src/` ;
- ajouter les modules vides mais importables ;
- ajouter un point d'entree `run.py`.

Verification :

- `python3 backend/src/run.py --help`
- import des modules principaux ;
- commit et push.

## Etape 2 - Roulette Board Et Types De Mises

Objectif :

- implementer les numeros europeens ;
- implementer rouge/noir, pair/impair, manque/passe ;
- implementer douzaines et colonnes ;
- generer les mises legales ;
- valider les payouts.

Verification :

- tests unitaires sur les payouts ;
- tests unitaires sur les tailles de couverture ;
- verification manuelle de quelques mises : plein, cheval, carre, douzaine.

## Etape 3 - Evaluateur Theorique

Objectif :

- calculer `gross_return` et `net_profit` ;
- evaluer une strategie sur les 37 numeros ;
- produire les metriques de base ;
- produire les explications de hits.

Verification :

- scenario connu sur le numero `17` ;
- esperance negative coherente avec la roulette europeenne ;
- exports temporaires lisibles.

## Etape 4 - Generation Grid Search Et Random Search

Objectif :

- generer des strategies respectant bankroll et unites ;
- implementer grid search ;
- implementer random search ;
- dedupliquer ou fusionner les mises si configure ;
- controler couverture et concentration.

Verification :

- generation rapide de `100` strategies ;
- generation plus large de `5000` strategies ;
- aucune strategie ne depasse la bankroll ;
- couverture dans les bornes configurees si active.

## Etape 5 - Scoring Et Selection

Objectif :

- implementer les profils `safe`, `balanced`, `aggressive` ;
- calculer un score comparable ;
- trier les strategies ;
- conserver `keep_top_n`.

Verification :

- `keep_top_n` respecte ;
- score stable sur seed fixe ;
- les meilleures strategies ont des metriques coherentes.

## Etape 6 - Exports CSV Et JSON

Objectif :

- generer `best_combos.csv` ;
- generer `best_combo_detail.json` ;
- generer `number_outcomes.csv` ;
- stabiliser les schemas de colonnes.

Verification :

- fichiers presents dans `outputs/` ;
- colonnes conformes a la documentation ;
- JSON valide ;
- lecture possible par le frontend.

## Etape 7 - Monte Carlo

Objectif :

- simuler `sessions` x `spins_per_session` ;
- suivre la bankroll spin par spin ;
- calculer drawdown, ruine, gros hits, profit final ;
- sortir les resultats agregees et trajectoires.

Verification :

- run rapide avec `100` sessions ;
- run intermediaire avec `1000` sessions ;
- `monte_carlo_results.csv` et `monte_carlo_paths.csv` generes ;
- aucune bankroll negative non controlee.

## Etape 8 - Visualisations HTML Plotly

Objectif :

- generer `monte_carlo_paths.html` ;
- generer `monte_carlo_summary.html` ;
- generer `monte_carlo_comparison.html` ;
- limiter l'affichage a `100` a `1000` courbes individuelles.

Verification :

- fichiers HTML ouvrables ;
- courbe moyenne visible ;
- distribution des bankrolls finales visible ;
- comparaison des strategies lisible.

## Etape 9 - Frontend React

Objectif :

- creer l'application React ;
- construire le tapis roulette ;
- afficher les overlays de mises ;
- afficher les couleurs par profit/perte ;
- afficher les tooltips ;
- afficher les graphiques Monte Carlo.

Verification :

- `npm install` ;
- `npm run dev` ;
- verification visuelle desktop et mobile ;
- aucune regression des exports backend.

## Etape 10 - Integration Complete

Objectif :

- connecter backend et frontend ;
- copier ou exposer `best_combo_detail.json` cote frontend ;
- permettre la selection d'une strategie ;
- verifier l'ensemble du flux.

Verification :

- pipeline backend complet ;
- frontend lance ;
- tapis coherent avec les donnees ;
- courbes Monte Carlo coherentes ;
- commit et push final V1.
