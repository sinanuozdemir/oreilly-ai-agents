#!/usr/bin/env python3
"""
MCP Code Review Server

This server provides tools for automated code review via MCP protocol.
Designed to run in Docker and be called from GitHub Actions.
"""

from fastmcp import FastMCP
import subprocess
import json
import os
from pathlib import Path

# Create the MCP server
mcp = FastMCP(
    name="CodeReviewServer",
    instructions="""
    This server provides code analysis tools for automated PR reviews.
    Available tools:
    - run_linter: Run flake8 on Python files
    - run_tests: Run pytest with coverage
    - check_security: Run bandit security scan
    - analyze_complexity: Calculate code complexity
    - get_changed_files: List files changed in the PR
    - read_file: Read contents of a file
    """
)

# Store repo path (set via environment variable or default)
REPO_PATH = os.getenv('REPO_PATH', '/repo')


@mcp.tool()
def get_changed_files() -> str:
    """
    Get list of files changed in the current PR/commit.
    
    Returns:
        JSON string with list of changed files
    """
    try:
        # Get changed files using git
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Try alternative: compare with main branch
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'origin/main', 'HEAD'],
                cwd=REPO_PATH,
                capture_output=True,
                text=True
            )
        
        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        
        # Filter for Python files only
        python_files = [f for f in files if f.endswith('.py')]
        
        return json.dumps({
            "all_files": files,
            "python_files": python_files,
            "count": len(files),
            "python_count": len(python_files)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file (relative to repo root)
        
    Returns:
        File contents or error message
    """
    try:
        full_path = Path(REPO_PATH) / file_path
        
        # Security check: ensure path is within repo
        if not str(full_path.resolve()).startswith(str(Path(REPO_PATH).resolve())):
            return "Error: Path traversal detected"
        
        if not full_path.exists():
            return f"Error: File not found: {file_path}"
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Limit output size
        if len(content) > 10000:
            content = content[:10000] + "\n... (truncated)"
        
        return content
        
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def run_linter(file_path: str = None) -> str:
    """
    Run flake8 linter on Python files.
    
    Args:
        file_path: Specific file to lint (optional, lints all if not provided)
        
    Returns:
        Linter output with any style issues found
    """
    try:
        cmd = ['flake8', '--max-line-length=100', '--extend-ignore=E203,W503']
        
        if file_path:
            full_path = Path(REPO_PATH) / file_path
            cmd.append(str(full_path))
        else:
            cmd.append(REPO_PATH)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return "✅ No linting issues found!"
        
        output = result.stdout if result.stdout else result.stderr
        
        if not output.strip():
            return "✅ No linting issues found!"
        
        # Format output
        lines = output.strip().split('\n')
        formatted = []
        for line in lines[:20]:  # Limit to first 20 issues
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 3:
                    file_name = parts[0].replace(REPO_PATH, '').lstrip('/')
                    line_num = parts[1]
                    col_num = parts[2]
                    message = ':'.join(parts[3:])
                    formatted.append(f"📍 {file_name}:{line_num}:{col_num} - {message}")
        
        if len(lines) > 20:
            formatted.append(f"\n... and {len(lines) - 20} more issues")
        
        return "\n".join(formatted) if formatted else output
        
    except subprocess.TimeoutExpired:
        return "⏱️ Linter timed out (took too long)"
    except FileNotFoundError:
        return "❌ Error: flake8 not installed. Install with: pip install flake8"
    except Exception as e:
        return f"❌ Linter error: {str(e)}"


@mcp.tool()
def run_tests(test_path: str = None) -> str:
    """
    Run pytest with coverage report.
    
    Args:
        test_path: Specific test file or directory (optional)
        
    Returns:
        Test results with coverage summary
    """
    try:
        cmd = [
            'python', '-m', 'pytest',
            '-v',
            '--tb=short',
            '--color=no',
            '-x'  # Stop on first failure
        ]
        
        # Try to add coverage if available
        try:
            import pytest_cov
            cmd.extend(['--cov=.', '--cov-report=term-missing'])
        except ImportError:
            pass
        
        if test_path:
            full_path = Path(REPO_PATH) / test_path
            cmd.append(str(full_path))
        else:
            cmd.append(REPO_PATH)
        
        result = subprocess.run(
            cmd,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout + "\n" + result.stderr
        
        # Summarize results
        if "passed" in output.lower():
            summary = "✅ Tests passed!"
        elif "failed" in output.lower():
            summary = "❌ Tests failed!"
        elif "error" in output.lower():
            summary = "⚠️ Test errors occurred"
        else:
            summary = "ℹ️ Test run completed"
        
        # Truncate if too long
        if len(output) > 8000:
            output = output[:8000] + "\n... (output truncated)"
        
        return f"{summary}\n\n{output}"
        
    except subprocess.TimeoutExpired:
        return "⏱️ Tests timed out (took longer than 120 seconds)"
    except FileNotFoundError:
        return "❌ Error: pytest not installed. Install with: pip install pytest"
    except Exception as e:
        return f"❌ Test error: {str(e)}"


@mcp.tool()
def check_security(file_path: str = None) -> str:
    """
    Run bandit security scanner on Python code.
    
    Args:
        file_path: Specific file to scan (optional, scans all if not provided)
        
    Returns:
        Security scan results
    """
    try:
        cmd = ['bandit', '-r', '-f', 'json']
        
        if file_path:
            full_path = Path(REPO_PATH) / file_path
            cmd.extend(['-f', 'txt', str(full_path)])
        else:
            cmd.append(REPO_PATH)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Bandit returns 1 when it finds issues (which is normal)
        if result.returncode == 0:
            return "✅ No security issues found!"
        
        output = result.stdout if result.stdout else result.stderr
        
        if not output.strip():
            return "✅ No security issues found!"
        
        return f"⚠️ Security scan results:\n\n{output}"
        
    except subprocess.TimeoutExpired:
        return "⏱️ Security scan timed out"
    except FileNotFoundError:
        return "❌ Error: bandit not installed. Install with: pip install bandit"
    except Exception as e:
        return f"❌ Security scan error: {str(e)}"


@mcp.tool()
def analyze_complexity(file_path: str) -> str:
    """
    Analyze code complexity using radon.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Complexity analysis results
    """
    try:
        full_path = Path(REPO_PATH) / file_path
        
        if not full_path.exists():
            return f"Error: File not found: {file_path}"
        
        result = subprocess.run(
            ['python', '-m', 'radon', 'cc', '-s', '-a', str(full_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        
        if not output.strip():
            return f"ℹ️ No complexity data for {file_path}"
        
        # Parse and format results
        lines = output.strip().split('\n')
        formatted = [f"📊 Complexity Analysis for {file_path}:", ""]
        
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    func_name = parts[0]
                    complexity = parts[1]
                    rank = parts[2]
                    
                    emoji = "🟢" if rank in ['A', 'B'] else "🟡" if rank == 'C' else "🔴"
                    formatted.append(f"{emoji} {func_name}: {complexity} ({rank})")
        
        return "\n".join(formatted)
        
    except subprocess.TimeoutExpired:
        return "⏱️ Complexity analysis timed out"
    except FileNotFoundError:
        return "❌ Error: radon not installed. Install with: pip install radon"
    except Exception as e:
        return f"❌ Complexity analysis error: {str(e)}"


@mcp.tool()
def post_review_comment(file_path: str, line_number: int, comment: str) -> str:
    """
    Format a code review comment (for GitHub Actions to post).
    
    Args:
        file_path: File being reviewed
        line_number: Line number for the comment
        comment: Review comment text
        
    Returns:
        Formatted comment string
    """
    return json.dumps({
        "file": file_path,
        "line": line_number,
        "comment": comment,
        "type": "review_comment"
    })


if __name__ == "__main__":
    # Run the server
    mcp.run(transport='stdio')
