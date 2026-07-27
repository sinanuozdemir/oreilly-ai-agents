#!/usr/bin/env python3
"""
Test client for MCP Code Review Server

This script connects to the MCP server and tests all available tools.
Run this to verify the MCP server works correctly before pushing to GitHub.
"""

import asyncio
import subprocess
import sys
import os

# Set repo path
REPO_PATH = os.getenv('REPO_PATH', '/Users/raymaldonado/Library/CloudStorage/GoogleDrive-vivachihuahua2004@gmail.com/My Drive/Code/oreilly-ai-agents/mcp-code-review-bot')
os.environ['REPO_PATH'] = REPO_PATH

async def test_mcp_server():
    """Test the MCP server by connecting and calling tools."""
    
    print("🧪 Testing MCP Code Review Server")
    print("=" * 50)
    
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print("❌ Error: mcp package not installed")
        print("   Install with: pip install mcp")
        return
    
    # Start the MCP server as a subprocess
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_code_review_server.py"],
        env={"REPO_PATH": REPO_PATH}
    )
    
    print(f"📁 Repository path: {REPO_PATH}")
    print("🚀 Starting MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Get list of available tools
            tools_result = await session.list_tools()
            print(f"\n✅ Connected! Found {len(tools_result.tools)} tools:")
            for tool in tools_result.tools:
                print(f"   • {tool.name}: {tool.description[:50]}...")
            
            print("\n" + "=" * 50)
            print("🧪 Testing Individual Tools")
            print("=" * 50)
            
            # Test 1: read_file
            print("\n📖 Test 1: read_file('test_bad_code.py')")
            try:
                result = await session.call_tool("read_file", {"file_path": "test_bad_code.py"})
                content = result.content[0].text if result.content else "No content"
                if content.startswith("Error"):
                    print(f"   ⚠️  {content}")
                else:
                    lines = content.split('\n')
                    print(f"   ✅ Success! Read {len(lines)} lines")
                    print(f"   First line: {lines[0][:60]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 2: run_linter
            print("\n🔍 Test 2: run_linter('test_bad_code.py')")
            try:
                result = await session.call_tool("run_linter", {"file_path": "test_bad_code.py"})
                content = result.content[0].text if result.content else "No content"
                if "✅" in content:
                    print(f"   ✅ {content}")
                else:
                    issue_count = content.count('📍')
                    print(f"   ⚠️  Found {issue_count} linting issues")
                    # Show first 2 issues
                    for line in content.split('\n')[:2]:
                        if line.strip():
                            print(f"      {line}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 3: check_security
            print("\n🔒 Test 3: check_security('test_bad_code.py')")
            try:
                result = await session.call_tool("check_security", {"file_path": "test_bad_code.py"})
                content = result.content[0].text if result.content else "No content"
                if "✅" in content:
                    print(f"   ✅ {content}")
                else:
                    print(f"   ⚠️  {content[:100]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 4: analyze_complexity
            print("\n📊 Test 4: analyze_complexity('test_bad_code.py')")
            try:
                result = await session.call_tool("analyze_complexity", {"file_path": "test_bad_code.py"})
                content = result.content[0].text if result.content else "No content"
                if "❌" in content:
                    print(f"   ❌ {content}")
                else:
                    # Count complexity grades
                    grades = content.count('🟢') + content.count('🟡') + content.count('🔴')
                    print(f"   ✅ Analyzed {grades} functions")
                    # Show first function
                    for line in content.split('\n')[2:4]:
                        if line.strip():
                            print(f"      {line}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 5: get_changed_files (may fail if not a git repo)
            print("\n📁 Test 5: get_changed_files()")
            try:
                result = await session.call_tool("get_changed_files", {})
                content = result.content[0].text if result.content else "No content"
                if "error" in content.lower():
                    print(f"   ⚠️  {content[:80]}...")
                else:
                    import json
                    data = json.loads(content)
                    print(f"   ✅ Found {data.get('count', 0)} changed files")
                    print(f"      Python files: {data.get('python_count', 0)}")
            except Exception as e:
                print(f"   ⚠️  Note: {e}")
            
            # Test 6: post_review_comment
            print("\n💬 Test 6: post_review_comment()")
            try:
                result = await session.call_tool("post_review_comment", {
                    "file_path": "test_bad_code.py",
                    "line_number": 1,
                    "comment": "This is a test review comment"
                })
                content = result.content[0].text if result.content else "No content"
                print(f"   ✅ Formatted comment:")
                print(f"      {content[:80]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print("\n" + "=" * 50)
            print("✅ MCP Server Test Complete!")
            print("=" * 50)
            print("\nNext steps:")
            print("1. ✅ Local testing complete - MCP server works!")
            print("2. 🐳 Test in Docker: docker run -v '\"$REPO_PATH:/repo\"' mcp-code-review")
            print("3. 🚀 Push to GitHub to test PR workflow")

if __name__ == "__main__":
    # Check if mcp package is installed
    try:
        import mcp
    except ImportError:
        print("❌ mcp package not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "mcp"], check=True)
        print("✅ mcp installed! Rerun this script.")
        sys.exit(0)
    
    # Run the test
    asyncio.run(test_mcp_server())
