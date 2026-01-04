import os
from langchain_core.messages import SystemMessage, AIMessage
from state import AgentState

def create_agent_node(llm, mission: str, name: str, context_size: int = 0):
    def node(state: AgentState):
        # 1. Global Context Ingestion
        # Even if the mission is pre-injected, we keep schema context dynamic
        # in case you update it mid-session.
        schema_context = f"\n\nCURRENT DATA SCHEMA:\n{state.get('data_schema', 'None')}"
        schema_notes = f"\n\nCURRENT DATA NOTES:\n{state.get('data_notes', 'None')}"
        
        system_prompt = SystemMessage(content=mission + schema_context + schema_notes)
        
        # 2. History Management
        messages = state["messages"][-context_size:] if context_size > 0 else state["messages"]

        # 3. LLM Execution
        response = llm.invoke([system_prompt] + messages)
        content = response.content

        # 4. Physical Save
        # This allows you, as the Architect, to review the markdown files in real-time.
        os.makedirs("outputs", exist_ok=True)
        with open(f"outputs/{name}_plan.md", "w", encoding="utf-8") as f:
            f.write(content)
 

        # 5. Return to State
        return {
            "messages": [AIMessage(content=content)],
            f"{name}_plan": content,
            "current_agent": name
        }
    return node