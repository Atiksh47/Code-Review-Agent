#!/usr/bin/env python3
"""
AI-Powered Code Review Agent
Main entry point for the code review system
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agent import CodeReviewAgent
from config import Config
from web_interface import WebInterface

console = Console()

def print_banner():
    """Print the application banner"""
    banner = Text("🤖 AI-Powered Code Review Agent", style="bold blue")
    subtitle = Text("Intelligent code analysis using local AI models", style="italic")
    
    console.print(Panel.fit(
        f"{banner}\n{subtitle}",
        border_style="blue"
    ))

async def main():
    """Main application entry point"""
    print_banner()
    
    try:
        # Load configuration
        config = Config()
        console.print("✅ Configuration loaded", style="green")
        
        # Initialize the code review agent
        agent = CodeReviewAgent(config)
        console.print("✅ Code review agent initialized", style="green")
        
        # Check if web interface is enabled
        if config.output.web_interface:
            console.print("🌐 Starting web interface...", style="blue")
            web_interface = WebInterface(agent, config)
            await web_interface.start()
        else:
            # Run in CLI mode
            if len(sys.argv) < 2:
                console.print("❌ Please provide a path to review", style="red")
                console.print("Usage: python main.py <path_to_code>", style="yellow")
                sys.exit(1)
            
            path = Path(sys.argv[1])
            if not path.exists():
                console.print(f"❌ Path does not exist: {path}", style="red")
                sys.exit(1)
            
            console.print(f"🔍 Analyzing code at: {path}", style="blue")
            results = await agent.review_code(path)
            
            # Display results
            agent.display_results(results)
    
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
