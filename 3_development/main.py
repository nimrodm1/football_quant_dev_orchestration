import os
import argparse
import shutil
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

# Core Logic Imports
from tools import create_tools
from agents import (
    architect_node, tester_node, developer_node, 
    test_runner_node, reviewer_node, human_node
)
from workflow import run_workflow
from state import AgentState
from utils import upload_package_to_sandbox, download_package_from_sandbox
from logger import SprintLogger

# Prompt Imports
from prompts import SPRINT_PROMPTS 
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

ORCHESTRATOR_ROOT = "." 
PACKAGE_ROOT = "../football_quant_package"

def main(stage: str):
    # 1. Validation & Prompt Loading
    if stage not in SPRINT_PROMPTS:
        print(f"❌ Error: Stage '{stage}' not found.")
        return

    print(f"🚀 Initialising FRESH Sprint Stage: {stage.upper()}")
    
    # 1.5 Initialize Logger
    logger = SprintLogger(stage)
    logger.sprint_start()

    # 2. Infrastructure: Sandbox & LLM
    sandbox = Sandbox.create(timeout=3600)
    install_cmd = (
        "pip install --quiet "
        "numpy==1.26.4 "       # The most stable 'LTS' version of NumPy 1.x
        "pandas>=2.2.0 "
        "xarray>=2024.1.0 "
        "pymc>=5.16.2 "
        "arviz>=0.18.0 "
        "pytensor>=2.22.1"
    )
    sandbox.commands.run(install_cmd)
    
    # --- SYNC UP ---
    # Put your local 'src' and 'configs' into the empty sandbox
    upload_package_to_sandbox(sandbox, PACKAGE_ROOT, ORCHESTRATOR_ROOT)
    
    tools = create_tools(sandbox)

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    stage_prompts = SPRINT_PROMPTS[stage]

    # 3. Node Wrappers (pass logger to each agent)
    architect_wrapper = lambda state: architect_node(state, llm, stage_prompts["ARCHITECT_SYSTEM_PROMPT"], tools, logger)
    tester_wrapper = lambda state: tester_node(state, llm, stage_prompts["TESTER_SYSTEM_PROMPT"], tools, logger)
    developer_wrapper = lambda state: developer_node(state, llm, stage_prompts["DEVELOPER_SYSTEM_PROMPT"], tools, logger)
    test_runner_wrapper = lambda state: test_runner_node(state, llm,stage_prompts["TEST_RUNNER_SYSTEM_PROMPT"], tools, logger)
    reviewer_wrapper = lambda state: reviewer_node(state, llm, stage_prompts["REVIEWER_SYSTEM_PROMPT"], tools, logger)
    human_wrapper = lambda state: human_node(state, logger)

    # 4. Compile Workflow (Notice: No checkpointer/memory passed here)
    app = run_workflow(
        architect_wrapper, tester_wrapper, developer_wrapper,
        test_runner_wrapper, reviewer_wrapper, human_wrapper, tools
    )
    
    #app = workflow.compile() 

    # 5. Initial State (The starting point for every fresh run)
    initial_state = AgentState(
        current_stage=stage,
        messages=[],
        iteration_count=0,
        active_failures=[],
        tool_loop_count=0,
        active_plan="",
        active_config="",
        active_mock_data="",
        active_tests="",
        active_requirements="",
        human_instruction=""
    )

    # 6. Execution
    try:
        # Standard invoke without config/thread_id because there is no persistence
        result = app.invoke(initial_state, {"recursion_limit": 100})

        # 7. Output Summary
        print("\n--- Session Complete ---")
        if "messages" in result:
            last_msg = result["messages"][-1]
            print(f"Final Status: {last_msg.content[:500]}...")

        logger.sprint_end("SUCCESS")
        print(f"\n📋 Log file: {logger.get_log_file()}")

        # --- SYNC DOWN ---
        # Persist the AI's coding work by bringing it back to your laptop
        download_package_from_sandbox(sandbox, PACKAGE_ROOT, ORCHESTRATOR_ROOT)

    except Exception as e:
        print(f"❌ Execution Error: {e}")
        logger.error(str(e))
        logger.sprint_end("FAILED")

    finally:
        # 8. Cleanup
        input("\nPress ENTER to close sandbox...")
        sandbox.kill()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Football Quant Orchestrator")
    parser.add_argument("--stage", type=str, default="data", help="Sprints: data, features, modelling")
    
    args = parser.parse_args()
    main(stage=args.stage)