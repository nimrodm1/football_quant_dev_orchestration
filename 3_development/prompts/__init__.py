# prompts/__init__.py

# 1. Import your individual stage files
from . import data_prompts
from . import feature_prompts
# from . import modelling_prompts (when you're ready)

# 2. Map them to a name
SPRINT_PROMPTS = {
    "data": data_prompts,
    "features": feature_prompts,
    # "modelling": modelling_prompts
}