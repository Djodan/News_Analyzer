"""
Main AI orchestration module for News trading.
Coordinates between Perplexity (data extraction) and ChatGPT (validation + trading signals).

NOTE: This file contains EXAMPLE/TEST implementations.
      These functions demonstrate the AI pipeline architecture and data flow.
      They are templates to be used when building the real News.py algorithm.
      The actual implementation should follow News_Flow.txt blueprint.
"""

import AI_Perplexity
import AI_ChatGPT
import Globals
import re


def process_news_event(event_name, currency, date, request_type="both"):
    """
    Main function to process a news event through the AI pipeline.
    
    ⚠️ EXAMPLE FUNCTION - Template for real implementation
    
    Flow:
    1. Query Perplexity for news data (Forecast/Actual)
    2. Validate format with ChatGPT
    3. If both values available, generate trading signals with ChatGPT
    4. Update Globals._Currencies_ and Globals._Affected_ dictionaries
    
    Args:
        event_name (str): Name of the news event (e.g., "Unemployment Rate")
        currency (str): Currency code (e.g., "EUR", "USD")
        date (str): Event date (e.g., "Nov 03, 04:10")
        request_type (str): "forecast", "actual", or "both"
        
    Returns:
        dict: {
            "perplexity_raw": str,
            "validated_data": str,
            "forecast": float or None,
            "actual": float or None,
            "affect": str or None,
            "trading_signals": str or None
        }
    """
    result = {
        "perplexity_raw": None,
        "validated_data": None,
        "forecast": None,
        "actual": None,
        "affect": None,
        "trading_signals": None
    }
    
    print(f"\n{'='*80}")
    print(f"PROCESSING EVENT: {currency} {event_name}")
    print(f"Date: {date}")
    print(f"Request Type: {request_type}")
    print(f"{'='*80}\n")
    
    # STEP 1: Query Perplexity for news data
    print("[STEP 1] Querying Perplexity for news data...")
    perplexity_response = AI_Perplexity.get_news_data(event_name, currency, date, request_type)
    result["perplexity_raw"] = perplexity_response
    print(f"Perplexity Response: {perplexity_response}")
    
    # STEP 2: Validate with ChatGPT
    print("\n[STEP 2] Validating format with ChatGPT...")
    validated_response = AI_ChatGPT.validate_news_data(perplexity_response)
    result["validated_data"] = validated_response
    print(f"ChatGPT Validated: {validated_response}")
    
    # STEP 3: Extract values using regex
    print("\n[STEP 3] Extracting values...")
    
    # Check for Source line
    source_match = re.search(r"Source\s*:\s*(.+)", validated_response)
    if source_match:
        source = source_match.group(1).strip()
        print(f"Source: {source}")
        if source != "MyFxBook":
            print(f"⚠️  WARNING: Data source is '{source}', not MyFxBook!")
    else:
        print("⚠️  WARNING: No source line found in response!")
    
    # Try to extract Forecast
    forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", validated_response)
    if forecast_match:
        forecast_str = forecast_match.group(1)
        if forecast_str != "N/A":
            result["forecast"] = float(forecast_str)
            print(f"Forecast: {result['forecast']}")
        else:
            print("Forecast: N/A")
    
    # Try to extract Actual
    actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+)", validated_response)
    if actual_match:
        result["actual"] = float(actual_match.group(1))
        print(f"Actual: {result['actual']}")
    elif "FALSE" in validated_response:
        print("Actual: Not released yet (FALSE)")
    
    # STEP 4: Calculate affect if both values available
    if result["forecast"] is not None and result["actual"] is not None:
        affect_value = ((result["actual"] - result["forecast"]) / result["forecast"]) * 100
        result["affect"] = f"{affect_value:.2f}%"
        print(f"Affect: {result['affect']}")
        
        # STEP 5: Generate trading signals
        print("\n[STEP 4] Generating trading signals with ChatGPT...")
        trading_signals = AI_ChatGPT.generate_trading_signals(
            currency, 
            event_name, 
            result["forecast"], 
            result["actual"]
        )
        result["trading_signals"] = trading_signals
        print(f"Trading Signals: {trading_signals}")
        
        # STEP 6: Update Globals._Currencies_ dictionary
        print("\n[STEP 5] Updating _Currencies_ dictionary...")
        Globals._Currencies_[currency] = {
            "date": date,
            "event": event_name,
            "forecast": result["forecast"],
            "actual": result["actual"],
            "affect": result["affect"],
            "retry_count": 0
        }
        print(f"_Currencies_[{currency}] = {Globals._Currencies_[currency]}")
        
        # STEP 7: Update Globals._Affected_ dictionary for each pair
        print("\n[STEP 6] Updating _Affected_ dictionary...")
        
        # Parse trading signals
        if trading_signals and trading_signals != "NEUTRAL":
            pairs = trading_signals.split(", ")
            for pair_action in pairs:
                if " : " in pair_action:
                    pair, action = pair_action.split(" : ")
                    Globals._Affected_[pair.strip()] = {
                        "date": date,
                        "event": f"{currency} {event_name}",
                        "position": action.strip()
                    }
                    print(f"_Affected_[{pair.strip()}] = {Globals._Affected_[pair.strip()]}")
        else:
            print("Trading signals: NEUTRAL - No pairs affected")
    else:
        print("\n[STEP 4] Skipping trading signals (insufficient data)")
    
    print(f"\n{'='*80}")
    print("PROCESSING COMPLETE")
    print(f"{'='*80}\n")
    
    return result


# Test with the EUR Unemployment Rate event
if __name__ == "__main__":
    result = process_news_event(
        event_name="HCOB Manufacturing PMI (Oct)",
        currency="EUR",
        date="Nov 03, 03:55",
        request_type="both"
    )
    
    print("\n" + "="*80)
    print("FINAL RESULT:")
    print("="*80)
    for key, value in result.items():
        print(f"{key}: {value}")
    
    print("\n" + "="*80)
    print("GLOBALS DICTIONARIES:")
    print("="*80)
    print(f"\n_Currencies_:")
    for currency, data in Globals._Currencies_.items():
        print(f"  {currency}: {data}")
    
    print(f"\n_Affected_:")
    for pair, data in Globals._Affected_.items():
        print(f"  {pair}: {data}")

