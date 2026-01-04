Okay, here's the complete and refined plan specifically for the **Data Stage** of the `quant_football` library, incorporating all previous specifications and MVP refinements:

### Data Stage Blueprint: `quant_football` Library Refined (MVP Focused)

This document provides a comprehensive development plan for the `data` directory within the `quant_football` library. This stage is responsible for loading raw data, cleaning, standardising, and performing initial transformations and validations. The aim is to produce a consistent and well-structured dataframe suitable for subsequent feature engineering and model training, while adhering to an MVP (Minimum Viable Product) approach.

#### 1. Data Schema and Type Mapping:

The following table defines the schema of the expected input data and maps each column to a pandas-compatible data type. Where ambiguity exists, `float64` is preferred for numerical columns to avoid potential precision issues. Columns involved in date/time handling are explicitly defined.

| Column Name | pandas Data Type | Notes |
|-----------------|--------------------|------------------------------------------------------------------------------------|
| Div | str | League Division (e.g., 'E0', 'E1'). Use `string` dtype. |
| Date | str | Match Date (dd/mm/yy).  Will be parsed to `datetime64[ns]` with custom function. |
| Time | str | Time of match kick off (HH:MM). Will be parsed to `datetime64[ns]` after combination with Date. |
| HomeTeam | str | Home Team. Use `string` dtype. |
| AwayTeam | str | Away Team. Use `string` dtype. |
| FTHG | int64 | Full Time Home Team Goals. |
| FTAG | int64 | Full Time Away Team Goals. |
| FTR | str | Full Time Result (H=Home Win, D=Draw, A=Away Win). Use `string` dtype. |
| HTHG | int64 | Half Time Home Team Goals. |
| HTAG | int64 | Half Time Away Team Goals. |
| HTR | str | Half Time Result (H=Home Win, D=Draw, A=Away Win). Use `string` dtype. |
| Referee | str | Match Referee. Can contain missing data. Use `string` dtype. |
| HS | int64 | Home Team Shots. Can contain missing data.|
| AS | int64 | Away Team Shots. Can contain missing data.|
| HST | int64 | Home Team Shots on Target. Can contain missing data.|
| AST | int64 | Away Team Shots on Target. Can contain missing data.|
| HF | int64 | Home Team Fouls Committed. Can contain missing data.|
| AF | int64 | Away Team Fouls Committed. Can contain missing data.|
| HC | int64 | Home Team Corners. Can contain missing data.|
| AC | int64 | Away Team Corners. Can contain missing data.|
| HY | int64 | Home Team Yellow Cards. Can contain missing data.|
| AY | int64 | Away Team Yellow Cards. Can contain missing data.|
| HR | int64 | Home Team Red Cards. Can contain missing data.|
| AR | int64 | Away Team Red Cards. Can contain missing data.|
| B365H | float64 | Bet365 home win odds. |
| B365D | float64 | Bet365 draw odds. |
| B365A | float64 | Bet365 away win odds. |
| BWH | float64 | Bet&Win home win odds. |
| BWD | float64 | Bet&Win draw odds. |
| BWA | float64 | Bet&Win away win odds. |
| IWH | float64 | Interwetten home win odds. |
| IWD | float64 | Interwetten draw odds. |
| IWA | float64 | Interwetten away win odds. |
| PSH | float64 | Pinnacle home win odds. |
| PSD | float64 | Pinnacle draw odds. |
| PSA | float64 | Pinnacle away win odds. |
| WHH | float64 | William Hill home win odds. |
| WHD | float64 | William Hill draw odds. |
| WHA | float64 | William Hill away win odds. |
| VCH | float64 | VC Bet home win odds. |
| VCD | float64 | VC Bet draw odds. |
| VCA | float64 | VC Bet away win odds. |
| MaxH | float64 | Market maximum home win odds. |
| MaxD | float64 | Market maximum draw odds. |
| MaxA | float64 | Market maximum away win odds. |
| AvgH | float64 | Market average home win odds. |
| AvgD | float64 | Market average draw odds. |
| AvgA | float64 | Market average away win odds. |
| B365>2.5 | float64 | Bet365 over 2.5 goals. |
| B365<2.5 | float64 | Bet365 under 2.5 goals. |
| P>2.5 | float64 | Pinnacle over 2.5 goals. |
| P<2.5 | float64 | Pinnacle under 2.5 goals. |
| Max>2.5 | float64 | Market maximum over 2.5 goals. |
| Max<2.5 | float64 | Market maximum under 2.5 goals. |
| Avg>2.5 | float64 | Market average over 2.5 goals. |
| Avg<2.5 | float64 | Market average under 2.5 goals. |
| AHh | float64 | Market size of handicap (home team). |
| B365AHH | float64 | Bet365 Asian handicap home team odds. |
| B365AHA | float64 | Bet365 Asian handicap away team odds. |
| PAHH | float64 | Pinnacle Asian handicap home team odds. |
| PAHA | float64 | Pinnacle Asian handicap away team odds. |
| MaxAHH | float64 | Market maximum Asian handicap home team odds. |
| MaxAHA | float64 | Market maximum Asian handicap away team odds. |
| AvgAHH | float64 | Market average Asian handicap home team odds. |
| AvgAHA | float64 | Market average Asian handicap away team odds. |
| B365CH | float64 | Closing Bet365 home win odds. |
| B365CD | float64 | Closing Bet365 draw odds. |
| B365CA | float64 | Closing Bet365 away win odds. |
| BWCH | float64 | Closing Bet&Win home win odds. |
| BWCD | float64 | Closing Bet&Win draw odds. |
| BWCA | float64 | Closing Bet&Win away win odds. |
| IWCH | float64 | Closing Interwetten home win odds. |
| IWCD | float64 | Closing Interwetten draw odds. |
| IWCA | float64 | Closing Interwetten away win odds. |
| PSCH | float64 | Closing Pinnacle home win odds. |
| PSCD | float64 | Closing Pinnacle draw odds. |
| PSCA | float64 | Closing Pinnacle away win odds. |
| WHCH | float64 | Closing William Hill home win odds. |
| WHCD | float64 | Closing William Hill draw odds. |
| WHCA | float64 | Closing William Hill away win odds. |
| VCCH | float64 | Closing VC Bet home win odds. |
| VCCD | float64 | Closing VC Bet draw odds. |
| VCCA | float64 | Closing VC Bet away win odds. |
| MaxCH | float64 | Closing Market maximum home win odds. |
| MaxCD | float64 | Closing Market maximum draw odds. |
| MaxCA | float64 | Closing Market maximum away win odds. |
| AvgCH | float64 | Closing Market average home win odds. |
| AvgCD | float64 | Closing Market average draw odds. |
| AvgCA | float64 | Closing Market average away win odds. |
| B365C>2.5 | float64 | Closing Bet365 over 2.5 goals. |
| B365C<2.5 | float64 | Closing Bet365 under 2.5 goals. |
| PC>2.5 | float64 | Closing Pinnacle over 2.5 goals. |
| PC<2.5 | float64 | Closing Pinnacle under 2.5 goals. |
| MaxC>2.5 | float64 | Closing Market maximum over 2.5 goals. |
| MaxC<2.5 | float64 | Closing Market maximum under 2.5 goals. |
| AvgC>2.5 | float64 | Closing Market average over 2.5 goals. |
| AvgC<2.5 | float64 | Closing Market average under 2.5 goals. |
| AHCh | float64 | Closing Market size of handicap (home team). |
| B365CAHH | float64 | Closing Bet365 Asian handicap home team odds. |
| B365CAHA | float64 | Closing Bet365 Asian handicap away team odds. |
| PCAHH | float64 | Closing Pinnacle Asian handicap home team odds. |
| PCAHA | float64 | Closing Pinnacle Asian handicap away team odds. |
| MaxCAHH | float64 | Closing Market maximum Asian handicap home team odds. |
| MaxCAHA | float64 | Closing Market maximum Asian handicap away team odds. |
| AvgCAHH | float64 | Closing Market average Asian handicap home team odds. |
| AvgCAHA | float64 | Closing Market average Asian handicap away team odds. |

*   **Note:** Missing data should be handled consistently. Empty strings or `#VALUE!` should be converted to `np.nan` during loading.
*   **Note:** Some columns (e.g., `Referee`, match statistics) have inconsistent availability across datasets and leagues. This will be handled by the `Preprocessor` while ensuring these columns aren't essential to the MVP.

#### 2. File Structure and Class Responsibilities:

The `data` directory contains two modules: `data_loader.py` and `preprocessor.py`.

*   **`data/data_loader.py`:**
    *   **`DataLoader` Class:** Responsible for loading raw CSV data.
        *   `__init__(self, config: DataConfig)`: Initialises the class with a `DataConfig` object from `core/config.py`. The `DataConfig` stores column mappings and date/time formats.
        *   `load_dataset(self, file_paths: List[str]) -> pd.DataFrame`:
            *   Accepts a list of file paths (strings) to the raw CSV files.
            *   Iterates through each file, reading it into a pandas DataFrame.
            *   Applies initial type casting based on the schema outlined above using `dtype`.
            *   Concatenates all DataFrames into a single DataFrame.
            *   Returns the concatenated DataFrame.
        *   `_read_csv(self, file_path: str) -> pd.DataFrame`: A private helper method to read a single CSV file into a pandas DataFrame. Uses `pd.read_csv` with specified `dtype` and `na_values` to handle missing values. The separator should be automatically detected. It should include proper error handling (try-except).

*   **`data/preprocessor.py`:**
    *   **`Preprocessor` Class:** Responsible for cleaning, standardising, team name standardization, initial transformations, and essential column validation on the raw data.
        *   `__init__(self, config: DataConfig)`: Initialises the class with a `DataConfig` object.
        *   `clean_and_standardise(self, df: pd.DataFrame) -> pd.DataFrame`:
            *   Renames columns using the `RAW_COL_MAP` from `DataConfig`.
            *   Converts the `Date` and `Time` columns to a single `datetime64[ns]` column named `match_date`.
                *   Handles different date formats (e.g., `dd/mm/yy`, `dd/mm/yyyy`) using `DataConfig.DATE_FORMAT`. The function should be flexible enough to automatically detect the appropriate format.
                *   If `Time` is missing, assume a default time (e.g., 12:00).
            *   Handles missing values consistently, replacing empty strings or other placeholder values with `np.nan` (using `MISSING_VALUE_PLACEHOLDERS` from `DataConfig`).
            *   Sorts the DataFrame chronologically by `match_date`.
            *   Returns the cleaned and standardised DataFrame.
        *   `standardise_team_names(self, df: pd.DataFrame) -> pd.DataFrame`:
            *   Creates a mapping of common team name variations to a standard format using `TEAM_NAME_MAPPING` from the `DataConfig`. For example, "Arsenal FC" becomes "Arsenal".
            *   Applies this mapping to the `HomeTeam` and `AwayTeam` columns, ensuring consistent team names across the dataset.
            *   Returns the DataFrame with standardised team names.
        *   `map_teams_to_ids(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]`:
            *   Assigns unique integer IDs to each team in the dataset. This is crucial for the Bayesian Poisson GLMM.
            *   Creates a dictionary mapping team names to their corresponding IDs.
            *   Adds two new columns to the DataFrame: `home_team_idx` and `away_team_idx`, containing the integer IDs for the home and away teams, respectively.
            *   Returns a tuple containing the updated DataFrame and the team-to-ID mapping dictionary.
        *   `get_market_odds_columns(self, df: pd.DataFrame, market_type: Market) -> Dict[str, List[str]]`:
            *   Identifies and returns a dictionary of available odds columns for a given market (e.g., 'MATCH_ODDS', 'OVER_UNDER_2_5') from the `ODDS_COL_PATTERNS` dictionary in `DataConfig`.
            *   The returned dictionary should map odds provider prefixes (e.g., 'B365', 'Max') to lists of corresponding column names (e.g., {'B365': ['B365H', 'B365D', 'B365A']}).
            *   Raises a `ValueError` if no odds columns are found for the specified market.
        *   `handle_inconsistent_columns(self, df: pd.DataFrame) -> pd.DataFrame`:
            *   **Simplified Logic for MVP:** Instead of a dynamic threshold, the method validates the existence and non-null status of a predefined set of `REQUIRED_COLUMNS` (defined in `DataConfig`).
            *   These `REQUIRED_COLUMNS` are: 'Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'.
            *   If *any* of these columns are missing or contain null values, raises a `ValueError` indicating which columns are problematic. This prevents the pipeline from continuing with incomplete essential data.
            *   For *all other* columns (i.e., columns *not* in `REQUIRED_COLUMNS`), missing values are explicitly filled with `np.nan` if not already so. The *columns themselves are not dropped*, regardless of their completeness.
            *   Returns the processed DataFrame.

#### 3. Data Loading and Preprocessing Flow:

The typical data loading and preprocessing flow would be:

1.  **Instantiate `DataLoader`:** Create an instance of the `DataLoader` class, passing in the `DataConfig` object.
2.  **Load Data:** Call the `load_dataset` method of the `DataLoader` instance, providing a list of file paths to the raw CSV files. This returns a concatenated DataFrame.
3.  **Instantiate `Preprocessor`:** Create an instance of the `Preprocessor` class, passing in the `DataConfig` object.
4.  **Clean and Standardise:** Call the `clean_and_standardise` method of the `Preprocessor` instance, passing in the DataFrame obtained from the `DataLoader`. This returns a cleaned and standardised DataFrame.
5.  **Standardise Team Names:** Call the `standardise_team_names` method of the `Preprocessor` instance, passing in the cleaned DataFrame.
6.  **Map Teams to IDs:** Call the `map_teams_to_ids` method of the `Preprocessor` instance, passing in the DataFrame with standardised team names. This returns a tuple containing the updated DataFrame and the team-to-ID mapping dictionary.
7.  **Handle Inconsistent Columns:** Call the `handle_inconsistent_columns` method of the `Preprocessor` instance, passing in the DataFrame with team IDs.
8.  **Data is now ready:** The returned DataFrame from step 7 is now ready for further feature engineering and model training. The team-to-ID mapping dictionary from step 6 should be stored for use during prediction.

#### 4. Error Handling and Logging:

*   The `DataLoader` should handle potential `FileNotFoundError` exceptions when loading CSV files.
*   The `DataLoader` should handle exceptions that may occur due to malformed CSV files.
*   The `Preprocessor` should handle `ValueError` exceptions that may occur during date/time conversion or data type casting.
*   The `Preprocessor` should explicitly raise a `ValueError` if any of the `REQUIRED_COLUMNS` are missing or contain null values.
*   All errors and warnings should be logged using the `utils/logger.py` module.

#### 5. Configuration:

The following parameters should be configurable in the `core/config.py` module within the `DataConfig` class:

*   `DataConfig.RAW_COL_MAP`: Mapping of raw column names to standardised names.
*   `DataConfig.DATE_FORMAT`: Format string for parsing the `Date` column. Multiple formats should be supported, and the code should attempt to automatically detect the correct format.
*   `DataConfig.TIME_FORMAT`: Format string for parsing the `Time` column.
*   `DataConfig.ODDS_COL_PATTERNS`: Regex patterns to identify pre-match and closing odds columns.
*   `DataConfig.MISSING_VALUE_PLACEHOLDERS`: A list of strings or values to be treated as missing values (e.g., '', '#VALUE!').
*   `DataConfig.REQUIRED_COLUMNS`: A list of column names that are essential for the pipeline (e.g., `['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']`).
*   `DataConfig.TEAM_NAME_MAPPING`: A dictionary mapping common team name variations to a standardised format (e.g., `{'Arsenal FC': 'Arsenal', 'Man United': 'Man Utd'}`).

This detailed blueprint provides a clear roadmap for implementing the `data` stage of the `quant_football` library. Following this plan will ensure that data is loaded, cleaned, standardised, and validated in a consistent and reliable manner, setting the stage for successful model development and backtesting, while adhering to the principles of an MVP. This is designed so the required pieces for training will exist. The optional columns can be handled later.