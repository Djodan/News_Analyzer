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
        strategy_id: Strategy number (1-5)
            1 = S1 (Sequential Same-Pair)
            2 = S2 (Multi-Pair with Alternatives)
            3 = S3 (Rolling Currency Mode)
            4 = S4 (Timed Portfolio Mode)
            5 = S5 (Adaptive Hybrid with Sentiment Scaling)
        verbose: Print summary after applying (default: True)
    
    Returns:
        bool: True if preset applied successfully, False if invalid strategy_id
    """
    
    if strategy_id not in [1, 2, 3, 4, 5]:
        print(f"[ERROR] Invalid strategy_id: {strategy_id}. Must be 1-5.")
        return False
    
    # Set the active strategy
    Globals.news_strategy = strategy_id
    
    # Apply strategy-specific preset
    if strategy_id == 1:
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


def _apply_s1_preset():
    """
    S1: Sequential Same-Pair
    - Trades same pair repeatedly on each news event
    - No pair limit, no currency limit
    - Fixed TP/SL (500/250)
    - 0.25% risk per trade
    """
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[1]  # 0.25%
    
    # Risk management filters
    Globals.news_filter_maxTrades = 0  # No limit on total trades
    Globals.news_filter_maxTradePerCurrency = 0  # No currency limit
    Globals.news_filter_maxTradePerPair = 0  # No pair limit (key feature: stack same pair)
    Globals.news_filter_findAvailablePair = False  # Don't search for alternatives
    Globals.news_filter_findAllPairs = False  # Not needed
    
    # Disable other strategy modes
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = False
    
    # Clear tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s2_preset():
    """
    S2: Multi-Pair with Alternatives
    - One position per currency
    - Searches for alternative pairs if primary is blocked
    - Fixed TP/SL (500/250)
    - 0.25% risk per trade
    """
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[2]  # 0.25%
    
    # Risk management filters
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 1  # Key: Max 1 position per currency
    Globals.news_filter_maxTradePerPair = 0  # No pair-specific limit
    Globals.news_filter_findAvailablePair = True  # Key: Search alternatives
    Globals.news_filter_findAllPairs = True  # Search all pairs in _Symbols_
    
    # Disable other strategy modes
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = False
    
    # Clear tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s3_preset():
    """
    S3: Rolling Currency Mode
    - One position per currency (enforced via _CurrencyPositions_)
    - Reverses position on conflicting signal
    - Fixed TP/SL (500/250)
    - 0.30% risk per trade (higher for agility)
    """
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[3]  # 0.30%
    
    # Risk management filters
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 1  # One position per currency
    Globals.news_filter_maxTradePerPair = 0  # No pair-specific limit
    Globals.news_filter_findAvailablePair = True  # Search alternatives
    Globals.news_filter_findAllPairs = True  # Search all pairs
    
    # Enable rolling mode
    Globals.news_filter_rollingMode = True  # Key: Enable reversal logic
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = False
    
    # Initialize tracking dictionary
    Globals._CurrencyPositions_ = {}  # Will track active position per currency
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}


def _apply_s4_preset():
    """
    S4: Timed Portfolio Mode
    - One trade per pair per week
    - ATR-based TP/SL (2×ATR / 1×ATR)
    - 0.25% risk per trade
    - Weekly reset on Monday 00:00
    """
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[4]  # 0.25%
    
    # Risk management filters
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 0  # No currency limit
    Globals.news_filter_maxTradePerPair = 1  # Key: Max 1 per pair per week
    Globals.news_filter_findAvailablePair = True  # Search alternatives
    Globals.news_filter_findAllPairs = True  # Search all pairs
    
    # Enable weekly first-only mode
    Globals.news_filter_rollingMode = False
    Globals.news_filter_weeklyFirstOnly = True  # Key: Enable weekly tracking
    Globals.news_filter_allowScaling = False
    
    # Initialize tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}  # Will track which pairs traded this week
    Globals._CurrencySentiment_ = {}
    
    # Initialize all pairs as available (False = not traded yet)
    for pair in Globals._Symbols_.keys():
        Globals._PairsTraded_ThisWeek_[pair] = False


def _apply_s5_preset():
    """
    S5: Adaptive Hybrid with Sentiment Scaling
    - Stacks positions when events agree (max 2)
    - Reverses on conflicting signals
    - ATR-based TP/SL (2×ATR / 1×ATR)
    - 0.25% base risk (scales to 0.15% on agreement)
    - Combines S3 reversal + S4 portfolio concepts
    """
    
    # Risk & TP/SL
    Globals.lot_size_percentage = Globals.strategy_risk[5]  # 0.25% base
    
    # Risk management filters
    Globals.news_filter_maxTrades = 0  # No global limit
    Globals.news_filter_maxTradePerCurrency = 2  # Key: Max 2 positions per currency (base + scaled)
    Globals.news_filter_maxTradePerPair = 0  # No pair-specific limit
    Globals.news_filter_findAvailablePair = True  # Search alternatives
    Globals.news_filter_findAllPairs = True  # Search all pairs
    
    # Enable sentiment scaling mode
    Globals.news_filter_rollingMode = False  # Uses custom sentiment logic instead
    Globals.news_filter_weeklyFirstOnly = False
    Globals.news_filter_allowScaling = True  # Key: Enable position scaling
    
    # Scaling configuration
    Globals.news_filter_maxScalePositions = 2  # Max 2 positions per currency
    Globals.news_filter_scalingFactor = 0.6  # Second position = 60% of first
    Globals.news_filter_conflictHandling = "reverse"  # Close all on conflict
    
    # Initialize tracking dictionaries
    Globals._CurrencyPositions_ = {}
    Globals._PairsTraded_ThisWeek_ = {}
    Globals._CurrencySentiment_ = {}  # Will track consensus per currency


def _get_strategy_name(strategy_id: int) -> str:
    """Get human-readable strategy name"""
    names = {
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
    
    # Risk settings
    risk_pct = Globals.lot_size_percentage * 100
    print(f"Risk per Trade: {risk_pct:.2f}%")
    
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
    
    # Alternative search
    print(f"\nAlternative Pair Search:")
    print(f"  Enabled: {Globals.news_filter_findAvailablePair}")
    if Globals.news_filter_findAvailablePair:
        print(f"  Search Scope: {'All _Symbols_' if Globals.news_filter_findAllPairs else 'symbolsToTrade only'}")
    
    # Strategy-specific features
    print(f"\nStrategy Features:")
    if strategy_id == 1:
        print(f"  ✓ Allows stacking same pair repeatedly")
        print(f"  ✓ No position limits")
    elif strategy_id == 2:
        print(f"  ✓ One position per currency")
        print(f"  ✓ Intelligent alternative pair search")
    elif strategy_id == 3:
        print(f"  ✓ Rolling mode enabled (reverses on conflict)")
        print(f"  ✓ One position per currency")
        print(f"  ✓ Higher risk (0.30%) for agility")
    elif strategy_id == 4:
        print(f"  ✓ Weekly first-only mode enabled")
        print(f"  ✓ One trade per pair per week")
        print(f"  ✓ ATR-based TP/SL")
        print(f"  ✓ Weekly reset: Monday 00:00")
    elif strategy_id == 5:
        print(f"  ✓ Sentiment scaling enabled")
        print(f"  ✓ Max {Globals.news_filter_maxScalePositions} positions per currency")
        print(f"  ✓ Scaling factor: {Globals.news_filter_scalingFactor*100:.0f}%")
        print(f"  ✓ Conflict handling: {Globals.news_filter_conflictHandling}")
        print(f"  ✓ ATR-based TP/SL")
    
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
