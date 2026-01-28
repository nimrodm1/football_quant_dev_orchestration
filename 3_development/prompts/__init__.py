# 1. Import the dictionaries from the specific files
from .data_prompts import DATA_PROMPTS
from .features_prompts import FEATURE_PROMPTS
from .modelling_prompts import MODELLING_PROMPTS
from .strategy_prompts import STRATEGY_PROMPTS

# 2. Map them to a name
SPRINT_PROMPTS = {
    "data": DATA_PROMPTS,
    "features": FEATURE_PROMPTS,
    "modelling": MODELLING_PROMPTS,
    "strategy": STRATEGY_PROMPTS
}