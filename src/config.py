"""
Configuration management for the Code Review Agent
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """AI model configuration"""
    ollama: Dict[str, Any] = Field(default_factory=dict)
    huggingface: Dict[str, Any] = Field(default_factory=dict)

class AnalysisConfig(BaseModel):
    """Code analysis configuration"""
    languages: List[str] = Field(default_factory=list)
    quality_checks: Dict[str, Any] = Field(default_factory=dict)
    security_checks: Dict[str, Any] = Field(default_factory=dict)

class GitConfig(BaseModel):
    """Git integration configuration"""
    enabled: bool = True
    auto_review_commits: bool = True
    review_branches: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)

class OutputConfig(BaseModel):
    """Output configuration"""
    console: bool = True
    json_output: bool = Field(default=True, alias='json')
    html: bool = True
    web_interface: bool = True
    port: int = 5000

class CriteriaConfig(BaseModel):
    """Review criteria configuration"""
    code_quality: List[str] = Field(default_factory=list)
    security: List[str] = Field(default_factory=list)
    performance: List[str] = Field(default_factory=list)

class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Parse configuration sections
        self.models = ModelConfig(**config_data.get('models', {}))
        self.analysis = AnalysisConfig(**config_data.get('analysis', {}))
        self.git = GitConfig(**config_data.get('git', {}))
        self.output = OutputConfig(**config_data.get('output', {}))
        self.criteria = CriteriaConfig(**config_data.get('criteria', {}))
    
    @property
    def ollama_host(self) -> str:
        """Get Ollama host URL"""
        return self.models.ollama.get('host', 'http://localhost:11434')
    
    @property
    def primary_model(self) -> str:
        """Get primary Ollama model"""
        return self.models.ollama.get('primary', 'llama3.2')
    
    @property
    def code_model(self) -> str:
        """Get code specialist model"""
        return self.models.ollama.get('code_specialist', 'codellama')
    
    @property
    def supported_languages(self) -> List[str]:
        """Get supported programming languages"""
        return self.analysis.languages
    
    @property
    def security_enabled(self) -> bool:
        """Check if security scanning is enabled"""
        return self.analysis.security_checks.get('enabled', True)
    
    @property
    def web_port(self) -> int:
        """Get web interface port"""
        return self.output.port
