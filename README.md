# 🤖 AI-Powered Code Review Agent

An intelligent code review system that analyzes code for quality, security, and performance issues using local AI models. The agent provides comprehensive analysis with both static analysis tools and AI-powered insights.

## ✨ Features

- **Multi-language Support**: Python, JavaScript, Java, C++, Go, Rust, and more
- **AI-Powered Analysis**: Uses Ollama with local models for intelligent code review
- **Security Scanning**: Detects vulnerabilities, hardcoded secrets, and security anti-patterns
- **Code Quality Analysis**: Identifies code smells, complexity issues, and best practice violations
- **Performance Analysis**: Finds performance bottlenecks and optimization opportunities
- **Git Integration**: Analyzes Git repositories, commits, and branch information
- **Multiple Output Formats**: JSON, HTML, and console reports
- **Web Interface**: Modern web-based UI for interactive code review
- **Configurable**: Highly customizable through YAML configuration

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Git (for repository analysis)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd code_review_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install and start Ollama:
```bash
# Install Ollama (see https://ollama.ai/)
ollama pull llama3.2
ollama pull codellama
```

### Usage

#### Command Line Interface

```bash
# Review a single file
python main.py /path/to/file.py

# Review a directory
python main.py /path/to/project/

# Review with web interface
python main.py
```

#### Web Interface

The web interface provides an interactive way to use the code review agent:

1. Start the agent (web interface enabled by default):
```bash
python main.py
```

2. Open your browser to `http://localhost:5000`

3. Enter the path to scan and click "Start Scan"

#### Programmatic Usage

```python
import asyncio
from pathlib import Path
from src.config import Config
from src.agent import CodeReviewAgent

async def review_code():
    config = Config()
    agent = CodeReviewAgent(config)
    
    results = await agent.review_code(Path("/path/to/code"))
    agent.display_results(results)

asyncio.run(review_code())
```

## ⚙️ Configuration

The agent is configured through `config.yaml`:

```yaml
# AI Model Settings
models:
  ollama:
    primary: "llama3.2"
    code_specialist: "codellama"
    host: "http://localhost:11434"

# Code Analysis Settings
analysis:
  languages: ["python", "javascript", "java", "cpp", "go", "rust"]
  quality_checks:
    complexity_threshold: 10
    max_function_length: 50
    max_file_length: 500
  security_checks:
    enabled: true
    check_secrets: true
    check_dependencies: true

# Output Settings
output:
  console: true
  json: true
  html: true
  web_interface: true
  port: 5000
```

## 🔍 Analysis Types

### Code Quality Analysis
- **Complexity Analysis**: Cyclomatic complexity, function length
- **Code Smells**: Long functions, duplicate code, poor naming
- **Best Practices**: Language-specific conventions and patterns
- **Documentation**: Missing docstrings and comments

### Security Analysis
- **Vulnerability Detection**: SQL injection, XSS, command injection
- **Secret Detection**: API keys, passwords, tokens
- **Authentication Issues**: Weak passwords, hardcoded credentials
- **Cryptographic Issues**: Weak algorithms, insecure random generation

### Performance Analysis
- **Bottleneck Detection**: Inefficient algorithms, memory leaks
- **Anti-patterns**: Performance-killing patterns
- **Optimization Suggestions**: Specific improvement recommendations

## 📊 Output Formats

### Console Output
Rich, colorized console output with tables and panels showing:
- Summary statistics
- Issue breakdown by severity
- Detailed file-by-file analysis

### JSON Reports
Structured JSON output for integration with other tools:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "files_reviewed": 10,
  "issues_found": 25,
  "security_issues": 5,
  "quality_issues": 15,
  "performance_issues": 5,
  "files": [...]
}
```

### HTML Reports
Beautiful, interactive HTML reports with:
- Summary dashboard
- File-by-file issue breakdown
- Severity-based color coding
- Responsive design

## 🛠️ Development

### Project Structure

```
code_review_agent/
├── src/
│   ├── __init__.py
│   ├── agent.py          # Main agent implementation
│   ├── config.py         # Configuration management
│   ├── code_analyzer.py  # Static code analysis
│   ├── security_scanner.py # Security vulnerability detection
│   ├── git_integration.py # Git repository analysis
│   ├── report_generator.py # Report generation
│   └── web_interface.py  # Web UI
├── templates/            # HTML templates
├── static/              # Static web assets
├── main.py              # Entry point
├── config.yaml          # Configuration file
├── requirements.txt     # Dependencies
└── README.md           # This file
```

### Running Tests

```bash
python test_agent.py
```

### Adding New Languages

1. Add language patterns to `CodeAnalyzer`
2. Add security patterns to `SecurityScanner`
3. Update file extension mapping
4. Add to configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local AI model serving
- [LangChain](https://langchain.com/) for AI integration
- [Rich](https://rich.readthedocs.io/) for beautiful console output
- [Flask](https://flask.palletsprojects.com/) for web interface