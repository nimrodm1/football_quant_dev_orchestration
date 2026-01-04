import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import tool
from e2b_code_interpreter import Sandbox

# Define the schema for the LLM
class WriteFilesInput(BaseModel):
    files: List[Dict[str, str]] = Field(
        description="List of dicts with 'path' (str) and 'content' (str)."
    )

def create_tools(sandbox: Sandbox):
    
    @tool
    def run_code(code: str):
        """Run Python code in the sandbox. Use this to execute pytest or verify data."""
        execution = sandbox.run_code(code)
        stdout = "\n".join(execution.logs.stdout)
        stderr = "\n".join(execution.logs.stderr)
    
        if not stdout and not stderr:
            return "Execution successful (no output produced)."
    
        return f"STDOUT: {stdout}\nSTDERR: {stderr}"

    @tool(args_schema=WriteFilesInput)
    def write_files(files: List[Dict[str, Any]]):
        """
        Writes multiple files to the sandbox filesystem. 
        Automatically creates directories if they don't exist.
        """
        try:
            paths_written = []
            for file_info in files:
                path = file_info['path']
                content = file_info['content']
                
                # CRITICAL FIX: Ensure directory structure exists in E2B
                # We do this by running a small shell command in the sandbox
                dir_path = os.path.dirname(path)
                if dir_path:
                    sandbox.commands.run(f"mkdir -p {dir_path}")
                
                sandbox.files.write(path, content)
                paths_written.append(path)
            
            return f"Successfully wrote {len(paths_written)} files: {', '.join(paths_written)}"
        except Exception as e:
            return f"Error writing files: {str(e)}"

    @tool
    def read_plan(stage_name: str):
        """Reads the .md plan file for a specific development stage."""
        # Using absolute path logic is safer for long-term research
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "..", "2_dev_plan", "outputs", f"dev_{stage_name}_plan.md")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: Plan for {stage_name} not found at {file_path}"

    # Inside create_tools(sandbox: Sandbox)
    
    return {
        "read_plan": read_plan,
        "exec_python": run_code,
        "write_files": write_files
    }