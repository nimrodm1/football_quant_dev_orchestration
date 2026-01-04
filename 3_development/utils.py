import re
import os

import os
import shutil
import io

def upload_package_to_sandbox(sandbox, package_root, orchestrator_root):
    """
    Combines the local package and orchestrator configs into one sandbox.
    """
    zip_path = "sync_package"
    temp_dir = "temp_sync_staging"

    # 1. Create a temporary staging area
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        # 2. Copy the Package code (src)
        src_local = os.path.join(package_root, "src")
        if os.path.exists(src_local):
            shutil.copytree(src_local, os.path.join(temp_dir, "src"))

        # 3. Copy the Orchestrator configs (configs)
        configs_local = os.path.join(orchestrator_root, "configs")
        if os.path.exists(configs_local):
            shutil.copytree(configs_local, os.path.join(temp_dir, "configs"))

        # 4. Zip the combined staging area
        shutil.make_archive(zip_path, 'zip', root_dir=temp_dir)

        # 5. Upload and Unzip
        with open(f"{zip_path}.zip", "rb") as f:
            sandbox.files.upload(f)
        
        sandbox.commands.run(f"unzip -o {zip_path}.zip -d .")
        sandbox.commands.run(f"rm {zip_path}.zip")
        
        print("✅ Sandbox synchronised: /src (from Package) and /configs (from Orchestrator)")

    finally:
        # Cleanup
        if os.path.exists(f"{zip_path}.zip"): os.remove(f"{zip_path}.zip")
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)

def download_package_from_sandbox(sandbox, package_root, orchestrator_root):
    """
    Sends 'src' updates back to the package and 'configs' updates to the orchestrator.
    """
    # Sync src -> Package
    src_bytes = sandbox.files.download("src")
    with open("src_sync.zip", "wb") as f: f.write(src_bytes)
    shutil.unpack_archive("src_sync.zip", package_root)
    os.remove("src_sync.zip")

    # Sync configs -> Orchestrator
    try:
        config_bytes = sandbox.files.download("configs")
        with open("cfg_sync.zip", "wb") as f: f.write(config_bytes)
        shutil.unpack_archive("cfg_sync.zip", orchestrator_root)
        os.remove("cfg_sync.zip")
    except:
        print("No configs found to download.")
    
    print("✅ Local files updated from Sandbox.")

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