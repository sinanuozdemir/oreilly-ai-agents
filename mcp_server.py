#!/usr/bin/env python3
"""
MCP Server - Model Context Protocol Server

This server provides tools for AI agents through the MCP protocol.
Run this file to start the server, then connect to it from the MCP_Tutorial.ipynb notebook.

Usage:
    python mcp_server.py

The server will run indefinitely until you press Ctrl+C to stop it.
"""

from fastmcp import FastMCP
import random
import hashlib

# Create the MCP server instance
# This is the main object that manages all tools and communication
mcp = FastMCP(
    name="TutorialServer",  # Name of your server
    instructions="""
    This server provides utility tools for calculations, weather, and text processing.
    Use these tools to help answer user questions.
    """
)

# =============================================================================
# CALCULATOR TOOLS
# =============================================================================

@mcp.tool()
def add(a: float, b: float) -> str:
    """
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b as a string
        
    Example:
        add(5, 3) -> "8.0"
    """
    result = a + b
    return f"{result}"


@mcp.tool()
def multiply(a: float, b: float) -> str:
    """
    Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The product of a and b as a string
        
    Example:
        multiply(4, 7) -> "28.0"
    """
    result = a * b
    return f"{result}"


@mcp.tool()
def divide(a: float, b: float) -> str:
    """
    Divide two numbers.
    
    Args:
        a: Numerator (number to divide)
        b: Denominator (number to divide by)
        
    Returns:
        The quotient as a string, or error message if dividing by zero
        
    Example:
        divide(10, 2) -> "5.0"
    """
    if b == 0:
        return "Error: Cannot divide by zero"
    result = a / b
    return f"{result}"


@mcp.tool()
def power(base: float, exponent: float) -> str:
    """
    Calculate base raised to the power of exponent.
    
    Args:
        base: The base number
        exponent: The power to raise base to
        
    Returns:
        The result as a string
        
    Example:
        power(2, 3) -> "8.0"
    """
    result = base ** exponent
    return f"{result}"


@mcp.tool()
def calculate_temperature(celsius: float = None, fahrenheit: float = None) -> str:
    """
    Convert temperature between Celsius and Fahrenheit.
    
    Provide either celsius OR fahrenheit, not both.
    
    Args:
        celsius: Temperature in Celsius (to convert to F)
        fahrenheit: Temperature in Fahrenheit (to convert to C)
        
    Returns:
        Converted temperature with both scales
        
    Example:
        calculate_temperature(celsius=25) -> "25°C = 77.0°F"
        calculate_temperature(fahrenheit=72) -> "72°F = 22.2°C"
    """
    if celsius is not None:
        f = (celsius * 9/5) + 32
        return f"{celsius}°C = {f:.1f}°F"
    elif fahrenheit is not None:
        c = (fahrenheit - 32) * 5/9
        return f"{fahrenheit}°F = {c:.1f}°C"
    else:
        return "Error: Provide either celsius or fahrenheit parameter"


# =============================================================================
# WEATHER TOOLS
# =============================================================================

@mcp.tool()
def get_weather(city: str) -> str:
    """
    Get the current weather for a city.
    
    Note: This is a simulated weather service for demo purposes.
    In production, you would call a real weather API.
    
    Args:
        city: Name of the city (e.g., "Paris", "Tokyo", "New York")
        
    Returns:
        Weather description including temperature and conditions
        
    Example:
        get_weather("Paris") -> "Weather in Paris: ☀️ Sunny, 72°F (22°C)"
    """
    # Simulate different weather conditions based on city name
    # In production, this would call OpenWeatherMap or similar API
    
    weather_conditions = [
        ("☀️ Sunny", 72, 22),
        ("☁️ Cloudy", 65, 18),
        ("🌧️ Rainy", 60, 15),
        ("⛈️ Stormy", 68, 20),
        ("❄️ Snowy", 32, 0),
        ("🌤️ Partly Cloudy", 70, 21),
        ("🌫️ Foggy", 55, 13),
    ]
    
    # Use hash of city name to pick consistent weather for same city
    hash_val = int(hashlib.md5(city.lower().encode()).hexdigest(), 16)
    condition, temp_f, temp_c = weather_conditions[hash_val % len(weather_conditions)]
    
    return f"Weather in {city}: {condition}, {temp_f}°F ({temp_c}°C)"


@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """
    Get a weather forecast for a city.
    
    Args:
        city: Name of the city
        days: Number of days to forecast (1-5)
        
    Returns:
        Multi-day weather forecast
        
    Example:
        get_forecast("London", days=3) -> "3-day forecast for London..."
    """
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]
    
    forecast_parts = [f"{days}-day forecast for {city}:"]
    
    for day in range(1, min(days + 1, 6)):
        # Pseudo-random but consistent for same city
        seed = hash(city + str(day)) % len(conditions)
        condition = conditions[seed]
        high = random.randint(60, 85)
        low = high - random.randint(15, 25)
        forecast_parts.append(f"  Day {day}: {condition}, High {high}°F, Low {low}°F")
    
    return "\n".join(forecast_parts)


# =============================================================================
# TEXT PROCESSING TOOLS
# =============================================================================

@mcp.tool()
def reverse_text(text: str) -> str:
    """
    Reverse a string.
    
    Args:
        text: The text to reverse
        
    Returns:
        The reversed text
        
    Example:
        reverse_text("Hello") -> "olleH"
    """
    return text[::-1]


@mcp.tool()
def count_words(text: str) -> str:
    """
    Count the number of words in a text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Word count as a string
        
    Example:
        count_words("Hello world") -> "2"
    """
    words = text.split()
    return f"{len(words)}"


@mcp.tool()
def to_uppercase(text: str) -> str:
    """
    Convert text to uppercase.
    
    Args:
        text: The text to convert
        
    Returns:
        Uppercase version of the text
        
    Example:
        to_uppercase("hello") -> "HELLO"
    """
    return text.upper()


@mcp.tool()
def to_lowercase(text: str) -> str:
    """
    Convert text to lowercase.
    
    Args:
        text: The text to convert
        
    Returns:
        Lowercase version of the text
        
    Example:
        to_lowercase("HELLO") -> "hello"
    """
    return text.lower()


@mcp.tool()
def is_palindrome(text: str) -> str:
    """
    Check if a text is a palindrome (reads same forwards and backwards).
    
    Ignores spaces, punctuation, and case.
    
    Args:
        text: The text to check
        
    Returns:
        Whether the text is a palindrome
        
    Example:
        is_palindrome("A man a plan a canal Panama") -> "Yes, it's a palindrome!"
        is_palindrome("hello") -> "No, not a palindrome"
    """
    # Remove non-alphanumeric and convert to lowercase
    cleaned = ''.join(char.lower() for char in text if char.isalnum())
    
    if cleaned == cleaned[::-1]:
        return f"Yes, '{text}' is a palindrome!"
    else:
        return f"No, '{text}' is not a palindrome"


# =============================================================================
# UTILITY TOOLS
# =============================================================================

@mcp.tool()
def generate_random_number(min: int = 1, max: int = 100) -> str:
    """
    Generate a random number within a range.
    
    Args:
        min: Minimum value (inclusive)
        max: Maximum value (inclusive)
        
    Returns:
        Random number as a string
        
    Example:
        generate_random_number(1, 6) -> "4" (like a dice roll)
    """
    result = random.randint(min, max)
    return f"{result}"


@mcp.tool()
def roll_dice(sides: int = 6, count: int = 1) -> str:
    """
    Roll dice.
    
    Args:
        sides: Number of sides on each die (default 6)
        count: Number of dice to roll (default 1)
        
    Returns:
        Results of the dice rolls
        
    Example:
        roll_dice(6, 2) -> "Rolled 2d6: [4, 6] = 10"
    """
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    
    if count == 1:
        return f"Rolled 1d{sides}: {rolls[0]}"
    else:
        return f"Rolled {count}d{sides}: {rolls} = {total}"


@mcp.tool()
def get_current_time() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current date and time as a formatted string
        
    Example:
        get_current_time() -> "2025-01-15 14:30:45"
    """
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🚀 Starting MCP Server: TutorialServer")
    print("="*60)
    print("\nAvailable tools:")
    print("  Calculator: add, multiply, divide, power, calculate_temperature")
    print("  Weather: get_weather, get_forecast")
    print("  Text: reverse_text, count_words, to_uppercase, to_lowercase, is_palindrome")
    print("  Utility: generate_random_number, roll_dice, get_current_time")
    print("\n📡 Server running on stdio transport")
    print("   (Waiting for client connections...)")
    print("\n⏹️  Press Ctrl+C to stop the server")
    print("="*60)
    
    # Run the server with stdio transport
    # This allows the server to communicate through standard input/output
    mcp.run(transport='stdio')
