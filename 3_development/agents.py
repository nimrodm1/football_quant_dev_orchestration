import re
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from utils import extract_config_from_response, read_plan_from_disk, extract_files_to_modify
import os
from output_schema import ArchitectOutput, TesterOutput, DeveloperOutput, ReviewerOutput


import os
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from output_schema import ArchitectOutput
from utils import read_plan_from_disk

def architect_node(state, llm, system_prompt, tools):
    stage = state["current_stage"]
    
    # 1. ADVANCED SITE SURVEY
    # We don't just want names; we want to see the logic in 'src' and any existing 'configs'
    discovery_script = """
import os
def get_structure(path):
    if not os.path.exists(path): return []
    return [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames]

def read_contents(files):
    contents = {}
    for f in files:
        if f.endswith('.py') or f.endswith('.yaml') or f.endswith('.yml'):
            try:
                with open(f, 'r') as file:
                    contents[f] = file.read()
            except: pass
    return contents

src_files = get_structure('src')
cfg_files = get_structure('configs')
print("STRUCTURE_START")
print(f"FILES: {src_files}")
print(f"CONFIGS: {cfg_files}")
print("CONTENTS_START")
print(read_contents(src_files + cfg_files))
"""
    
    discovery_raw = tools["exec_python"].invoke({"code": discovery_script})

    # 2. READ RESEARCH PLAN
    plan_content = read_plan_from_disk(stage)

    # 3. BUILD CONTEXTUAL PROMPT
    # We merge the discovery results with the system prompt to give the LLM full awareness
    full_human_message = (
        f"--- SANDBOX ENVIRONMENT SURVEY ---\n{discovery_raw}\n\n"
        f"--- NEW SPRINT GOAL: {stage.upper()} ---\n{plan_content}\n\n"
        "INSTRUCTIONS:\n"
        "1. Examine the 'CONTENTS' above. If a required configuration file from a previous stage "
        "(like data.yaml) is missing from the 'configs' folder but the code exists in 'src', "
        "REVERSE ENGINEER the missing config based on the source code.\n"
        "2. Propose a NEW development plan and config for the current stage that integrates "
        "seamlessly with the existing logic.\n"
        "3. Do not overwrite existing files unless necessary for the current stage."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=full_human_message)
    ]

    # 4. INVOKE STRUCTURED LLM
    structured_llm = llm.with_structured_output(ArchitectOutput)
    output = structured_llm.invoke(messages)

    # 5. PERSIST THE CONFIG (This creates the YAML in the sandbox)
    tools["write_files"].invoke({
        "files": [{"path": f"configs/{stage}.yaml", "content": output.config_yaml}]
    })

    # 6. UPDATE STATE
    return {
        "messages": [AIMessage(content=f"Architected {stage}. Verified existing codebase and reverse-engineered missing configs where necessary.")],
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
    tools["write_files"].invoke({"files": files_to_write})

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
    llm_with_tools = llm.bind_tools(list(tools.values()))
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
    print('--- TEST RUNNER START ---')
    
    # 1. Use the dictionary key we defined in create_tools
    test_tool = tools.get('exec_python') 
    
    if not test_tool:
        return {"messages": [HumanMessage(content="Error: exec_python tool not found.")]}

    # 2. Run pytest inside the sandbox
    pytest_script = "import sys; sys.path.insert(0, 'src'); import pytest; pytest.main(['-vv'])"
    
    raw_result = test_tool.invoke({"code": pytest_script})

    # 3. Format the output so the Reviewer knows exactly what it's looking at
    # We wrap it in a block to distinguish it from conversation
    formatted_content = f"SANDBOX_TEST_RESULTS:\n\n{raw_result}"

    print(f"\n[TEST RUNNER] Results captured ({len(raw_result)} chars)")
    print(raw_result)
    print('--- TEST RUNNER END ---')
    
    # We return an AIMessage here because this node is "reporting" back to the graph
    return {"messages": [AIMessage(content=formatted_content)],
            "last_test_output": raw_result # Store it in state for the Human Node
    }

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

from langchain_core.messages import HumanMessage

def human_node(state):
    print("\n" + "="*60)
    print("📋 RAW PYTEST LOG SNAPSHOT")
    print("="*60)
    
    # 1. Show the raw output from the last test run (if available)
    # We take the last 30 lines to avoid flooding the terminal while showing the errors
    raw_output = state.get("last_test_output", "No raw pytest output found in state.")
    if raw_output:
        lines = raw_output.splitlines()
        snapshot = "\n".join(lines[-30:]) if len(lines) > 30 else raw_output
        print(snapshot)
    
    print("\n" + "="*60)
    print("🛠️  HUMAN INTERVENTION REQUIRED")
    print("="*60)

    # 2. Show the parsed failures (from the state list)
    if state.get("active_failures"):
        print("\n❌ LATEST TEST FAILURES (Parsed):")
        for failure in state["active_failures"]:
            # If the failure is a dict from the reviewer, print it cleanly
            if isinstance(failure, dict):
                file = failure.get('file_path', 'Unknown')
                cause = failure.get('root_cause', 'Unknown error')
                print(f" • [{file}]: {cause}")
            else:
                print(f" • {failure}")

    # 3. Show the Reviewer's high-level summary
    if state.get("messages"):
        last_msg = state["messages"][-1]
        # Only print if it looks like it's from the reviewer
        print("\n📝 REVIEWER'S ASSESSMENT:")
        print(last_msg.content)

    print("\n" + "-"*60)
    print("CONTROLS:")
    print(" - Type specific instructions for the Developer (e.g., 'Fix the import on line 10').")
    print(" - Type 'EXIT' to end the sprint and download all files to your local machine.")
    print("-"*60)
    
    user_input = input(">> ").strip()
    
    if user_input.upper() == "EXIT":
        return {
            "messages": [HumanMessage(content="User requested exit and download.")],
            "human_instruction": "EXIT_SIGNAL" 
        }
    
    # We clear active_failures so the next loop starts fresh
    return {
        "messages": [HumanMessage(content=user_input)],
        "human_instruction": user_input,
        "active_failures": [] 
    }