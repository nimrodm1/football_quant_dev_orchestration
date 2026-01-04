# 1. Import the dictionaries from the specific files
from .data_prompts import DATA_PROMPTS
from .features_prompts import FEATURE_PROMPTS

# 2. Map them to a name
SPRINT_PROMPTS = {
    "data": DATA_PROMPTS,
    "features": FEATURE_PROMPTS,
}