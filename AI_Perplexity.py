"""
Perplexity AI integration module.
Handles data extraction from MyFxBook Economic Calendar.

NOTE: These functions are EXAMPLES/TEMPLATES.
      Demonstrates how to query Perplexity with instruction sets.
      Use these patterns when building the real News.py implementation.
"""

import Globals
from openai import OpenAI


def query_perplexity(prompt, system_instructions=None):
    """
    Query Perplexity with a prompt and optional system instructions.
    
    Args:
        prompt (str): The prompt to send to Perplexity
        system_instructions (str): Optional system instructions to guide Perplexity's behavior
        
    Returns:
        str: Perplexity's response
    """
    client = OpenAI(api_key=Globals.API_KEY_PPXT, base_url="https://api.perplexity.ai")
    
    # Default system message if none provided
    if system_instructions is None:
        system_instructions = (
            "You are an artificial intelligence assistant and you need to "
            "engage in a helpful, detailed, polite conversation with a user."
        )
    
    messages = [
        {
            "role": "system",
            "content": system_instructions
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages
    )
    
    return response.choices[0].message.content.strip()


def get_news_data(event_name, currency, date, request_type="both"):
    """
    Query Perplexity for news event data (Forecast and/or Actual).
    Uses News_Research.txt instruction set.
    Data sourced from MyFxBook Economic Calendar.
    
    Args:
        event_name (str): Name of the news event (e.g., "Unemployment Rate")
        currency (str): Currency code (e.g., "EUR", "USD")
        date (str): Event date (e.g., "Nov 03, 04:10")
        request_type (str): "forecast", "actual", or "both"
        
    Returns:
        str: Perplexity's response in format "Forecast : X" or "Actual : Y" or both
    """
    # Load News_Research instructions
    with open("News_Research.txt", "r", encoding="utf-8") as f:
        research_instructions = f.read()
    
    # Build the query based on request type
    if request_type == "forecast":
        query = f"Find the Forecast value for: {currency} {event_name} on {date}. Check MyFxBook Economic Calendar (https://www.myfxbook.com/forex-economic-calendar). Return ONLY in format: Forecast : [number]"
    elif request_type == "actual":
        query = f"Find the Actual value for: {currency} {event_name} on {date}. Check MyFxBook Economic Calendar (https://www.myfxbook.com/forex-economic-calendar). Return ONLY in format: Actual : [number]. If not released yet, return: FALSE"
    else:  # both
        query = f"Find the Forecast and Actual values for: {currency} {event_name} on {date}. Check MyFxBook Economic Calendar (https://www.myfxbook.com/forex-economic-calendar). Return ONLY in format: Forecast : [number], Actual : [number]"
    
    return query_perplexity(query, research_instructions)


# Test function
if __name__ == "__main__":
    result = query_perplexity("Hello")
    print(f"Perplexity: {result}")

