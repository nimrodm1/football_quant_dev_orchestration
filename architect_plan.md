Right, team. I've thoroughly reviewed the specific plans from the Modeller and Analyst. The Bayesian Poisson GLMM, including time decay and hierarchical team strengths, is a powerful foundation. The value betting strategy, incorporating EV calculation, Fractional Kelly staking, and explicit CLV tracking, provides a robust decision-making layer.

I've refined the `architect_plan.md` to ensure the directory structure, class responsibilities, and method signatures fully accommodate these detailed mathematical and logical specifications.

---

## Architectural Blueprint: `quant_football` Library Refined Plan

The `quant_football` library is designed as a **modular, 'Plug-and-Play' local Python framework** for football quantitative analysis and backtesting. Its core purpose is to facilitate the development, evaluation, and backtesting of predictive models and betting strategies in a **realistic, Event-to-Bet (E2B) chronological environment**.

### Core Principles:
*   **Modularity:** Distinct components for data, features, models, and backtesting.
*   **Extensibility:** Easy integration of new datasets, models, and strategies via abstract interfaces.
*   **Configurability:** Centralised parameters with flexible overrides for experimentation.
*   **E2B Backtesting:** Strict chronological processing to prevent look-ahead bias and simulate real-world betting.

### 1. Directory Structure Overview:

The library is organised into logical domains:

*   **`quant_football/`**
    *   `__init__.py`: Package initialisation.
    *   **`core/`**: Foundational elements and shared utilities.
        *   `__init__.py`
        *   `config.py`: Central repository for all configurable parameters (column mappings, date/time formats, model hyperparameters, backtesting parameters).
        *   `constants.py`: Enumerations and fixed values for market types, outcomes, standard column names.
        *   `pipeline.py`: Orchestrates the overall data flow, integrating various components for E2B execution.
    *   **`data/`**: Data handling layer.
        *   `__init__.py`
        *   `data_loader.py`: Manages loading raw data files.
        *   `preprocessor.py`: Cleans, standardises, and performs initial transformations on raw data, including date/time conversion and team ID mapping.
    *   **`features/`**: Feature engineering modules.
        *   `__init__.py`
        *   `base_features.py`: Implements general-purpose features (e.g., rolling statistics) and data preparation for Bayesian models (e.g., `delta_t`, team indices).
        *   `odds_features.py`: Derives features specifically from betting odds (e.g., implied probabilities).
    *   **`models/`**: Predictive modelling algorithms.
        *   `__init__.py`
        *   `base_model.py`: Abstract interface for all predictive models, ensuring a consistent API.
        *   `bayesian_poisson_glmm.py`: **Concrete implementation of the Bayesian Poisson GLMM using PyMC, as specified by the Modeller.**
        *   `xg_boost_model.py`: Example of another potential model implementation.
    *   **`backtesting/`**: Simulation and evaluation of betting strategies.
        *   `__init__.py`
        *   `backtester.py`: The core engine for chronological backtesting, managing bankroll and bet execution.
        *   `base_strategy.py`: Abstract base class for all betting strategies, defining the common interface.
        *   `value_bet_strategy.py`: **Concrete implementation of the value betting strategy, incorporating EV calculation, Fractional Kelly staking, and CLV tracking, as specified by the Analyst.**
    *   **`utils/`**: Helper functions and non-core utilities.
        *   `__init__.py`
        *   `logger.py`: Custom logging setup.
        *   `metrics.py`: Functions for calculating performance statistics (PnL, ROI, CLV score, etc.).
    *   **`config/` (Optional)**: Directory for external configuration files (e.g., YAML) if a more complex parameter management system is desired.
    *   `README.md`: Project documentation.

### 2. Key Class Names and Method Signatures (Refined Details)

#### `core/config.py`
*   **Purpose:** Centralises all static and default configuration parameters.
*   **Classes/Concepts:**
    *   `DataConfig`:
        *   `RAW_COL_MAP`: Mapping for original dataset columns to standardised names (e.g., `Div` -> `league`, `Date` -> `raw_date`, `FTHG` -> `home_goals`, `B365H` -> `bet365_H_pre`, `MaxH` -> `max_H_pre`, `MaxCH` -> `max_H_close`).
        *   `DATE_FORMAT`, `TIME_FORMAT`.
        *   `ODDS_COL_PATTERNS`: Regex patterns to identify various pre-match and closing odds columns for 1X2, OU2.5, AH markets.
    *   `ModelConfig`:
        *   `BAYESIAN_POISSON_GLMM_PARAMS`: Default PyMC sampling parameters (`draws`, `chains`, `tune`), `ref_date_strategy` (e.g., 'latest_training_data'), `time_decay_scaling_factor` (e.g., 30 days for alpha to be per month).
        *   `PRIOR_HYPERPARAMETERS`: Defaults for $\mu$, $\text{h\_adv}$, $\sigma_{\text{att}}$, $\sigma_{\text{def}}$, $\alpha$.
    *   `BacktestConfig`:
        *   `INITIAL_BANKROLL`, `VALUE_BET_THRESHOLD` (e.g., EV > 0.02), `STAKING_STRATEGY` ('flat', 'full_kelly', 'fractional_kelly'), `KELLY_FRACTION_K` (e.g., 0.5 for Half-Kelly), `FLAT_STAKE_UNIT` (e.g., 10.0 or 0.01 for 1% of initial).
        *   `TRAINING_WINDOW_MONTHS`, `MIN_TRAINING_DATA_POINTS`.
        *   `DEFAULT_ODDS_PROVIDER_PRE_MATCH`: e.g., 'Max' (for `MaxH`, `MaxD`, `MaxA`).
        *   `DEFAULT_ODDS_PROVIDER_CLOSE`: e.g., 'MaxC' (for `MaxCH`, `MaxCD`, `MaxCA`).

#### `core/constants.py`
*   **Purpose:** Defines immutable constants and enumerations.
*   **Classes/Concepts:**
    *   `Outcome`: `HOME_WIN`, `DRAW`, `AWAY_WIN`, `OVER_2_5_GOALS`, `UNDER_2_5_GOALS`, etc.
    *   `Market`: `MATCH_ODDS`, `OVER_UNDER_2_5`, `ASIAN_HANDICAP`.
    *   `TeamType`: `HOME`, `AWAY`.

#### `data/data_loader.py`
*   **Class:** `DataLoader`
*   **Key Methods:**
    *   `load_dataset(file_paths: List[str]) -> pd.DataFrame`: Loads multiple raw CSVs.

#### `data/preprocessor.py`
*   **Class:** `Preprocessor`
*   **Key Methods:**
    *   `clean_and_standardise(df: pd.DataFrame) -> pd.DataFrame`: Renames columns, converts `Date`/`Time` to `datetime` objects, handles NaNs, and sorts data chronologically.
    *   `map_teams_to_ids(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]`: Assigns unique integer IDs to teams, crucial for Bayesian models. Returns updated DataFrame and team-to-ID mapping.
    *   `get_market_odds_columns(df: pd.DataFrame, market_type: Market) -> Dict[str, List[str]]`: Identifies available odds columns for a given market from `DataConfig`.

#### `features/base_features.py`
*   **Class:** `BaseFeatureEngineer`
*   **Key Methods:**
    *   `calculate_time_decay_factor(df: pd.DataFrame, current_ref_date: pd.Timestamp, scaling_factor: float) -> pd.DataFrame`: Computes `delta_t` for each match based on `current_ref_date` and `scaling_factor`, as required by the Bayesian Poisson GLMM. `ref_date` will dynamically be the latest date in the training window for E2B.
    *   `add_team_indices(df: pd.DataFrame, team_map: Dict[str, int]) -> pd.DataFrame`: Adds `home_team_idx` and `away_team_idx` columns.
    *   (Existing methods like `calculate_rolling_averages` would still apply for non-Bayesian models or for initial data exploration, but are not directly used by the specified Bayesian model in its core likelihood).

#### `features/odds_features.py`
*   **Class:** `OddsFeatureEngineer`
*   **Key Methods:**
    *   `calculate_implied_probabilities(df: pd.DataFrame, bookmaker_prefix: str) -> pd.DataFrame`: Converts odds (e.g., `MaxH`) into implied probabilities (e.g., `implied_prob_home`).
    *   `get_best_pre_match_odds(df: pd.DataFrame, market_type: Market) -> pd.DataFrame`: Consolidates `MaxH`, `MaxD`, `MaxA` (or similar for OU2.5) into a single 'best odds' column for the strategy.
    *   `get_closing_odds(df: pd.DataFrame, market_type: Market) -> pd.DataFrame`: Retrieves `MaxCH`, `MaxCD`, `MaxCA` (or similar) for CLV tracking.

#### `models/base_model.py`
*   **Class:** `BaseModel` (Abstract Base Class)
*   **Key Abstract Methods:**
    *   `train(X_train: pd.DataFrame, y_train: pd.DataFrame, training_params: Dict[str, Any], current_fixture_date: pd.Timestamp)`: Trains the model. `training_params` would include PyMC specific settings for the Bayesian model.
    *   `predict_outcome_probabilities(X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`: Predicts '1X2' or 'OU2.5' probabilities.
    *   `predict_scoreline_probabilities(X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`: Predicts specific scoreline probabilities.
*   **Common Methods:** `save_model`, `load_model`.

#### `models/bayesian_poisson_glmm.py`
*   **Class:** `BayesianPoissonGLMM` (inherits from `BaseModel`)
*   **Purpose:** Implements the specified Bayesian Poisson GLMM using PyMC.
*   **Key Methods:**
    *   `__init__(model_name: str, config: ModelConfig)`: Initialises with model-specific configuration, including prior hyperparameters and PyMC sampling parameters.
    *   `_build_pymc_model(home_team_idx, away_team_idx, goals_home, goals_away, delta_t, num_teams, priors)`: **Internal method to construct the PyMC model graph with `pm.Data` containers and `pm.Potential` for weighted likelihood, as described by the Modeller.**
    *   `train(X_train: pd.DataFrame, y_train: pd.DataFrame, training_params: Dict[str, Any], current_fixture_date: pd.Timestamp)`:
        *   Prepares `home_team_idx`, `away_team_idx`, `goals_home`, `goals_away`, `delta_t` from `X_train`, `y_train`.
        *   Sets `ref_date` for `delta_t` calculation to `current_fixture_date - 1 day` to ensure no look-ahead.
        *   Builds the PyMC model using `_build_pymc_model`.
        *   Calls `pm.sample()` with configured `training_params` to perform MCMC inference. Stores the `InferenceData`.
    *   `predict_outcome_probabilities(X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`:
        *   Prepares `new_home_team_idx`, `new_away_team_idx`, `new_delta_t` for `X_test`.
        *   Uses `pm.set_data()` to update the PyMC model's data containers for prediction.
        *   Performs `pm.sample_posterior_predictive()` to get posterior samples of `log_lambda_home` and `log_lambda_away`.
        *   **Simulates match outcomes (goals) from posterior $\lambda$s, as described by the Modeller.**
        *   Calculates and returns $P(\text{Home Win})$, $P(\text{Draw})$, $P(\text{Away Win})$, $P(\text{Over 2.5 Goals})$, $P(\text{Under 2.5 Goals})$ by averaging across simulations.
    *   `predict_scoreline_probabilities(...)`: A specific extension if detailed scoreline probabilities are required (likely handled internally by the `predict_outcome_probabilities` and then aggregated).

#### `core/pipeline.py`
*   **Class:** `DataPipeline`
*   **Key Methods:**
    *   `run_preprocessing(file_names: List[str]) -> pd.DataFrame`: Loads, cleans, and standardises data, including `map_teams_to_ids` to create team indices required by the Bayesian model.
    *   `generate_features(df: pd.DataFrame, current_fixture_date: pd.Timestamp) -> pd.DataFrame`: Adds `delta_t` to the DataFrame using `current_fixture_date` as the `ref_date`. Ensures proper feature preparation for the Bayesian model.
*   **Class:** `ModelPipeline`
*   **Key Method:**
    *   `train_and_predict_for_fixture(training_data, fixture_data, current_fixture_date, model_training_params, model_prediction_params) -> pd.DataFrame`:
        *   Prepares `training_data` and `fixture_data` for the specific `BaseModel` instance. This means extracting `home_team_idx`, `away_team_idx`, `goals_home`, `goals_away`, and `delta_t` for both training and prediction.
        *   Calls `model.train()` with the appropriate subset of `training_data` and `model_training_params`.
        *   Calls `model.predict_outcome_probabilities()` on `fixture_data` with `model_prediction_params`.
        *   Merges predictions back into `fixture_data`.

#### `backtesting/base_strategy.py`
*   **Class:** `BaseStrategy` (Abstract Base Class)
*   **Key Abstract Method:**
    *   `decide_bets(fixture_data_with_preds: pd.DataFrame, current_bankroll: float) -> List[Dict[str, Any]]`:
        *   **Inputs:** DataFrame containing current fixture details, model probabilities (`P_model`), pre-match odds (`O_market`), and closing odds (`O_close`). The current total bankroll.
        *   **Output:** List of dictionaries, each describing a proposed bet (market, outcome, calculated stake, odds taken, reference to closing odds).

#### `backtesting/value_bet_strategy.py`
*   **Class:** `ValueBetStrategy` (inherits from `BaseStrategy`)
*   **Purpose:** Implements the value betting logic from the Analyst.
*   **Key Methods:**
    *   `__init__(name: str, config: BacktestConfig, strategy_params: Dict[str, Any] = None)`: Initialises with `BacktestConfig` for defaults (`VALUE_BET_THRESHOLD`, `STAKING_STRATEGY`, `KELLY_FRACTION_K`, `FLAT_STAKE_UNIT`) and strategy-specific overrides.
    *   `_calculate_expected_value(p_model: float, o_market: float) -> float`: Implements the EV formula: $(P_{\text{model}} \times (O_{\text{market}} - 1)) - ((1 - P_{\text{model}}) \times 1)$.
    *   `_calculate_stake(current_bankroll: float, p_model: float, o_market: float) -> float`:
        *   Applies the chosen staking strategy (`STAKING_STRATEGY` from `BacktestConfig`):
            *   **Flat Staking:** Returns `FLAT_STAKE_UNIT`.
            *   **Full Kelly:** Calculates $f = \frac{(O_{\text{market}} - 1) \times P_{\text{model}} - (1 - P_{\text{model}})}{O_{\text{market}} - 1}$, then `f * current_bankroll`.
            *   **Fractional Kelly:** Calculates $f$ as above, then `k * f * current_bankroll` (where `k` is `KELLY_FRACTION_K`).
        *   Ensures stake is non-negative and capped by `current_bankroll`.
    *   `decide_bets(fixture_data_with_preds: pd.DataFrame, current_bankroll: float) -> List[Dict[str, Any]]`:
        *   Iterates through each fixture in `fixture_data_with_preds`.
        *   For each outcome (e.g., Home Win, Draw, Away Win, Over/Under 2.5):
            *   Retrieves `P_model` (from `pred_home_win`, `pred_draw`, etc.) and `O_market` (e.g., `max_H_pre` for the pre-match odds `O_taken`).
            *   Calls `_calculate_expected_value`.
            *   If `EV > VALUE_BET_THRESHOLD`:
                *   Calls `_calculate_stake`.
                *   Records the bet, including `odds_taken`, `closing_odds` (from `max_H_close`, etc.), for CLV tracking.

#### `backtesting/backtester.py`
*   **Class:** `Backtester`
*   **Purpose:** The E2B engine.
*   **Key Method `run_backtest(...)`:**
    *   Handles parameter overrides for `initial_bankroll`, `stake_percentage` (now effectively `kelly_fraction_k` or `flat_stake_unit` for the chosen strategy), `training_window_months`, `min_training_data_points`.
    *   Iterates `unique_dates`.
    *   Dynamically prepares `training_data` and `current_fixtures`.
    *   Calls `data_pipeline.generate_features()` for *both* `training_data` and `current_fixtures`, passing the appropriate `current_fixture_date` for `delta_t` calculation to prevent look-ahead.
    *   Calls `model_pipeline.train_and_predict_for_fixture()` for the current batch.
    *   Calls `strategy.decide_bets()` with `fixtures_with_preds` (which now contain model probabilities, chosen pre-match odds, and closing odds) and `current_bankroll`.
    *   Executes bets, updates `bankroll`, and records in `betting_history`: including `odds_taken`, `closing_odds`, `profit_loss`, `bankroll_after`, and `is_win`.
*   **Key Method `evaluate_performance() -> Dict[str, float]`:**
    *   Calculates `Total PnL`, `ROI`, `Number of Bets`, `Win Rate`.
    *   **Crucially, calculates average `CLV Score` using `odds_taken` and `closing_odds` from `betting_history`, as specified by the Analyst.** Also calculates the percentage of bets that beat the closing line.

#### `utils/metrics.py`
*   **Purpose:** Provides functions for calculating common performance metrics.
*   **Key Functions:**
    *   `calculate_pnl(profit_loss_series)`
    *   `calculate_roi(total_pnl, total_staked)`
    *   `calculate_clv_score(odds_taken, odds_close)`: Implements the formula: $(\frac{O_{\text{taken}}}{O_{\text{close}}} - 1)$.
    *   `calculate_win_rate(is_win_series)`
    *   (Further functions for maximum drawdown, Sharpe ratio, etc. can be added here).

---

This refined plan explicitly incorporates the detailed mathematical models and strategy logic, ensuring that the library's architecture is perfectly aligned with the Modeller's and Analyst's requirements. The flow is robust, from data ingestion to model training, prediction, strategy execution, and comprehensive performance evaluation including critical CLV tracking.