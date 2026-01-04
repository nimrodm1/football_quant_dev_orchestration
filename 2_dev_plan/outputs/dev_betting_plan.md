Okay, I've updated the Betting Strategy Blueprint to incorporate the safety refinements, while maintaining the existing structure and EV calculation.

### Betting Strategy Stage Blueprint (Safety Refinements)

This section details the implementation of the `strategy` directory, focusing on the abstract base strategy and the value betting strategy with added safety measures: exposure control, outcome selection, and staking safety.

#### 1. Strategy Requirements:

The betting strategy needs to:

*   Calculate the expected value (EV) of each bet.
*   Determine the stake size based on the EV and staking strategy (Flat, Full Kelly, Fractional Kelly).
*   Decide which bets to place based on an EV threshold.
*   Track closing line value (CLV).
*   Provide a consistent interface for use by the backtesting engine.
*   **Limit exposure on a single match.**
*   **Select only the best outcome per match.**
*   **Apply the Kelly fraction to Full Kelly staking.**

#### 2. File Structure and Class Responsibilities:

The `strategy` directory contains two modules: `base_strategy.py` and `value_bet_strategy.py`.

*   **`strategy/base_strategy.py`:**
    *   **`BaseStrategy` Class:** (Abstract Base Class)
        *   `__init__(self, name: str, config: BacktestConfig, strategy_params: Dict[str, Any] = None)`:
            *   Initialises the class with a `BacktestConfig` object from `core/config.py` and optional strategy-specific parameters.
        *   `decide_bets(self, fixture_data_with_preds: pd.DataFrame, current_bankroll: float, current_fixture_date: pd.Timestamp) -> List[Dict[str, Any]]`:
            *   Abstract method that takes a DataFrame of fixtures with model predictions, the current bankroll, and the current fixture date, and returns a list of dictionaries, each representing a bet.

*   **`strategy/value_bet_strategy.py`:**
    *   **`ValueBetStrategy` Class:** (inherits from `BaseStrategy`)
        *   `__init__(self, name: str, config: BacktestConfig, strategy_params: Dict[str, Any] = None)`:
            *   Initialises the class with a `BacktestConfig` object from `core/config.py` and optional strategy-specific parameters.
        *   `_calculate_expected_value(self, p_model: float, o_market: float) -> float`:
            *   Calculates the expected value (EV) of a bet using the formula:
                *   $EV = (P_{model} \times (O_{market} - 1)) - ((1 - P_{model}) \times 1)$
        *   `_calculate_stake(self, current_bankroll: float, p_model: float, o_market: float) -> float`:
            *   Calculates the stake size based on the chosen staking strategy (Flat, Full Kelly, Fractional Kelly).
            *   **Flat Staking:** Stake = `FLAT_STAKE_UNIT` (from `BacktestConfig`).
            *   **Full Kelly:**
                *   $f = \frac{(O_{market} - 1) \times P_{model} - (1 - P_{model})}{O_{market} - 1}$
                *   **Stake = `kelly_fraction_k * f * current_bankroll`** (Applies the Kelly Fraction to the Full Kelly stake for safety).
            *   **Fractional Kelly:**
                *   $f = \frac{(O_{market} - 1) \times P_{model} - (1 - P_{model})}{O_{market} - 1}$
                *   Stake = `kelly_fraction_k * f * current_bankroll` (where `kelly_fraction_k` is from `BacktestConfig`).
            *   Ensures the stake is non-negative and capped by the current bankroll.
        *   `decide_bets(self, fixture_data_with_preds: pd.DataFrame, current_bankroll: float, current_fixture_date: pd.Timestamp) -> List[Dict[str, Any]]`:
            *   Iterates through each fixture in the DataFrame.
            *   Calculates the EV for each outcome (Home Win, Draw, Away Win, Over/Under 2.5 Goals) using `_calculate_expected_value` and stores it alongside the bet details.
            *   **Implements Outcome Selection Logic:**
                *   Creates a dictionary to store the best bet (highest EV) for each match.
                *   Compares calculated EV to `VALUE_BET_THRESHOLD` (from `BacktestConfig`).
                *   If any `EV` is greater than the `VALUE_BET_THRESHOLD` (from `BacktestConfig`), calculates the stake using `_calculate_stake`.
                *   If multiple outcomes in the same match meet the `VALUE_BET_THRESHOLD`, stores only the bet with the highest EV.
                *   If any calculated stake exceeds the match exposure limit, then it is set to this limit and a log is written, unless there is a higher staking limit, in which case it is set to this limit.
            *   **Implements Match Exposure Control:**
                *   Retrieves `MAX_MATCH_EXPOSURE` from `BacktestConfig`.
                *   Calculates the total amount staked on the current fixture based on current active stakes on the particular fixture in question.
            *   Creates a bet dictionary with the following information:
                *   `date`: Match date.
                *   `home_team`: Home team.
                *   `away_team`: Away team.
                *   `market`: Betting market (e.g., 'Match Odds', 'Over/Under 2.5').
                *   `outcome`: Bet outcome (e.g., 'Home Win', 'Draw', 'Over 2.5').
                *   `stake`: Bet stake.
                *   `odds_taken`: Odds at which the bet was placed.
                *   `closing_odds`: Closing odds for the same outcome.
            *   Returns a list of bet dictionaries.

#### 3. Strategy Execution Flow:

1.  **Instantiate `ValueBetStrategy`:** Create an instance of the `ValueBetStrategy` class, passing in the `BacktestConfig` object.
2.  **Decide Bets:** Call the `decide_bets` method, providing the DataFrame of fixtures with model predictions, the current bankroll, and the current fixture date. This returns a list of bet dictionaries.

#### 4. Error Handling and Logging:

*   The `ValueBetStrategy` should handle cases where required columns (e.g., odds, model predictions) are missing from the DataFrame.
*   The `ValueBetStrategy` should log a warning if the calculated stake exceeds the `MAX_MATCH_EXPOSURE` and is reduced.
*   All errors and warnings should be logged using the `utils/logger.py` module.

#### 5. Configuration:

The following parameters should be configurable in the `core/config.py` module within the `BacktestConfig` class:

*   `BacktestConfig.VALUE_BET_THRESHOLD`: EV threshold for placing bets.
*   `BacktestConfig.STAKING_STRATEGY`: Staking strategy ('flat', 'full_kelly', 'fractional_kelly').
*   `BacktestConfig.KELLY_FRACTION_K`: Kelly fraction for Fractional Kelly staking.
*   `BacktestConfig.FLAT_STAKE_UNIT`: Fixed stake unit for Flat staking.
*   **`BacktestConfig.MAX_MATCH_EXPOSURE`: Maximum percentage of bankroll to stake on a single match.**

This detailed blueprint provides a clear roadmap for implementing the `strategy` directory and the value betting strategy, now incorporating key safety refinements to protect the bankroll and improve the robustness of the strategy. The `current_fixture_date` continues to be explicitly passed to `decide_bets`, and the Direct Comparison method for EV Calculation is maintained.