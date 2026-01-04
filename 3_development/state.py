from typing import TypedDict, Annotated, Sequence, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_stage: str
    active_plan: str           # From Architect
    active_config: str         # From Architect
    active_mock_data: str      # Added for Tester
    active_tests: str          # Added for Tester
    active_requirements: str   # Added for Tester
    iteration_count: int
    active_failures: List[dict]
    human_instruction: str
    tool_loop_count: int