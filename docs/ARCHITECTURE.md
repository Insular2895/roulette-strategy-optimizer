# Architecture Technique

Ce document decrit la logique cible du moteur Roulette Strategy Optimizer.

## Principe General

Le systeme se compose de trois blocs :

- un backend Python pour generer, evaluer, scorer et simuler les strategies ;
- un dossier `outputs/` pour stocker les exports data et visualisations HTML ;
- un frontend React pour afficher le tapis roulette, les overlays de mises et les courbes Monte Carlo.

Le moteur ne modifie pas les probabilites fondamentales de la roulette. Il analyse des profils de session et compare des structures de mises selon leur risque, leur couverture, leur potentiel de gros hit et leur comportement en simulation.

## Backend

### `roulette_board.py`

Responsabilites :

- representer la roulette europeenne ;
- fournir les numeros `0` a `36` ;
- definir les couleurs rouge/noir ;
- definir les douzaines, colonnes, pair/impair, manque/passe ;
- exposer les voisinages utiles au tapis.

### `bet_types.py`

Responsabilites :

- definir les types de mises supportes ;
- stocker les payouts ;
- generer les mises legales du tapis ;
- valider qu'une mise est coherente.

Types cibles :

- `straight`
- `split`
- `street`
- `corner`
- `sixline`
- `dozen`
- `column`
- `even_money`

### `combo_generator.py`

Responsabilites :

- generer des combinaisons de mises ;
- supporter `grid`, `random` et `hybrid` ;
- respecter la bankroll et les tailles autorisees ;
- controler la couverture et la concentration ;
- permettre les mises repetees si configure.

Le mode hybride pourra muter et recombiner les meilleures strategies.

### `evaluator.py`

Responsabilites :

- simuler chaque strategie sur les 37 issues possibles ;
- calculer le retour brut et le profit net par numero ;
- identifier les numeros couverts, profitables et explosifs ;
- produire des explications de profit par numero.

Formules :

```text
gross_return = sum(winning_stake * (payout + 1))
net_profit = gross_return - total_staked
```

### `scoring.py`

Responsabilites :

- calculer les scores selon le profil choisi ;
- ponderer couverture, probabilite de profit, gain moyen, gros hits, max profit et risque ;
- normaliser les metriques pour comparer les strategies.

Profils cibles :

```yaml
profiles:
  safe:
    coverage_weight: 0.55
    profit_probability_weight: 0.20
    avg_win_weight: 0.10
    big_hit_weight: 0.05
    risk_weight: 0.10

  balanced:
    coverage_weight: 0.35
    profit_probability_weight: 0.20
    avg_win_weight: 0.20
    big_hit_weight: 0.15
    max_profit_weight: 0.10
    risk_weight: 0.10

  aggressive:
    coverage_weight: 0.20
    profit_probability_weight: 0.10
    avg_win_weight: 0.20
    big_hit_weight: 0.30
    max_profit_weight: 0.20
    risk_weight: 0.10
```

### `optimizer.py`

Responsabilites :

- orchestrer generation, evaluation et scoring ;
- trier les strategies ;
- conserver `keep_top_n` ;
- preparer les meilleures strategies pour Monte Carlo.

### `monte_carlo.py`

Responsabilites :

- simuler des sessions aleatoires ;
- appliquer les profits et pertes spin par spin ;
- calculer les trajectoires bankroll ;
- mesurer drawdown, ruine, final bankroll, gros hits et volatilite.

### `visual_export.py`

Responsabilites :

- exporter les fichiers CSV et JSON ;
- generer les visualisations HTML avec Plotly ;
- produire les fichiers consommes par le frontend.

### `run.py`

Responsabilites :

- charger `config.yaml` ;
- accepter les overrides CLI ;
- lancer le pipeline complet ;
- ecrire les outputs.

## Frontend

Le frontend doit lire les exports du backend et afficher deux vues principales.

### Vue Tapis Roulette

Composants cibles :

- `RouletteBoard.jsx`
- `RouletteWheel.jsx`
- `BetOverlay.jsx`
- `NumberTooltip.jsx`
- `StrategySummary.jsx`

La vue doit montrer :

- le tapis europeen ;
- les mises posees ;
- les zones couvertes ;
- les zones de superposition ;
- les gains par numero ;
- les hits explosifs ;
- une explication au survol.

### Vue Monte Carlo

Composants cibles :

- `MonteCarloChart.jsx`
- `MonteCarloSummary.jsx`

La vue doit montrer :

- les trajectoires individuelles en transparence ;
- la courbe moyenne ;
- la mediane optionnelle ;
- la distribution des bankrolls finales ;
- le filtrage par strategie.

## Exports Data

### `best_combos.csv`

Colonnes :

- `combo_id`
- `rank`
- `profile`
- `score`
- `total_staked`
- `coverage_probability`
- `profit_probability`
- `avg_profit_if_win`
- `max_profit`
- `min_profit`
- `expected_value`
- `big_hit_probability`
- `variance`

### `best_combo_detail.json`

Contenu :

- bankroll ;
- tailles de mises autorisees ;
- liste complete des mises ;
- metriques globales ;
- resultats par numero ;
- explication des gros hits.

### `number_outcomes.csv`

Colonnes :

- `combo_id`
- `number`
- `gross_return`
- `net_profit`
- `is_covered`
- `is_profitable`
- `is_big_hit`
- `winning_bets`
- `explanation`

### `monte_carlo_results.csv`

Colonnes :

- `combo_id`
- `sessions`
- `spins_per_session`
- `final_bankroll_avg`
- `final_bankroll_median`
- `probability_profit`
- `probability_bust`
- `avg_max_drawdown`
- `max_drawdown_seen`
- `biggest_hit_seen`
- `avg_hit_frequency`
- `big_hit_frequency`

### `monte_carlo_paths.csv`

Colonnes :

- `combo_id`
- `session_id`
- `spin_index`
- `bankroll`

## Verification Continue

A chaque nouvelle fonctionnalite :

1. lancer les tests existants ;
2. verifier que les exports precedents restent generes ;
3. verifier que les colonnes publiques ne changent pas sans raison ;
4. lancer un petit scenario rapide ;
5. committer et pousser avant de passer a l'etape suivante.
