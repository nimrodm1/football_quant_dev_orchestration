import os
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from core.state import AgentState
import pandas as pd
from e2b_code_interpreter import Sandbox
from core.llm import gemini_2_5
import re
import json

def create_agent_node(llm, mission: str, name: str, context_size: int = 0):
    def node(state: AgentState):
        # We inject the data_schema into the system prompt if it exists
        # This ensures the agent 'sees' the data structure as part of its 'eyes'
        schema_context = f"\n\nCURRENT DATA SCHEMA:\n{state.get('data_schema', 'None')}"
        schema_notes = f"\n\nCURRENT DATA Notes:\n{state.get('data_notes', 'None')}"
        system_prompt = SystemMessage(content=mission + schema_context + schema_notes)
        
        messages = state["messages"][-context_size:] if context_size > 0 else state["messages"]
        # --- REFINEMENT LOGIC ---
        # If this is the Architect's second visit (post-Analyst), add a specific instruction
        if name == "architect" and state.get("analyst_plan"):
            m_plan = state.get("modeller_plan", "No modeller plan found.")
            a_plan = state.get("analyst_plan", "No analyst plan found.")
            refinement_instruction = (
                "THE PREVIOUS STEPS ARE COMPLETE. I have retrieved the specific plans from the Modeller and Analyst.\n\n"
                f"### MODELLER'S PROPOSED MODELS:\n{m_plan}\n\n"
                f"### ANALYST'S STAKING STRATEGY:\n{a_plan}\n\n"
                "YOUR TASK: Refine the final 'architect_plan.md'. Ensure that the directory structure "
                "accommodates these specific models and that the class signatures (especially for the 'Strategy' "
                "and 'Model' modules) are compatible with the math and logic described above."
            )
            messages.append(HumanMessage(content=refinement_instruction))
        response = llm.invoke([system_prompt] + messages)
        content = response.content

        # Save to file
        with open(f"{name}_plan.md", "w", encoding="utf-8") as f:
            f.write(content)

        # Logic to end the loop:
        # If the architect is speaking and we already have an analyst plan,
        # we mark the session as complete.
        is_complete = False
        if name == "architect" and state.get("analyst_plan"):
            is_complete = True

        return {
            "messages": [AIMessage(content=content)],
            "current_agent": name,
            f"{name}_plan": content,
            "planning_complete": is_complete
        }
    return node


def create_profiler_node(csv_path: str, notes_path: str = "data/notes.txt"):
    def node(state: AgentState):
        # 1. Handle the Text Notes
        notes_info = "No additional notes provided."
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                notes_info = f.read()

        # 2. Handle the CSV Schema
        if not os.path.exists(csv_path):
            schema_info = "Warning: CSV file not found."
        else:
            try:
                df = pd.read_csv(csv_path, nrows=5)
                schema_info = (
                    f"COLUMNS: {', '.join(df.columns)}\n"
                    f"TYPES:\n{df.dtypes.to_string()}"
                )
            except Exception as e:
                schema_info = f"Error: {str(e)}"

        return {
            "messages": [AIMessage(content="Profiler has indexed the dataset and notes.")],
            "data_schema": schema_info,
            "data_notes": notes_info, # <--- Storing as a separate attribute
            "current_agent": "profiler"
        }
    return node

