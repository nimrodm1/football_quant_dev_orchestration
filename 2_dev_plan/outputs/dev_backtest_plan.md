Okay, I've refined the Infrastructure Stage Blueprint to include the `RETRAIN_FREQUENCY` parameter and updated the `Backtester` logic to only retrain the model when this frequency threshold is met. All existing features are maintained and integrated.

### Infrastructure Stage Blueprint (Retrain Frequency)

This section details the implementation of the `backtesting` directory, focusing on the backtesting engine. It covers the core simulation loop, data handling, performance evaluation, the model-only evaluation mode, and the new `RETRAIN_FREQUENCY` parameter for optimized model retraining. The betting strategy logic is externalised in the `strategy/` directory.

#### 1. Infrastructure Requirements:

The backtesting engine needs to simulate a real-world betting scenario, processing matches chronologically to avoid look-ahead bias. It needs to:

*   Load and prepare data.
*   Manage a virtual bankroll (when in betting mode).
*   Determine the training and testing data for each match.
*   Train the model using historical data, respecting the `RETRAIN_FREQUENCY`.
*   Generate predictions for the current match.
*   Apply the betting strategy (from `strategy/`) to decide which bets to place (when in betting mode).
*   Execute the bets and update the bankroll (when in betting mode).
*   Record all model probabilities and goal rates, regardless of value (when in `eval_only` mode).
*   Track betting history and performance metrics, including probabilistic metrics (Brier Score, Log-Loss, MAE).

#### 2. File Structure and Class Responsibilities:

The `backtesting` directory contains only one module: `backtester.py`. The strategy logic has been moved to the `strategy/` directory.

*   **`backtesting/backtester.py`:**
    *   **`Backtester` Class:** The core engine for chronological backtesting.
        *   `__init__(self, data_pipeline: DataPipeline, model_pipeline: ModelPipeline, config: BacktestConfig)`:
            *   Initialises the class with instances of `DataPipeline` and `ModelPipeline`, as well as a `BacktestConfig` object from `core/config.py`. The `BacktestConfig` will define parameters for the backtest, such as the lookback window, bankroll size, the odds provider, and the `RETRAIN_FREQUENCY`.
        *   `run_backtest(self, file_paths: List[str], strategy: BaseStrategy = None, initial_bankroll: float = None, training_window_months: int = None, min_training_data_points: int = None, default_odds_provider_pre_match: str = None, default_odds_provider_close: str = None, mode: str = 'betting', retrain_frequency: int = None) -> pd.DataFrame`:
            *   **Core method to run the backtest.**
            *   Overrides the `initial_bankroll`, `training_window_months`, `min_training_data_points`, `default_odds_provider_pre_match`, `default_odds_provider_close`, and `retrain_frequency` variables of `BacktestConfig` with provided arguments if they are not `None`. These arguments are passed in at runtime so they can override default config values.
            *   Validates that the `mode` parameter is one of `'betting'` or `'eval_only'`.
            *   Loads the data using the `DataPipeline`.
            *   Gets unique match dates.
            *   Initialises the `current_bankroll` to the value defined by `BacktestConfig.INITIAL_BANKROLL` if `mode == 'betting'`.
            *   Initialises `last_retrain_date` to `None`.
            *   Initialises `model` to `None` (the model is trained on the first loop).
            *   Iterates through each match date in chronological order:
                *   **Retraining Logic:**
                    *   Calculates the number of days since the last model retraining:
                        *   If `last_retrain_date` is `None`, then `days_since_retrain` is initialised to a number greater than `retrain_frequency`.
                        *   Otherwise, `days_since_retrain` is calculated as the difference (in days) between the `current_fixture_date` and the `last_retrain_date`.
                    *   If `days_since_retrain >= BacktestConfig.RETRAIN_FREQUENCY` (or `days_since_retrain >= retrain_frequency` if overriden):
                        *   Determines the training data based on the `training_window_months` and `min_training_data_points` from `BacktestConfig`.
                        *   Trains the model using the `ModelPipeline`, passing in the training data and `current_fixture_date`. Stores the trained model to the `model` variable.
                        *   Updates `last_retrain_date` to the `current_fixture_date`.
                *   **Intra-Day Staking Lock:** If `mode == 'betting'`, locks the `current_bankroll` at the *start* of each `current_fixture_date` and stores it in `bankroll_at_start_of_day`. All staking decisions for that day are based on `bankroll_at_start_of_day`.
                *   Determines the current fixture(s) based on `current_fixture_date`.
                *   Generates features for the current fixture(s) using the `DataPipeline`, passing in the correct `current_fixture_date`.
                *   **Mode-Specific Logic:**
                    *   **If `mode == 'betting'`:**
                        *   Validates the `strategy` has been initialised.
                        *   Calls the `decide_bets` method of the passed-in `BaseStrategy` (e.g., `ValueBetStrategy`), passing in the fixture data with predictions, `bankroll_at_start_of_day`, and the `current_fixture_date`. This returns a list of bet dictionaries.
                        *   Executes the bets:
                            *   For each bet:
                                *   Checks if the `bankroll_at_start_of_day` is sufficient to cover the stake. If not, log an error and skip the bet.
                                *   Determines the outcome of the bet based on the actual match result.
                                *   Calculates the profit or loss based on the bet outcome and odds taken.
                                *   Updates the `current_bankroll`.
                                *   Records the betting history (date, match, bet type, stake, odds taken, closing odds, profit/loss, bankroll after bet) as a new row in the `betting_history` DataFrame.
                    *   **If `mode == 'eval_only'`:**
                        *   Records all model probabilities and goal rates for each fixture in a dictionary. No bets are placed, and the `current_bankroll` is not used or updated.
            *   Returns the `betting_history` (or the dictionary of model outputs if in `eval_only` mode) as a pandas DataFrame.
        *   `evaluate_performance(self, backtest_results: pd.DataFrame, mode: str = 'betting') -> Dict[str, float]`:
            *   Calculates performance metrics based on the `backtest_results` (the `betting_history` DataFrame from `run_backtest`).
            *   Validates that the `mode` parameter is one of `'betting'` or `'eval_only'`.
            *   **Mode-Specific Metric Calculation:**
                *   **If `mode == 'betting'`:**
                    *   Calculates the following performance metrics:
                        *   Total PnL (Profit and Loss).
                        *   ROI (Return on Investment).
                        *   Number of Bets.
                        *   Win Rate.
                        *   Average CLV Score (Closing Line Value).
                        *   Percentage of bets that beat the closing line.
                *   **If `mode == 'eval_only'`:**
                    *   Calculates the following probabilistic metrics:
                        *   **Brier Score:** Measures the accuracy of the predicted probabilities.
                        *   **Log-Loss (Cross-Entropy):** Measures the performance of a probabilistic prediction model.
                        *   **Mean Absolute Error (MAE) for Goal Predictions:** Measures the average magnitude of the errors in predicting the number of goals scored by each team.
            *   Returns a dictionary of performance metrics.

#### 3. Backtesting Flow:

1.  **Instantiate `DataPipeline` and `ModelPipeline`:** Create instances of the required data and model classes.
2.  **Instantiate `Backtester`:** Create an instance of the `Backtester` class, passing in the instances of the pipelines and the `BacktestConfig` object.
3.  **Instantiate `BaseStrategy` (if in betting mode):** Create an instance of the desired betting strategy (e.g., `ValueBetStrategy`), passing in the `BacktestConfig` object.
4.  **Run the Backtest:** Call the `run_backtest` method, providing the file paths to the data, the `BaseStrategy` instance (if in betting mode), and overriding any default `BacktestConfig` parameters, as well as setting the `mode` parameter to either `'betting'` or `'eval_only'` and the `retrain_frequency` (if overriding).
5.  **Evaluate Performance:** Call the `evaluate_performance` method, providing the results from `run_backtest` and the corresponding `mode`.

#### 4. Error Handling and Logging:

*   The `Backtester` should handle potential exceptions during data loading, model training, strategy execution, and bet settlement.
*   The `Backtester` should log a warning if the current bankroll is insufficient to cover a proposed bet.
*   The `Backtester` should log a warning if the `mode` parameter is invalid.
*   All errors and warnings should be logged using the `utils/logger.py` module.

#### 5. Configuration:

The following parameters should be configurable in the `core/config.py` module within the `BacktestConfig` class:

*   `BacktestConfig.INITIAL_BANKROLL`: Initial bankroll for the backtest.
*   `BacktestConfig.TRAINING_WINDOW_MONTHS`: Number of months of historical data to use for training.
*   `BacktestConfig.MIN_TRAINING_DATA_POINTS`: Minimum number of data points required to train the model.
*   `BacktestConfig.DEFAULT_ODDS_PROVIDER_PRE_MATCH`: Default odds provider for pre-match odds.
*   `BacktestConfig.DEFAULT_ODDS_PROVIDER_CLOSE`: Default odds provider for closing odds.
*   **`BacktestConfig.RETRAIN_FREQUENCY`: Number of days between model retrainings.**

This detailed blueprint provides a clear roadmap for implementing the `backtesting` directory and the core backtesting engine. The `RETRAIN_FREQUENCY` parameter enables optimization of model training frequency, trading off performance against computational cost. All existing features are seamlessly integrated, ensuring a robust and flexible backtesting framework.