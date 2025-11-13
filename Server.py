"""
Simple HTTP server to receive JSON payloads from the News Analyzer EA.
- Expects POST requests with Content-Type: application/json
- Logs a summary to stdout and appends full payloads to received_log.jsonl
- No external dependencies (uses Python standard library)

Usage (PowerShell):
    python Server.py --host 0.0.0.0 --port 5000

In MetaTrader 5, add this URL to:
  Tools > Options > Expert Advisors > Allow WebRequest for listed URL:
  http://<host>:<port>
"""

# Check and install required packages before importing anything else
import check_packages
check_packages.check_and_install_packages()

import argparse
import os
import json
import sys
import importlib
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple
from datetime import datetime
import Globals
import Functions
from Functions import (
    now_iso,
    ingest_payload,
    get_next_command,
    record_command_delivery,
    get_client_open,
    get_client_closed_online,
    list_clients,
    enqueue_command,
    ack_command,
    process_ack_response,
    get_client_mode,
    get_client_stats,
    is_client_online,
    display_idle_screen,
)
from save_news_dictionaries import save_news_dictionaries
import subprocess


class TeeOutput:
    """
    Custom output stream that writes to both stdout and a log file.
    This allows all print statements to be automatically logged to Output.txt.
    """
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, 'a', encoding='utf-8', buffering=1)  # Line buffering
        # Write session header
        self.log.write(f"\n{'='*80}\n")
        self.log.write(f"SERVER SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log.write(f"{'='*80}\n")
        self.log.flush()
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # Ensure immediate write to file
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        if hasattr(self, 'log') and self.log:
            self.log.write(f"\n{'='*80}\n")
            self.log.write(f"SERVER SESSION ENDED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log.write(f"{'='*80}\n\n")
            self.log.close()


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for handler function names."""
    # Insert underscore before uppercase letters (except at start)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore before uppercase letters that follow lowercase
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class NewsAnalyzerRequestHandler(BaseHTTPRequestHandler):
    server_version = "NewsAnalyzerHTTP/1.0"

    def log_message(self, format: str, *args) -> None:
        # Silence default HTTP logs to avoid noisy JSON prints.
        return

    def _send_json(self, code: int, payload: dict) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        # Simple health check
        if self.path in ("/", "/health", "/status"):
            self._send_json(200, {"status": "ok", "ts": now_iso()})
            return

        # Back-compat message
        if self.path == "/message":
            self._send_json(200, {"message": getattr(Globals, "test_message", "")})
            return

        # EA polls next command: /command/<id>
        if self.path.startswith("/command/"):
            parts = [p for p in self.path.split("/") if p]
            if len(parts) == 2:
                client_id = parts[1]
                msg = get_next_command(client_id)
                # Record delivery stats based on current planned state
                int_state = 0
                if "state" in msg:
                    try:
                        int_state = int(msg.get("state", 0))
                    except Exception:
                        int_state = 0
                stats = record_command_delivery(client_id, int_state)
                
                # Dynamic Algorithm Routing: Load and execute selected mode
                try:
                    selected_mode = getattr(Globals, "ModeSelect", None)
                    modes_list = getattr(Globals, "ModesList", [])
                    
                    if selected_mode and selected_mode in modes_list:
                        # Dynamically import the selected algorithm module
                        algorithm_module = importlib.import_module(selected_mode)
                        
                        # Call the algorithm's handler function
                        # Convention: handle_<snake_case_name> e.g., TestingMode -> handle_testing_mode
                        handler_name = f"handle_{camel_to_snake(selected_mode)}"
                        if hasattr(algorithm_module, handler_name):
                            handler_func = getattr(algorithm_module, handler_name)
                            injected = handler_func(client_id, stats)
                            if injected:
                                print(f"Server: INJECTED command for Client: [{client_id}] ({selected_mode})")
                                # Save dictionaries after algorithm execution
                                save_news_dictionaries()
                                # Refresh command if one was injected and current state is 0
                                if int(msg.get("state", 0)) == 0:
                                    msg = get_next_command(client_id)
                        else:
                            print(f"Warning: Algorithm '{selected_mode}' does not have '{handler_name}' function")
                    elif selected_mode and selected_mode not in modes_list:
                        print(f"Warning: Selected mode '{selected_mode}' not in ModesList")
                except Exception as e:
                    print(f"Error loading algorithm: {e}")
                    pass
                
                # Build a list of MetaTrader clients and print status
                eff_state = 0
                try:
                    eff_state = int(msg.get("state", 0))
                except Exception:
                    eff_state = 0
                try:
                    # Include the currently polling client even if it hasn't posted a snapshot yet
                    all_ids = sorted(set(list_clients()) | {str(client_id)})
                    for cid in all_ids:
                        # Determine platform prefix
                        mode_label = get_client_mode(cid)
                        prefix = "Metatrader -"
                        # Open count
                        try:
                            oc = len(get_client_open(cid))
                        except Exception:
                            oc = 0
                        # Last action for that client
                        try:
                            la = int(get_client_stats(cid).get("last_action", 0))
                        except Exception:
                            la = 0
                        # State logic: MetaTrader always Online
                        state_str = "Online"
                        # Colorize State text: green for Online
                        color = "\x1b[32m"
                        reset = "\x1b[0m"
                        try:
                            show = bool(getattr(Globals, "PRINT_STATUS_LINES", False))
                        except Exception:
                            show = False
                        if show:
                            sys.stdout.write(f"{prefix} {color}State {state_str}{reset} ID={cid} Open={oc} LastAction={la} Replies={stats['replies']}\n")
                except Exception:
                    pass
                # New concise view: main MT5 account
                try:
                    main_id = str(getattr(Globals, "MAIN_MT5_ACCOUNT", ""))
                except Exception:
                    main_id = ""
                try:
                    if main_id:
                        main_open = get_client_open(main_id)
                        sys.stdout.write(f"Trades on main account : {len(main_open)}\n")
                        for p in main_open:
                            try:
                                side = "BUY" if int(p.get("type", 0)) == 0 else "SELL"
                            except Exception:
                                side = str(p.get("type"))
                            entry = p.get("openPrice", None)
                            if entry is None:
                                entry = p.get("price")
                            vol = p.get("volume")
                            tpv = p.get("tp")
                            slv = p.get("sl")
                            sys.stdout.write(f"  Type\n    {side}\n")
                            sys.stdout.write(f"  Entry\n    {entry}\n")
                            sys.stdout.write(f"  Volume\n    {vol}\n")
                            if vol is not None:
                                try:
                                    sys.stdout.write(f"  size\n    {int(vol)}\n")
                                except Exception:
                                    pass
                            sys.stdout.write(f"  TP\n    {tpv}\n")
                            sys.stdout.write(f"  SL\n    {slv}\n")
                except Exception:
                    pass
                # Optional: print each open trade's entry, TP, and SL (diagnostic)
                try:
                    def _truthy(v):
                        return str(v).strip().lower() in ("1", "true", "yes", "on")
                    dbg_env = os.environ.get("NEWS_ANALYZER_PRINT_OPEN_DETAILS", "")
                    dbg_glob = getattr(Globals, "PRINT_OPEN_DETAILS", "")
                    if _truthy(dbg_env) or _truthy(dbg_glob):
                        # MT5 client open details
                        opens = get_client_open(client_id)
                        for pos in opens:
                            sym = pos.get("symbol")
                            tkt = pos.get("ticket")
                            entry = pos.get("openPrice", None)
                            if entry is None:
                                entry = pos.get("price")
                            tpv = pos.get("tp")
                            slv = pos.get("sl")
                            sys.stdout.write(f"[{now_iso()}] OPEN {sym} ticket={tkt} entry={entry} TP={tpv} SL={slv}\n")
                except Exception:
                    pass
                # If this is an open order command, also print a single summary line
                if eff_state in (1,2):
                    side = "BUY" if eff_state==1 else "SELL"
                    sym = msg.get("symbol")
                    vol = msg.get("volume")
                    tp = msg.get("tp") if "tp" in msg else msg.get("tpPips")
                    sl = msg.get("sl") if "sl" in msg else msg.get("slPips")
                    print(f"Server: Sending {side} command to Client: [{client_id}] - {sym} Vol={vol} TP={tp} SL={sl}")
                elif eff_state == 3:
                    print(f"Server: Sending CLOSE command to Client: [{client_id}]")
                self._send_json(200, msg)
            else:
                self._send_json(400, {"error": "bad_path"})
            return

        # Client views
        if self.path.startswith("/clients"):
            parts = [p for p in self.path.split("/") if p]
            if len(parts) == 1:  # /clients
                self._send_json(200, {"clients": list_clients()})
                return
            if len(parts) >= 2:
                client_id = parts[1]
                if len(parts) == 3 and parts[2] == "open":
                    self._send_json(200, {"id": client_id, "open": get_client_open(client_id)})
                    return
                if len(parts) == 3 and parts[2] == "closed_online":
                    self._send_json(200, {"id": client_id, "closed_online": get_client_closed_online(client_id)})
                    return
                # default: client summary
                self._send_json(200, {
                    "id": client_id,
                    "open_count": len(get_client_open(client_id)),
                    "closed_online_count": len(get_client_closed_online(client_id)),
                })
                return

        # Not found
        self._send_json(404, {"status": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body.decode("utf-8"))
        except Exception as exc:  # malformed JSON
            self.log_message("Malformed JSON from %s: %s", self.client_address[0], exc)
            self._send_json(400, {"status": "error", "error": "invalid_json"})
            return

        # Routes: payload ingest or command enqueue/ack
        path = self.path
        if path == "/":
            # Process and store per-client snapshots
            summary, identity = ingest_payload(data)
            self.log_message(
                "Received payload: id=%s mode=%s open=%d",
                identity.get("id"), identity.get("mode"), summary.get("open", 0)
            )
            
            # Get symbols currently open from Globals
            symbols_open = getattr(Globals, "symbolsCurrentlyOpen", [])
            symbols_str = ", ".join(symbols_open) if symbols_open else "None"
            
            # Display idle screen in live mode, or print details in debug mode
            if Globals.liveMode:
                display_idle_screen(
                    client_id=str(identity.get('id')),
                    open_count=summary.get('open', 0),
                    closed_count=summary.get('closed_online', 0)
                )
            else:
                # Print incoming communication from MT5 (debug mode only)
                print(f"Client: [{identity.get('id')}] - Sent snapshot with {summary.get('open')} open, {summary.get('closed_online')} closed online")
                print(f"  Symbols Currently Open: [{symbols_str}]")
            
            # Save news dictionaries snapshot to file (overwrites previous)
            save_news_dictionaries()
            
            self._send_json(200, {"status": "ok", "received": summary, **identity})
            return

        if path.startswith("/command/"):
            # Enqueue a command to a client: POST /command/<id>
            parts = [p for p in path.split("/") if p]
            if len(parts) == 2:
                client_id = parts[1]
                # Expect { state: 0|1|2|3, payload?: {...} }
                state = int(data.get("state", 0))
                payload = data.get("payload") or {}
                cmd = enqueue_command(client_id, state, payload)
                self._send_json(200, {"status": "queued", "command": cmd})
                return
            self._send_json(400, {"error": "bad_path"})
            return

        if path.startswith("/ack/"):
            # EA acknowledges a command: POST /ack/<id>
            parts = [p for p in path.split("/") if p]
            if len(parts) == 2:
                client_id = parts[1]
                cmd_id = data.get("cmdId")
                success = bool(data.get("success", False))
                details = data.get("details") or {}
                
                # Process ACK through Functions.py
                ack_result = process_ack_response(client_id, cmd_id, success, details)
                
                # Log trade info
                trade_info = ack_result.get("trade_info", {})
                print(f"Client: [{trade_info['client_id']}] - ACK cmdId={cmd_id} success={trade_info['success']} "
                      f"Symbol={trade_info['symbol']} Type={trade_info['type']} Vol={trade_info['volume']} "
                      f"Price={trade_info['price']} TP={trade_info['tp']} SL={trade_info['sl']}")
                
                self._send_json(200, ack_result["result"])
                return
            self._send_json(400, {"error": "bad_path"})
            return

        if path == "/trade_outcome":
            # EA reports trade closure: POST /trade_outcome
            # Expected payload: { ticket: 12345, outcome: "TP" | "SL" }
            # Uses ticket number to match the trade and update NID counters
            from Functions import update_trade_outcome_by_ticket
            
            ticket = data.get("ticket")
            outcome = data.get("outcome")
            
            if not ticket or outcome not in ["TP", "SL"]:
                self._send_json(400, {"error": "invalid_payload", "expected": {"ticket": "int", "outcome": "TP|SL"}})
                return
            
            result = update_trade_outcome_by_ticket(ticket, outcome)
            
            if result.get("ok"):
                tid = result.get('TID')
                nid = result.get('NID')
                symbol = result.get('symbol')
                print(f"Server: Trade {tid} ({symbol}, Ticket: {ticket}) closed at {outcome} (NID_{nid})")
                self._send_json(200, result)
            else:
                self._send_json(400, result)
            return

        # Default: unknown POST route
        self._send_json(404, {"status": "not_found"})


def parse_args(argv=None) -> Tuple[str, int]:
    """
    Parse command-line arguments for host and port.
    Falls back to Globals.SERVER_HOST and Globals.SERVER_PORT if not provided.
    """
    parser = argparse.ArgumentParser(description="News Analyzer JSON receiver")
    parser.add_argument("--host", default=None, help=f"Bind address (default: {Globals.SERVER_HOST})")
    parser.add_argument("--port", default=None, type=int, help=f"Port to listen on (default: {Globals.SERVER_PORT})")
    args = parser.parse_args(argv)
    
    # Use command-line args if provided, otherwise use Globals
    host = args.host if args.host is not None else Globals.SERVER_HOST
    port = args.port if args.port is not None else Globals.SERVER_PORT
    
    return host, port


def main() -> None:
    # Setup automatic logging to Output.txt
    log_file = os.path.join(os.path.dirname(__file__), 'Output.txt')
    
    # Clear Output.txt at the start of each server session
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("NEWS ANALYZER - OUTPUT LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("Purpose: Log all server outputs for diagnostics and debugging\n")
            f.write("=" * 80 + "\n\n")
    except Exception as e:
        print(f"Warning: Could not clear Output.txt: {e}")
    
    tee = TeeOutput(log_file)
    sys.stdout = tee
    
    try:
        # Clear terminal on start (Windows: cls, others: clear)
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except Exception:
            pass
        
        # Display selected mode
        selected_mode = getattr(Globals, "ModeSelect", "Unknown")
        modes_list = getattr(Globals, "ModesList", [])
        
        print("=" * 60)
        print("NEWS ANALYZER SERVER")
        print("=" * 60)
        print(f"Selected Mode: {selected_mode}")
        print(f"Current Strategy: S{Globals.news_strategy} (from Globals.py default)")
        
        if selected_mode not in modes_list:
            print(f"WARNING: '{selected_mode}' is not in ModesList!")
            print(f"Available modes: {', '.join(modes_list)}")
        
        print("=" * 60)
        print(f"Logging to: {log_file}")
        print("=" * 60)
        
        host, port = parse_args()
        server = HTTPServer((host, port), NewsAnalyzerRequestHandler)
        print(f"[{now_iso()}] Listening on http://{host}:{port} (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n[{now_iso()}] Shutting down...")
        finally:
            server.server_close()
    finally:
        # Restore stdout and close log file
        sys.stdout = tee.terminal
        tee.close()


if __name__ == "__main__":
    main()
