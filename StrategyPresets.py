"""
StrategyPresets.py
Centralized strategy configuration presets for News Analyzer strategies S1-S5.
Call apply_strategy_preset() with strategy number to configure all related Globals settings.

Updated: 2025-11-09
- Verified against .newsStrategy documentation files
- Aligned with risk profiles, data capture requirements, and Globals reference
- Implements all 28 trade-level fields + 20 strategy-level metrics
"""

import Globals


def apply_strategy_preset(strategy_id: int, verbose: bool = True):
    """
    Apply complete preset configuration for a given strategy.
    
    Args:
        strategy_id: Strategy number (0-5)
            0 = S0 (No Preset - Use Globals defaults)
            1 = S1 (Sequential Same-Pair)
            2 = S2 (Multi-Pair with Alternatives)
            3 = S3 (Rolling Currency Mode)
            4 = S4 (Timed Portfolio Mode)
            5 = S5 (Adaptive Hybrid with Sentiment Scaling)
        verbose: Print summary after applying (default: True)
    
    Returns:
        bool: True if preset applied successfully, False if invalid strategy_id
    """
    
    if strategy_id not in [0, 1, 2, 3, 4, 5]:
        print(f"[ERROR] Invalid strategy_id: {strategy_id}. Must be 0-5.")
        return False
    
    # Set the active strategy
    Globals.news_strategy = strategy_id
    
    # Apply strategy-specific preset
    if strategy_id == 0:
        _apply_s0_preset()
    elif strategy_id == 1:
        _apply_s1_preset()
    elif strategy_id == 2:
        _apply_s2_preset()
    elif strategy_id == 3:
        _apply_s3_preset()
    elif strategy_id == 4:
        _apply_s4_preset()
    elif strategy_id == 5:
        _apply_s5_preset()
    
    if verbose:
        print(f"✅ Strategy preset applied: S{strategy_id} ({_get_strategy_name(strategy_id)})")
        _print_strategy_summary(strategy_id)
    
    return True


def _apply_s0_preset():
    """
    S0: No Preset (Use Globals Defaults)
    - Does not modify any settings
    - Allows manual configuration via Globals.py
    - Use this for custom testing or manual strategy tuning
    - TESTING MODE: Uses current Globals.py settings (liveMode, TestingMode, etc.)
    """
    
    # Token optimization: Fetch forecast and actual together (saves 50% API calls)
    Globals.user_process_forecast_first = False
    
    # S0 is testing mode - don't override any production flags
    # User controls all settings manually via Globals.py
    
    if Globals.news_strategy != 0:
        print(f"[INFO] S0 activated - using current Globals settings without preset modifications")
        print(f"[INFO] symbolsToTrade: {Globals.symbolsToTrade}")
        print(f"[INFO] liveMode: {Globals.liveMode}, TestingMode: {Globals.TestingMode}")
        print(f"[INFO] Manual configuration mode enabled")


def _apply_s1_preset():
    """
    S1: Stack Same Pair (Controlled Accumulation)
    - Stacks up to 4 positions per currency (1% max exposure at 0.25% per trade)
    - No pair limit (allows multiple positions on same pair)
    - Each signal processed independently (no intentional hedging)
    - Fixed TP/SL (500/250)
    - 0.25% risk per trade
    - COMPLIANT: Max 1% exposure per currency (4 positions × 0.25% = 1%)
    - PRODUCTION MODE: Always sets liveMode=True, TestingMode=False, news_test_mode=False
    """
    
    # ========== PRODUCTION SETTINGS (AUTO-ENABLED FOR S1-S5) ==========
    Globals.liveMode = True
    Globals.TestingMode = False
    Globals.news_test_mode = False
    Globals.news_process_past_events = False  # Only process future events in production
    Globals.user_process_forecast_first = False  # Fetch forecast+actual together (saves 50% API calls)
    # ===================================================================
    
    # Symbol selection: Focus on high-liquidity major pairs
    # S1 works best with pairs that have tight spreads and deep liquidity for stacking
    Globals.symbolsToTrade = {"EURUSD", "GBPUSD", "USDJPY"}
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[1]  # 0.25%
    
    # Risk management filters
    Globals.news_filter_maxTrades = 0  # No limit on total trades
    Globals.news_filter_maxTradePerCurrency = 4  # Max 4 positions per currency (1% max exposure)
    Globals.news_filter_maxTradePerPair = 0  # No pair limit (allows stacking same pair)
    Globals.news_filter_findAvailablePair = False  # Always use primary pair
    Globals.news_filter_findAllPairs = False  # Not needed
    
    # Disable other strategy modes
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = False
    Globals.news_filter_confirmationRequired = False
    
    # Clear tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s2_preset():
    """
    S2: Diversify Pairs (Risk Spreading)
    - One position per currency across different pairs
    - Searches for alternative pairs if primary is blocked (EURUSD→EURGBP→EURCHF)
    - Fixed TP/SL (500/250)
    - 0.25% risk per trade
    - COMPLIANT: Max 0.25% exposure per currency (1 position × 0.25% = 0.25%)
    - PRODUCTION MODE: Always sets liveMode=True, TestingMode=False, news_test_mode=False
    """
    
    # ========== PRODUCTION SETTINGS (AUTO-ENABLED FOR S1-S5) ==========
    Globals.liveMode = True
    Globals.TestingMode = False
    Globals.news_test_mode = False
    Globals.news_process_past_events = False  # Only process future events in production
    Globals.user_process_forecast_first = False  # Fetch forecast+actual together (saves 50% API calls)
    # ===================================================================
    
    # Symbol selection: Enhanced with crosses for better alternative searching
    # USD majors + key crosses for each major currency
    Globals.symbolsToTrade = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "USDCAD", "NZDUSD"}
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[2]  # 0.25%
    
    # Risk management filters (Prop Firm Compliant)
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 1  # Max 1 position per currency (0.25% exposure)
    Globals.news_filter_maxTradePerPair = 1  # Max 1 position per pair
    Globals.news_filter_findAvailablePair = True  # KEY: Search alternatives if primary blocked
    Globals.news_filter_findAllPairs = True  # Search all pairs in _Symbols_
    
    # Disable other strategy modes
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = False
    Globals.news_filter_confirmationRequired = False
    
    # Clear tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s3_preset():
    """
    S3: Close & Reverse (Agile Adaptation)
    - One position per currency (enforced via _CurrencyPositions_)
    - Closes existing position and reverses on opposite signal
    - Uses enqueue_command(CLOSE) for active reversal
    - Fixed TP/SL (500/250)
    - 0.30% risk per trade (higher for agility)
    - COMPLIANT: Max 0.30% exposure per currency (1 position × 0.30% = 0.30%)
    - PRODUCTION MODE: Always sets liveMode=True, TestingMode=False, news_test_mode=False
    """
    
    # ========== PRODUCTION SETTINGS (AUTO-ENABLED FOR S1-S5) ==========
    Globals.liveMode = True
    Globals.TestingMode = False
    Globals.news_test_mode = False
    Globals.news_process_past_events = False  # Only process future events in production
    Globals.user_process_forecast_first = False  # Fetch forecast+actual together (saves 50% API calls)
    # ===================================================================
    
    # Symbol selection: Fast-moving pairs with good reversibility
    # Enhanced with EURGBP for non-USD exposure and better currency coverage
    Globals.symbolsToTrade = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP", "EURJPY"}
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[3]  # 0.30%
    
    # Risk management filters (Prop Firm Compliant)
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 1  # Max 1 position per currency (0.30% exposure)
    Globals.news_filter_maxTradePerPair = 1  # Max 1 position per pair
    Globals.news_filter_findAvailablePair = False  # Don't search alternatives (reverses on same pair)
    Globals.news_filter_findAllPairs = False  # Not needed
    
    # Enable rolling mode (KEY: activates reversal logic in News.py)
    Globals.news_filter_rollingMode = True  # KEY: Enable reversal on opposite signal
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = False
    Globals.news_filter_confirmationRequired = False
    
    # Initialize tracking dictionary
    Globals._CurrencyPositions_ = {}  # Will track active position per currency
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s4_preset():
    """
    S4: First Only (Patient Selectivity)
    - One trade per currency (locks while position open)
    - Ignores subsequent signals until position closes
    - Simplified: Lock until position closes (no daily timer needed)
    - Fixed TP/SL (500/250)
    - 0.25% risk per trade
    - COMPLIANT: Max 0.25% exposure per currency (1 position × 0.25% = 0.25%)
    - PRODUCTION MODE: Always sets liveMode=True, TestingMode=False, news_test_mode=False
    """
    
    # ========== PRODUCTION SETTINGS (AUTO-ENABLED FOR S1-S5) ==========
    Globals.liveMode = True
    Globals.TestingMode = False
    Globals.news_test_mode = False
    Globals.news_process_past_events = False  # Only process future events in production
    Globals.user_process_forecast_first = False  # Fetch forecast+actual together (saves 50% API calls)
    # ===================================================================
    
    # Symbol selection: Quality over quantity - majors + key cross for diversification
    # Replaced USDCHF with EURGBP for non-USD exposure
    Globals.symbolsToTrade = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP", "USDCAD"}
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[4]  # 0.25%
    
    # Risk management filters (Prop Firm Compliant)
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 1  # Max 1 position per currency (0.25% exposure)
    Globals.news_filter_maxTradePerPair = 1  # Max 1 per pair
    Globals.news_filter_findAvailablePair = False  # Don't search alternatives
    Globals.news_filter_findAllPairs = False  # Not needed
    
    # Disable other modes (simplified locking via _CurrencyPositions_ only)
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = False  # Not using weekly timer anymore
    Globals.news_filter_allowScaling = False
    Globals.news_filter_confirmationRequired = False
    
    # Initialize tracking dictionaries
    Globals._CurrencyPositions_ = {}  # Tracks which currencies are locked
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s5_preset():
    """
    S5: Adaptive Hybrid (Confirmation + Scaling)
    - Requires 2+ agreeing signals before opening first position
    - Scales up to 4 positions when additional agreeing signals arrive
    - Resets counter on conflicting signal
    - Fixed TP/SL (500/250)
    - 0.25% risk per trade (all positions equal size)
    - COMPLIANT: Max 1.00% exposure per currency (4 positions × 0.25% = 1.00%)
    - PRODUCTION MODE: Always sets liveMode=True, TestingMode=False, news_test_mode=False
    """
    
    # ========== PRODUCTION SETTINGS (AUTO-ENABLED FOR S1-S5) ==========
    Globals.liveMode = True
    Globals.TestingMode = False
    Globals.news_test_mode = False
    Globals.news_process_past_events = False  # Only process future events in production
    Globals.user_process_forecast_first = False  # Fetch forecast+actual together (saves 50% API calls)
    # ===================================================================
    
    # Symbol selection: Wide coverage with crosses for confirmation signals
    # CRITICAL: S5 needs multiple pairs per currency to generate 2+ confirming signals
    # Enhanced with EURGBP, EURJPY, GBPJPY, EURCHF, AUDJPY for cross-confirmation
    Globals.symbolsToTrade = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "USDCAD", "NZDUSD"}
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[5]  # 0.25% base
    
    # Risk management filters (Prop Firm Compliant)
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 4  # Max 4 positions per currency (1% exposure)
    Globals.news_filter_maxTradePerPair = 1  # Max 1 position per pair
    Globals.news_filter_findAvailablePair = False  # Don't search alternatives
    Globals.news_filter_findAllPairs = False  # Not needed
    
    # Enable confirmation mode + scaling (KEY: activates both features in News.py)
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = True  # KEY: Enable scaling on agreeing signals
    Globals.news_filter_confirmationRequired = True  # KEY: Require 2+ signals before first position
    Globals.news_filter_confirmationThreshold = 2    # Number of agreeing signals for first position
    Globals.news_filter_maxScalePositions = 4  # Max 4 total positions (1% compliance)
    Globals.news_filter_scalingFactor = 1.0    # Equal sizing for all positions
    
    # Initialize tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}  # Will track consensus per currency


def _get_strategy_name(strategy_id: int) -> str:
    """Get human-readable strategy name"""
    names = {
        0: "No Preset (Manual Configuration)",
        1: "Sequential Same-Pair",
        2: "Multi-Pair with Alternatives",
        3: "Rolling Currency Mode",
        4: "Timed Portfolio Mode",
        5: "Adaptive Hybrid with Sentiment Scaling"
    }
    return names.get(strategy_id, "Unknown")


def _print_strategy_summary(strategy_id: int):
    """Print summary of applied strategy configuration"""
    
    print(f"\n{'='*60}")
    print(f"STRATEGY S{strategy_id} CONFIGURATION")
    print(f"{'='*60}")
    
    # Production mode indicator (only for S1-S5)
    if strategy_id > 0:
        print(f"\n🔴 PRODUCTION MODE ENABLED")
        print(f"  liveMode: {Globals.liveMode}")
        print(f"  TestingMode: {Globals.TestingMode}")
        print(f"  news_test_mode: {Globals.news_test_mode}")
        print(f"  news_process_past_events: {Globals.news_process_past_events}")
    
    # Show symbolsToTrade
    symbols_list = ', '.join(sorted(Globals.symbolsToTrade))
    print(f"\nTrading Pairs: {symbols_list}")
    print(f"Total Pairs: {len(Globals.symbolsToTrade)}")
    
    # S0 has minimal output
    if strategy_id == 0:
        print(f"\nMode: Manual Configuration")
        print(f"Note: No preset applied - using current Globals settings")
        print(f"{'='*60}\n")
        return
    
    # Risk settings
    risk_pct = Globals.lot_size_percentage * 100
    print(f"\nRisk per Trade: {risk_pct:.2f}%")
    
    # TP/SL settings
    tp_sl = Globals.strategy_tp_sl[strategy_id]
    if tp_sl["TP"] == 0:
        print(f"TP/SL: ATR-based (2×ATR TP, 1×ATR SL)")
    else:
        print(f"TP: {tp_sl['TP']} points | SL: {tp_sl['SL']} points")
    
    # Risk limits
    print(f"\nRisk Management:")
    print(f"  Max Total Trades: {'Unlimited' if Globals.news_filter_maxTrades == 0 else Globals.news_filter_maxTrades}")
    print(f"  Max per Currency: {'Unlimited' if Globals.news_filter_maxTradePerCurrency == 0 else Globals.news_filter_maxTradePerCurrency}")
    print(f"  Max per Pair: {'Unlimited' if Globals.news_filter_maxTradePerPair == 0 else Globals.news_filter_maxTradePerPair}")
    
    # Prop firm compliance indicator
    if Globals.news_filter_maxTradePerCurrency > 0:
        max_exposure = Globals.news_filter_maxTradePerCurrency * (Globals.lot_size_percentage * 100)
        print(f"  🏦 Prop Firm Compliance: {max_exposure:.2f}% max exposure per currency")
    
    # Alternative search
    print(f"\nAlternative Pair Search:")
    print(f"  Enabled: {Globals.news_filter_findAvailablePair}")
    if Globals.news_filter_findAvailablePair:
        print(f"  Search Scope: {'All _Symbols_' if Globals.news_filter_findAllPairs else 'symbolsToTrade only'}")
    
    # Strategy-specific features
    print(f"\nStrategy Features:")
    if strategy_id == 1:
        print(f"  ✓ Allows stacking same pair (up to 4 positions per currency)")
        print(f"  ✓ Prop firm compliant: Max 1% exposure per currency (4 × 0.25%)")
    elif strategy_id == 2:
        print(f"  ✓ One position per currency")
        print(f"  ✓ Intelligent alternative pair search")
        print(f"  ✓ Prop firm compliant: Max 0.25% exposure per currency")
    elif strategy_id == 3:
        print(f"  ✓ Rolling mode enabled (reverses on conflict)")
        print(f"  ✓ One position per currency")
        print(f"  ✓ Higher risk (0.30%) for agility")
        print(f"  ✓ Prop firm compliant: Max 0.30% exposure per currency")
    elif strategy_id == 4:
        print(f"  ✓ Weekly first-only mode enabled")
        print(f"  ✓ One trade per pair per week")
        print(f"  ✓ ATR-based TP/SL")
        print(f"  ✓ Weekly reset: Monday 00:00")
        print(f"  ✓ Prop firm compliant: Max 0.25% exposure per currency")
    elif strategy_id == 5:
        print(f"  ✓ Confirmation mode enabled (requires {Globals.news_filter_confirmationThreshold}+ agreeing signals)")
        print(f"  ✓ Scaling enabled (up to {Globals.news_filter_maxScalePositions} positions per currency)")
        print(f"  ✓ Scaling factor: {Globals.news_filter_scalingFactor*100:.0f}% (equal sizing)")
        print(f"  ✓ Resets counter on conflicting signal")
        print(f"  ✓ Prop firm compliant: Max 1.00% exposure per currency")
    
    print(f"{'='*60}\n")


def get_current_strategy_info() -> dict:
    """
    Get current strategy configuration as dictionary.
    Useful for logging or displaying current settings.
    
    Returns:
        dict: Current strategy configuration
    """
    
    strategy_id = Globals.news_strategy
    
    return {
        "strategy_id": strategy_id,
        "strategy_name": _get_strategy_name(strategy_id),
        "risk_percentage": Globals.lot_size_percentage,
        "tp_sl": Globals.strategy_tp_sl[strategy_id],
        "max_trades": Globals.news_filter_maxTrades,
        "max_per_currency": Globals.news_filter_maxTradePerCurrency,
        "max_per_pair": Globals.news_filter_maxTradePerPair,
        "find_alternatives": Globals.news_filter_findAvailablePair,
        "search_all_pairs": Globals.news_filter_findAllPairs,
        "rolling_mode": Globals.news_filter_rollingMode,
        "weekly_first_only": Globals.news_filter_weeklyFirstOnly,
        "allow_scaling": Globals.news_filter_allowScaling,
        "scaling_factor": Globals.news_filter_scalingFactor if Globals.news_filter_allowScaling else None,
        "conflict_handling": Globals.news_filter_conflictHandling if Globals.news_filter_allowScaling else None
    }


# ========== USAGE EXAMPLE ==========
if __name__ == "__main__":
    # Example: Switch to S3 (Rolling Currency Mode)
    apply_strategy_preset(3)
    
    # Get current configuration
    config = get_current_strategy_info()
    print(f"\nCurrent Strategy: {config['strategy_name']}")
    print(f"Risk: {config['risk_percentage']*100:.2f}%")
