from pydantic import BaseModel, Field
from typing import List, Optional

class ArchitectOutput(BaseModel):
    """The plan and configuration produced by the Architect."""
    development_plan: str = Field(
        description="A detailed step-by-step plan for the developers."
    )
    config_yaml: str = Field(
        description="The YAML configuration content for the stage."
    )
    files_to_create: List[str] = Field(
        description="A list of relative file paths that need to be created or modified."
    )
    complexity_score: int = Field(
        description="A score from 1-10 of how difficult this stage is."
    )

############ To integrate to code
# class ArchitectOutput(BaseModel):
#     reasoning: str = Field(description="Explanation of the design decisions.")
#     development_plan: str = Field(description="The full MD plan for the developer.")
#     config_yaml: str = Field(description="The YAML configuration.")
#     critical_columns: List[str] = Field(
#         default=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG'],
#         description="List of columns that, if null, require the row to be dropped."
#     )

class TesterOutput(BaseModel):
    mock_data: str = Field(description="The raw CSV content for mock data.")
    skipped_tests: str = Field(description="The pytest python code containing skipped tests.")
    testing_requirements: str = Field(description="Summary of what needs to be tested.")

class FileUpdate(BaseModel):
    """Schema for a single file update."""
    path: str = Field(description="The relative path to the file (e.g., 'src/data/loader.py')")
    content: str = Field(description="The complete, updated content of the file.")

class DeveloperOutput(BaseModel):
    """The structured response from the Developer agent."""
    reasoning: str = Field(description="Briefly explain the changes and fixes made.")
    files: List[FileUpdate] = Field(description="A list of files to be written to the sandbox.")

class FailureAnalysis(BaseModel):
    """Analysis of a single test failure."""
    file_path: str = Field(description="The file where the failure occurred.")
    test_name: str = Field(description="The name of the failing test.")
    failure_type: str = Field(description="e.g., 'KeyError', 'AssertionError', 'ModuleNotFoundError'")
    root_cause: str = Field(description="Detailed explanation of why it failed.")
    actionable_fix: str = Field(description="Specific logic changes required to fix this.")

class ReviewerOutput(BaseModel):
    """The structured analysis of the entire test suite."""
    summary: str = Field(description="High-level overview of the current state of the code.")
    failures: List[FailureAnalysis] = Field(description="List of specific failures to be addressed.")
    developer_priority_instructions: str = Field(description="Overall strategic guidance for the Developer.")
    can_proceed_to_next_stage: bool = Field(description="Set to True if all tests passed.")