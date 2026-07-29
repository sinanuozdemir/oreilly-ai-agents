# 🤖 MCP Tutorial - Quick Start Guide

This tutorial teaches you how to build and use MCP (Model Context Protocol) servers and clients.

## 📁 Files in This Tutorial

| File | Description |
|------|-------------|
| `mcp_server.py` | The MCP server providing tools (calculator, weather, text processing) |
| `notebooks/MCP_Tutorial.ipynb` | Jupyter notebook with step-by-step tutorial |
| `.vscode/launch.json` | VS Code debugging configuration |
| `MCP_README.md` | This file - quick reference guide |

## 🚀 Quick Start

### Step 1: Install Dependencies

Open a terminal and run:

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install MCP packages
pip install fastmcp mcp langchain-mcp-adapters langgraph
```

### Step 2: Verify Your API Key

Make sure your `.env` file has your Moonshot API key:

```bash
MOONSHOT_API_KEY=your_key_here
```

### Step 3: Run the MCP Server

**Option A: From Terminal**
```bash
python mcp_server.py
```

**Option B: From VS Code**
1. Open `mcp_server.py`
2. Press `F5` or click the Run button (▶️)
3. The server will start in the integrated terminal

You should see:
```
🚀 Starting MCP Server: TutorialServer
Available tools:
  Calculator: add, multiply, divide, power, calculate_temperature
  Weather: get_weather, get_forecast
  Text: reverse_text, count_words, to_uppercase, to_lowercase, is_palindrome
  Utility: generate_random_number, roll_dice, get_current_time
```

### Step 4: Use the Tutorial Notebook

1. Open `notebooks/MCP_Tutorial.ipynb` in VS Code
2. Make sure your kernel is set to the `.venv` environment
3. Run through the cells step by step

## 🛠️ Available Tools

### Calculator Tools
- `add(a, b)` - Add two numbers
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide two numbers
- `power(base, exponent)` - Calculate powers
- `calculate_temperature(celsius/fahrenheit)` - Convert temperatures

### Weather Tools
- `get_weather(city)` - Get current weather for a city
- `get_forecast(city, days)` - Get multi-day forecast

### Text Processing Tools
- `reverse_text(text)` - Reverse a string
- `count_words(text)` - Count words in text
- `to_uppercase(text)` - Convert to uppercase
- `to_lowercase(text)` - Convert to lowercase
- `is_palindrome(text)` - Check if text is a palindrome

### Utility Tools
- `generate_random_number(min, max)` - Generate random numbers
- `roll_dice(sides, count)` - Roll dice
- `get_current_time()` - Get current date/time

## 🐛 Debugging in VS Code

### Setting Up Breakpoints

1. Open `mcp_server.py`
2. Click in the left gutter (next to line numbers) to set a breakpoint
3. A red dot will appear indicating the breakpoint

### Running with Debugger

1. Press `F5` or go to Run → Start Debugging
2. The server will start and pause at your breakpoint
3. Use these controls:
   - `F10` - Step over (execute current line, move to next)
   - `F11` - Step into (enter function calls)
   - `F5` - Continue (run until next breakpoint)
   - `Shift+F5` - Stop debugging

### Inspecting Variables

When stopped at a breakpoint:
- **Hover** over variables to see their values
- Check the **Variables** panel on the left sidebar
- Use the **Debug Console** (bottom panel) to evaluate expressions

### Debug Panels

- **Variables** - Shows all variables in scope
- **Watch** - Monitor specific expressions
- **Call Stack** - See how you arrived at current line
- **Breakpoints** - Manage all breakpoints

## 📖 Tutorial Sections

The notebook covers:

1. **Setup** - Environment and dependencies
2. **MCP Concepts** - Understanding the protocol
3. **Server File** - How `mcp_server.py` works
4. **Client Setup** - Connecting to the server
5. **Testing Connection** - Verify everything works
6. **Calling Tools** - Direct tool execution
7. **LangChain Integration** - Using with AI agents
8. **VS Code Debugging** - Step-by-step debugging
9. **Advanced Concepts** - Resources, prompts, auth
10. **Practice Exercises** - Hands-on challenges

## 🎯 Example Usage

### Direct Tool Call

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        result = await session.call_tool("add", {"a": 5, "b": 3})
        print(result.content[0].text)  # "8.0"
```

### With AI Agent

```python
from langgraph.prebuilt import create_react_agent

# Agent automatically chooses tools
response = await agent.ainvoke({
    "messages": [{"role": "user", "content": "What's 25 times 17?"}]
})
# AI will call multiply tool and return "425.0"
```

## 🔧 Troubleshooting

### "Server not found"
- Check that `mcp_server.py` exists in project root
- Verify the path in notebook's `server_params`

### "Connection refused"
- Make sure server is running
- Check no other server instance is using the port

### "Tool not found"
- Tool names are case-sensitive
- Check spelling matches exactly

### Import errors
- Make sure you're in the virtual environment
- Run: `pip install fastmcp mcp langchain-mcp-adapters`

## 📚 Learning Resources

- [Model Context Protocol Docs](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

## 🎓 Next Steps

After completing this tutorial:

1. **Add more tools** to the server (file operations, API calls)
2. **Try HTTP transport** for remote connections
3. **Add resources** for reading files/databases
4. **Implement authentication** for production use
5. **Deploy** your server to a cloud VM

## 💡 Tips for VS Code

- Use **IntelliSense** (Ctrl+Space) for code completion
- Press **F12** on a function to go to its definition
- Use **Ctrl+Shift+F** to search across files
- Install the **Python** and **Jupyter** extensions for best experience
