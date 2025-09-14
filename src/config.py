"""
Configuration Management for the Code Review Agent

This module provides comprehensive configuration management using Pydantic models
to ensure type safety and validation. It handles loading configuration from YAML
files and provides convenient access to all settings throughout the application.

Key Features:
- Type-safe configuration with automatic validation
- YAML-based configuration files
- Environment variable support
- Default value management
- Configuration validation and error handling

Author: Atiksh Kotikalapudi
Version: 1.0.0
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """
    Configuration for AI models used in code analysis.
    
    This class manages settings for both Ollama (local AI models) and
    Hugging Face transformers, providing flexibility in AI model selection
    and configuration.
    
    Attributes:
        ollama (Dict[str, Any]): Ollama model settings including:
            - primary: Main model for general analysis (e.g., "llama3.2")
            - code_specialist: Specialized model for code analysis (e.g., "codellama")
            - host: Ollama server URL (e.g., "http://localhost:11434")
        huggingface (Dict[str, Any]): Hugging Face model settings including:
            - enabled: Whether to use Hugging Face models
            - model_name: Specific model to use
            - max_length: Maximum token length for generation
    """
    ollama: Dict[str, Any] = Field(default_factory=dict)
    huggingface: Dict[str, Any] = Field(default_factory=dict)

class AnalysisConfig(BaseModel):
    """
    Configuration for code analysis parameters and rules.
    
    This class defines what types of analysis to perform and the specific
    rules and thresholds to apply during code review.
    
    Attributes:
        languages (List[str]): Programming languages to analyze
        quality_checks (Dict[str, Any]): Quality analysis settings including:
            - complexity_threshold: Maximum cyclomatic complexity
            - max_function_length: Maximum function length in lines
            - max_file_length: Maximum file length in lines
        security_checks (Dict[str, Any]): Security analysis settings including:
            - enabled: Whether security scanning is active
            - severity_levels: Which severity levels to check
            - check_secrets: Whether to scan for hardcoded secrets
            - check_dependencies: Whether to check for vulnerable dependencies
    """
    languages: List[str] = Field(default_factory=list)
    quality_checks: Dict[str, Any] = Field(default_factory=dict)
    security_checks: Dict[str, Any] = Field(default_factory=dict)

class GitConfig(BaseModel):
    """
    Configuration for Git repository integration.
    
    This class manages Git-related features including repository analysis,
    commit tracking, and branch-specific settings.
    
    Attributes:
        enabled (bool): Whether Git integration is active
        auto_review_commits (bool): Whether to automatically review commits
        review_branches (List[str]): Specific branches to focus on
        exclude_patterns (List[str]): File patterns to exclude from analysis
    """
    enabled: bool = True
    auto_review_commits: bool = True
    review_branches: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)

class OutputConfig(BaseModel):
    """
    Configuration for output formats and destinations.
    
    This class controls how analysis results are presented and where they
    are sent, supporting multiple output formats simultaneously.
    
    Attributes:
        console (bool): Whether to display results in the console
        json_output (bool): Whether to generate JSON reports
        html (bool): Whether to generate HTML reports
        web_interface (bool): Whether to start the web interface
        port (int): Port number for the web interface
    """
    console: bool = True
    json_output: bool = Field(default=True, alias='json')
    html: bool = True
    web_interface: bool = True
    port: int = 5000

class CriteriaConfig(BaseModel):
    """
    Configuration for review criteria and standards.
    
    This class defines the specific criteria used to evaluate code quality,
    security, and performance, allowing customization for different teams
    and projects.
    
    Attributes:
        code_quality (List[str]): Code quality criteria to check
        security (List[str]): Security criteria to validate
        performance (List[str]): Performance criteria to analyze
    """
    code_quality: List[str] = Field(default_factory=list)
    security: List[str] = Field(default_factory=list)
    performance: List[str] = Field(default_factory=list)

class Config:
    """
    Main configuration class that loads and manages all application settings.
    
    This class serves as the central configuration manager, loading settings from
    YAML files and providing convenient access methods throughout the application.
    It uses Pydantic models for type safety and validation.
    
    Attributes:
        config_path (Path): Path to the configuration file
        models (ModelConfig): AI model configuration
        analysis (AnalysisConfig): Code analysis settings
        git (GitConfig): Git integration settings
        output (OutputConfig): Output format settings
        criteria (CriteriaConfig): Review criteria settings
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str): Path to the YAML configuration file
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
            ValidationError: If configuration values are invalid
        """
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self):
        """
        Load and parse configuration from YAML file.
        
        This method reads the YAML configuration file and parses it into
        structured Pydantic models with automatic validation.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
            ValidationError: If configuration values don't match expected types
        """
        # Check if configuration file exists
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        # Load YAML configuration
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Parse configuration sections into typed models
        # Each section is validated according to its Pydantic model
        self.models = ModelConfig(**config_data.get('models', {}))
        self.analysis = AnalysisConfig(**config_data.get('analysis', {}))
        self.git = GitConfig(**config_data.get('git', {}))
        self.output = OutputConfig(**config_data.get('output', {}))
        self.criteria = CriteriaConfig(**config_data.get('criteria', {}))
    
    @property
    def ollama_host(self) -> str:
        """
        Get the Ollama server host URL.
        
        Returns:
            str: The Ollama server URL, defaults to 'http://localhost:11434'
        """
        return self.models.ollama.get('host', 'http://localhost:11434')
    
    @property
    def primary_model(self) -> str:
        """
        Get the primary AI model name for general analysis.
        
        Returns:
            str: The primary model name, defaults to 'llama3.2'
        """
        return self.models.ollama.get('primary', 'llama3.2')
    
    @property
    def code_model(self) -> str:
        """
        Get the specialized code analysis model name.
        
        Returns:
            str: The code specialist model name, defaults to 'codellama'
        """
        return self.models.ollama.get('code_specialist', 'codellama')
    
    @property
    def supported_languages(self) -> List[str]:
        """
        Get the list of supported programming languages.
        
        Returns:
            List[str]: List of programming language names (e.g., ['python', 'javascript'])
        """
        return self.analysis.languages
    
    @property
    def security_enabled(self) -> bool:
        """
        Check if security scanning is enabled.
        
        Returns:
            bool: True if security scanning is active, False otherwise
        """
        return self.analysis.security_checks.get('enabled', True)
    
    @property
    def web_port(self) -> int:
        """
        Get the port number for the web interface.
        
        Returns:
            int: Port number, defaults to 5000
        """
        return self.output.port
