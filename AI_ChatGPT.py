"""
ChatGPT AI integration module.
Handles validation and trading signal generation.

NOTE: These functions are EXAMPLES/TEMPLATES.
      Demonstrates how to query ChatGPT with instruction sets.
      Use these patterns when building the real News.py implementation.
"""

import Globals
from openai import OpenAI


def query_chatgpt(prompt, system_instructions=None):
    """
    Query ChatGPT with a prompt and optional system instructions.
    
    Args:
        prompt (str): The prompt to send to ChatGPT
        system_instructions (str): Optional system instructions to guide ChatGPT's behavior
        
    Returns:
        str: ChatGPT's response
    """
    client = OpenAI(api_key=Globals.API_KEY_GPT)
    
    # If system instructions provided, use them; otherwise just send user message
    if system_instructions:
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt}
        ]
    else:
        messages = [{"role": "user", "content": prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    return response.choices[0].message.content.strip()


def validate_news_data(perplexity_response):
    """
    Validate Perplexity's response using ChatGPT with News_Research.txt rules.
    
    Args:
        perplexity_response (str): The response from Perplexity to validate
        
    Returns:
        str: ChatGPT's validated/corrected response
    """
    # Load News_Research instructions
    with open("News_Research.txt", "r", encoding="utf-8") as f:
        research_instructions = f.read()
    
    validation_prompt = f"""
Validate and correct this response if needed:

{perplexity_response}

Ensure it matches the exact format from the instruction set. Return ONLY the corrected format.
"""
    
    return query_chatgpt(validation_prompt, research_instructions)


def generate_trading_signals(currency, event_name, forecast, actual):
    """
    Generate trading signals using ChatGPT with News_Rules.txt.
    
    Args:
        currency (str): Currency code (e.g., "EUR", "USD")
        event_name (str): Name of the event (e.g., "Unemployment Rate")
        forecast (float): Forecast value
        actual (float): Actual value
        
    Returns:
        str: Trading signals in format "PAIR : ACTION, PAIR : ACTION" or "NEUTRAL"
    """
    # Load News_Rules instructions
    with open("News_Rules.txt", "r", encoding="utf-8") as f:
        rules_instructions = f.read()
    
    # Get available trading pairs from Globals._Symbols_
    available_pairs = list(Globals._Symbols_.keys())
    pairs_list = ", ".join(available_pairs)
    
    analysis_prompt = f"""
Event: {currency} {event_name}
Forecast: {forecast}
Actual: {actual}

Available trading pairs: {pairs_list}

Generate trading signals for pairs containing {currency}. Return ONLY in the exact output format specified - no explanations, no reasoning, just the final output line.
"""
    
    return query_chatgpt(analysis_prompt, rules_instructions)


# Test function
if __name__ == "__main__":
    result = query_chatgpt("Hello")
    print(f"ChatGPT: {result}")

