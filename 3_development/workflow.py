from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from state import AgentState

def create_workflow(architect_node, developer_node, tester_node):
    workflow = StateGraph(AgentState)

    def should_continue(state: AgentState):
        if state["is_ready_for_next_stage"]:
            stages = ["data", "features", "modelling", "betting", "backtesting"]
            current_idx = stages.index(state["current_stage"])
            if current_idx < len(stages) - 1:
                state["current_stage"] = stages[current_idx + 1]
                return "next_stage"
            return "finish"
        return "retry"

    workflow.add_node("architect", architect_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("tester", tester_node)

    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "tester")
    workflow.add_conditional_edges("tester", should_continue, {
        "next_stage": "architect", "retry": "developer", "finish": END
    })
    
    return workflow.compile()