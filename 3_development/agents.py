import re
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from utils import extract_config_from_response, read_plan_from_disk, extract_files_to_modify
import os
from output_schema import ArchitectOutput, TesterOutput, DeveloperOutput, ReviewerOutput


def architect_node(state, llm, system_prompt, tools):
    stage = state["current_stage"]
    
    # 1. READ FROM LOCAL DISK
    plan_content = read_plan_from_disk(stage)

    if plan_content.startswith("Error:"):
        return {"messages": [HumanMessage(content=f"Stop: {plan_content}")]}

    # 2. INVOKE STRUCTURED LLM
    structured_llm = llm.with_structured_output(ArchitectOutput)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Architect stage: {stage}. Research Plan:\n\n{plan_content}")
    ]
    
    output = structured_llm.invoke(messages)

    # 3. PUSH CONFIG TO SANDBOX
    # Now we move information from 'Local' to 'Sandbox'
    tools["coding"][1].invoke({
        "files": [{"path": f"configs/{stage}.yaml", "content": output.config_yaml}]
    })

    # 4. UPDATE STATE
    return {
        "messages": [AIMessage(content=f"Architected {stage} based on local research plan.")],
        "active_plan": output.development_plan,
        "active_config": output.config_yaml
    }

def tester_node(state, llm, system_prompt, tools):
    stage = state["current_stage"]
    # We now get the config directly from state instead of reading from disk!
    config_text = state.get("active_config", "")
    
    if not config_text:
        return {"messages": [HumanMessage(content="Stop: No config found in state.")]}

    # 1. Bind the structured output
    structured_llm = llm.with_structured_output(TesterOutput)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Generate tests for stage '{stage}' using this config:\n{config_text}\n\n"
            "Important: Provide these as 'skipped' tests (using @pytest.mark.skip). "
            "The Developer will be responsible for implementing the logic."
        ))
    ]

    # 2. Invoke
    output = structured_llm.invoke(messages)

    # 3. Write files to sandbox (Keeping your existing tool logic)
    files_to_write = [
        {"path": f"tester_outputs/{stage}_mock_data.csv", "content": output.mock_data},
        {"path": f"tester_outputs/{stage}_tests.py", "content": output.skipped_tests},
        {"path": f"tester_outputs/{stage}_requirements.txt", "content": output.testing_requirements}
    ]
    tools["coding"][1].invoke({"files": files_to_write})

    # 4. Return the data to the global state
    return {
        "messages": [AIMessage(content="Tester has generated mock data and test scaffolding.")],
        "active_mock_data": output.mock_data,
        "active_tests": output.skipped_tests,
        "active_requirements": output.testing_requirements
    }

def developer_node(state, llm, system_prompt, tools):
    print('\n--- DEVELOPER START ---')
    stage = state["current_stage"]
    loop_count = state.get("tool_loop_count", 0) + 1
    # 1. Retrieve Structured Blueprints from State
    plan = state.get("active_plan", "")
    config = state.get("active_config", "")
    mock_data = state.get("active_mock_data", "")
    test_templates = state.get("active_tests", "")
    failures_list = state.get("active_failures", [])
    
    # 2. Retrieve Human Intervention
    human_advice = state.get("human_instruction", "No specific human instructions provided.")

    # 3. Format Structured Failures for the checklist
    error_context = ""
    if failures_list:
        error_context = "CHECKLIST OF FAILURES TO FIX:\n"
        for i, failure in enumerate(failures_list, 1):
            error_context += f"{i}. {failure.get('failure_type')} in {failure.get('file_path')}: {failure.get('actionable_fix')}\n"

    # 4. Build the Prompt with ALL context
    prompt = f"""
Current Stage: {stage}

### 1. ARCHITECT_PLAN & CONFIG
Plan:
{plan}

Config:
{config}

### 2. MOCK_DATA & TEST_TEMPLATES
Mock Data Context:
{mock_data}

Test Scaffolding (Implementation Reference):
{test_templates}

### 3. STRUCTURED_BUG_CHECKLIST
{error_context if error_context else "No structured failures yet."}

### 4. AD HOC HUMAN INSTRUCTION (CRITICAL PRIORITY)
The user has provided these specific directions. 
FOLLOW THESE EVEN IF THEY CONTRADICT YOUR OWN OPINION:
"{human_advice}"

Your Task:
- Implement the Python logic in the 'src' directory.
- Fix all issues in the checklist using the "Actionable Fix" recipes.
- Prioritise the Human Instruction above all other logic.
"""
    
    if loop_count > 3:
        prompt += f"\nWARNING: You have used {loop_count} attempts. If you cannot fix it this time, explain why and stop."
    llm_with_tools = llm.bind_tools(tools["coding"])
    # 5. Invoke & Write
    #structured_llm = llm.with_structured_output(DeveloperOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    history = state.get("messages", [])
    current_request = HumanMessage(content=prompt)
    
    response = llm_with_tools.invoke(history + [current_request])
        
    return {
        "messages": [response], 
        "human_instruction": "", 
        "tool_loop_count": loop_count
    }
    
def test_runner_node(state, llm, system_prompt, tools):
    print('test_runner Start')
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Run pytest now.")
    ]

    # Run pytest inside the sandbox
    result = tools["coding"][0].invoke({
        # -vv provides the full detail needed for the Agent to see the CSV ParserError properly
        "code": "import sys; sys.path.insert(0, 'src'); import pytest; pytest.main(['-vv'])"
    })
    print("\n[TEST RUNNER] Pytest output:\n", result)
    print('test_runner ends')
    # Return raw output
    return {"messages": [AIMessage(content=result)]}

def reviewer_node(state, llm, system_prompt, tools):
    print("--- REVIEWER START ---")

    # 1. Extract context
    pytest_output = state["messages"][-1].content
    iteration_count = state.get("iteration_count", 0) + 1
    
    # 2. Bind structured output
    structured_llm = llm.with_structured_output(ReviewerOutput)

    # 3. Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Iteration Number: {iteration_count}\n"
            f"Analyze this pytest output and provide structured feedback:\n\n"
            f"{pytest_output}"
        ))
    ]

    # 4. Invoke
    response_data = structured_llm.invoke(messages)

    # 5. Format a clean message for the Developer's chat history
    # We create a string version for the 'messages' list, but the 
    # Developer can also access the raw data if we save it to state.
    review_msg = f"REVIEWER SUMMARY: {response_data.summary}\n"
    for f in response_data.failures:
        review_msg += f"\n- [{f.failure_type}] in {f.file_path}: {f.actionable_fix}"

    print(f"Reviewer: Found {len(response_data.failures)} issues.")
    print("--- REVIEWER ENDS ---")

    return {
        "messages": [AIMessage(content=review_msg)],
        "iteration_count": iteration_count,
        # We store the structured failures so the Developer node can see them directly
        "active_failures": [f.dict() for f in response_data.failures], 
        "tool_loop_count": 0
    }

def human_node(state):
    print("\n--- 🛠️ HUMAN INTERVENTION ---")
    print("The Reviewer has analysed the failures. Current failures:")
    for f in state.get("active_failures", []):
        print(f" - {f.get('failure_type')}: {f.get('actionable_fix')}")
    
    # Prompt the user for ad hoc instructions
    user_input = input("\nProvide specific instructions for the Developer (or press Enter to let the agent proceed): ")
    
    return {
        "human_instruction": user_input if user_input.strip() else "No additional instructions."
    }