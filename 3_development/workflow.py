from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from state import AgentState

# --- 1. Router Functions ---

def architect_condition(state):
    last_message = state["messages"][-1].content
    if last_message.startswith("Stop:"):
        return END
    return "tester"

def should_continue(state) -> Literal["tools", "test_runner"]:
    messages = state["messages"]
    last_message = messages[-1]
    loop_count = state.get("tool_loop_count", 0)
    
    if last_message.tool_calls and loop_count < 5:
        return "tools"
    
    # Handover to official test runner after tools or if limit reached
    return "test_runner"

def human_router(state: AgentState):
    """
    The Master Gatekeeper. 
    Only the Human Instructor can decide to finish the sprint.
    """
    # Check the state for your instruction
    instruction = state.get("human_instruction", "").upper()
    
    if "EXIT" in instruction or "DONE" in instruction or "FINISH" in instruction:
        print("🏁 Human validated the work. Closing Sprint...")
        return END
    
    # Default: Send your feedback back to the developer to iterate
    print("🔄 Sending human feedback to Developer for iteration.")
    return "developer"

# --- 2. Main Workflow Construction ---

def run_workflow(architect_node, tester_node, developer_node, test_runner_node, reviewer_node, human_node, tools):
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("architect", architect_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("tools", ToolNode(list(tools.values())))
    workflow.add_node("test_runner", test_runner_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("human_instructor", human_node)

    # Define the Flow
    workflow.set_entry_point("architect")

    # A. Architect -> Tester -> Developer
    workflow.add_conditional_edges("architect", architect_condition, {END: END, "tester": "tester"})
    workflow.add_edge("tester", "developer")

    # B. The Developer Tool Loop
    workflow.add_conditional_edges(
        "developer",
        should_continue,
        {
            "tools": "tools",
            "test_runner": "test_runner"
        }
    )
    workflow.add_edge("tools", "developer")

    # C. The Validation Chain
    # We force test_runner results to go to the Reviewer for analysis
    workflow.add_edge("test_runner", "reviewer")
    
    # D. The Analysis Chain
    # The Reviewer provides thoughts, then passes the 'file' to you
    workflow.add_edge("reviewer", "human_instructor")

    # E. The Final Decision (Human Only)
    workflow.add_conditional_edges(
        "human_instructor", 
        human_router,
        {
            "developer": "developer",
            END: END
        }
    )

    return workflow.compile()