from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ArchitectOutput(BaseModel):
    """The strategy produced by the Architect for the current sprint."""
    reasoning: str = Field(description="Internal logic for the proposed architecture.")
    development_plan: str = Field(description="Step-by-step MD plan for the developer.")
    config_yaml: str = Field(description="The YAML configuration (hyperparameters, columns, or paths).")
    files_to_create: List[str] = Field(description="Paths to be created or modified.")
    # We use a Dict here so you can pass 'critical_columns' for Data or 'model_type' for Modelling
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Sprint-specific details (e.g., critical columns for data, loss functions for models)."
    )

class TesterOutput(BaseModel):
    """Scaffolding for validation."""
    mock_data: str = Field(description="CSV or JSON content for mock testing data.")
    skipped_tests: str = Field(description="The pytest code with @pytest.mark.skip markers.")
    testing_requirements: str = Field(description="Specific edge cases the developer must handle.")

class FileUpdate(BaseModel):
    path: str = Field(description="Path (e.g., 'src/features/indicators.py')")
    content: str = Field(description="The full Python code content.")

class DeveloperOutput(BaseModel):
    """The code changes from the Developer."""
    reasoning: str = Field(description="Explanation of the coding logic and fixes applied.")
    files: List[FileUpdate] = Field(description="The actual files to write to the sandbox.")

class FailureAnalysis(BaseModel):
    file_path: str = Field(description="Source of the error.")
    test_name: str = Field(description="Failing test function.")
    failure_type: str = Field(description="Exception type (e.g. KeyError).")
    root_cause: str = Field(description="Why it failed.")
    actionable_fix: str = Field(description="Code recipe to fix it.")

class ReviewerOutput(BaseModel):
    """The gatekeeper's final report."""
    summary: str = Field(description="Overview of test results.")
    failures: List[FailureAnalysis] = Field(default_factory=list)
    developer_priority_instructions: str = Field(description="What to focus on in the next iteration.")
    can_proceed_to_next_stage: bool = Field(description="True if logic is complete and tests pass.")