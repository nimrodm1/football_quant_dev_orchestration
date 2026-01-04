Okay, I've updated the Modelling Stage Blueprint to incorporate the Sum-to-Zero constraint for the team-specific parameters.

### Complete Blueprint: Features and Modelling Stages

This document consolidates the development plans for the Features and Modelling stages of the `quant_football` library.

### Features Stage Blueprint

This section details the implementation of the `features` directory, focusing on feature engineering for the Bayesian Poisson GLMM and creating odds-related features for the betting strategy. The `get_closing_odds` method is updated to prioritise a specific odds provider and fall back to the market maximum if necessary.

#### 1. Feature Requirements:

The following features are required:

*   `home_team_idx`: Integer ID representing the home team. Created in the `data` stage.
*   `away_team_idx`: Integer ID representing the away team. Created in the `data` stage.
*   `delta_t`: Time decay factor, calculated as the scaled time difference between the match date and a reference date.
*   `home_goals`: Number of goals scored by the home team (FTHG).
*   `away_goals`: Number of goals scored by the away team (FTAG).
*   `implied_prob_home`: Implied probability of a home win, derived from betting odds.
*   `implied_prob_draw`: Implied probability of a draw, derived from betting odds.
*   `implied_prob_away`: Implied probability of an away win, derived from betting odds.
*   `implied_prob_over_2_5`: Implied probability of over 2.5 goals, derived from betting odds.
*   `implied_prob_under_2_5`: Implied probability of under 2.5 goals.
*   `best_odds_home`: Best available pre-match odds for a home win.
*   `best_odds_draw`: Best available pre-match odds for a draw.
*   `best_odds_away`: Best available pre-match odds for an away win.
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

---

### Modelling Stage Blueprint

This section details the implementation of the `models` directory, focusing on the Bayesian Poisson GLMM, which utilizes `home_team_idx`, `away_team_idx`, and `delta_t` features.

#### 1. Model Overview:

We will model the number of goals scored by the home team ($y_{H,i}$) and the away team ($y_{A,i}$) in a match $i$ as independent Poisson random variables. The mean rates ($\lambda_{H,i}$ and $\lambda_{A,i}$) for these Poisson distributions will be linked to a linear predictor via a logarithmic link function. This linear predictor incorporates a global intercept ($\mu$), a home-pitch advantage fixed effect ($\text{h\_adv}$), and team-specific attack ($\text{att}_k$) and defence ($\text{def}_k$) strengths (random effects). A crucial aspect is the time-decay component, which weights the likelihood contribution of each historical match, giving more importance to recent results, with the weight $w_i$ . To ensure model identifiability, we implement a **sum-to-zero constraint** for the team-specific parameters ($\text{att}_k$ and $\text{def}_k$).

Let $H_i$ denote the home team and $A_i$ denote the away team for match $i$.

**Likelihood Function:**
The observed full-time goals are modelled as Poisson distributed:
$$ y_{H,i} \sim \text{Poisson}(\lambda_{H,i}) $$
$$ y_{A,i} \sim \text{Poisson}(\lambda_{A,i}) $$
The mean goal rates $\lambda_{H,i}$ and $\lambda_{A,i}$ are determined by the following log-linear models:
$$ \log(\lambda_{H,i}) = \mu + \text{h\_adv} + \text{att}_{H_i} + \text{def}_{A_i} $$
$$ \log(\lambda_{A,i}) = \mu + \text{att}_{A_i} + \text{def}_{H_i} $$
Where:
*   $\mu$: A global intercept representing the average log-goal rate in the league.
*   $\text{h\_adv}$: A fixed effect for the home-pitch advantage.
*   $\text{att}_k$: The attack strength of team $k$.
*   $\text{def}_k$: The defence strength of team $k$.

**Time-Decay Component for Historical Fixtures:**
To ensure that more recent matches influence the parameter estimates more strongly, we introduce a time-decay weight $w_i$ for each match $i$. This weight is applied to the log-likelihood contribution of that match. The weight for match $i$ is:
$$ w_i = \exp(-\alpha \times \Delta t_i) $$
Where $\alpha$ is a positive decay rate parameter and $\Delta t_i$ is the `delta_t` feature calculated in the Features stage.

**Prior Distributions:**
We use weakly informative priors to allow the data to dominate the inference while providing some regularisation and stability.

1.  **Global Intercept ($\mu$)**:
    $$ \mu \sim \text{Normal}(0, 1) $$

2.  **Home-Pitch Advantage ($\text{h\_adv}$)**:
    $$ \text{h\_adv} \sim \text{Normal}(0.3, 0.2) $$

3.  **Team-Specific Strengths ($\text{att}_k, \text{def}_k$)**:
    $$ \text{att}_k \sim \text{Normal}(0, \sigma_{\text{att}}) \quad \text{for } k=1, \dots, N_{\text{teams}} $$
    $$ \text{def}_k \sim \text{Normal}(0, \sigma_{\text{def}}) \quad \text{for } k=1, \dots, N_{\text{teams}} $$

4.  **Standard Deviations for Team Strengths ($\sigma_{\text{att}}, \sigma_{\text{def}}$)**:
    $$ \sigma_{\text{att}} \sim \text{HalfNormal}(0, 0.5) $$
    $$ \sigma_{\text{def}} \sim \text{HalfNormal}(0, 0.5) $$

5.  **Time-Decay Rate ($\alpha$)**:
    $$ \alpha \sim \text{HalfNormal}(0, 0.1) $$

#### 2. File Structure and Class Responsibilities:

The `models` directory contains two modules: `base_model.py` and `bayesian_poisson_glmm.py`.

*   **`models/base_model.py`:**
    *   **`BaseModel` Class:** (Abstract Base Class)
        *   `train(X_train: pd.DataFrame, y_train: pd.DataFrame, training_params: Dict[str, Any], current_fixture_date: pd.Timestamp)`: Abstract method for training the model.
        *   `predict_outcome_probabilities(X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`: Abstract method for predicting outcome probabilities.
        *   `predict_scoreline_probabilities(X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`: Abstract method for predicting scoreline probabilities.
        *   `save_model(self, path: str)`: Method for saving the trained model.
        *   `load_model(self, path: str)`: Method for loading a trained model.

*   **`models/bayesian_poisson_glmm.py`:**
    *   **`BayesianPoissonGLMM` Class:** (inherits from `BaseModel`)
        *   `__init__(self, model_name: str, config: ModelConfig)`:
            *   Initialises the class with a `ModelConfig` object from `core/config.py`.
            *   Retrieves prior hyperparameters and PyMC sampling parameters from the `ModelConfig`.
        *   `_build_pymc_model(self, home_team_idx, away_team_idx, goals_home, goals_away, delta_t, num_teams, priors)`:
            *   **Internal method to construct the PyMC model graph.**
            *   Defines the PyMC model using `pm.Model()`.
            *   Creates `pm.Data` containers for observed values (`home_team_idx`, `away_team_idx`, `goals_home`, `goals_away`, `delta_t`).
            *   Defines the prior distributions for $\mu$, $\text{h\_adv}$, $\sigma_{\text{att}}$, $\sigma_{\text{def}}$, and $\alpha$.
            *   Defines the team-specific attack and defence strengths as random effects.
            *   **Implements the sum-to-zero constraint for `att_k` and `def_k` using `pm.Deterministic` and appropriate PyMC transformations. Specifically, the last team's attack and defence strengths will be calculated as the negative sum of the other teams' strengths to enforce the constraint.**
            *   Defines the log-rates for home and away goals based on the model structure.
            *   Calculates time-decay weights for each match.
            *   Uses `pm.Potential` to implement the weighted likelihood function.
            *   Returns the PyMC model.
        *   `train(self, X_train: pd.DataFrame, y_train: pd.DataFrame, training_params: Dict[str, Any], current_fixture_date: pd.Timestamp)`:
            *   Prepares the training data (`home_team_idx`, `away_team_idx`, `goals_home`, `goals_away`, `delta_t`).
            *   Calls the `_build_pymc_model` method to construct the PyMC model.
            *   Performs MCMC sampling using `pm.sample()` with the specified `training_params`.
            *   Stores the `InferenceData` object.
        *   `predict_outcome_probabilities(self, X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`:
            *   Prepares the test data (`home_team_idx`, `away_team_idx`, `delta_t`).
            *   Uses `pm.set_data()` to update the PyMC model's data containers for prediction.
            *   Performs posterior predictive sampling using `pm.sample_posterior_predictive()`.
            *   Simulates match outcomes (goals) from the posterior predictive samples.
            *   Calculates and returns the probabilities for Home Win, Draw, Away Win, Over 2.5 Goals, and Under 2.5 Goals.
        *   `predict_scoreline_probabilities(self, X_test: pd.DataFrame, prediction_params: Dict[str, Any] = None) -> pd.DataFrame`:
            *   (Optional) Predicts specific scoreline probabilities.

#### 3. Model Training and Prediction Flow:

1.  **Instantiate `BayesianPoissonGLMM`:** Create an instance of the `BayesianPoissonGLMM` class, passing in the `ModelConfig` object.
2.  **Train the Model:** Call the `train` method, providing the training data (X_train, y_train), training parameters, and the reference date (`current_fixture_date`).
3.  **Predict Outcome Probabilities:** Call the `predict_outcome_probabilities` method, providing the test data (X_test) and any prediction parameters.

#### 4. Error Handling and Logging:

*   The `BayesianPoissonGLMM` should handle potential `ValueError` exceptions during data preparation.
*   The `BayesianPoissonGLMM` should handle exceptions that may occur during PyMC sampling.
*   All errors and warnings should be logged using the `utils/logger.py` module.

#### 5. Configuration:

The following parameters should be configurable in the `core/config.py` module within the `ModelConfig` class:

*   `ModelConfig.BAYESIAN_POISSON_GLMM_PARAMS`: Dictionary containing PyMC sampling parameters (e.g., `draws`, `chains`, `tune`).
*   `ModelConfig.PRIOR_HYPERPARAMETERS`: Dictionary containing the hyperparameters for the prior distributions ($\mu$, $\text{h\_adv}$, $\sigma_{\text{att}}$, $\sigma_{\text{def}}$, $\alpha$).

This complete document provides a clear roadmap for implementing the Features and Modelling stages of the `quant_football` library. Following these plans will ensure that the necessary features are engineered, and the Bayesian Poisson GLMM is implemented, trained, and used for prediction in a consistent and reliable manner. The sum-to-zero constraint ensures model identifiability.