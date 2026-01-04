import os
import time
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from agents import get_team
from workflow import create_workflow
from langchain_core.messages import HumanMessage

load_dotenv()

prompts = {
    "architect": (
        "You are the Lead Architect."
        "Your task is to ingest the .md requirements and create a technical implementation ticket "
        "for the developers. Specify the file paths (inside 'src/'), class names, and method signatures. "
        "Maintain a consistent package structure and use British English throughout."
    ),
    "data_engineer": (
        "You are a Senior Data Engineer. You work exclusively in the E2B sandbox. "
        "Your goal is to implement Stage 1: Data."
        "Crucially, implement mock data according to the data schema"
        "and odds so the pipeline can be tested without real API keys. "
        "Always verify your code by running it in the sandbox before finishing."
    ),
    "feature_engineer": (
        "You are a Quant/Feature Engineer. You work exclusively in the E2B sandbox. "
        "You handle Stage 2 (Features) and Stage 3 (Modelling). Use the dummy data from Stage 1 to calculate "
        "metrics like rolling averages or ELO. Ensure all mathematical logic is robust."
    ),
    "betting_strategist": (
        "You are a Betting Market Expert. You work exclusively in the E2B sandbox. "
        "You handle Stage 4.betting strategy."
        "Test this logic against synthetic model outputs."
    ),
    "qa_tester": (
        "You are the QA and DevOps Lead. You handle Stage 5 and final packaging. "
        "1. Write and run pytest suites for every module in 'src/'. "
        "2. Ensure the full pipeline runs from dummy data to betting recommendation. "
        "3. When the Architect signals completion, use 'run_code' to execute: "
        "zip -r football_package.zip . -x '**/__pycache__/*' "
        "4. Confirm the zip file exists in the sandbox root."
    )
}

def run_development():
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("E2B_API_KEY"):
        raise ValueError("Missing API keys! Please check your .env file.")

    # 1. Start the persistent sandbox
    with Sandbox.create() as sandbox:
        print(f"Sandbox started. ID: {sandbox.sandbox_id}")
        
        team = get_team(sandbox)
        app = create_workflow(team)
        
        initial_state = {
        "messages": [],
        "current_stage": "data",
        "is_ready_for_next_stage": False
    }

        # Added config for safety and future persistence
        config = {
            "recursion_limit": 50, # Sufficient for a multi-stage dev loop
            "configurable": {
            "thread_id": "dev_run_1"
            }
        }

        print("Starting development loop...")
        try:
            # Pass the config as the second argument
            app.invoke(initial_state, config=config)
        except Exception as e:
            print(f"Workflow failed: {e}")
        print("\n--- DEVELOPMENT STAGES COMPLETE ---")

        # 3. INTERRUPT: Pause before closing the sandbox
        print(f"\n[INSPECTION MODE]")
        print(f"The sandbox is still LIVE. You can use the E2B CLI or Dashboard to inspect it.")
        print(f"Sandbox URL: https://e2b.dev/dashboard?sandboxId={sandbox.sandbox_id}")
        input("Press Enter to proceed to packaging and download (or Ctrl+C to abort)...")

        # 4. DOWNLOAD LOGIC
        print("Requesting the QA Agent to package the project...")
        # We manually trigger the QA agent one last time to zip the files
        zipping_task = (
            "Please zip the entire /home/user directory (excluding __pycache__) "
            "into a file named 'football_package.zip'."
        )
        print("Requesting the QA Agent to package the project...")
        team["qa_tester"].invoke({
            "input": zipping_task
        })

        print("Downloading package to local disk...")
        try:
            # E2B stores files in /home/user by default
            remote_path = "/home/user/football_package.zip"
            buffer = sandbox.download_file(remote_path)
            
            local_filename = f"football_betting_pkg_{int(time.time())}.zip"
            with open(local_filename, "wb") as f:
                f.write(buffer)
            
            print(f"✅ Success! Package saved as: {local_filename}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("Check if the QA agent created the zip file correctly in /home/user/")

if __name__ == "__main__":
    run_development()