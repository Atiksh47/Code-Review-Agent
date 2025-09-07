"""
Security Scanner module for detecting security vulnerabilities
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    """Represents a security issue found during scanning"""
    type: str
    severity: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    file_path: Optional[str] = None
    cwe_id: Optional[str] = None

class SecurityScanner:
    """Security vulnerability scanner for various programming languages"""
    
    def __init__(self, config):
        self.config = config
        self.check_secrets = config.analysis.security_checks.get('check_secrets', True)
        self.check_dependencies = config.analysis.security_checks.get('check_dependencies', True)
        
        # Initialize security patterns
        self._init_security_patterns()
    
    def _init_security_patterns(self):
        """Initialize security vulnerability patterns"""
        self.patterns = {
            'secrets': [
                # API Keys
                (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'HIGH', 'CWE-798', 'Hardcoded API key detected'),
                (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'HIGH', 'CWE-798', 'Hardcoded secret key detected'),
                (r'(?i)(access[_-]?token|accesstoken)\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'HIGH', 'CWE-798', 'Hardcoded access token detected'),
                
                # Passwords
                (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^"\'\s]{6,}["\']?', 'HIGH', 'CWE-798', 'Hardcoded password detected'),
                (r'(?i)(db[_-]?password|database[_-]?password)\s*[=:]\s*["\']?[^"\'\s]{6,}["\']?', 'HIGH', 'CWE-798', 'Hardcoded database password detected'),
                
                # Database URLs
                (r'(?i)(mongodb|mysql|postgresql)://[^:]+:[^@]+@', 'HIGH', 'CWE-798', 'Database credentials in connection string'),
                
                # JWT Tokens
                (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', 'MEDIUM', 'CWE-798', 'JWT token detected (may contain sensitive data)'),
            ],
            
            'sql_injection': [
                (r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*\+.*["\']', 'HIGH', 'CWE-89', 'Potential SQL injection vulnerability'),
                (r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*\$.*["\']', 'HIGH', 'CWE-89', 'Potential SQL injection vulnerability'),
                (r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*%s.*["\']', 'HIGH', 'CWE-89', 'Potential SQL injection vulnerability'),
                (r'(?i)execute\s*\(\s*["\'][^"\']*\+[^"\']*["\']', 'HIGH', 'CWE-89', 'Dynamic SQL execution with string concatenation'),
            ],
            
            'xss': [
                (r'(?i)innerHTML\s*=\s*[^;]*\+', 'MEDIUM', 'CWE-79', 'Potential XSS vulnerability with innerHTML'),
                (r'(?i)document\.write\s*\([^)]*\+', 'MEDIUM', 'CWE-79', 'Potential XSS vulnerability with document.write'),
                (r'(?i)eval\s*\([^)]*\+', 'HIGH', 'CWE-95', 'Use of eval() with dynamic content'),
            ],
            
            'authentication': [
                (r'(?i)password\s*=\s*["\'][^"\']{1,7}["\']', 'MEDIUM', 'CWE-521', 'Weak password (too short)'),
                (r'(?i)if\s*\(\s*password\s*==\s*["\'][^"\']+["\']', 'HIGH', 'CWE-798', 'Hardcoded password comparison'),
                (r'(?i)admin\s*=\s*["\'][^"\']+["\']', 'MEDIUM', 'CWE-798', 'Hardcoded admin credentials'),
            ],
            
            'crypto': [
                (r'(?i)md5\s*\(', 'MEDIUM', 'CWE-327', 'MD5 is cryptographically broken, use SHA-256 or better'),
                (r'(?i)sha1\s*\(', 'MEDIUM', 'CWE-327', 'SHA-1 is cryptographically broken, use SHA-256 or better'),
                (r'(?i)des\s*\(', 'HIGH', 'CWE-327', 'DES is cryptographically broken, use AES'),
                (r'(?i)random\s*\(\s*\)', 'MEDIUM', 'CWE-330', 'Use cryptographically secure random number generator'),
            ],
            
            'file_operations': [
                (r'(?i)open\s*\([^)]*\+[^)]*\)', 'MEDIUM', 'CWE-22', 'Potential path traversal vulnerability'),
                (r'(?i)file_get_contents\s*\([^)]*\+[^)]*\)', 'MEDIUM', 'CWE-22', 'Potential path traversal vulnerability'),
                (r'(?i)include\s*\([^)]*\+[^)]*\)', 'HIGH', 'CWE-94', 'Potential code injection vulnerability'),
                (r'(?i)require\s*\([^)]*\+[^)]*\)', 'HIGH', 'CWE-94', 'Potential code injection vulnerability'),
            ],
            
            'network': [
                (r'(?i)http://[^"\'\s]+', 'MEDIUM', 'CWE-319', 'Insecure HTTP connection detected'),
                (r'(?i)ftp://[^"\'\s]+', 'MEDIUM', 'CWE-319', 'Insecure FTP connection detected'),
                (r'(?i)curl\s+[^"\']*http://', 'MEDIUM', 'CWE-319', 'Insecure HTTP request with curl'),
            ],
            
            'input_validation': [
                (r'(?i)input\s*\([^)]*\)\s*(?!\.strip\(\))', 'LOW', 'CWE-20', 'Input not validated or sanitized'),
                (r'(?i)raw_input\s*\([^)]*\)\s*(?!\.strip\(\))', 'LOW', 'CWE-20', 'Input not validated or sanitized'),
                (r'(?i)request\.get\s*\([^)]*\)\s*(?!\.strip\(\))', 'LOW', 'CWE-20', 'Request parameter not validated'),
            ]
        }
    
    def scan(self, content: str, language: str, file_path: Path) -> List[Dict]:
        """Scan code for security vulnerabilities"""
        issues = []
        
        # Scan for different types of vulnerabilities
        for category, patterns in self.patterns.items():
            for pattern, severity, cwe_id, message in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(SecurityIssue(
                        type='security',
                        severity=severity,
                        message=message,
                        line=line_num,
                        file_path=str(file_path),
                        cwe_id=cwe_id
                    ))
        
        # Language-specific security checks
        if language == 'python':
            issues.extend(self._scan_python_security(content, file_path))
        elif language == 'javascript':
            issues.extend(self._scan_javascript_security(content, file_path))
        elif language == 'java':
            issues.extend(self._scan_java_security(content, file_path))
        
        # Check for secrets if enabled
        if self.check_secrets:
            issues.extend(self._scan_for_secrets(content, file_path))
        
        return [self._issue_to_dict(issue) for issue in issues]
    
    def _scan_python_security(self, content: str, file_path: Path) -> List[SecurityIssue]:
        """Python-specific security checks"""
        issues = []
        
        # Check for dangerous functions
        dangerous_functions = [
            (r'eval\s*\(', 'HIGH', 'CWE-95', 'Use of eval() is dangerous'),
            (r'exec\s*\(', 'HIGH', 'CWE-95', 'Use of exec() is dangerous'),
            (r'__import__\s*\(', 'HIGH', 'CWE-95', 'Dynamic import can be dangerous'),
            (r'pickle\.loads?\s*\(', 'HIGH', 'CWE-502', 'Pickle deserialization can be dangerous'),
            (r'yaml\.load\s*\(', 'MEDIUM', 'CWE-502', 'YAML.load() can be dangerous, use yaml.safe_load()'),
        ]
        
        for pattern, severity, cwe_id, message in dangerous_functions:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    type='security',
                    severity=severity,
                    message=message,
                    line=line_num,
                    file_path=str(file_path),
                    cwe_id=cwe_id
                ))
        
        return issues
    
    def _scan_javascript_security(self, content: str, file_path: Path) -> List[SecurityIssue]:
        """JavaScript-specific security checks"""
        issues = []
        
        # Check for dangerous functions
        dangerous_functions = [
            (r'eval\s*\(', 'HIGH', 'CWE-95', 'Use of eval() is dangerous'),
            (r'Function\s*\(', 'HIGH', 'CWE-95', 'Use of Function constructor is dangerous'),
            (r'setTimeout\s*\([^,]*["\'][^"\']*\+', 'MEDIUM', 'CWE-95', 'Dynamic code execution with setTimeout'),
            (r'setInterval\s*\([^,]*["\'][^"\']*\+', 'MEDIUM', 'CWE-95', 'Dynamic code execution with setInterval'),
        ]
        
        for pattern, severity, cwe_id, message in dangerous_functions:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    type='security',
                    severity=severity,
                    message=message,
                    line=line_num,
                    file_path=str(file_path),
                    cwe_id=cwe_id
                ))
        
        return issues
    
    def _scan_java_security(self, content: str, file_path: Path) -> List[SecurityIssue]:
        """Java-specific security checks"""
        issues = []
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'Runtime\.getRuntime\(\)\.exec\s*\(', 'HIGH', 'CWE-78', 'Command injection vulnerability'),
            (r'ProcessBuilder\s*\([^)]*\+', 'HIGH', 'CWE-78', 'Command injection vulnerability'),
            (r'Class\.forName\s*\([^)]*\+', 'MEDIUM', 'CWE-95', 'Dynamic class loading can be dangerous'),
        ]
        
        for pattern, severity, cwe_id, message in dangerous_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    type='security',
                    severity=severity,
                    message=message,
                    line=line_num,
                    file_path=str(file_path),
                    cwe_id=cwe_id
                ))
        
        return issues
    
    def _scan_for_secrets(self, content: str, file_path: Path) -> List[SecurityIssue]:
        """Scan for hardcoded secrets and credentials"""
        issues = []
        
        # Common secret patterns
        secret_patterns = [
            # AWS
            (r'AKIA[0-9A-Z]{16}', 'HIGH', 'CWE-798', 'AWS Access Key ID detected'),
            (r'[0-9a-zA-Z/+]{40}', 'HIGH', 'CWE-798', 'AWS Secret Access Key detected'),
            
            # GitHub
            (r'ghp_[0-9a-zA-Z]{36}', 'HIGH', 'CWE-798', 'GitHub Personal Access Token detected'),
            (r'gho_[0-9a-zA-Z]{36}', 'HIGH', 'CWE-798', 'GitHub OAuth Token detected'),
            
            # Google
            (r'AIza[0-9A-Za-z_-]{35}', 'HIGH', 'CWE-798', 'Google API Key detected'),
            
            # Slack
            (r'xoxb-[0-9]{11}-[0-9]{11}-[0-9a-zA-Z]{24}', 'HIGH', 'CWE-798', 'Slack Bot Token detected'),
            
            # Generic tokens
            (r'[0-9a-f]{32}', 'MEDIUM', 'CWE-798', 'Potential MD5 hash or token detected'),
            (r'[0-9a-f]{40}', 'MEDIUM', 'CWE-798', 'Potential SHA-1 hash or token detected'),
        ]
        
        for pattern, severity, cwe_id, message in secret_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    type='security',
                    severity=severity,
                    message=message,
                    line=line_num,
                    file_path=str(file_path),
                    cwe_id=cwe_id
                ))
        
        return issues
    
    def _issue_to_dict(self, issue: SecurityIssue) -> Dict:
        """Convert SecurityIssue to dictionary"""
        return {
            "type": issue.type,
            "severity": issue.severity,
            "message": issue.message,
            "line": issue.line,
            "column": issue.column,
            "file_path": issue.file_path,
            "cwe_id": issue.cwe_id,
            "source": "security_scanner"
        }
