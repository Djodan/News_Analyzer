//+------------------------------------------------------------------+
//|                                               News_Analyzer.mq5 |
//|                                             DjoDan Maviaki      |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "DjoDan Maviaki"
#property link      ""
#property version   "1.00"
#property description "News Analyzer - Expert Advisor for automated news trading"

//--- Includes
#include "Inputs.mqh"           // Inputs moved to separate file
#include "GlobalVariables.mqh"  // Globals moved to separate file
#include "Trades.mqh"           // Trade tracking helpers
#include "TestingMode.mqh"      // Testing mode helpers
#include "Server.mqh"           // HTTP sender

//+------------------------------------------------------------------+
//| Ensure symbol is loaded in Market Watch and has history data    |
//+------------------------------------------------------------------+
bool EnsureSymbolLoaded(string symbol)
{
    // Add symbol to Market Watch if not already there
    if(!SymbolSelect(symbol, true))
    {
        Print("Failed to select symbol: ", symbol);
        return false;
    }
    
    // Request historical data to trigger synchronization
    MqlRates rates[];
    ArraySetAsSeries(rates, true);
    
    // Try to copy some bars - this triggers MT5 to download data if missing
    int copied = CopyRates(symbol, PERIOD_M5, 0, 100, rates);
    
    if(copied <= 0)
    {
        Print("Warning: No history data available yet for ", symbol, " - will retry on next tick");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== News Analyzer EA Started ===");
    Print("Print Interval: ", PrintInterval, " seconds");
    Print("Print on Tick: ", PrintOnTick ? "Yes" : "No");
    
    // Ensure all symbols are loaded before initializing ATR indicators
    Print("Ensuring all symbols are loaded in Market Watch...");
    string symbols[] = {
        "AUDCAD", "AUDJPY", "AUDUSD", "AUDCHF", "AUDNZD",
        "CADJPY", "CADCHF", "EURAUD", "EURCAD", "EURCHF",
        "EURGBP", "EURJPY", "EURNZD", "EURUSD", "GBPAUD",
        "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
        "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD",
        "USDCHF", "USDJPY", "CHFJPY", "BITCOIN"
    };
    
    int loaded = 0;
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        if(EnsureSymbolLoaded(symbols[i]))
            loaded++;
    }
    Print("Loaded ", loaded, " out of ", ArraySize(symbols), " symbols");
    
    // Initialize ATR indicator handles for Packet C (14-period ATR on M5)
    g_atrHandle_AUDCAD = iATR("AUDCAD", PERIOD_M5, 14);
    g_atrHandle_AUDJPY = iATR("AUDJPY", PERIOD_M5, 14);
    g_atrHandle_AUDUSD = iATR("AUDUSD", PERIOD_M5, 14);
    g_atrHandle_AUDCHF = iATR("AUDCHF", PERIOD_M5, 14);
    g_atrHandle_AUDNZD = iATR("AUDNZD", PERIOD_M5, 14);
    g_atrHandle_CADJPY = iATR("CADJPY", PERIOD_M5, 14);
    g_atrHandle_CADCHF = iATR("CADCHF", PERIOD_M5, 14);
    g_atrHandle_EURAUD = iATR("EURAUD", PERIOD_M5, 14);
    g_atrHandle_EURCAD = iATR("EURCAD", PERIOD_M5, 14);
    g_atrHandle_EURCHF = iATR("EURCHF", PERIOD_M5, 14);
    g_atrHandle_EURGBP = iATR("EURGBP", PERIOD_M5, 14);
    g_atrHandle_EURJPY = iATR("EURJPY", PERIOD_M5, 14);
    g_atrHandle_EURNZD = iATR("EURNZD", PERIOD_M5, 14);
    g_atrHandle_EURUSD = iATR("EURUSD", PERIOD_M5, 14);
    g_atrHandle_GBPAUD = iATR("GBPAUD", PERIOD_M5, 14);
    g_atrHandle_GBPCAD = iATR("GBPCAD", PERIOD_M5, 14);
    g_atrHandle_GBPCHF = iATR("GBPCHF", PERIOD_M5, 14);
    g_atrHandle_GBPJPY = iATR("GBPJPY", PERIOD_M5, 14);
    g_atrHandle_GBPNZD = iATR("GBPNZD", PERIOD_M5, 14);
    g_atrHandle_GBPUSD = iATR("GBPUSD", PERIOD_M5, 14);
    g_atrHandle_NZDCAD = iATR("NZDCAD", PERIOD_M5, 14);
    g_atrHandle_NZDCHF = iATR("NZDCHF", PERIOD_M5, 14);
    g_atrHandle_NZDJPY = iATR("NZDJPY", PERIOD_M5, 14);
    g_atrHandle_NZDUSD = iATR("NZDUSD", PERIOD_M5, 14);
    g_atrHandle_USDCAD = iATR("USDCAD", PERIOD_M5, 14);
    g_atrHandle_USDCHF = iATR("USDCHF", PERIOD_M5, 14);
    g_atrHandle_USDJPY = iATR("USDJPY", PERIOD_M5, 14);
    g_atrHandle_CHFJPY = iATR("CHFJPY", PERIOD_M5, 14);
    g_atrHandle_BITCOIN = iATR("BITCOIN", PERIOD_M5, 14);
    
    Print("ATR indicators initialized for 29 currency pairs (28 forex + 1 crypto)");
    
    // Set timer for periodic printing
    EventSetTimer(PrintInterval);
    
    // Initial sync of trade lists then print counts
    SyncOpenTradesFromTerminal();
    CollectRecentClosedDeals(50);
    PrintAllTrades();
    // Initial send to server (optional)
    SendArrays();

    if(TestingMode)
        Testing_OnInit();
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release ATR indicator handles
    if(g_atrHandle_AUDCAD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_AUDCAD);
    if(g_atrHandle_AUDJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_AUDJPY);
    if(g_atrHandle_AUDUSD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_AUDUSD);
    if(g_atrHandle_AUDCHF != INVALID_HANDLE) IndicatorRelease(g_atrHandle_AUDCHF);
    if(g_atrHandle_AUDNZD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_AUDNZD);
    if(g_atrHandle_CADJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_CADJPY);
    if(g_atrHandle_CADCHF != INVALID_HANDLE) IndicatorRelease(g_atrHandle_CADCHF);
    if(g_atrHandle_EURAUD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURAUD);
    if(g_atrHandle_EURCAD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURCAD);
    if(g_atrHandle_EURCHF != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURCHF);
    if(g_atrHandle_EURGBP != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURGBP);
    if(g_atrHandle_EURJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURJPY);
    if(g_atrHandle_EURNZD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURNZD);
    if(g_atrHandle_EURUSD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_EURUSD);
    if(g_atrHandle_GBPAUD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_GBPAUD);
    if(g_atrHandle_GBPCAD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_GBPCAD);
    if(g_atrHandle_GBPCHF != INVALID_HANDLE) IndicatorRelease(g_atrHandle_GBPCHF);
    if(g_atrHandle_GBPJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_GBPJPY);
    if(g_atrHandle_GBPNZD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_GBPNZD);
    if(g_atrHandle_GBPUSD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_GBPUSD);
    if(g_atrHandle_NZDCAD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_NZDCAD);
    if(g_atrHandle_NZDCHF != INVALID_HANDLE) IndicatorRelease(g_atrHandle_NZDCHF);
    if(g_atrHandle_NZDJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_NZDJPY);
    if(g_atrHandle_NZDUSD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_NZDUSD);
    if(g_atrHandle_USDCAD != INVALID_HANDLE) IndicatorRelease(g_atrHandle_USDCAD);
    if(g_atrHandle_USDCHF != INVALID_HANDLE) IndicatorRelease(g_atrHandle_USDCHF);
    if(g_atrHandle_USDJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_USDJPY);
    if(g_atrHandle_CHFJPY != INVALID_HANDLE) IndicatorRelease(g_atrHandle_CHFJPY);
    if(g_atrHandle_BITCOIN != INVALID_HANDLE) IndicatorRelease(g_atrHandle_BITCOIN);
    
    EventKillTimer();
    Print("=== News Analyzer EA Stopped ===");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Keep lists updated
    SyncOpenTradesFromTerminal();
    if(PrintOnTick)
    {
        PrintAllTrades();
    }
    // Poll server for commands frequently (lightweight GET)
    if(Mode==Sender)
        ProcessServerCommand();
    if(TestingMode)
        Testing_OnTick();
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
    // Periodic refresh of trade lists
    SyncOpenTradesFromTerminal();
    CollectRecentClosedDeals(50);
    PrintAllTrades();
    
    // Send Packet A (TradeState) - every 30s
    SendArrays();
    
    // Send Packet B (AccountInfo) - every 30-60s with change detection
    SendPacket_B();
    
    // Send Packet C (SymbolData) - every 30s with ATR data
    SendPacket_C();
    
    // Send Packet D (PositionAnalytics) - every 5s when positions open
    SendPacket_D();
    
    // Also poll server for commands on timer
    if(Mode==Sender)
        ProcessServerCommand();
    // Fetch two-way test message and print it
    FetchAndPrintMessage();
    if(TestingMode)
        Testing_OnTimer();
}

//+------------------------------------------------------------------+
//| Function to print counts of tracked trades                      |
//+------------------------------------------------------------------+
void PrintAllTrades()
{
    Print("===============================================");
    // Print("TRADE TRACKING - ", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS));
    // List tickets for currently open positions
    int openCount = ArraySize(openTickets);
    if(openCount > 0)
    {
        Print("Open position tickets:");
        for(int i=0;i<openCount;i++)
            Print(" - ", openTickets[i]);
    }
    Print("Trades currently open (tracked): ", ArraySize(openTickets));
    Print("Trades closed offline (tracked): ", ArraySize(closedOfflineDeals));
    Print("Trades closed online (tracked): ", ArraySize(closedOnlineDeals));
    Print("===============================================");
}

//+------------------------------------------------------------------+
//| OnTradeTransaction: capture online-closed trades                |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans,const MqlTradeRequest& request,const MqlTradeResult& result)
{
    if(trans.type==TRADE_TRANSACTION_DEAL_ADD)
    {
        ulong deal = trans.deal;
        if(HistoryDealSelect(deal))
        {
            long entry = HistoryDealGetInteger(deal, DEAL_ENTRY);
            if(entry==DEAL_ENTRY_OUT)
            {
                // Trade closed - get details
                string symbol = HistoryDealGetString(deal, DEAL_SYMBOL);
                double closePrice = HistoryDealGetDouble(deal, DEAL_PRICE);
                string comment = HistoryDealGetString(deal, DEAL_COMMENT);
                ulong positionId = HistoryDealGetInteger(deal, DEAL_POSITION_ID);
                
                // Get more trade details for Packet E
                long dealType = HistoryDealGetInteger(deal, DEAL_TYPE);
                double volume = HistoryDealGetDouble(deal, DEAL_VOLUME);
                double profit = HistoryDealGetDouble(deal, DEAL_PROFIT);
                double swap = HistoryDealGetDouble(deal, DEAL_SWAP);
                double commission = HistoryDealGetDouble(deal, DEAL_COMMISSION);
                datetime closeTime = (datetime)HistoryDealGetInteger(deal, DEAL_TIME);
                
                // Find the position's open price and time from arrays
                double openPrice = 0.0;
                datetime openTime = 0;
                double mae = 0.0;
                double mfe = 0.0;
                int idx = FindOpenTradeIndexByTicket(positionId);
                if(idx >= 0)
                {
                    openPrice = openOpenPrices[idx];
                    openTime = openOpenTimes[idx];
                    mae = (idx < ArraySize(openMAE)) ? openMAE[idx] : 0.0;
                    mfe = (idx < ArraySize(openMFE)) ? openMFE[idx] : 0.0;
                }
                else
                {
                    // Position not in tracking arrays - try to get from history
                    HistorySelectByPosition(positionId);
                    int deals = HistoryDealsTotal();
                    for(int i = 0; i < deals; i++)
                    {
                        ulong d = HistoryDealGetTicket(i);
                        if(HistoryDealGetInteger(d, DEAL_ENTRY) == DEAL_ENTRY_IN)
                        {
                            openPrice = HistoryDealGetDouble(d, DEAL_PRICE);
                            openTime = (datetime)HistoryDealGetInteger(d, DEAL_TIME);
                            break;
                        }
                    }
                }
                
                // Detect if this was TP or SL closure
                string outcome = DetectTPSLClosure(symbol, positionId, closePrice, comment);
                
                // DEBUG: Print before sending Packet E
                Print("=== SENDING PACKET E ===");
                Print("Ticket=", positionId, " Symbol=", symbol);
                Print("OpenPrice=", openPrice, " ClosePrice=", closePrice);
                Print("Profit=", profit, " MAE=", mae, " MFE=", mfe);
                Print("Close Reason=", outcome);
                
                // Send Packet E with full trade details
                bool packetSent = SendPacket_E(
                    positionId,
                    symbol,
                    dealType,
                    volume,
                    openPrice,
                    closePrice,
                    openTime,
                    closeTime,
                    profit,
                    swap,
                    commission,
                    mae,
                    mfe,
                    outcome,     // Pass the close reason (TP, SL, or Manual)
                    StrategyID   // Pass the strategy ID from EA input
                );
                
                if(packetSent)
                    Print("✅ Packet E sent successfully");
                else
                    Print("❌ Packet E send FAILED");
                
                // Send outcome notification if TP or SL
                if(outcome == "TP" || outcome == "SL")
                {
                    Print("Trade closed at ", outcome, ": Ticket=", positionId, " Symbol=", symbol, " Price=", DoubleToString(closePrice, _Digits));
                    SendTradeOutcome(positionId, outcome, ServerIP, (int)ServerPort);
                }
                
                // Add to closed trades tracking
                AddClosedOnline(
                    deal,
                    symbol,
                    dealType,
                    volume,
                    openPrice,
                    closePrice,
                    profit,
                    swap,
                    commission,
                    closeTime
                );
            }
            else if(entry==DEAL_ENTRY_IN)
            {
                // New position opened: trigger testing action if enabled
                if(TestingMode)
                {
                    // Try to resolve the position ticket associated with this deal
                    ulong pos_ticket = (ulong)HistoryDealGetInteger(deal, DEAL_POSITION_ID);
                    if(pos_ticket!=0)
                        Testing_HandleOpenedPosition(pos_ticket);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Function to print trade history (optional)                      |
//+------------------------------------------------------------------+
void PrintTradeHistory(int maxRecords = 10)
{
    Print("--- RECENT TRADE HISTORY (Last ", maxRecords, " trades) ---");
    
    // Select history for today
    if(!HistorySelect(iTime(Symbol(), PERIOD_D1, 0), TimeCurrent()))
    {
        Print("Failed to select history");
        return;
    }
    
    int totalDeals = HistoryDealsTotal();
    int startIndex = MathMax(0, totalDeals - maxRecords);
    
    for(int i = startIndex; i < totalDeals; i++)
    {
        ulong ticket = HistoryDealGetTicket(i);
        if(ticket > 0)
        {
            string symbol = HistoryDealGetString(ticket, DEAL_SYMBOL);
            long type = HistoryDealGetInteger(ticket, DEAL_TYPE);
            double volume = HistoryDealGetDouble(ticket, DEAL_VOLUME);
            double price = HistoryDealGetDouble(ticket, DEAL_PRICE);
            double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            datetime time = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            
            string typeStr = "";
            switch(type)
            {
                case DEAL_TYPE_BUY: typeStr = "BUY"; break;
                case DEAL_TYPE_SELL: typeStr = "SELL"; break;
                default: typeStr = "OTHER";
            }
            
            Print("Deal ", i+1, ": ", symbol, " ", typeStr, " ", DoubleToString(volume, 2), 
                  " at ", DoubleToString(price, _Digits), " P&L: ", DoubleToString(profit, 2),
                  " Time: ", TimeToString(time, TIME_SECONDS));
        }
    }
}
