import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from core.state import AgentState

def router(state: AgentState):
    current = state.get("current_agent")
    user_msg = state["messages"][-1].content.upper() if state["messages"] else ""

    # If the user says PROCEED, move to the next expert
    if user_msg == "PROCEED":
        if current == "profiler": return "architect"
        if current == "architect": 
            if state.get("planning_complete"): return "end"
            return "modeller"
        if current == "modeller": return "analyst"
        if current == "analyst": return "architect"
    
    # If the user provides feedback (not PROCEED), stay on the current agent
    return current

def create_planner_graph(profiler_node, arch_node, mod_node, ana_node):
    conn = sqlite3.connect("planning_session.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)

    workflow = StateGraph(AgentState)
    
    workflow.add_node("profiler", profiler_node)
    workflow.add_node("architect", arch_node)
    workflow.add_node("modeller", mod_node)
    workflow.add_node("analyst", ana_node)

    # 1. Fixed starting sequence
    workflow.add_edge(START, "profiler")
    workflow.add_edge("profiler", "architect")

    # 2. Conditional Edges for Experts
    # We define a single mapping dictionary that the router uses
    routing_map = {
        "profiler": "profiler",
        "architect": "architect",
        "modeller": "modeller", 
        "analyst": "analyst", 
        "end": END
    }

    # Apply the router to each node
    workflow.add_conditional_edges("architect", router, routing_map)
    workflow.add_conditional_edges("modeller", router, routing_map)
    workflow.add_conditional_edges("analyst", router, routing_map)

    return workflow.compile(
        checkpointer=memory, 
        # This ensures the terminal waits for you before every expert speaks
        interrupt_before=["architect", "modeller", "analyst"]
    )