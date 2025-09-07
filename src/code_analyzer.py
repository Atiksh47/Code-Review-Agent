"""
Code Analyzer module for static code analysis
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    type: str
    severity: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    file_path: Optional[str] = None

class CodeAnalyzer:
    """Static code analyzer for various programming languages"""
    
    def __init__(self, config):
        self.config = config
        self.complexity_threshold = config.analysis.quality_checks.get('complexity_threshold', 10)
        self.max_function_length = config.analysis.quality_checks.get('max_function_length', 50)
        self.max_file_length = config.analysis.quality_checks.get('max_file_length', 500)
    
    def analyze(self, content: str, language: str, file_path: Path) -> List[Dict]:
        """Analyze code for quality issues"""
        issues = []
        
        if language == 'python':
            issues.extend(self._analyze_python(content, file_path))
        elif language == 'javascript':
            issues.extend(self._analyze_javascript(content, file_path))
        elif language == 'java':
            issues.extend(self._analyze_java(content, file_path))
        elif language == 'cpp':
            issues.extend(self._analyze_cpp(content, file_path))
        elif language == 'go':
            issues.extend(self._analyze_go(content, file_path))
        elif language == 'rust':
            issues.extend(self._analyze_rust(content, file_path))
        
        # General analysis
        issues.extend(self._analyze_general(content, file_path))
        
        return [self._issue_to_dict(issue) for issue in issues]
    
    def analyze_performance(self, content: str, language: str, file_path: Path) -> List[Dict]:
        """Analyze code for performance issues"""
        issues = []
        
        if language == 'python':
            issues.extend(self._analyze_python_performance(content, file_path))
        elif language == 'javascript':
            issues.extend(self._analyze_javascript_performance(content, file_path))
        
        return [self._issue_to_dict(issue) for issue in issues]
    
    def _analyze_python(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze Python code"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Check file length
            lines = content.splitlines()
            if len(lines) > self.max_file_length:
                issues.append(CodeIssue(
                    type="quality",
                    severity="MEDIUM",
                    message=f"File is too long ({len(lines)} lines). Consider splitting into smaller modules.",
                    file_path=str(file_path)
                ))
            
            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues.extend(self._analyze_python_function(node, file_path))
                elif isinstance(node, ast.ClassDef):
                    issues.extend(self._analyze_python_class(node, file_path))
        
        except SyntaxError as e:
            issues.append(CodeIssue(
                type="quality",
                severity="HIGH",
                message=f"Syntax error: {e.msg}",
                line=e.lineno,
                column=e.offset,
                file_path=str(file_path)
            ))
        
        return issues
    
    def _analyze_python_function(self, node: ast.FunctionDef, file_path: Path) -> List[CodeIssue]:
        """Analyze a Python function"""
        issues = []
        
        # Check function length
        if node.end_lineno and node.lineno:
            function_length = node.end_lineno - node.lineno
            if function_length > self.max_function_length:
                issues.append(CodeIssue(
                    type="quality",
                    severity="MEDIUM",
                    message=f"Function '{node.name}' is too long ({function_length} lines). Consider refactoring.",
                    line=node.lineno,
                    file_path=str(file_path)
                ))
        
        # Check complexity (simplified)
        complexity = self._calculate_complexity(node)
        if complexity > self.complexity_threshold:
            issues.append(CodeIssue(
                type="quality",
                severity="MEDIUM",
                message=f"Function '{node.name}' has high complexity ({complexity}). Consider simplifying.",
                line=node.lineno,
                file_path=str(file_path)
            ))
        
        # Check for long parameter lists
        if len(node.args.args) > 5:
            issues.append(CodeIssue(
                type="quality",
                severity="LOW",
                message=f"Function '{node.name}' has many parameters ({len(node.args.args)}). Consider using a data structure.",
                line=node.lineno,
                file_path=str(file_path)
            ))
        
        return issues
    
    def _analyze_python_class(self, node: ast.ClassDef, file_path: Path) -> List[CodeIssue]:
        """Analyze a Python class"""
        issues = []
        
        # Check for missing docstrings
        if not self._has_docstring(node):
            issues.append(CodeIssue(
                type="quality",
                severity="LOW",
                message=f"Class '{node.name}' is missing a docstring.",
                line=node.lineno,
                file_path=str(file_path)
            ))
        
        return issues
    
    def _analyze_python_performance(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze Python code for performance issues"""
        issues = []
        
        # Check for inefficient patterns
        patterns = [
            (r'for\s+\w+\s+in\s+range\(len\([^)]+\)\)', "Use enumerate() instead of range(len())"),
            (r'\.append\([^)]*\)\s*$', "Consider using list comprehension for better performance"),
            (r'import\s+\*', "Avoid wildcard imports for better performance"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="performance",
                    severity="LOW",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_javascript(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze JavaScript code"""
        issues = []
        
        # Check for common issues
        patterns = [
            (r'var\s+\w+', "Consider using 'let' or 'const' instead of 'var'"),
            (r'==\s*[^=]', "Use strict equality (===) instead of loose equality (=)"),
            (r'console\.log\(', "Remove console.log statements from production code"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="quality",
                    severity="LOW",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_javascript_performance(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze JavaScript code for performance issues"""
        issues = []
        
        # Check for performance anti-patterns
        patterns = [
            (r'document\.getElementById\([^)]+\)\.innerHTML\s*=', "Use textContent instead of innerHTML for better performance"),
            (r'for\s*\(\s*var\s+\w+\s*=\s*0', "Use let instead of var in for loops"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="performance",
                    severity="MEDIUM",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_java(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze Java code"""
        issues = []
        
        # Check for common Java issues
        patterns = [
            (r'System\.out\.print', "Use proper logging instead of System.out.print"),
            (r'catch\s*\(\s*Exception\s+\w+\s*\)', "Avoid catching generic Exception, be more specific"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="quality",
                    severity="MEDIUM",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_cpp(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze C++ code"""
        issues = []
        
        # Check for common C++ issues
        patterns = [
            (r'using namespace std;', "Avoid 'using namespace std' in header files"),
            (r'#include\s*<iostream>', "Consider using specific headers instead of iostream"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="quality",
                    severity="LOW",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_go(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze Go code"""
        issues = []
        
        # Check for Go best practices
        patterns = [
            (r'panic\s*\(', "Avoid using panic, return errors instead"),
            (r'fmt\.Print', "Use proper logging instead of fmt.Print"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="quality",
                    severity="MEDIUM",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_rust(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Analyze Rust code"""
        issues = []
        
        # Check for Rust best practices
        patterns = [
            (r'unwrap\s*\(', "Consider using proper error handling instead of unwrap()"),
            (r'println!\s*\(', "Use proper logging instead of println! in production"),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    type="quality",
                    severity="MEDIUM",
                    message=message,
                    line=line_num,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _analyze_general(self, content: str, file_path: Path) -> List[CodeIssue]:
        """General code analysis applicable to all languages"""
        issues = []
        
        lines = content.splitlines()
        
        # Check for very long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(CodeIssue(
                    type="quality",
                    severity="LOW",
                    message=f"Line {i} is too long ({len(line)} characters). Consider breaking it up.",
                    line=i,
                    file_path=str(file_path)
                ))
        
        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                issues.append(CodeIssue(
                    type="quality",
                    severity="LOW",
                    message=f"Line {i} has trailing whitespace.",
                    line=i,
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _has_docstring(self, node) -> bool:
        """Check if a node has a docstring"""
        if not node.body:
            return False
        
        first_stmt = node.body[0]
        return (isinstance(first_stmt, ast.Expr) and 
                isinstance(first_stmt.value, ast.Constant) and 
                isinstance(first_stmt.value.value, str))
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict:
        """Convert CodeIssue to dictionary"""
        return {
            "type": issue.type,
            "severity": issue.severity,
            "message": issue.message,
            "line": issue.line,
            "column": issue.column,
            "file_path": issue.file_path,
            "source": "static_analysis"
        }
