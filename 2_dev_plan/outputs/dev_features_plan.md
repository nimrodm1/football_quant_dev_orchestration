Okay, the Features Stage Blueprint has been updated to correct the minor typo in Section 1.

### Features Stage Blueprint (Updated)

This section details the implementation of the `features` directory, focusing on feature engineering for the Bayesian Poisson GLMM and creating odds-related features for the betting strategy. The `get_closing_odds` method is updated to prioritise a specific odds provider and fall back to the market maximum if necessary.

#### 1. Feature Requirements:

The feature requirements remain the same as previously defined.

*   `home_team_idx`: Integer ID representing the home team. Created in the `data` stage.
*   `away_team_idx`: Integer ID representing the away team. Created in the `data` stage.
*   `delta_t`: Time decay factor, calculated as the scaled time difference between the match date and a reference date.
*   `home_goals`: Number of goals scored by the home team (FTHG).
*   `away_goals`: Number of goals scored by the away team (FTAG).
*   `implied_prob_home`: Implied probability of a home win, derived from betting odds.
*   `implied_prob_draw`: Implied probability of a draw, derived from betting odds.
*   `implied_prob_away`: Implied probability of an away win, derived from betting odds.
*   `implied_prob_over_2_5`: Implied probability of over 2.5 goals, derived from betting odds.
*   `implied_prob_under_2_5`: Implied probability of under 2.5 goals, derived from betting odds.
*   `best_odds_home`: Best available pre-match odds for a home win.
*   `best_odds_draw`: Best available pre-match odds for a draw.
*   `best_odds_away`: **Best available pre-match odds for an away win.**
*   `best_odds_over_2_5`: Best available pre-match odds for over 2.5 goals.
*   `best_odds_under_2_5`: Best available pre-match odds for under 2.5 goals.
*   `closing_odds_home`: Closing odds for a home win.
*   `closing_odds_draw`: Closing odds for a draw.
*   `closing_odds_away`: Closing odds for an away win.

#### 2. File Structure and Class Responsibilities:

The file structure remains the same, with modifications only to the `OddsFeatureEngineer` class.

*   **`features/base_features.py`:**
    *   **`BaseFeatureEngineer` Class:** Remains unchanged.
        *   `__init__(self, config: ModelConfig)`: Initialises the class.
        *   `calculate_time_decay_factor(self, df: pd.DataFrame, current_ref_date: pd.Timestamp) -> pd.DataFrame`: Calculates the `delta_t`.
        *   `add_team_indices(self, df: pd.DataFrame, team_map: Dict[str, int]) -> pd.DataFrame`: NO-OP for MVP.

*   **`features/odds_features.py`:**
    *   **`OddsFeatureEngineer` Class:**
        *   `__init__(self, config: DataConfig)`: Initialises the class.
        *   `calculate_implied_probabilities(self, df: pd.DataFrame, bookmaker_prefix: str) -> pd.DataFrame`: Calculates implied probabilities (Match Odds). Remains unchanged.
 	    *   `calculate_implied_probabilities_over_under(self, df: pd.DataFrame, bookmaker_prefix: str) -> pd.DataFrame`: Calculates implied probabilities (Over/Under). Remains unchanged.
        *   `get_best_pre_match_odds(self, df: pd.DataFrame, market_type: Market) -> pd.DataFrame`: Gets best pre-match odds. Remains unchanged.
        *   `get_closing_odds(self, df: pd.DataFrame, market_type: Market, provider_prefix: str = None) -> pd.DataFrame`:
            *   Retrieves the closing odds for a given market (e.g., 'MATCH_ODDS') from the available bookmakers, **prioritising a specific provider and falling back to the market maximum if necessary.**
            *   Uses the `ODDS_COL_PATTERNS` from `DataConfig` to find the relevant columns.
            *   **If `provider_prefix` is provided:**
                *   Attempts to retrieve the closing odds columns for that specific provider (e.g., `PSCH`, `PSCD`, `PSCA` for `provider_prefix='PS'`).
                *   If *any* of these columns are missing for a given row (i.e., contain `np.nan`), it falls back to the market maximum closing odds (`MaxCH`, `MaxCD`, `MaxCA`).
            *   **If `provider_prefix` is `None`:**
                *   Directly uses the market maximum closing odds (`MaxCH`, `MaxCD`, `MaxCA`).
            *   Adds new columns `closing_odds_home`, `closing_odds_draw`, and `closing_odds_away` to the DataFrame, containing the selected closing odds.
            *   Returns the updated DataFrame.

#### 3. Feature Engineering Flow (Updated):

The feature engineering flow is modified to incorporate the updated `get_closing_odds` method.

1.  **Instantiate `BaseFeatureEngineer`:** Create an instance of the `BaseFeatureEngineer` class, passing in the `ModelConfig` object.
2.  **Calculate Time Decay Factor:** Call the `calculate_time_decay_factor` method.
3.  **Validate Team Indices:** Call the `add_team_indices` method.
4.  **Instantiate `OddsFeatureEngineer`:** Create an instance of the `OddsFeatureEngineer` class, passing in the `DataConfig` object.
5.  **Calculate Implied Probabilities (Match Odds):** Call the `calculate_implied_probabilities` method for relevant bookmakers.
6.  **Calculate Implied Probabilities (Over/Under):** Call the `calculate_implied_probabilities_over_under` method for relevant bookmakers.
7.  **Get Best Pre-Match Odds (Match Odds):** Call the `get_best_pre_match_odds` method for `Market.MATCH_ODDS`.
8.  **Get Best Pre-Match Odds (Over/Under):** Call the `get_best_pre_match_odds` method for `Market.OVER_UNDER_2_5`.
9.  **Get Closing Odds (Match Odds):** Call the `get_closing_odds` method, providing the desired `provider_prefix` (e.g., 'PS') or `None` to use the market maximum.

#### 4. Error Handling and Logging:

*   The `BaseFeatureEngineer` and `OddsFeatureEngineer` should handle `KeyError` exceptions if required columns are missing from the DataFrame.
*   The `OddsFeatureEngineer.get_closing_odds` method should handle cases where the specified `provider_prefix` is not found in the `ODDS_COL_PATTERNS` or if the corresponding columns are missing from the DataFrame. Log a warning message if the specified `provider_prefix` is not found and fallback to market maximum is enforced.
*   All errors and warnings should be logged using the `utils/logger.py` module.

#### 5. Configuration:

The configuration parameters remain the same.

*   `ModelConfig.time_decay_scaling_factor`: Scaling factor for the time decay calculation.
*   `DataConfig.ODDS_COL_PATTERNS`: Regex patterns to identify pre-match and closing odds columns.
*   List of relevant bookmaker prefixes for calculating implied probabilities (e.g., `['B365', 'Max']`).
*   Potentially a configurable default `provider_prefix` for closing odds if a specific provider is generally preferred.

The blueprint now has the minor typo corrected.