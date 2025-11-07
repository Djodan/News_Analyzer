import sys
sys.path.insert(0, '..')

"""
Test Multiple Events at Same Time
==================================

This test verifies that the AI correctly handles multiple events
occurring at the same timestamp for the same currency according to
the rules in News_Rules.txt STEP 2.

Test Scenarios:
1. All events same direction (all POSITIVE) → Use shared direction
2. All events same direction (all NEGATIVE) → Use shared direction
3. Conflicting events (POSITIVE + NEGATIVE) → Use impact hierarchy
4. Equal impact conflict → NEUTRAL
5. One event incomplete (N/A) → Ignore and use complete events
"""

import json
from datetime import datetime
from openai import OpenAI
import os

# Import API key from config
try:
    from config import API_KEY_GPT
except ImportError:
    API_KEY_GPT = os.environ.get("OPENAI_API_KEY", "")

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY_GPT)

# Available pairs
PAIRS = ["GBPAUD", "GBPCHF", "GBPJPY", "GBPUSD", "EURGBP", "GBPNZD", "GBPCAD"]

def load_rules():
    """Load the News_Rules.txt instruction set"""
    with open("News_Rules.txt", "r", encoding="utf-8") as f:
        return f.read()

def ask_ai(events_data, pairs):
    """
    Ask AI to analyze multiple events at same time
    
    events_data: list of dicts with keys: event, forecast, actual, currency, country
    pairs: list of available trading pairs
    """
    
    rules = load_rules()
    
    # Build the prompt
    events_desc = "\n".join([
        f"- {e['currency']} ({e['country']}) {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}"
        for e in events_data
    ])
    
    prompt = f"""
{rules}

═══════════════════════════════════════════════════════════════════════════════

MULTIPLE EVENTS AT SAME TIME:

{events_desc}

Available trading pairs: {', '.join(pairs)}

Remember STEP 2: Multiple Events at the Same Time rules.

Output your trading decision:
"""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a forex trading signal generator. Follow the rules exactly."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

def test_scenario_1_all_positive():
    """Test: All events point POSITIVE → Should use shared direction"""
    print("\n" + "="*80)
    print("TEST 1: All Events Same Direction (POSITIVE)")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Unemployment Rate",
            "forecast": "4.5%",
            "actual": "4.2%"  # Lower unemployment = POSITIVE
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Employment Change",
            "forecast": "50K",
            "actual": "75K"  # Higher employment = POSITIVE
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: GBP STRENGTHENS → All GBP-base pairs BUY")
    print(f"AI Response: {result}")
    
    # Check if response indicates BUY for GBP pairs
    if "BUY" in result and "GBPAUD" in result:
        print("✅ PASS: AI correctly identified shared POSITIVE direction")
    else:
        print("❌ FAIL: AI did not handle all-positive events correctly")
    
    return result

def test_scenario_2_all_negative():
    """Test: All events point NEGATIVE → Should use shared direction"""
    print("\n" + "="*80)
    print("TEST 2: All Events Same Direction (NEGATIVE)")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "GDP Growth Rate",
            "forecast": "0.5%",
            "actual": "0.2%"  # Lower GDP = NEGATIVE
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Manufacturing PMI",
            "forecast": "52.0",
            "actual": "48.5"  # Below 50 = NEGATIVE
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: GBP WEAKENS → All GBP-base pairs SELL")
    print(f"AI Response: {result}")
    
    if "SELL" in result and "GBPAUD" in result:
        print("✅ PASS: AI correctly identified shared NEGATIVE direction")
    else:
        print("❌ FAIL: AI did not handle all-negative events correctly")
    
    return result

def test_scenario_3_conflict_monetary_wins():
    """Test: Conflict → Monetary (highest impact) should win"""
    print("\n" + "="*80)
    print("TEST 3: Conflicting Events → Monetary Wins (Impact Hierarchy)")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Interest Rate Decision",
            "forecast": "5.00%",
            "actual": "5.25%"  # Rate increase = POSITIVE (Monetary - highest)
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Retail Sales",
            "forecast": "0.5%",
            "actual": "0.1%"  # Lower sales = NEGATIVE (Activity - lower)
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    print("\nImpact Hierarchy: Monetary > Inflation > Jobs > GDP > Trade > Activity")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: Monetary wins → GBP STRENGTHENS → BUY")
    print(f"AI Response: {result}")
    
    if "BUY" in result:
        print("✅ PASS: AI correctly used Monetary as tiebreaker")
    else:
        print("❌ FAIL: AI did not follow impact hierarchy")
    
    return result

def test_scenario_4_conflict_inflation_wins():
    """Test: Conflict without Monetary → Inflation should win"""
    print("\n" + "="*80)
    print("TEST 4: Conflicting Events → Inflation Wins Over Jobs")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "CPI (Consumer Price Index)",
            "forecast": "2.5%",
            "actual": "3.1%"  # Higher inflation = POSITIVE (Inflation)
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Unemployment Rate",
            "forecast": "4.0%",
            "actual": "4.5%"  # Higher unemployment = NEGATIVE (Jobs)
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    print("\nImpact Hierarchy: Monetary > Inflation > Jobs")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: Inflation wins → GBP STRENGTHENS → BUY")
    print(f"AI Response: {result}")
    
    if "BUY" in result:
        print("✅ PASS: AI correctly prioritized Inflation over Jobs")
    else:
        print("❌ FAIL: AI did not follow impact hierarchy")
    
    return result

def test_scenario_5_equal_impact_conflict():
    """Test: Equal impact + conflict → NEUTRAL"""
    print("\n" + "="*80)
    print("TEST 5: Equal Impact Conflict → Should Return NEUTRAL")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Manufacturing PMI",
            "forecast": "50.0",
            "actual": "52.5"  # POSITIVE (Activity)
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Services PMI",
            "forecast": "53.0",
            "actual": "49.0"  # NEGATIVE (Activity - same level)
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    print("\nBoth are Activity level → Same impact → Conflict → NEUTRAL")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: NEUTRAL")
    print(f"AI Response: {result}")
    
    if result == "NEUTRAL":
        print("✅ PASS: AI correctly returned NEUTRAL for equal-impact conflict")
    else:
        print("❌ FAIL: AI should return NEUTRAL for equal-impact conflicts")
    
    return result

def test_scenario_6_ignore_incomplete():
    """Test: One event N/A → Ignore it, use complete events"""
    print("\n" + "="*80)
    print("TEST 6: Incomplete Event (N/A) → Ignore and Use Complete Events")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "GDP Growth Rate",
            "forecast": "N/A",
            "actual": "0.5%"  # Incomplete (Forecast N/A)
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Unemployment Rate",
            "forecast": "4.5%",
            "actual": "4.2%"  # POSITIVE (Complete - use this)
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: Ignore GDP (N/A), use Unemployment → GBP STRENGTHENS → BUY")
    print(f"AI Response: {result}")
    
    if "BUY" in result:
        print("✅ PASS: AI correctly ignored incomplete event")
    else:
        print("❌ FAIL: AI should ignore N/A events and use complete data")
    
    return result

def test_scenario_7_all_incomplete():
    """Test: All events N/A → NEUTRAL"""
    print("\n" + "="*80)
    print("TEST 7: All Events Incomplete → Should Return NEUTRAL")
    print("="*80)
    
    events = [
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "GDP Growth Rate",
            "forecast": "N/A",
            "actual": "0.5%"
        },
        {
            "currency": "GBP",
            "country": "United Kingdom",
            "event": "Trade Balance",
            "forecast": "5.0B",
            "actual": "N/A"
        }
    ]
    
    print("\nEvents:")
    for e in events:
        print(f"  - {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}")
    
    result = ask_ai(events, PAIRS)
    
    print(f"\nExpected: NEUTRAL (all incomplete)")
    print(f"AI Response: {result}")
    
    if result == "NEUTRAL":
        print("✅ PASS: AI correctly returned NEUTRAL for all-incomplete events")
    else:
        print("❌ FAIL: AI should return NEUTRAL when all events incomplete")
    
    return result

def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("TESTING MULTIPLE EVENTS AT SAME TIME - RULE COMPLIANCE")
    print("="*80)
    print("\nThis test verifies News_Rules.txt STEP 2 is followed correctly")
    print("Testing against GBP events with pairs:", ", ".join(PAIRS))
    
    results = {}
    
    try:
        results['test1'] = test_scenario_1_all_positive()
        results['test2'] = test_scenario_2_all_negative()
        results['test3'] = test_scenario_3_conflict_monetary_wins()
        results['test4'] = test_scenario_4_conflict_inflation_wins()
        results['test5'] = test_scenario_5_equal_impact_conflict()
        results['test6'] = test_scenario_6_ignore_incomplete()
        results['test7'] = test_scenario_7_all_incomplete()
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n✅ All tests completed. Results saved to test_results.json")
        print("\nManual review recommended to verify AI responses align with rules.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check for API key
    if not API_KEY_GPT:
        print("❌ ERROR: API_KEY_GPT not set in config.py")
        print("Please add your OpenAI API key to config.py")
    else:
        run_all_tests()
