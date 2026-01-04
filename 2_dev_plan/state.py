from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    
    # New variable for the experts to see
    data_schema: Optional[str]
    data_notes: Optional[str]
    architect_plan: Optional[str]
    modeller_plan: Optional[str]
    analyst_plan: Optional[str]
    planning_complete: bool
    sandbox_id: str             # To keep track of the E2B session
    generated_files: List[str]  # Tracking which files are in the sandbox
    test_results: str           # Output from running the PyMC model
    iteration_count: int
    current_phase: str
    planned_files: List[str]
    dev_data_plan: Optional[str]
    dev_modelling_plan: Optional[str]
    dev_betting_plan: Optional[str]
    dev_backtest_plan: Optional[str]