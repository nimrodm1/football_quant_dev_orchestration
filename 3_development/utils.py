import re
import os

def read_plan_from_disk(stage: str) -> str:
    """
    Robustly reads the .md plan file using absolute paths.
    Expected structure: 
    C:/.../football_betting/2_dev_plen/outputs/dev_{stage}_plan.md
    """
    # 1. Get the directory where agents.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up one level to the project root (football_betting/)
    project_root = os.path.dirname(current_dir)
    
    # 3. Construct the path to the plan file
    # Ensure it handles the '2_dev_plen' folder correctly
    file_path = os.path.join(
        project_root, 
        "2_dev_plan", 
        "outputs", 
        f"dev_{stage}_plan.md"
    )
    
    # Normalize for Windows
    file_path = os.path.normpath(file_path)

    if not os.path.exists(file_path):
        return f"Error: Plan file not found at {file_path}. Please check the folder name and location."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def extract_config_from_response(text: str) -> str | None:
    pattern = r"### CONFIG_FILE.*?```(?:yaml|json)?\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


from pathlib import Path

from pathlib import Path
import re

from pathlib import Path
import re

def extract_files_to_modify(text):
    # 1. Isolate the FILES_TO_MODIFY block (colon optional)
    match = re.search(
        r"FILES_TO_MODIFY\s*:?\s*(.*?)(?:\n###\s*[A-Z_]+\s*|\Z)",
        text,
        flags=re.DOTALL
    )

    if not match:
        return []

    block = match.group(1)

    # 2. Extract .py paths ONLY from this block
    matches = re.findall(
        r"`([^`]+?\.py)`|([A-Za-z0-9_\-/]+?\.py)",
        block
    )

    paths = []
    for m1, m2 in matches:
        if m1:
            paths.append(m1.strip())
        elif m2:
            paths.append(m2.strip())

    # 3. Deduplicate while preserving order
    paths = list(dict.fromkeys(paths))

    # 4. Remove bare filenames if a full path exists
    full_paths = {Path(p).name: p for p in paths if "/" in p or "\\" in p}

    cleaned = []
    for p in paths:
        name = Path(p).name
        if name in full_paths and p != full_paths[name]:
            continue
        cleaned.append(p)

    return cleaned