
from mcp.server.fastmcp import FastMCP
from langchain_community.utilities import SerpAPIWrapper
import os

mcp = FastMCP("MCP Example")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def google_something(query: str) -> str:
    """Online Realtime Web Search"""
    serpapi = SerpAPIWrapper(serpapi_api_key="dbfd8b5b815e486ed203c0401c905bbae1a19592b2d785923e4b674f2dc270df")
    return serpapi.run(query)

if __name__ == "__main__":
    mcp.run(transport="stdio")
