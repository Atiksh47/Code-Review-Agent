#!/usr/bin/env python3
"""
AI-Powered Code Review Agent
Main entry point for the code review system

This module serves as the primary entry point for the Code Review Agent application.
It handles command-line arguments, initializes the system, and determines whether
to run in CLI mode or start the web interface.

Usage:
    python main.py                    # Start web interface
    python main.py /path/to/code      # Analyze specific path in CLI mode
    python main.py --help             # Show help information

Author: Atiksh Kotikalapudi
Version: 1.0.0
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add src directory to Python path for imports
# This allows us to import modules from the src/ directory
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import core components
from agent import CodeReviewAgent      # Main code review engine
from config import Config             # Configuration management
from web_interface import WebInterface # Web-based user interface

# Initialize Rich console for beautiful terminal output
console = Console()

def print_banner():
    """
    Print a beautiful application banner using Rich formatting.
    
    This function creates an attractive welcome message that displays
    when the application starts, showing the application name and
    a brief description of its capabilities.
    """
    # Create styled text elements for the banner
    banner = Text("🤖 AI-Powered Code Review Agent", style="bold blue")
    subtitle = Text("Intelligent code analysis using local AI models", style="italic")
    
    # Display the banner in a bordered panel
    console.print(Panel.fit(
        f"{banner}\n{subtitle}",
        border_style="blue"
    ))

async def main():
    """
    Main application entry point.
    
    This function orchestrates the entire application flow:
    1. Displays the welcome banner
    2. Loads configuration from config.yaml
    3. Initializes the code review agent with all components
    4. Determines execution mode (CLI or Web Interface)
    5. Handles errors gracefully with user-friendly messages
    
    Raises:
        SystemExit: If required arguments are missing or paths don't exist
        KeyboardInterrupt: If user presses Ctrl+C to exit
        Exception: For any other unexpected errors during initialization
    """
    print_banner()
    
    try:
        # Step 1: Load configuration from config.yaml
        # This includes AI model settings, analysis rules, and output preferences
        config = Config()
        console.print("✅ Configuration loaded", style="green")
        
        # Step 2: Initialize the code review agent
        # This sets up all analysis components (code analyzer, security scanner, etc.)
        agent = CodeReviewAgent(config)
        console.print("✅ Code review agent initialized", style="green")
        
        # Step 3: Determine execution mode based on configuration
        if config.output.web_interface:
            # Web Interface Mode: Start Flask server for interactive use
            console.print("🌐 Starting web interface...", style="blue")
            web_interface = WebInterface(agent, config)
            await web_interface.start()  # This blocks until server stops
        else:
            # CLI Mode: Analyze code from command line arguments
            if len(sys.argv) < 2:
                console.print("❌ Please provide a path to review", style="red")
                console.print("Usage: python main.py <path_to_code>", style="yellow")
                sys.exit(1)
            
            # Validate that the provided path exists
            path = Path(sys.argv[1])
            if not path.exists():
                console.print(f"❌ Path does not exist: {path}", style="red")
                sys.exit(1)
            
            # Perform code analysis and display results
            console.print(f"🔍 Analyzing code at: {path}", style="blue")
            results = await agent.review_code(path)
            
            # Display results in the console with Rich formatting
            agent.display_results(results)
    
    except KeyboardInterrupt:
        # Handle graceful shutdown when user presses Ctrl+C
        console.print("\n👋 Goodbye!", style="yellow")
    except Exception as e:
        # Handle any unexpected errors with clear error messages
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
