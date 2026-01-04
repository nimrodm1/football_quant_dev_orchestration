
from state import AgentState
from langgraph.graph import StateGraph, END
 

def architect_condition(state):
    last_message = state["messages"][-1].content
    if last_message.startswith("Stop:"):
        return END  # Kill the workflow immediately
    return "tester"

def test_runner_condition(state):
    last_message = state["messages"][-1].content
    
    # We add signals for when pytest finds nothing to do
    stop_signals = [
        "FAILED", 
        "ERROR", 
        "ImportError", 
        "SyntaxError", 
        "Interrupted",
        "collected 0 items",      # NEW: Captures empty test collection
        "no tests ran"            # NEW: Captures the final pytest summary line
    ]
    
    if any(signal in last_message for signal in stop_signals):
        print("🚩 Error detected (or no tests found). Routing to Reviewer.")
        return "reviewer"
        
    return "end"


from typing import Literal

def should_continue(state) -> Literal["tools", "test_runner"]:
    messages = state["messages"]
    last_message = messages[-1]
    loop_count = state.get("tool_loop_count", 0)
    
    # If the LLM made a tool call AND we are under the limit
    if last_message.tool_calls and loop_count < 5:
        return "tools"
    
    # Circuit Breaker: If we've looped 5+ times, force a handover
    if last_message.tool_calls and loop_count >= 5:
        print(f"⚠️ Max iterations ({loop_count}) reached. Forcing handover.")
        return "test_runner"
    
    # Otherwise, the Developer finished normally
    return "test_runner"

from langgraph.prebuilt import ToolNode

def run_workflow(architect_node, tester_node, developer_node, test_runner_node, reviewer_node, human_node, tools):
    workflow = StateGraph(AgentState)

    # 1. Add all nodes (including the new Tools node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("tools", ToolNode(tools["coding"])) # NEW: The Sandbox Executor
    workflow.add_node("test_runner", test_runner_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("human_instructor", human_node)

    workflow.set_entry_point("architect")

    # 2. Existing start of flow
    workflow.add_conditional_edges("architect", architect_condition, {END: END, "tester": "tester"})
    workflow.add_edge("tester", "developer")

    # 3. NEW: The Developer's Internal Loop
    # Instead of going straight to test_runner, we check if the developer wants to use tools
    workflow.add_conditional_edges(
        "developer",
        should_continue, # This function checks for tool_calls
        {
            "tools": "tools",            # Loop to E2B Sandbox
            "test_runner": "test_runner" # No more tool calls? Go to official testing
        }
    )

    # After tools run, they MUST go back to the developer to process the result
    workflow.add_edge("tools", "developer")

    # 4. Official Validation Gate
    workflow.add_conditional_edges(
        "test_runner",
        test_runner_condition,
        {
            "reviewer": "reviewer",
            "end": END
        }
    )

    # 5. The Fix Loop (Human-in-the-loop)
    workflow.add_edge("reviewer", "human_instructor")
    workflow.add_edge("human_instructor", "developer")

    return workflow.compile()