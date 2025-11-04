"""
Test script to verify dynamic algorithm routing works correctly
"""

import sys
import importlib
import re


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for handler function names."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Simulate Globals
class MockGlobals:
    ModesList = ["TestingMode"]
    ModeSelect = "TestingMode"

# Test dynamic import and function call
selected_mode = MockGlobals.ModeSelect
modes_list = MockGlobals.ModesList

print(f"Testing dynamic routing...")
print(f"ModesList: {modes_list}")
print(f"ModeSelect: {selected_mode}")

if selected_mode and selected_mode in modes_list:
    print(f"\n✓ Selected mode '{selected_mode}' is in ModesList")
    
    # Dynamically import the module
    try:
        algorithm_module = importlib.import_module(selected_mode)
        print(f"✓ Successfully imported module: {selected_mode}")
    except ImportError as e:
        print(f"✗ Failed to import module: {e}")
        sys.exit(1)
    
    # Check for handler function using camel_to_snake conversion
    handler_name = f"handle_{camel_to_snake(selected_mode)}"
    print(f"\nConverted '{selected_mode}' to handler name: '{handler_name}'")
    
    if hasattr(algorithm_module, handler_name):
        print(f"✓ Found handler function: {handler_name}")
        handler_func = getattr(algorithm_module, handler_name)
        print(f"✓ Handler function: {handler_func}")
        print(f"\n✓ Dynamic routing is working correctly!")
    else:
        print(f"✗ Handler function '{handler_name}' not found")
        print(f"  Available functions: {[attr for attr in dir(algorithm_module) if not attr.startswith('_')]}")
        sys.exit(1)
else:
    print(f"✗ Selected mode '{selected_mode}' not in ModesList")
    sys.exit(1)

print("\n✓ All tests passed!")
