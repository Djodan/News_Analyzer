"""
Test Plain mode routing
"""

import sys
import importlib
import re


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for handler function names."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Test Plain mode
selected_mode = "Plain"

print(f"Testing Plain mode routing...")
print(f"Selected mode: {selected_mode}")

try:
    # Dynamically import the module
    algorithm_module = importlib.import_module(selected_mode)
    print(f"✓ Successfully imported module: {selected_mode}")
    
    # Check for handler function
    handler_name = f"handle_{camel_to_snake(selected_mode)}"
    print(f"Handler name: {handler_name}")
    
    if hasattr(algorithm_module, handler_name):
        print(f"✓ Found handler function: {handler_name}")
        handler_func = getattr(algorithm_module, handler_name)
        
        # Test calling the function
        mock_client_id = "123456"
        mock_stats = {"replies": 1}
        result = handler_func(mock_client_id, mock_stats)
        
        print(f"✓ Handler executed successfully")
        print(f"  Returned: {result} (should be False for Plain mode)")
        
        if result == False:
            print(f"\n✓ Plain mode is working correctly!")
        else:
            print(f"\n✗ Plain mode returned {result}, expected False")
            sys.exit(1)
    else:
        print(f"✗ Handler function '{handler_name}' not found")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All Plain mode tests passed!")
