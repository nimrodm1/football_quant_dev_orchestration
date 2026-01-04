Okay, let's formulate a robust Bayesian Poisson GLMM (Generalised Linear Mixed Model) using PyMC for predicting football match outcomes ('1X2' and 'Total Goals'). This model will incorporate team-specific random effects, a fixed effect for home-pitch advantage, and a time-decay component for historical fixtures to ensure more recent matches have greater influence.

---

## Bayesian Poisson GLMM for Football Match Prediction

### Model Overview

We will model the number of goals scored by the home team ($y_H$) and the away team ($y_A$) in a match $i$ as independent Poisson random variables. The mean rates ($\lambda_H$ and $\lambda_A$) for these Poisson distributions will be linked to a linear predictor via a logarithmic link function. This linear predictor incorporates a global intercept, a home-pitch advantage fixed effect, and team-specific attack and defence strengths (random effects). A crucial aspect is the time-decay component, which weights the likelihood contribution of each historical match, giving more importance to recent results.

Let $H_i$ denote the home team and $A_i$ denote the away team for match $i$.
Let $y_{H,i}$ be the goals scored by the home team and $y_{A,i}$ be the goals scored by the away team.

#### 1. Prior Distributions and Likelihood Function

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
To ensure that more recent matches influence the parameter estimates more strongly, we introduce a time-decay weight $w_i$ for each match $i$. This weight is applied to the log-likelihood contribution of that match.
Let $t_i$ be the date of match $i$ and $t_{\text{ref}}$ be a reference date (e.g., the latest match date in the training dataset).
Let $\Delta t_i = (t_{\text{ref}} - t_i) / \text{scaling\_factor}$ be the scaled time difference (e.g., in months or years). We ensure $\Delta t_i \ge 0$.
The weight for match $i$ is:
$$ w_i = \exp(-\alpha \times \Delta t_i) $$
Where $\alpha$ is a positive decay rate parameter. A larger $\alpha$ implies faster decay of influence for older matches. The total log-likelihood for the model will then be the sum of these weighted log-likelihoods:
$$ \mathcal{L}(\theta | \mathbf{y}, \mathbf{X}, \mathbf{w}) = \sum_{i=1}^{N} w_i \times \left( \log P(y_{H,i} | \lambda_{H,i}) + \log P(y_{A,i} | \lambda_{A,i}) \right) $$
In PyMC, this can be implemented using `pm.Potential`.

**Prior Distributions:**
We use weakly informative priors to allow the data to dominate the inference while providing some regularisation and stability.

1.  **Global Intercept ($\mu$)**:
    A `Normal` prior reflecting a general belief about the average log-goal rate, typically centered around values like $\log(1.2)$ to $\log(1.5)$ goals per team.
    $$ \mu \sim \text{Normal}(0, 1) $$

2.  **Home-Pitch Advantage ($\text{h\_adv}$)**:
    A `Normal` prior, typically centered at a small positive value reflecting the common expectation of a home advantage.
    $$ \text{h\_adv} \sim \text{Normal}(0.3, 0.2) $$
    (A value like $e^{0.3} \approx 1.35$, suggesting home teams score about 35% more goals due to home advantage).

3.  **Team-Specific Strengths ($\text{att}_k, \text{def}_k$)**:
    These are modelled as random effects drawn from hierarchical `Normal` distributions, centered at 0. This allows for 'borrowing strength' across teams, meaning a team with limited data benefits from the overall league variability.
    $$ \text{att}_k \sim \text{Normal}(0, \sigma_{\text{att}}) \quad \text{for } k=1, \dots, N_{\text{teams}} $$
    $$ \text{def}_k \sim \text{Normal}(0, \sigma_{\text{def}}) \quad \text{for } k=1, \dots, N_{\text{teams}} $$
    For identifiability with the global intercept $\mu$, these are typically modelled as deviations from the league average, which $\mu$ then captures.

4.  **Standard Deviations for Team Strengths ($\sigma_{\text{att}}, \sigma_{\text{def}}$)**:
    These are hyperparameters representing the variability in attack and defence strengths among teams in the league. `HalfNormal` priors are standard for positive-constrained scale parameters.
    $$ \sigma_{\text{att}} \sim \text{HalfNormal}(0, 0.5) $$
    $$ \sigma_{\text{def}} \sim \text{HalfNormal}(0, 0.5) $$

5.  **Time-Decay Rate ($\alpha$)**:
    This parameter determines the steepness of the time decay. It must be positive. A `HalfNormal` or `Exponential` prior is suitable.
    $$ \alpha \sim \text{HalfNormal}(0, 0.1) $$
    (A smaller $\sigma$ here suggests a prior belief that the decay isn't extremely rapid, making $\alpha$ small and leading to a gentle decay.)

#### 2. Handling Home-Pitch Advantage as a Fixed Effect

As described above, `h_adv` is included as a single, fixed parameter in the linear predictor for the home team's log-expected goals. It is a constant across all home teams and matches, representing the average boost a team gets when playing at their home ground. It's estimated directly from the data alongside all other parameters.
$$ \log(\lambda_{H,i}) = \mu + \mathbf{h\_adv} + \text{att}_{H_i} + \text{def}_{A_i} $$
This formulation allows us to quantify the home advantage as a multiplicative factor on the expected goals: $e^{\text{h\_adv}}$.

#### 3. PyMC Model Structure

Before defining the PyMC model, prepare your data:
*   Map team names to unique integer IDs: `home_team_idx`, `away_team_idx`.
*   Store observed goals: `goals_home`, `goals_away`.
*   Determine the total number of unique teams: `num_teams`.
*   Convert match dates to a numerical format (e.g., days since epoch, or days from the first match).
*   Calculate `delta_t`: For each match $i$, compute `(ref_date - match_date_i) / days_scaling`. `ref_date` could be the latest date in your training set. `days_scaling` (e.g., 30 for months, 365 for years) helps make `alpha` interpretable. Ensure `delta_t` values are non-negative.

```latex
\begin{align*}
\text{import pymc as pm}& \\
\text{import pytensor.tensor as pt}& \\
\text{import numpy as np}& \\
& \\
\text{with pm.Model() as football\_model:}& \\
\quad \text{// Data containers for observed values and for potential prediction (using pm.Data)}& \\
\quad \text{// These can be updated for prediction using model.set_data()}& \\
\quad \text{home\_team\_data = pm.Data('home\_team\_data', home\_team\_idx)}& \\
\quad \text{away\_team\_data = pm.Data('away\_team\_data', away\_team\_idx)}& \\
\quad \text{goals\_home\_data = pm.Data('goals\_home\_data', goals\_home)}& \\
\quad \text{goals\_away\_data = pm.Data('goals\_away\_data', goals\_away)}& \\
\quad \text{delta\_t\_data = pm.Data('delta\_t\_data', delta\_t)}& \\
\quad & \\
\quad \text{// Priors for Global Parameters}& \\
\quad \mu \sim \text{pm.Normal}('mu', mu=0, sigma=1)& \\
\quad \text{h\_adv} \sim \text{pm.Normal}('home\_advantage', mu=0.3, sigma=0.2)& \\
\quad & \\
\quad \text{// Priors for Hierarchical Standard Deviations}& \\
\quad \sigma_{\text{att}} \sim \text{pm.HalfNormal}('sigma\_attack', sigma=0.5)& \\
\quad \sigma_{\text{def}} \sim \text{pm.HalfNormal}('sigma\_defence', sigma=0.5)& \\
\quad & \\
\quad \text{// Priors for Team-Specific Random Effects (Strengths)}& \\
\quad \text{att\_strengths} \sim \text{pm.Normal}('attack\_strengths', mu=0, sigma=\sigma_{\text{att}}, shape=\text{num\_teams})& \\
\quad \text{def\_strengths} \sim \text{pm.Normal}('defence\_strengths', mu=0, sigma=\sigma_{\text{def}}, shape=\text{num\_teams})& \\
\quad & \\
\quad \text{// Prior for Time-Decay Rate}& \\
\quad \alpha \sim \text{pm.HalfNormal}('alpha', sigma=0.1)& \\
\quad & \\
\quad \text{// Log-Rates for Home and Away Goals based on the model structure}& \\
\quad \text{log\_lambda\_home = pm.Deterministic}(& \\
\quad \quad \text{'log\_lambda\_home', } \mu + \text{h\_adv} + \text{att\_strengths}[\text{home\_team\_data}] + \text{def\_strengths}[\text{away\_team\_data}]& \\
\quad )& \\
\quad \text{log\_lambda\_away = pm.Deterministic}(& \\
\quad \quad \text{'log\_lambda\_away', } \mu + \text{att\_strengths}[\text{away\_team\_data}] + \text{def\_strengths}[\text{home\_team\_data}]& \\
\quad )& \\
\quad & \\
\quad \text{// Calculate time-decay weights for each match}& \\
\quad \text{weights = pm.Deterministic('weights', pt.exp(-alpha * delta\_t\_data))}& \\
\quad & \\
\quad \text{// Custom log-likelihood contribution for weighted Poisson observations}& \\
\quad \text{// Compute log-probabilities for home and away goals for each match}& \\
\quad \text{home\_logp = pm.Poisson.logp(goals\_home\_data, pt.exp(log\_lambda\_home))}& \\
\quad \text{away\_logp = pm.Poisson.logp(goals\_away\_data, pt.exp(log\_lambda\_away))}& \\
\quad \text{// Apply weights and sum for the total weighted log-likelihood}& \\
\quad \text{total\_weighted\_logp = pt.sum(weights * (home\_logp + away\_logp))}& \\
\quad \text{pm.Potential('weighted\_likelihood', total\_weighted\_logp)}& \\
\end{align*}
```

### Prediction for '1X2' and 'Total Goals' Markets

After sampling from the posterior distribution using `pm.sample()`, you will obtain an `InferenceData` object (`idata`) containing samples for all model parameters. To make predictions for a new match (e.g., between `TeamX` at home and `TeamY` away, on `new_match_date`):

1.  **Prepare New Data**: Create a new dictionary (`new_match_data`) for the specific match, containing the integer IDs for the home and away teams (`new_home_team_idx`, `new_away_team_idx`) and the `new_delta_t` (time difference from `ref_date` to `new_match_date`). Observed goals are not needed for prediction.

2.  **Generate Posterior Predictive Samples**:
    ```python
    # Example for one new match
    new_match_data = {
        'home_team_data': np.array([team_X_id]),
        'away_team_data': np.array([team_Y_id]),
        'delta_t_data': np.array([(ref_date - new_match_date) / days_scaling])
    }

    with football_model:
        pm.set_data(new_match_data) # Update pm.Data variables for prediction
        # Sample posterior predictive for log_lambdas. We don't need observed_rvs here.
        ppc = pm.sample_posterior_predictive(idata, var_names=['log_lambda_home', 'log_lambda_away'], extend_inferencedata=False)

    # Extract log_lambdas for the new match from the posterior predictive samples
    # Assuming ppc.posterior contains 'log_lambda_home' and 'log_lambda_away'
    # Shape will be (chain, draw, num_matches), so for 1 match: (chain, draw, 1)
    lambda_home_samples = np.exp(ppc.posterior['log_lambda_home'].values.flatten())
    lambda_away_samples = np.exp(ppc.posterior['log_lambda_away'].values.flatten())
    ```

3.  **Simulate Match Outcomes**: For each pair of ($\lambda_H$, $\lambda_A$) samples from the posterior, simulate a large number of goal outcomes.

    ```python
    N_sim_per_sample = 100 # Number of goal simulations per posterior lambda sample
    num_posterior_samples = len(lambda_home_samples) # Total number of posterior samples

    # Simulate goals for each posterior lambda sample
    simulated_home_goals = np.random.poisson(lambda_home_samples[:, None], size=(num_posterior_samples, N_sim_per_sample)).flatten()
    simulated_away_goals = np.random.poisson(lambda_away_samples[:, None], size=(num_posterior_samples, N_sim_per_sample)).flatten()
    ```

4.  **Calculate Probabilities for '1X2' Market**:
    $$ P(\text{Home Win}) = \text{mean}( \text{simulated\_home\_goals} > \text{simulated\_away\_goals} ) $$
    $$ P(\text{Draw}) = \text{mean}( \text{simulated\_home\_goals} == \text{simulated\_away\_goals} ) $$
    $$ P(\text{Away Win}) = \text{mean}( \text{simulated\_home\_goals} < \text{simulated\_away\_goals} ) $$

5.  **Calculate Probabilities for 'Total Goals' Market (e.g., Over/Under 2.5 Goals)**:
    $$ \text{total\_simulated\_goals} = \text{simulated\_home\_goals} + \text{simulated\_away\_goals} $$
    $$ P(\text{Over 2.5 Goals}) = \text{mean}( \text{total\_simulated\_goals} > 2.5 ) $$
    $$ P(\text{Under 2.5 Goals}) = \text{mean}( \text{total\_simulated\_goals} \le 2.5 ) $$
    (Note: For discrete goal counts, 'Under 2.5' is equivalent to 'total goals $\le 2$').

This Bayesian Poisson GLMM provides a principled framework for football match prediction, allowing for robust parameter estimation, quantifiable uncertainties, and explicit incorporation of domain knowledge (like home advantage and time decay).