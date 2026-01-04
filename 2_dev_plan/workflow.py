import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from state import AgentState
from langchain_core.messages import HumanMessage

def router(state: AgentState):
    current = state.get("current_agent")
    user_msg = state["messages"][-1].content.upper() if state["messages"] else ""

    # Now we are checking the actual command you typed
    if user_msg == "PROCEED":
        if current == "dev_data": return "dev_modelling"
        if current == "dev_modelling": return "dev_betting"
        if current == "dev_betting": return "dev_backtest"
        if current == "dev_backtest": return "end"
    
    # If no "PROCEED" found, stay put
    return current

def create_planner_graph(dev_data_node, dev_modelling_node, dev_betting_node, dev_backtest_node, checkpointer):

    workflow = StateGraph(AgentState)
    
    workflow.add_node("dev_data", dev_data_node)
    workflow.add_node("dev_modelling", dev_modelling_node)
    workflow.add_node("dev_betting", dev_betting_node)
    workflow.add_node("dev_backtest", dev_backtest_node)

    # 1. Fixed starting sequence
    workflow.add_edge(START, "dev_data")

    # 2. Conditional Edges for Experts
    # We define a single mapping dictionary that the router uses
    routing_map = {
        "dev_data": "dev_data",
        "dev_modelling": "dev_modelling",
        "dev_betting": "dev_betting", 
        "dev_backtest": "dev_backtest", 
        "end": END
    }

    # Apply the router to each node
    workflow.add_conditional_edges("dev_data", router, routing_map)
    workflow.add_conditional_edges("dev_modelling", router, routing_map)
    workflow.add_conditional_edges("dev_betting", router, routing_map)
    workflow.add_conditional_edges("dev_backtest", router, routing_map)

    return workflow.compile(
        checkpointer=checkpointer, 
        # This ensures the terminal waits for you before every expert speaks
        interrupt_before=["dev_data", "dev_modelling", "dev_betting", "dev_backtest"]
    )