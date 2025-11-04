# News Analyzer - Modular Architecture

## Overview
The News Analyzer system follows a clean modular architecture with clear separation of concerns:

## Core Modules

### Server.py
**Purpose**: HTTP communication routing and orchestration
**Responsibilities**:
- Handle HTTP GET/POST requests
- Route requests to appropriate functions
- Orchestrate algorithm execution (e.g., call TestingMode)
- Display console output and status logging
- NO business logic - purely communication layer

**Endpoints**:
- `GET /command/<id>` - EA polls for next command
- `POST /` - EA sends trade snapshot
- `POST /command/<id>` - Manual API: enqueue command
- `POST /ack/<id>` - EA acknowledges command execution
- `GET /clients` - List all clients
- `GET /clients/<id>/open` - Get client's open positions
- `GET /clients/<id>/closed_online` - Get client's closed positions

### Functions.py
**Purpose**: Business logic and state management
**Responsibilities**:
- Command queue management (`enqueue_command`, `get_next_command`, `ack_command`)
- Client state tracking (`get_client_open`, `get_client_closed_online`)
- Payload processing (`ingest_payload`, `process_ack_response`)
- Statistics tracking (`get_client_stats`, `record_command_delivery`)
- Client lifecycle management (`is_client_online`, `list_clients`)

**Key Functions**:
- `process_ack_response(client_id, cmd_id, success, details)` - Processes ACK and extracts trade info for logging

### TestingMode.py
**Purpose**: Testing algorithm module
**Responsibilities**:
- Implement specific trading algorithm logic
- Inject commands at appropriate times
- Self-contained and independent

**Pattern**: Each algorithm should be its own file following this pattern

### Globals.py
**Purpose**: Global configuration and settings
**Responsibilities**:
- Store configuration flags (e.g., `TestingMode`, `MAIN_MT5_ACCOUNT`)
- Define shared constants

## Data Flow

### EA → Python (Trade Snapshot)
1. EA sends POST to `/` with trade data
2. Server.py routes to `Functions.ingest_payload()`
3. Functions.py processes and stores per-client state
4. Server.py logs summary to console

### Python → EA (Command)
1. Algorithm (e.g., TestingMode) calls `Functions.enqueue_command()`
2. EA polls GET `/command/<id>`
3. Server.py calls `Functions.get_next_command()`
4. Server.py returns command to EA
5. Server.py logs command to console

### EA → Python (Acknowledgement)
1. EA sends POST to `/ack/<id>` with execution results
2. Server.py routes to `Functions.process_ack_response()`
3. Functions.py processes ACK and extracts trade details
4. Server.py logs formatted trade info to console

### Manual API (External Control)
1. External system sends POST to `/command/<id>`
2. Server.py routes to `Functions.enqueue_command()`
3. Same flow as algorithm-generated commands

## Design Principles

1. **Separation of Concerns**
   - Server.py = Communication layer only
   - Functions.py = Business logic
   - <Algorithm>.py = Trading strategy

2. **Modularity**
   - Each algorithm is a separate file
   - Algorithms can be enabled/disabled via Globals
   - New algorithms can be added without modifying existing code

3. **Single Responsibility**
   - Each module has one clear purpose
   - Functions are focused and reusable
   - No duplicate business logic

4. **Testability**
   - Business logic is separate from HTTP handling
   - Functions can be unit tested independently
   - Algorithms can be tested in isolation

## Adding New Algorithms

To add a new trading algorithm:

1. Create `YourAlgorithm.py` in the News_Analyzer directory
2. Implement `handle_your_algorithm(client_id, stats)` function (snake_case)
3. Add "YourAlgorithm" to `Globals.ModesList` (CamelCase)
4. Set `Globals.ModeSelect = "YourAlgorithm"` to activate it
5. Server.py will automatically route to your algorithm via dynamic import

**Important**: The handler function must be named using snake_case conversion of the module name:
- Module: `TestingMode.py` → Handler: `handle_testing_mode()`
- Module: `LiveTrading.py` → Handler: `handle_live_trading()`
- Module: `NewsTrading.py` → Handler: `handle_news_trading()`
- Module: `MyStrategy.py` → Handler: `handle_my_strategy()`

The conversion is automatic using a CamelCase → snake_case converter.

Example:
```python
# MyStrategy.py
from Functions import enqueue_command

def handle_my_strategy(client_id, stats):
    """
    Handler function for MyStrategy algorithm.
    Must return True if a command was injected, False otherwise.
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: True if command was injected, False otherwise
    """
    # Your trading logic here
    replies = int(stats.get("replies", 0))
    
    if condition_met:
        enqueue_command(client_id, state=1, payload={
            "symbol": "XAUUSD",
            "volume": 0.01,
            "tpPips": 50,
            "slPips": 25
        })
        return True
    return False
```

Then in `Globals.py`:
```python
ModesList = [
    "TestingMode",
    "MyStrategy",  # Add your algorithm here (CamelCase)
]

ModeSelect = "MyStrategy"  # Select which algorithm to use
```

## Algorithm Selection

The system uses dynamic routing controlled by two variables in `Globals.py`:

- **ModesList**: List of all available algorithms
- **ModeSelect**: The currently active algorithm (must be in ModesList)

Server.py automatically imports and executes the selected algorithm without code changes. Simply update `Globals.ModeSelect` to switch between algorithms.

## File Structure
```
News_Analyzer/
├── News_Analyzer.mq5        # Main EA
├── Server.py                 # HTTP server (communication only)
├── Functions.py              # Business logic
├── TestingMode.py            # Example algorithm
├── Globals.py                # Configuration (ModesList, ModeSelect)
├── *.mqh                     # MQL5 include files
└── ARCHITECTURE.md           # This file
```
