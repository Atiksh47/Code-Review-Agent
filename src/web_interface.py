"""
Web Interface module for the Code Review Agent
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import threading

class WebInterface:
    """Web-based interface for the Code Review Agent"""
    
    def __init__(self, agent, config):
        self.agent = agent
        self.config = config
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        
        self.app = Flask(__name__, 
                        template_folder=str(project_root / 'templates'),
                        static_folder=str(project_root / 'static'))
        CORS(self.app)
        
        # Store recent results
        self.recent_results = []
        self.max_recent_results = 10
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')
        
        @self.app.route('/api/scan', methods=['POST'])
        def scan_code():
            """API endpoint to scan code"""
            try:
                data = request.get_json()
                path = data.get('path', '')
                
                if not path:
                    return jsonify({'error': 'Path is required'}), 400
                
                # Run the scan in a separate thread
                def run_scan():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        results = loop.run_until_complete(
                            self.agent.review_code(Path(path))
                        )
                        self._store_results(results)
                        return results
                    finally:
                        loop.close()
                
                # Start scan in background
                thread = threading.Thread(target=run_scan)
                thread.start()
                
                return jsonify({'message': 'Scan started', 'status': 'running'})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/results')
        def get_results():
            """Get recent scan results"""
            return jsonify(self.recent_results)
        
        @self.app.route('/api/results/<int:result_id>')
        def get_result(result_id):
            """Get specific result by ID"""
            if 0 <= result_id < len(self.recent_results):
                return jsonify(self.recent_results[result_id])
            return jsonify({'error': 'Result not found'}), 404
        
        @self.app.route('/api/config')
        def get_config():
            """Get current configuration"""
            return jsonify({
                'models': {
                    'primary': self.config.primary_model,
                    'code_specialist': self.config.code_model,
                    'ollama_host': self.config.ollama_host
                },
                'analysis': {
                    'languages': self.config.supported_languages,
                    'security_enabled': self.config.security_enabled
                },
                'output': {
                    'web_interface': self.config.output.web_interface,
                    'port': self.config.web_port
                }
            })
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/api/git/info', methods=['POST'])
        def get_git_info():
            """Get Git repository information"""
            try:
                data = request.get_json()
                path = data.get('path', '')
                
                if not path:
                    return jsonify({'error': 'Path is required'}), 400
                
                git_info = self.agent.git_integration.get_repository_info(Path(path))
                return jsonify(git_info)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/git/commits', methods=['POST'])
        def get_git_commits():
            """Get recent Git commits"""
            try:
                data = request.get_json()
                path = data.get('path', '')
                since = data.get('since')
                
                if not path:
                    return jsonify({'error': 'Path is required'}), 400
                
                since_date = None
                if since:
                    since_date = datetime.fromisoformat(since)
                
                commits = self.agent.git_integration.get_commits_since(Path(path), since_date)
                
                # Convert commits to serializable format
                commits_data = []
                for commit in commits:
                    commits_data.append({
                        'hash': commit.hash,
                        'author': commit.author,
                        'email': commit.email,
                        'date': commit.date.isoformat(),
                        'message': commit.message,
                        'files_changed': commit.files_changed,
                        'insertions': commit.insertions,
                        'deletions': commit.deletions
                    })
                
                return jsonify(commits_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/generate', methods=['POST'])
        def generate_report():
            """Generate reports for a specific result"""
            try:
                data = request.get_json()
                result_id = data.get('result_id')
                formats = data.get('formats', ['json', 'html'])
                
                if result_id is None or result_id >= len(self.recent_results):
                    return jsonify({'error': 'Invalid result ID'}), 400
                
                result = self.recent_results[result_id]
                reports = self.agent.report_generator.generate_reports(result)
                
                # Filter requested formats
                filtered_reports = {fmt: reports[fmt] for fmt in formats if fmt in reports}
                
                return jsonify(filtered_reports)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _store_results(self, results: Dict[str, Any]):
        """Store results in recent results list"""
        results['id'] = len(self.recent_results)
        results['timestamp'] = datetime.now().isoformat()
        
        self.recent_results.append(results)
        
        # Keep only recent results
        if len(self.recent_results) > self.max_recent_results:
            self.recent_results = self.recent_results[-self.max_recent_results:]
    
    async def start(self):
        """Start the web interface"""
        port = self.config.web_port
        
        # Create templates directory if it doesn't exist
        project_root = Path(__file__).parent.parent
        templates_dir = project_root / 'templates'
        templates_dir.mkdir(exist_ok=True)
        
        # Create static directory if it doesn't exist
        project_root = Path(__file__).parent.parent
        static_dir = project_root / 'static'
        static_dir.mkdir(exist_ok=True)
        
        # Create the main template
        self._create_templates()
        
        print(f"🌐 Starting web interface on http://localhost:{port}")
        
        # Run Flask app
        self.app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    
    def _create_templates(self):
        """Create HTML templates"""
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        templates_dir = project_root / 'templates'
        
        # Main template
        index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Review Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        
        .tab {
            flex: 1;
            padding: 15px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: white;
            border-bottom: 3px solid #667eea;
            color: #667eea;
            font-weight: bold;
        }
        
        .tab-content {
            padding: 30px;
            min-height: 500px;
        }
        
        .tab-pane {
            display: none;
        }
        
        .tab-pane.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: 500;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .result-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        
        .result-card h3 {
            margin-bottom: 10px;
            color: #333;
        }
        
        .result-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }
        
        .issue-count {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
        }
        
        .issue-high { background: #dc3545; color: white; }
        .issue-medium { background: #ffc107; color: #333; }
        .issue-low { background: #28a745; color: white; }
        
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .config-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }
        
        .config-item:last-child {
            border-bottom: none;
        }
        
        .config-label {
            font-weight: 600;
        }
        
        .config-value {
            color: #666;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Code Review Agent</h1>
            <p>Intelligent code analysis using local AI models</p>
        </div>
        
        <div class="main-content">
            <div class="tabs">
                <button class="tab active" onclick="showTab('scan')">Code Scan</button>
                <button class="tab" onclick="showTab('results')">Results</button>
                <button class="tab" onclick="showTab('config')">Configuration</button>
            </div>
            
            <div class="tab-content">
                <!-- Scan Tab -->
                <div id="scan" class="tab-pane active">
                    <h2>Scan Code</h2>
                    <form id="scanForm">
                        <div class="form-group">
                            <label for="scanPath">Path to scan:</label>
                            <input type="text" id="scanPath" placeholder="/path/to/your/code" required>
                        </div>
                        <button type="submit" class="btn" id="scanBtn">Start Scan</button>
                    </form>
                    <div id="scanStatus"></div>
                </div>
                
                <!-- Results Tab -->
                <div id="results" class="tab-pane">
                    <h2>Recent Results</h2>
                    <div id="resultsContainer">
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>Loading results...</p>
                        </div>
                    </div>
                </div>
                
                <!-- Config Tab -->
                <div id="config" class="tab-pane">
                    <h2>Configuration</h2>
                    <div id="configContainer">
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>Loading configuration...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentResults = [];
        
        // Tab switching
        function showTab(tabName) {
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab pane
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Load content for specific tabs
            if (tabName === 'results') {
                loadResults();
            } else if (tabName === 'config') {
                loadConfig();
            }
        }
        
        // Scan form submission
        document.getElementById('scanForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const path = document.getElementById('scanPath').value;
            const scanBtn = document.getElementById('scanBtn');
            const statusDiv = document.getElementById('scanStatus');
            
            scanBtn.disabled = true;
            scanBtn.textContent = 'Scanning...';
            
            statusDiv.innerHTML = '<div class="status info">Starting scan...</div>';
            
            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ path: path })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="status success">Scan started successfully! Check the Results tab for progress.</div>';
                    // Switch to results tab
                    showTab('results');
                } else {
                    statusDiv.innerHTML = `<div class="status error">Error: ${result.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">Error: ${error.message}</div>`;
            } finally {
                scanBtn.disabled = false;
                scanBtn.textContent = 'Start Scan';
            }
        });
        
        // Load results
        async function loadResults() {
            const container = document.getElementById('resultsContainer');
            
            try {
                const response = await fetch('/api/results');
                const results = await response.json();
                
                currentResults = results;
                
                if (results.length === 0) {
                    container.innerHTML = '<div class="status info">No scan results yet. Start a scan to see results here.</div>';
                    return;
                }
                
                container.innerHTML = results.map((result, index) => `
                    <div class="result-card">
                        <h3>Scan #${index + 1}</h3>
                        <div class="result-meta">
                            Path: ${result.path}<br>
                            Files: ${result.files_reviewed}<br>
                            Timestamp: ${new Date(result.timestamp).toLocaleString()}
                        </div>
                        <div>
                            <span class="issue-count issue-high">High: ${result.security_issues || 0}</span>
                            <span class="issue-count issue-medium">Medium: ${result.quality_issues || 0}</span>
                            <span class="issue-count issue-low">Low: ${result.performance_issues || 0}</span>
                        </div>
                        <button class="btn" onclick="viewResult(${index})" style="margin-top: 15px;">View Details</button>
                    </div>
                `).join('');
                
            } catch (error) {
                container.innerHTML = `<div class="status error">Error loading results: ${error.message}</div>`;
            }
        }
        
        // Load configuration
        async function loadConfig() {
            const container = document.getElementById('configContainer');
            
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                container.innerHTML = `
                    <div class="config-section">
                        <h3>AI Models</h3>
                        <div class="config-item">
                            <span class="config-label">Primary Model:</span>
                            <span class="config-value">${config.models.primary}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Code Specialist:</span>
                            <span class="config-value">${config.models.code_specialist}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Ollama Host:</span>
                            <span class="config-value">${config.models.ollama_host}</span>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h3>Analysis Settings</h3>
                        <div class="config-item">
                            <span class="config-label">Supported Languages:</span>
                            <span class="config-value">${config.analysis.languages.join(', ')}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Security Scanning:</span>
                            <span class="config-value">${config.analysis.security_enabled ? 'Enabled' : 'Disabled'}</span>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h3>Output Settings</h3>
                        <div class="config-item">
                            <span class="config-label">Web Interface:</span>
                            <span class="config-value">${config.output.web_interface ? 'Enabled' : 'Disabled'}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Port:</span>
                            <span class="config-value">${config.output.port}</span>
                        </div>
                    </div>
                `;
                
            } catch (error) {
                container.innerHTML = `<div class="status error">Error loading configuration: ${error.message}</div>`;
            }
        }
        
        // View result details
        function viewResult(index) {
            const result = currentResults[index];
            if (result) {
                // Create a new window with detailed results
                const newWindow = window.open('', '_blank');
                newWindow.document.write(`
                    <html>
                    <head>
                        <title>Scan Results - ${result.path}</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 20px; }
                            .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                            .file-result { margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; }
                            .file-header { background: #e9ecef; padding: 15px; font-weight: bold; }
                            .issue { padding: 10px; border-bottom: 1px solid #eee; }
                            .issue:last-child { border-bottom: none; }
                            .severity-high { border-left: 4px solid #dc3545; }
                            .severity-medium { border-left: 4px solid #ffc107; }
                            .severity-low { border-left: 4px solid #28a745; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>Scan Results</h1>
                            <p><strong>Path:</strong> ${result.path}</p>
                            <p><strong>Files Reviewed:</strong> ${result.files_reviewed}</p>
                            <p><strong>Total Issues:</strong> ${result.issues_found}</p>
                            <p><strong>Timestamp:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
                        </div>
                        
                        ${result.files ? result.files.map(file => `
                            <div class="file-result">
                                <div class="file-header">${file.file_path}</div>
                                ${file.issues ? file.issues.map(issue => `
                                    <div class="issue severity-${issue.severity.toLowerCase()}">
                                        <strong>[${issue.severity}]</strong> ${issue.message}
                                        <br><small>Type: ${issue.type} | Source: ${issue.source}</small>
                                    </div>
                                `).join('') : '<div class="issue">No issues found</div>'}
                            </div>
                        `).join('') : '<p>No files analyzed</p>'}
                    </body>
                    </html>
                `);
            }
        }
        
        // Load initial data
        loadResults();
        loadConfig();
    </script>
</body>
</html>
        """
        
        with open(templates_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_template)
