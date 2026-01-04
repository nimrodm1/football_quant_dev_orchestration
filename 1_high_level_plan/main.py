import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# Load keys from .env (GOOGLE_API_KEY, E2B_API_KEY)
load_dotenv()

# Ensure modules are discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from agents import create_agent_node, create_profiler_node
from workflow import create_planner_graph

csv_path = "data/2020.csv"
notes_path = "data/data_dict.txt"

# --- PROJECT CONFIGURATION ---
FOOTBALL_MISSIONS = {
  "architect": (
        "You are a Senior Football Quant Architect. Your goal is to design a local Python library. "
        "1. Define the directory structure (e.g., /core, /models, /utils). "
        "2. Specify the Class names and Method signatures (e.g., class PoissonModel -> method predict_outcome). "
        "3. Ensure the library is 'Plug-and-Play' for different football datasets. "
        "4. Plan for an E2B execution environment for backtesting. "
        "Style: Use British English (fixtures, maximise). Output a clear Pythonic blueprint in architect_plan.md."
    ),
    "modeller": (
        "You are a Sports Statistician specialising in association football. "
        "Specifically, you must propose a Bayesian Poisson GLMM (Generalised Linear Mixed Model) using PyMC, "
        "incorporating team-specific random effects and a time-decay component for historical fixtures. "
        "1. Explain the prior distributions (e.g., Half-Normal for variance) and the likelihood function. "
        "2. Address how to handle home-pitch advantage as a fixed effect. "
        "3. Provide the PyMC model structure in LaTeX or pseudo-code. "
        "Style: Use LaTeX for equations. Focus on '1X2' and 'Total Goals' markets."
    ),
    
    "analyst": (
        "You are a Betting Risk Analyst. Your mission is to design the strategy layer that sits on top of the Modeller's probability outputs. "
        "1. Propose 3 betting/staking strategies (e.g., Flat Staking, Kelly Criterion, and a fractional/conservative variant). "
        "2. Evaluate each strategy based on risk of ruin, bankroll volatility, and expected ROI. "
        "3. Provide the mathematical formulation for how the model's 'value' (probability vs. market odds) triggers a bet. "
        "4. Suggest methods for handling 'Market Overround' and 'Closing Line Value' (CLV). "
        "Style: Use British English. Ensure your strategies are compatible with decimal odds."
    )
}

def main():
    # 1. Initialise the Gemini model
    # Note: Use "gemini-1.5-flash" or "gemini-2.0-flash" if 2.5 is not yet in your region's SDK
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    # 2. Create Nodes using the Factory
    nodes = {
        "profiler": create_profiler_node(csv_path, notes_path),
        "architect": create_agent_node(llm, FOOTBALL_MISSIONS["architect"], "architect", context_size=0),
        "modeller": create_agent_node(llm, FOOTBALL_MISSIONS["modeller"], "modeller", context_size=3),
        "analyst": create_agent_node(llm, FOOTBALL_MISSIONS["analyst"], "analyst", context_size=3)
    }

    # 3. Compile the Graph
    app = create_planner_graph(
        nodes['profiler'],
        nodes["architect"], 
        nodes["modeller"], 
        nodes["analyst"]
    )

    # 4. Configuration
    config = {"configurable": {"thread_id": "football_project_2025"}}

    print("\n" + "="*50)
    print("FOOTBALL BETTING LIBRARY - PLANNING SUITE")
    print("="*50)
    print("Commands: 'PROCEED' (Next Expert), 'EXIT' (Save & Quit)")

    # --- STARTUP LOGIC ---
    # Check if this thread is brand new. If so, kick it off.
    current_state = app.get_state(config)
    if not current_state.values.get("messages"):
        print("\n[SYSTEM]: Initialising the team...")
        app.invoke(
            {"messages": [HumanMessage(content="Team, let's start designing the football betting library. Architect, please begin.")]}, 
            config
        )

    # --- MAIN INTERACTION LOOP ---
    while True:
        agent_name = "the team"
        
        # stream(None) resumes execution from the breakpoint
        for event in app.stream(None, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if isinstance(last_msg, AIMessage):
                    agent_name = event.get("current_agent", "UNKNOWN").upper()
                    print(f"\n--- {agent_name} ---")
                    print(last_msg.content)

        # The graph is now paused at an interrupt_before
        user_input = input(f"\nFeedback for {agent_name} (or 'PROCEED'): ").strip()

        if user_input.upper() == "EXIT":
            break

        # CRITICAL: Use update_state to inject the command
        app.update_state(config, {"messages": [HumanMessage(content=user_input)]})
        
        # Check if we are finished
        if not app.get_state(config).next:
            print("\nPlanning complete.")
            break

if __name__ == "__main__":
    main()