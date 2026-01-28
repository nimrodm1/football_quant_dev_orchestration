Okay, I've updated the Betting Strategy Blueprint to incorporate the safety refinements and independent architecture. The strategy module is now **completely independent of the backtesting module** and can be used standalone or integrated with any backtesting system.

### Betting Strategy Stage Blueprint (Safety Refinements & Independent Architecture)

This section details the implementation of the `strategy` directory, focusing on the abstract base strategy and concrete staking strategy implementations with added safety measures: exposure control, outcome selection, and staking safety.

#### 1. Strategy Requirements:

The betting strategy needs to:

*   Calculate the expected value (EV) of each bet.
*   Determine the stake size based on the selected staking strategy (Flat, Full Kelly, Fractional Kelly).
*   Decide which bets to place based on an EV threshold.
*   Track closing line value (CLV).
*   **Operate independently with no dependency on backtesting or configuration modules.**
*   **Limit exposure on a single match.**
*   **Select only the best outcome per match.**
*   **Apply the Kelly fraction to Full Kelly staking.**

#### 2. File Structure and Class Responsibilities:

The `strategy` directory contains three modules: `base_strategy.py`, `flat_staking.py`, and `kelly_staking.py`.

*   **`strategy/base_strategy.py`:**
    *   **`BaseStrategy` Class:** (Abstract Base Class)
        *   `__init__(self, name: str, value_bet_threshold: float, max_match_exposure: float)`:
            *   Initialises the class with a name, EV threshold, and maximum match exposure limit.
            *   No dependency on any configuration objects.
        *   `calculate_expected_value(self, p_model: float, o_market: float) -> float`:
            *   Calculates the expected value (EV) of a bet using the formula:
                *   $EV = (P_{model} \times (O_{market} - 1)) - ((1 - P_{model}) \times 1)$
        *   `calculate_stake(self, current_bankroll: float, p_model: float, o_market: float) -> float`:
            *   Abstract method that subclasses must implement.
            *   Calculates the stake size based on the staking strategy.
        *   `decide_bets(self, fixture_data_with_preds: pd.DataFrame, current_bankroll: float) -> List[Dict[str, Any]]`:
            *   Takes a DataFrame of fixtures with model predictions and current bankroll.
            *   Iterates through each fixture and calculates EV for each outcome.
            *   Selects only the best outcome per match (highest EV).
            *   Applies exposure control to limit stake on a single match.
            *   Returns a list of bet dictionaries with all relevant information.

*   **`strategy/flat_staking.py`:**
    *   **`FlatStaking` Class:** (inherits from `BaseStrategy`)
        *   `__init__(self, name: str, value_bet_threshold: float, max_match_exposure: float, flat_stake_unit: float)`:
            *   Initialises the class with a name, EV threshold, match exposure limit, and fixed stake unit.
        *   `calculate_stake(self, current_bankroll: float, p_model: float, o_market: float) -> float`:
            *   **Flat Staking Logic:** Returns the fixed `flat_stake_unit` regardless of bankroll or odds.
            *   Ensures the stake is non-negative and capped by the current bankroll.

*   **`strategy/kelly_staking.py`:** 
    *   **`KellyStaking` Class:** (inherits from `BaseStrategy`)
        *   `__init__(self, name: str, value_bet_threshold: float, max_match_exposure: float, kelly_fraction_k: float = 0.25)`:
            *   Initialises the class with a name, EV threshold, match exposure limit, and Kelly fraction.
            *   The `kelly_fraction_k` parameter determines the fraction of Full Kelly to use.
        *   `calculate_stake(self, current_bankroll: float, p_model: float, o_market: float) -> float`:
            *   **Fractional Kelly Logic:**
                *   $f = \frac{(O_{market} - 1) \times P_{model} - (1 - P_{model})}{O_{market} - 1}$
                *   Stake = `kelly_fraction_k * f * current_bankroll` (where `kelly_fraction_k` is between 0 and 1).
            *   Ensures the stake is non-negative and capped by the current bankroll.

#### 3. Bet Decision and Exposure Control Logic (in `BaseStrategy.decide_bets`):

1.  **Iterate through each fixture** in the DataFrame.
2.  **Calculate EV for each outcome** (Home Win, Draw, Away Win, Over/Under 2.5 Goals) using `calculate_expected_value`.
3.  **Outcome Selection:**
    *   Store only the bet with the highest EV for each match.
    *   Compare the EV to `value_bet_threshold`.
    *   Only proceed if `EV > value_bet_threshold`.
4.  **Calculate stake** using the subclass's `calculate_stake` method.
5.  **Exposure Control:**
    *   Retrieve the current total staked on the fixture (from active bets).
    *   If adding this bet would exceed `max_match_exposure * current_bankroll`, reduce the stake to fit within the limit.
    *   Log a warning if the stake is capped due to exposure limits.
6.  **Create bet dictionary** with:
    *   `date`: Match date.
    *   `home_team`: Home team.
    *   `away_team`: Away team.
    *   `market`: Betting market (e.g., 'Match Odds', 'Over/Under 2.5').
    *   `outcome`: Bet outcome (e.g., 'Home Win', 'Draw', 'Over 2.5').
    *   `stake`: Bet stake.
    *   `odds_taken`: Odds at which the bet was placed.
    *   `closing_odds`: Closing odds for the same outcome.
    *   `ev`: Expected value of the bet.
7.  **Return list of bet dictionaries**.

#### 4. Strategy Instantiation & Usage:

```python
# Choose staking strategy
strategy = FlatStaking(
    name="flat_betting",
    value_bet_threshold=0.05,
    max_match_exposure=0.10,
    flat_stake_unit=10.0
)

# Or use Kelly-based strategies
strategy = KellyStaking(
    name="kelly_betting",
    value_bet_threshold=0.05,
    max_match_exposure=0.10,
    kelly_fraction_k=0.25
)

# Get bets for a fixture dataset
bets = strategy.decide_bets(fixture_data_with_preds, current_bankroll=1000.0)
```

#### 5. Error Handling and Logging:

*   Each strategy should handle cases where required columns (e.g., odds, model predictions) are missing from the DataFrame.
*   Log a warning if the calculated stake exceeds `max_match_exposure` and is reduced.
*   Log all bet decisions with reasoning (EV calculation, stake determination, exposure control).
*   Use standard Python logging or the `utils/logger.py` module if available.

#### 6. Independence Principle:

The strategy module has **zero dependencies** on:
*   Backtesting configuration objects.
*   Backtesting engine classes.
*   External configuration files or YAML settings.

All required parameters are passed directly to the strategy class constructors, making them reusable in any context (live betting, paper trading, research, etc.).