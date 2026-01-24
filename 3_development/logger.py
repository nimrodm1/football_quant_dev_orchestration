import logging
import os
from datetime import datetime
from pathlib import Path

class SprintLogger:
    """
    Lightweight logger for sprint execution.
    Logs to both console and file with timestamps.
    """
    
    def __init__(self, stage: str, log_dir: str = "../logs"):
        self.stage = stage
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.log_dir / f"{timestamp}_{stage}_sprint.log"
        
        # Set up logger
        self.logger = logging.getLogger(f"sprint_{stage}")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Formatter with timestamp
        formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        
        self.logger.addHandler(fh)
    
    def sprint_start(self):
        """Log sprint initialization"""
        self.logger.info(f"🚀 SPRINT START: {self.stage.upper()}")
    
    def sprint_end(self, status: str = "COMPLETE"):
        """Log sprint completion"""
        self.logger.info(f"✅ SPRINT END: {status}")
    
    def agent_start(self, agent_name: str):
        """Log agent starting"""
        self.logger.info(f"→ {agent_name.upper()} started")
    
    def agent_end(self, agent_name: str, details: str = ""):
        """Log agent completion"""
        if details:
            self.logger.info(f"✅ {agent_name.upper()} complete ({details})")
        else:
            self.logger.info(f"✅ {agent_name.upper()} complete")
    
    def reasoning(self, agent_name: str, reasoning_text: str):
        """Log agent's reasoning/strategy"""
        # Take first 200 chars to keep it concise
        summary = reasoning_text[:200].replace('\n', ' ').strip()
        if len(reasoning_text) > 200:
            summary += "..."
        self.logger.info(f"💭 [{agent_name}] {summary}")
    
    def iteration_summary(self, iteration: int, agent: str, files_modified: int, status: str):
        """Log iteration summary"""
        self.logger.info(f"📊 ITERATION {iteration} ({agent.upper()})")
        self.logger.info(f"├─ Files modified: {files_modified}")
        self.logger.info(f"└─ Status: {status}")
    
    def reviewer_feedback(self, summary: str, failures: list, priority_instructions: str):
        """Log structured reviewer feedback"""
        self.logger.info(f"❌ REVIEWER FEEDBACK")
        self.logger.info(f"├─ Summary: {summary}")
        
        if failures:
            for i, failure in enumerate(failures, 1):
                file_path = failure.get('file_path', 'Unknown')
                failure_type = failure.get('failure_type', 'Unknown')
                root_cause = failure.get('root_cause', 'Unknown')
                actionable_fix = failure.get('actionable_fix', 'No fix provided')
                
                self.logger.info(f"├─ [{failure_type}] {file_path}: {root_cause}")
                self.logger.info(f"│  └─ Fix: {actionable_fix}")
        
        if priority_instructions:
            self.logger.info(f"└─ Priority: {priority_instructions}")
    
    def human_instruction(self, instruction: str):
        """Log human intervention"""
        summary = instruction[:150].replace('\n', ' ').strip()
        if len(instruction) > 150:
            summary += "..."
        self.logger.info(f"🛠️  HUMAN INSTRUCTION: {summary}")
    
    def tool_execution(self, tool_name: str, status: str, details: str = ""):
        """Log tool execution"""
        if details:
            self.logger.info(f"🔧 Tool: {tool_name} | Status: {status} | {details}")
        else:
            self.logger.info(f"🔧 Tool: {tool_name} | Status: {status}")
    
    def error(self, message: str):
        """Log error"""
        self.logger.error(f"⚠️  ERROR: {message}")
    
    def info(self, message: str):
        """Log general info"""
        self.logger.info(message)
    
    def get_log_file(self) -> str:
        """Return the path to the log file"""
        return str(self.log_file)
