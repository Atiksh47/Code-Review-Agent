"""
Report Generator module for creating various output formats
"""

import json
import html
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Template

class ReportGenerator:
    """Generate reports in various formats (JSON, HTML, etc.)"""
    
    def __init__(self, config):
        self.config = config
        self.console_output = config.output.console
        self.json_output = config.output.json_output
        self.html_output = config.output.html
    
    def generate_reports(self, results: Dict[str, Any], output_dir: Optional[Path] = None) -> Dict[str, str]:
        """Generate all configured report formats"""
        reports = {}
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate JSON report
        if self.json_output:
            json_report = self.generate_json_report(results)
            reports['json'] = json_report
            
            if output_dir:
                json_path = output_dir / f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    f.write(json_report)
        
        # Generate HTML report
        if self.html_output:
            html_report = self.generate_html_report(results)
            reports['html'] = html_report
            
            if output_dir:
                html_path = output_dir / f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_report)
        
        return reports
    
    def generate_json_report(self, results: Dict[str, Any]) -> str:
        """Generate JSON report"""
        # Clean up the results for JSON serialization
        json_results = self._prepare_for_json(results)
        
        return json.dumps(json_results, indent=2, ensure_ascii=False, default=str)
    
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML report"""
        template = Template(self._get_html_template())
        
        # Prepare data for template
        template_data = {
            'results': results,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': results.get('summary', {}),
            'files': results.get('files', []),
            'total_issues': results.get('issues_found', 0),
            'security_issues': results.get('security_issues', 0),
            'quality_issues': results.get('quality_issues', 0),
            'performance_issues': results.get('performance_issues', 0)
        }
        
        return template.render(**template_data)
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a concise summary report"""
        summary = results.get('summary', {})
        
        report = f"""
Code Review Summary
==================

Files Reviewed: {results.get('files_reviewed', 0)}
Total Issues: {results.get('issues_found', 0)}

Issue Breakdown:
- Security Issues: {results.get('security_issues', 0)}
- Quality Issues: {results.get('quality_issues', 0)}
- Performance Issues: {results.get('performance_issues', 0)}

Severity Breakdown:
- High: {summary.get('severity_breakdown', {}).get('HIGH', 0)}
- Medium: {summary.get('severity_breakdown', {}).get('MEDIUM', 0)}
- Low: {summary.get('severity_breakdown', {}).get('LOW', 0)}

Top Issues by File:
"""
        
        # Get files with most issues
        files_with_issues = [
            (file_result['file_path'], len(file_result.get('issues', [])))
            for file_result in results.get('files', [])
            if file_result.get('issues')
        ]
        files_with_issues.sort(key=lambda x: x[1], reverse=True)
        
        for file_path, issue_count in files_with_issues[:5]:
            report += f"- {Path(file_path).name}: {issue_count} issues\n"
        
        return report
    
    def _prepare_for_json(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare results for JSON serialization"""
        # Create a deep copy and ensure all values are JSON serializable
        json_results = {}
        
        for key, value in results.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                json_results[key] = value
            elif isinstance(value, (list, tuple)):
                json_results[key] = [self._prepare_for_json(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                json_results[key] = self._prepare_for_json(value)
            else:
                json_results[key] = str(value)
        
        return json_results
    
    def _get_html_template(self) -> str:
        """Get HTML template for reports"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .summary {
            padding: 30px;
            border-bottom: 1px solid #eee;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 2em;
        }
        .summary-card p {
            margin: 0;
            color: #666;
            font-weight: 500;
        }
        .severity-breakdown {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .severity-item {
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }
        .severity-high { background-color: #dc3545; }
        .severity-medium { background-color: #ffc107; color: #333; }
        .severity-low { background-color: #28a745; }
        .files-section {
            padding: 30px;
        }
        .file-item {
            margin-bottom: 30px;
            border: 1px solid #eee;
            border-radius: 8px;
            overflow: hidden;
        }
        .file-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-name {
            font-weight: bold;
            color: #333;
        }
        .file-stats {
            color: #666;
            font-size: 0.9em;
        }
        .issues-list {
            padding: 20px;
        }
        .issue-item {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid;
        }
        .issue-high { background-color: #f8d7da; border-left-color: #dc3545; }
        .issue-medium { background-color: #fff3cd; border-left-color: #ffc107; }
        .issue-low { background-color: #d4edda; border-left-color: #28a745; }
        .issue-severity {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 10px;
        }
        .issue-message {
            margin: 5px 0;
        }
        .issue-meta {
            font-size: 0.9em;
            color: #666;
        }
        .no-issues {
            text-align: center;
            color: #28a745;
            font-size: 1.2em;
            padding: 40px;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Code Review Report</h1>
            <p>Generated on {{ timestamp }}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>{{ results.files_reviewed }}</h3>
                    <p>Files Reviewed</p>
                </div>
                <div class="summary-card">
                    <h3>{{ total_issues }}</h3>
                    <p>Total Issues</p>
                </div>
                <div class="summary-card">
                    <h3>{{ security_issues }}</h3>
                    <p>Security Issues</p>
                </div>
                <div class="summary-card">
                    <h3>{{ quality_issues }}</h3>
                    <p>Quality Issues</p>
                </div>
                <div class="summary-card">
                    <h3>{{ performance_issues }}</h3>
                    <p>Performance Issues</p>
                </div>
            </div>
            
            {% if summary.severity_breakdown %}
            <h3>Severity Breakdown</h3>
            <div class="severity-breakdown">
                <div class="severity-item severity-high">
                    High: {{ summary.severity_breakdown.HIGH or 0 }}
                </div>
                <div class="severity-item severity-medium">
                    Medium: {{ summary.severity_breakdown.MEDIUM or 0 }}
                </div>
                <div class="severity-item severity-low">
                    Low: {{ summary.severity_breakdown.LOW or 0 }}
                </div>
            </div>
            {% endif %}
        </div>
        
        <div class="files-section">
            <h2>File Analysis</h2>
            {% if files %}
                {% for file in files %}
                    {% if file.issues %}
                    <div class="file-item">
                        <div class="file-header">
                            <div class="file-name">{{ file.file_path.split('/')[-1] }}</div>
                            <div class="file-stats">
                                {{ file.language }} • {{ file.lines }} lines • {{ file.issues|length }} issues
                            </div>
                        </div>
                        <div class="issues-list">
                            {% for issue in file.issues %}
                            <div class="issue-item issue-{{ issue.severity.lower() }}">
                                <span class="issue-severity severity-{{ issue.severity.lower() }}">
                                    {{ issue.severity }}
                                </span>
                                <div class="issue-message">{{ issue.message }}</div>
                                <div class="issue-meta">
                                    Type: {{ issue.type }} • 
                                    {% if issue.line %}Line: {{ issue.line }} • {% endif %}
                                    Source: {{ issue.source }}
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                {% endfor %}
            {% else %}
                <div class="no-issues">
                    🎉 No issues found! Great job!
                </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Generated by AI-Powered Code Review Agent</p>
        </div>
    </div>
</body>
</html>
        """
