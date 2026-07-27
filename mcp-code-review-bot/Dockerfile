# MCP Code Review Server - Dockerfile
# This container runs the MCP server for automated code review

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastmcp>=0.4.0 \
    mcp>=1.0.0 \
    flake8 \
    pytest \
    pytest-cov \
    bandit \
    radon

# Copy the MCP server
COPY mcp_code_review_server.py /app/

# Set environment variables
ENV REPO_PATH=/repo
ENV PYTHONUNBUFFERED=1

# Expose port (for HTTP transport if needed)
EXPOSE 8080

# Run the MCP server
CMD ["python", "mcp_code_review_server.py"]
