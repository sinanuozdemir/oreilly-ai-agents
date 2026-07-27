# 🤖 MCP Code Review Bot

An AI-powered code review system using MCP (Model Context Protocol), Docker, and GitHub Actions.

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t mcp-code-review .
```

### 2. Test Locally

```bash
# Run analysis on current directory
docker run --rm -v $(pwd):/repo mcp-code-review \
  flake8 --max-line-length=100 /repo
```

### 3. Set Up GitHub Actions

1. Push this code to a GitHub repository
2. Create a Pull Request with Python file changes
3. The workflow automatically runs and posts a review comment

## Features

- 🐳 **Dockerized**: Runs in isolated containers
- 🔧 **MCP Protocol**: Extensible tool system
- 🚀 **GitHub Actions**: Automated PR reviews
- 📊 **Multiple Tools**: flake8, bandit, pytest, radon

## Tools Included

| Tool | Purpose |
|------|---------|
| flake8 | Style guide enforcement |
| bandit | Security vulnerability scanner |
| pytest | Testing framework with coverage |
| radon | Code complexity analysis |

## Project Structure

```
.
├── mcp_code_review_server.py   # MCP server with analysis tools
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
├── .github/workflows/           # GitHub Actions
│   └── code-review.yml
└── MCP_Code_Review_Tutorial.ipynb  # Detailed tutorial
```

## Usage

### Local Testing

```bash
# Build image
docker build -t mcp-code-review .

# Run container
docker run -it --rm -v $(pwd):/repo mcp-code-review

# Test MCP Inspector
npx @modelcontextprotocol/inspector docker run -i --rm -v $(pwd):/repo mcp-code-review
```

### GitHub Actions

The workflow automatically triggers on PRs that modify Python files:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
```

## Extending

Add new tools by editing `mcp_code_review_server.py`:

```python
@mcp.tool()
def my_custom_check(file_path: str) -> str:
    """Your custom analysis."""
    # Your code here
    return "Analysis results"
```

## Requirements

- Docker
- Python 3.11+
- GitHub repository (for Actions)

## License

MIT
