"""
Code Analyzer - Finds issues in code
"""
import logging
import re

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Performs basic static code analysis"""
    
    def __init__(self):
        self.patterns = {
            "console_log": re.compile(r'console\.(log|debug|warn|error)'),
            "todo": re.compile(r'(TODO|FIXME|HACK|XXX)', re.IGNORECASE),
            "hardcoded_password": re.compile(r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
        }
        logger.info("Code Analyzer initialized")
    
    def analyze_code(self, code_text):
        """
        Analyze code and find issues
        
        Args:
            code_text: String of code to analyze
        
        Returns:
            List of issues found
        """
        issues = []
        
        if not code_text:
            return issues
        
        lines = code_text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for console.log
            if self.patterns["console_log"].search(line):
                issues.append({
                    "type": "console_log",
                    "severity": "low",
                    "message": "Console log statement found",
                    "line": line_num,
                    "code": line.strip()
                })
            
            # Check for TODOs
            if self.patterns["todo"].search(line):
                issues.append({
                    "type": "todo",
                    "severity": "info",
                    "message": "TODO/FIXME comment found",
                    "line": line_num,
                    "code": line.strip()
                })
            
            # Check for hardcoded passwords
            if self.patterns["hardcoded_password"].search(line):
                issues.append({
                    "type": "security",
                    "severity": "high",
                    "message": "Possible hardcoded password detected",
                    "line": line_num,
                    "code": line.strip()
                })
            
            # Check line length
            if len(line) > 120:
                issues.append({
                    "type": "style",
                    "severity": "low",
                    "message": f"Line too long ({len(line)} characters)",
                    "line": line_num,
                    "code": line[:50].strip() + "..."
                })
        
        logger.info(f"Found {len(issues)} issues in code")
        return issues