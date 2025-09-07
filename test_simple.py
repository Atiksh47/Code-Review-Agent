#!/usr/bin/env python3
"""
Simple test script for the Code Review Agent
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Config
from agent import CodeReviewAgent

console = Console()

async def test_agent():
    """Test the code review agent"""
    console.print("🧪 Testing Code Review Agent", style="bold blue")
    
    try:
        # Load configuration
        console.print("📋 Loading configuration...", style="yellow")
        config = Config()
        console.print("✅ Configuration loaded successfully", style="green")
        
        # Initialize agent
        console.print("🤖 Initializing agent...", style="yellow")
        agent = CodeReviewAgent(config)
        console.print("✅ Agent initialized successfully", style="green")
        
        # Test with a simple Python file
        test_code = '''
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
'''
        
        # Create a temporary test file
        test_file = Path("test_sample.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        console.print(f"🔍 Testing with sample file: {test_file}", style="blue")
        
        # Run review
        results = await agent.review_code(test_file)
        
        # Display results
        console.print("\n📊 Review Results:", style="bold green")
        agent.display_results(results)
        
        # Clean up
        test_file.unlink()
        
        console.print("\n🎉 Test completed successfully!", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}", style="red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
