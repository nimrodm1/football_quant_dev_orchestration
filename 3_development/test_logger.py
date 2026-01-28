"""
Unit tests for SprintLogger functionality using pytest.

Run with:
    pytest test_logger.py -v
    
Or for detailed output:
    pytest test_logger.py -v -s
"""

import pytest
import os
from pathlib import Path
from logger import SprintLogger


class TestSprintLogger:
    """Test suite for SprintLogger class."""
    
    @pytest.fixture
    def logger(self):
        """Create a fresh logger for each test."""
        logger = SprintLogger("test_unit", log_dir="../logs")
        yield logger
        # Cleanup: Remove the test log file after test (close file first)
        try:
            # Close the logger's file handler
            for handler in logger.logger.handlers:
                handler.close()
            
            import time
            time.sleep(0.1)  # Small delay for file release
            
            if os.path.exists(logger.get_log_file()):
                os.remove(logger.get_log_file())
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_logger_creates_file(self, logger):
        """Test that logger creates a log file."""
        log_file = logger.get_log_file()
        logger.sprint_start()
        
        assert os.path.exists(log_file), f"Log file not created at {log_file}"
        assert log_file.endswith(".log"), "Log file should have .log extension"
    
    def test_log_file_has_content(self, logger):
        """Test that log file contains data after logging."""
        log_file = logger.get_log_file()
        logger.sprint_start()
        logger.info("Test message")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 0, "Log file is empty"
        assert "🚀 SPRINT START" in content, "Sprint start marker not found"
        assert "Test message" in content, "Test message not logged"
    
    def test_sprint_lifecycle(self, logger):
        """Test sprint start and end logging."""
        log_file = logger.get_log_file()
        logger.sprint_start()
        logger.sprint_end("SUCCESS")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "🚀 SPRINT START" in content
        assert "✅ SPRINT END: SUCCESS" in content
    
    def test_agent_lifecycle(self, logger):
        """Test agent start and end logging."""
        log_file = logger.get_log_file()
        logger.agent_start("architect")
        logger.agent_end("architect", "5 files discovered")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "→ ARCHITECT started" in content
        assert "✅ ARCHITECT complete (5 files discovered)" in content
    
    def test_reasoning_logging(self, logger):
        """Test that reasoning is logged correctly."""
        log_file = logger.get_log_file()
        reasoning = "Implementing data validation before loading. Using pandas for ETL."
        logger.reasoning("developer", reasoning)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "💭 [developer]" in content
        assert "Implementing data validation" in content
    
    def test_tool_execution_logging(self, logger):
        """Test tool execution logging."""
        log_file = logger.get_log_file()
        logger.tool_execution("pytest", "COMPLETE", "5 passed, 2 failed")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "🔧 Tool: pytest" in content
        assert "5 passed, 2 failed" in content
    
    def test_reviewer_feedback_logging(self, logger):
        """Test reviewer feedback with failures."""
        log_file = logger.get_log_file()
        failures = [
            {
                'file_path': 'src/features/indicators.py',
                'failure_type': 'KeyError',
                'root_cause': "Column 'close_price' not found",
                'actionable_fix': "Add column validation"
            }
        ]
        logger.reviewer_feedback(
            "2/5 tests passed",
            failures,
            "Fix imports first"
        )
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "❌ REVIEWER FEEDBACK" in content
        assert "2/5 tests passed" in content
        assert "KeyError" in content
        assert "src/features/indicators.py" in content
        assert "Add column validation" in content
        assert "Fix imports first" in content
    
    def test_human_instruction_logging(self, logger):
        """Test human instruction logging."""
        log_file = logger.get_log_file()
        instruction = "Check the CSV format. The close_price column might be named differently."
        logger.human_instruction(instruction)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "🛠️  HUMAN INSTRUCTION" in content
        assert "close_price" in content
    
    def test_error_logging(self, logger):
        """Test error logging."""
        log_file = logger.get_log_file()
        logger.error("Sandbox timeout while running pytest")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "⚠️  ERROR" in content
        assert "Sandbox timeout" in content
    
    def test_log_timestamps(self, logger):
        """Test that logs include timestamps."""
        log_file = logger.get_log_file()
        logger.sprint_start()
        logger.info("Test")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check first line has timestamp format YYYY-MM-DD HH:MM:SS
        assert len(lines) > 0
        first_line = lines[0]
        assert "|" in first_line, "Timestamp separator not found"
        # Should have date format YYYY-MM-DD
        assert "-" in first_line and ":" in first_line
    
    def test_reasoning_truncation(self, logger):
        """Test that very long reasoning is truncated in logs."""
        log_file = logger.get_log_file()
        long_reasoning = "x" * 500  # Very long text
        logger.reasoning("test", long_reasoning)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reasoning should be truncated to ~200 chars, verify it's there with ellipsis
        assert "💭 [test]" in content
        assert "..." in content  # Should have ellipsis for truncation
    
    def test_log_file_path_format(self, logger):
        """Test that log file has correct timestamp format."""
        log_file = logger.get_log_file()
        filename = Path(log_file).name
        
        # Format should be: YYYY-MM-DD_HH-MM-SS_stage_sprint.log
        # Example: 2026-01-25_00-46-08_test_unit_sprint.log
        assert filename.endswith("_sprint.log"), f"Should end with _sprint.log: {filename}"
        assert "test_unit" in filename, f"Should contain stage name: {filename}"
        # Verify date format YYYY-MM-DD_HH-MM-SS at start
        parts = filename.split("_")
        assert len(parts) >= 4, f"Not enough parts in filename: {filename}"
    
    def test_full_workflow_logging(self, logger):
        """Integration test: simulate a full sprint workflow."""
        log_file = logger.get_log_file()
        
        # Full workflow
        logger.sprint_start()
        
        # Architect phase
        logger.agent_start("architect")
        logger.reasoning("architect", "Analyzing codebase structure")
        logger.agent_end("architect", "8 files discovered")
        
        # Tester phase
        logger.agent_start("tester")
        logger.agent_end("tester", "mock data & tests generated")
        
        # Developer phase (iteration 1)
        logger.agent_start("developer (iteration 1)")
        logger.reasoning("developer", "Implementing feature extraction")
        logger.agent_end("developer", "Iteration 1")
        
        # Test runner
        logger.agent_start("test_runner")
        logger.tool_execution("pytest", "COMPLETE", "3 passed, 2 failed")
        logger.agent_end("test_runner", "Tests run")
        
        # Reviewer
        logger.agent_start("reviewer")
        failures = [{'file_path': 'src/test.py', 'failure_type': 'KeyError', 'root_cause': 'Missing', 'actionable_fix': 'Add'}]
        logger.reviewer_feedback("2/5 passed", failures, "Priority instruction")
        logger.agent_end("reviewer", "2 issues found")
        
        # Human
        logger.human_instruction("Fix the import")
        
        # End
        logger.sprint_end("SUCCESS")
        
        # Verify
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check all major sections present
        assert "🚀 SPRINT START" in content
        assert "→ ARCHITECT" in content
        assert "→ TESTER" in content
        assert "→ DEVELOPER" in content
        assert "→ TEST_RUNNER" in content
        assert "→ REVIEWER" in content
        assert "🛠️" in content  # Human intervention
        assert "✅ SPRINT END" in content
        
        # Check line count is reasonable
        lines = content.splitlines()
        assert len(lines) > 10, "Log should have multiple lines for full workflow"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

