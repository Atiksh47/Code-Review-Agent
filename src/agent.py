"""
Core Code Review Agent Implementation

This module contains the main CodeReviewAgent class that orchestrates the entire
code review process. It combines multiple analysis engines (static analysis,
security scanning, AI-powered analysis) to provide comprehensive code review
capabilities.

Key Responsibilities:
- Initialize and coordinate all analysis components
- Orchestrate the code review workflow
- Integrate AI models for intelligent analysis
- Generate comprehensive reports
- Provide user-friendly result display

Author: Atiksh Kotikalapudi
Version: 1.0.0
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# AI/ML Libraries
from langchain_community.llms import Ollama              # Local AI model integration
from langchain_core.messages import HumanMessage, SystemMessage  # AI message handling
from langchain.prompts import PromptTemplate            # AI prompt management
from transformers import pipeline                       # Hugging Face transformers

# Internal modules
from config import Config                               # Configuration management
from code_analyzer import CodeAnalyzer                 # Static code analysis
from security_scanner import SecurityScanner           # Security vulnerability detection
from git_integration import GitIntegration             # Git repository analysis
from report_generator import ReportGenerator           # Report generation

# Initialize Rich console for beautiful terminal output
console = Console()

class CodeReviewAgent:
    """
    Main Code Review Agent class that orchestrates comprehensive code analysis.
    
    This class serves as the central coordinator for all code analysis activities.
    It initializes and manages multiple analysis engines, AI models, and reporting
    components to provide a complete code review solution.
    
    Attributes:
        config (Config): Configuration object containing all settings
        console (Console): Rich console for formatted output
        code_analyzer (CodeAnalyzer): Static code analysis engine
        security_scanner (SecurityScanner): Security vulnerability detector
        git_integration (GitIntegration): Git repository analysis tools
        report_generator (ReportGenerator): Report generation system
        ollama_llm (Ollama): Primary AI model for general analysis
        code_llm (Ollama): Specialized AI model for code analysis
        hf_pipeline: Hugging Face transformers pipeline (optional)
    """
    
    def __init__(self, config: Config):
        """
        Initialize the Code Review Agent with all required components.
        
        This constructor sets up the entire analysis pipeline including:
        - AI model initialization (Ollama, Hugging Face)
        - Analysis engine setup (code, security, Git, reporting)
        - Prompt template creation for AI analysis
        
        Args:
            config (Config): Configuration object with all settings
        """
        self.config = config
        self.console = Console()
        
        # Initialize AI models for intelligent analysis
        self._init_models()
        
        # Initialize all analysis components
        self.code_analyzer = CodeAnalyzer(config)        # Static code analysis
        self.security_scanner = SecurityScanner(config)   # Security scanning
        self.git_integration = GitIntegration(config)     # Git repository analysis
        self.report_generator = ReportGenerator(config)   # Report generation
        
        # Initialize AI prompt templates for consistent analysis
        self._init_prompts()
    
    def _init_models(self):
        """
        Initialize AI models for intelligent code analysis.
        
        This method sets up the AI infrastructure including:
        - Primary Ollama model for general analysis tasks
        - Specialized code model for code-specific analysis
        - Optional Hugging Face transformers for specific tasks
        
        The models are configured based on settings in config.yaml and run
        locally to ensure privacy and performance.
        
        Raises:
            Exception: If model initialization fails (e.g., Ollama not running)
        """
        try:
            # Initialize primary Ollama model for general analysis
            # This model handles overall code quality and best practices
            self.ollama_llm = Ollama(
                model=self.config.primary_model,        # e.g., "llama3.2"
                base_url=self.config.ollama_host        # e.g., "http://localhost:11434"
            )
            
            # Initialize specialized code model for code-specific analysis
            # This model is optimized for understanding programming languages
            self.code_llm = Ollama(
                model=self.config.code_model,           # e.g., "codellama"
                base_url=self.config.ollama_host
            )
            
            # Initialize Hugging Face model for specific tasks (optional)
            # This provides additional AI capabilities for specialized analysis
            if self.config.models.huggingface.get('enabled', False):
                self.hf_pipeline = pipeline(
                    "text-generation",
                    model=self.config.models.huggingface.get('model_name', 'microsoft/DialoGPT-medium'),
                    max_length=self.config.models.huggingface.get('max_length', 512)
                )
            else:
                self.hf_pipeline = None
            
            self.console.print("✅ AI models initialized", style="green")
            
        except Exception as e:
            # If AI models fail to initialize, the system can still work
            # with static analysis tools, but AI features will be unavailable
            self.console.print(f"❌ Error initializing models: {e}", style="red")
            raise
    
    def _init_prompts(self):
        """Initialize review prompts"""
        self.code_quality_prompt = PromptTemplate(
            input_variables=["code", "language", "file_path"],
            template="""
            You are an expert code reviewer. Analyze the following {language} code for quality issues:
            
            File: {file_path}
            Code:
            {code}
            
            Please provide:
            1. Code quality issues (complexity, readability, maintainability)
            2. Best practices violations
            3. Performance concerns
            4. Improvement suggestions
            
            Format your response as JSON with categories: quality_issues, best_practices, performance, suggestions
            """
        )
        
        self.security_prompt = PromptTemplate(
            input_variables=["code", "language", "file_path"],
            template="""
            You are a security expert. Analyze the following {language} code for security vulnerabilities:
            
            File: {file_path}
            Code:
            {code}
            
            Look for:
            1. Hardcoded secrets or credentials
            2. SQL injection vulnerabilities
            3. XSS vulnerabilities
            4. Input validation issues
            5. Authentication/authorization problems
            6. Insecure cryptographic practices
            
            Format your response as JSON with severity levels: HIGH, MEDIUM, LOW
            """
        )
    
    async def review_code(self, path: Path) -> Dict[str, Any]:
        """
        Main method to perform comprehensive code review.
        
        This is the primary entry point for code analysis. It orchestrates the entire
        review process by:
        1. Discovering all code files in the target path
        2. Running multiple analysis types on each file
        3. Aggregating results and generating summary statistics
        4. Returning structured results for display or further processing
        
        Args:
            path (Path): Path to file or directory to analyze
            
        Returns:
            Dict[str, Any]: Comprehensive review results including:
                - timestamp: When the analysis was performed
                - path: Original path analyzed
                - files_reviewed: Number of files processed
                - issues_found: Total issues discovered
                - security_issues: Security vulnerabilities found
                - quality_issues: Code quality problems found
                - performance_issues: Performance bottlenecks found
                - files: Detailed results for each file
                - summary: Aggregated statistics and breakdown
        """
        self.console.print(f"🔍 Starting code review for: {path}", style="blue")
        
        # Initialize comprehensive results structure
        # This will hold all analysis results and metadata
        results = {
            "timestamp": datetime.now().isoformat(),    # Analysis timestamp
            "path": str(path),                          # Original target path
            "files_reviewed": 0,                       # Counter for processed files
            "issues_found": 0,                         # Total issues discovered
            "security_issues": 0,                      # Security vulnerabilities
            "quality_issues": 0,                       # Code quality problems
            "performance_issues": 0,                   # Performance issues
            "files": []                                # Detailed file results
        }
        
        try:
            # Step 1: Discover all files to analyze
            # This handles both single files and directory trees
            files_to_review = self._get_files_to_review(path)
            self.console.print(f"📁 Found {len(files_to_review)} files to review", style="blue")
            
            # Step 2: Analyze each file individually
            # This runs all analysis types (quality, security, performance, AI)
            for file_path in files_to_review:
                self.console.print(f"🔍 Reviewing: {file_path.name}", style="yellow")
                
                # Perform comprehensive analysis on this file
                file_results = await self._review_file(file_path)
                
                # Add file results to overall results
                results["files"].append(file_results)
                results["files_reviewed"] += 1
                
                # Aggregate issue counts for summary statistics
                results["issues_found"] += len(file_results.get("issues", []))
                results["security_issues"] += len(file_results.get("security_issues", []))
                results["quality_issues"] += len(file_results.get("quality_issues", []))
                results["performance_issues"] += len(file_results.get("performance_issues", []))
            
            # Step 3: Generate comprehensive summary
            # This creates high-level statistics and breakdowns
            results["summary"] = self._generate_summary(results)
            
            self.console.print("✅ Code review completed", style="green")
            return results
            
        except Exception as e:
            # Handle any errors during the review process gracefully
            self.console.print(f"❌ Error during code review: {e}", style="red")
            results["error"] = str(e)
            return results
    
    def _get_files_to_review(self, path: Path) -> List[Path]:
        """Get list of files to review"""
        files = []
        
        if path.is_file():
            if self._should_review_file(path):
                files.append(path)
        else:
            for file_path in path.rglob("*"):
                if file_path.is_file() and self._should_review_file(file_path):
                    files.append(file_path)
        
        return files
    
    def _should_review_file(self, file_path: Path) -> bool:
        """Check if file should be reviewed"""
        # Check file extension
        if file_path.suffix.lower() not in ['.py', '.js', '.java', '.cpp', '.go', '.rs']:
            return False
        
        # Check exclude patterns
        for pattern in self.config.git.exclude_patterns:
            if file_path.match(pattern):
                return False
        
        return True
    
    async def _review_file(self, file_path: Path) -> Dict[str, Any]:
        """Review a single file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine language
            language = self._get_language(file_path)
            
            # Initialize file results
            file_results = {
                "file_path": str(file_path),
                "language": language,
                "size": len(content),
                "lines": len(content.splitlines()),
                "issues": [],
                "security_issues": [],
                "quality_issues": [],
                "performance_issues": [],
                "suggestions": []
            }
            
            # Code quality analysis
            quality_issues = await self._analyze_code_quality(content, language, file_path)
            file_results["quality_issues"] = quality_issues
            file_results["issues"].extend(quality_issues)
            
            # Security analysis
            if self.config.security_enabled:
                security_issues = await self._analyze_security(content, language, file_path)
                file_results["security_issues"] = security_issues
                file_results["issues"].extend(security_issues)
            
            # Performance analysis
            performance_issues = await self._analyze_performance(content, language, file_path)
            file_results["performance_issues"] = performance_issues
            file_results["issues"].extend(performance_issues)
            
            return file_results
            
        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
                "issues": []
            }
    
    def _get_language(self, file_path: Path) -> str:
        """Determine programming language from file extension"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust'
        }
        return ext_to_lang.get(file_path.suffix.lower(), 'unknown')
    
    async def _analyze_code_quality(self, content: str, language: str, file_path: Path) -> List[Dict]:
        """Analyze code quality using AI"""
        try:
            # Use static analysis tools first
            static_issues = self.code_analyzer.analyze(content, language, file_path)
            
            # Use AI for additional analysis
            prompt = self.code_quality_prompt.format(
                code=content[:2000],  # Limit content size
                language=language,
                file_path=str(file_path)
            )
            
            response = await self._call_ollama(prompt)
            ai_issues = self._parse_ai_response(response, "quality")
            
            return static_issues + ai_issues
            
        except Exception as e:
            self.console.print(f"⚠️ Error in quality analysis: {e}", style="yellow")
            return []
    
    async def _analyze_security(self, content: str, language: str, file_path: Path) -> List[Dict]:
        """Analyze security using AI and tools"""
        try:
            # Use security scanning tools
            security_issues = self.security_scanner.scan(content, language, file_path)
            
            # Use AI for additional security analysis
            prompt = self.security_prompt.format(
                code=content[:2000],
                language=language,
                file_path=str(file_path)
            )
            
            response = await self._call_ollama(prompt)
            ai_issues = self._parse_ai_response(response, "security")
            
            return security_issues + ai_issues
            
        except Exception as e:
            self.console.print(f"⚠️ Error in security analysis: {e}", style="yellow")
            return []
    
    async def _analyze_performance(self, content: str, language: str, file_path: Path) -> List[Dict]:
        """Analyze performance using AI"""
        try:
            # Use static analysis for performance
            performance_issues = self.code_analyzer.analyze_performance(content, language, file_path)
            
            return performance_issues
            
        except Exception as e:
            self.console.print(f"⚠️ Error in performance analysis: {e}", style="yellow")
            return []
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama model"""
        try:
            # Use asyncio to run the synchronous call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.ollama_llm(prompt)
            )
            return response
        except Exception as e:
            self.console.print(f"⚠️ Error calling Ollama: {e}", style="yellow")
            return ""
    
    def _parse_ai_response(self, response: str, analysis_type: str) -> List[Dict]:
        """Parse AI response into structured format"""
        try:
            # Try to parse as JSON
            if response.strip().startswith('{'):
                data = json.loads(response)
                return data.get('issues', [])
            else:
                # Fallback: create basic issue from text
                return [{
                    "type": analysis_type,
                    "severity": "MEDIUM",
                    "message": response[:200],
                    "source": "AI"
                }]
        except:
            return []
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of review results"""
        return {
            "total_files": results["files_reviewed"],
            "total_issues": results["issues_found"],
            "security_issues": results["security_issues"],
            "quality_issues": results["quality_issues"],
            "performance_issues": results["performance_issues"],
            "severity_breakdown": self._get_severity_breakdown(results)
        }
    
    def _get_severity_breakdown(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Get breakdown of issues by severity"""
        breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for file_result in results["files"]:
            for issue in file_result.get("issues", []):
                severity = issue.get("severity", "MEDIUM")
                breakdown[severity] = breakdown.get(severity, 0) + 1
        
        return breakdown
    
    def display_results(self, results: Dict[str, Any]):
        """Display results in console"""
        # Create summary table
        table = Table(title="Code Review Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Files Reviewed", str(results["files_reviewed"]))
        table.add_row("Total Issues", str(results["issues_found"]))
        table.add_row("Security Issues", str(results["security_issues"]))
        table.add_row("Quality Issues", str(results["quality_issues"]))
        table.add_row("Performance Issues", str(results["performance_issues"]))
        
        self.console.print(table)
        
        # Display detailed results for each file
        for file_result in results["files"]:
            if file_result.get("issues"):
                self._display_file_results(file_result)
    
    def _display_file_results(self, file_result: Dict[str, Any]):
        """Display results for a single file"""
        file_path = file_result["file_path"]
        issues = file_result.get("issues", [])
        
        if not issues:
            return
        
        # Create file panel
        content = f"Found {len(issues)} issues in {file_path}\n\n"
        
        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "MEDIUM")
            message = issue.get("message", "No message")
            content += f"{i}. [{severity}] {message}\n"
        
        panel = Panel(
            content,
            title=f"📁 {Path(file_path).name}",
            border_style="red" if any(i.get("severity") == "HIGH" for i in issues) else "yellow"
        )
        
        self.console.print(panel)
