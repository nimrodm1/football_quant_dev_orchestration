import os
import sys
import sqlite3
from dotenv import load_dotenv
from typing import Optional, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver

# Load keys
load_dotenv()

# Ensure modules are discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from agents import create_agent_node
from workflow import create_planner_graph

# --- 1. SEEDING LOGIC ---
def get_initial_state_from_db():
    stage_1_path = r"C:/Nimrod/ai_ds_team/projects/football_betting/1_high_level_plan/planning_session.sqlite"
    
    if not os.path.exists(stage_1_path):
        print(f"[ERROR]: Stage 1 database not found at {stage_1_path}")
        return {}

    # Connect with check_same_thread=False for safety
    conn = sqlite3.connect(stage_1_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    config = {"configurable": {"thread_id": "football_project_2025"}}
    
    checkpoint_tuple = saver.get_tuple(config)
    
    if checkpoint_tuple:
        print("✅ Found Stage 1 data! Injecting plans into missions...")
        checkpoint_dict = checkpoint_tuple.checkpoint
        old_values = checkpoint_dict.get("values", checkpoint_dict.get("channel_values", {}))
    else:
        print("[WARNING]: Thread not found in Stage 1 DB. Using defaults.")
        old_values = {}

    return {
        "messages": [HumanMessage(content="Initialising development plan phase.")],
        "current_agent": "dev_data",
        "data_schema": old_values.get("data_schema", "TBD"),
        "data_notes": old_values.get("data_notes", "TBD"),
        "architect_plan": old_values.get("architect_plan", "No plan found"),
        "modeller_plan": old_values.get("modeller_plan", "No plan found"), 
        "analyst_plan": old_values.get("analyst_plan", "No plan found")   
    }

# --- 2. MISSIONS TEMPLATES ---
MISSIONS = {
    "dev_data": (
        "You are the Data Architect. Below is the HIGH-LEVEL DATA PLAN we previously agreed upon:\n"
        "### HIGH-LEVEL PLAN:\n{plan}\n\n"
        "Your mission is to expand this into a detailed technical blueprint. Focus on data stage. "
        "1. Map the 'data_schema' to specific Python types (e.g., Polars Date, Float64). "
        "2. Break down the file structure (e.g., data/loader.py, data/features.py). "
        "3. The plan should assume we're going to use pandas"
        "4. Don't write python code."
        "Style: British English."
    ),
    "dev_modelling": (
        "You are the Quant Modeller. Below is the HIGH-LEVEL MODELLING PLAN:\n"
        "### HIGH-LEVEL PLAN:\n{plan}\n\n"
        "Modelling Plan: \n {model_plan}\n\n"
        "Your mission is to expand this into a technical specification."
        "Don't write python code, just ensure there's a clear development plan "
        "Style: Use LaTeX for equations."
    ),
    "dev_betting": (
        "You are the Betting Strategist. Below is the HIGH-LEVEL BETTING PLAN:\n"
        "### HIGH-LEVEL PLAN:\n{plan}\n\n"
        "Betting Plan: \n{betting_plan}\n"
        "Your mission is to turn this into coding requirements. "
        "Don't write python code, just ensure there's a clear development plan "
        "Style: British English. Ensure logic is compatible with decimal odds."
    ),
    "dev_backtest": (
        "You are the Backtest Analyst. Below is the HIGH-LEVEL BACKTEST PLAN:\n"
        "### HIGH-LEVEL PLAN:\n{plan}\n\n"
        "Your mission is to expand this into a robust testing suite. "
        "Don't write python code, just ensure there's a clear development plan "
        "Style: British English."
    )
}

def main():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", # Use 2.0 unless you have specific 2.5 access
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )
    
    # --- PREPARE SEEDS ---
    seeds = get_initial_state_from_db()
    
    PREPARED_MISSIONS = {
        "dev_data": MISSIONS["dev_data"].format(plan=seeds.get("architect_plan")),
        "dev_modelling": MISSIONS["dev_modelling"].format(
            plan=seeds.get("architect_plan"),
            model_plan=seeds.get("modeller_plan")
        ),
        "dev_betting": MISSIONS["dev_betting"].format(
            plan=seeds.get("architect_plan"),
            betting_plan=seeds.get("analyst_plan")
        ),
        "dev_backtest": MISSIONS["dev_backtest"].format(plan=seeds.get("analyst_plan"))
    }

    # --- DEFINE NODES ---
    dev_data_node = create_agent_node(llm, PREPARED_MISSIONS["dev_data"], "dev_data")
    dev_modelling_node = create_agent_node(llm, PREPARED_MISSIONS["dev_modelling"], "dev_modelling")
    dev_betting_node = create_agent_node(llm, PREPARED_MISSIONS["dev_betting"], "dev_betting")
    dev_backtest_node = create_agent_node(llm, PREPARED_MISSIONS["dev_backtest"], "dev_backtest")

    # --- COMPILE & RUN ---
    with SqliteSaver.from_conn_string("dev_plan_session.sqlite") as memory:
        
        app = create_planner_graph(
            dev_data_node, 
            dev_modelling_node, 
            dev_betting_node, 
            dev_backtest_node,
            checkpointer=memory
        )

        config = {"configurable": {"thread_id": "dev_session_2025_v1"}}

        # Seeding check
        current_state = app.get_state(config)
        if not current_state.values.get("messages"):
            print("\n[SYSTEM]: Seeding state from Phase 1...")
            app.invoke(seeds, config)

        while True:
            # 1. This runs the current node (e.g. dev_data) and stops at the NEXT interrupt
            for event in app.stream(None, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        agent_name = event.get("current_agent", "AGENT").upper()
                        print(f"\n--- {agent_name} ---")
                        print(last_msg.content)

            # 2. Now we are paused. Get the active agent name for the prompt.
            curr_state = app.get_state(config)
            active_agent = curr_state.values.get("current_agent", "the team")
            
            user_input = input(f"\nFeedback for {active_agent} (or 'PROCEED'): ").strip()

            if user_input.upper() == "EXIT":
                break
            
            # 3. This 'invoke' pushes your command into the state and triggers the router
            app.update_state(config, {"messages": [HumanMessage(content=user_input)]})
            
            # 4. Check if the graph has reached the END node
            if not app.get_state(config).next:
                print("\n[SYSTEM]: Planning session successfully finalised.")
                break

if __name__ == "__main__":
    main()