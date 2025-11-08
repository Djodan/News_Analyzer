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
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== News Analyzer EA Started ===");
    Print("Print Interval: ", PrintInterval, " seconds");
    Print("Print on Tick: ", PrintOnTick ? "Yes" : "No");
    
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
                
                // Detect if this was TP or SL closure
                string outcome = DetectTPSLClosure(symbol, positionId, closePrice, comment);
                
                // Send outcome notification if TP or SL
                if(outcome == "TP" || outcome == "SL")
                {
                    Print("Trade closed at ", outcome, ": Ticket=", positionId, " Symbol=", symbol, " Price=", DoubleToString(closePrice, _Digits));
                    SendTradeOutcome(positionId, outcome, ServerIP, ServerPort);
                }
                
                // Add to closed trades tracking
                AddClosedOnline(
                    deal,
                    symbol,
                    HistoryDealGetInteger(deal, DEAL_TYPE),
                    HistoryDealGetDouble(deal, DEAL_VOLUME),
                    0.0, // openPrice unknown here
                    closePrice,
                    HistoryDealGetDouble(deal, DEAL_PROFIT),
                    HistoryDealGetDouble(deal, DEAL_SWAP),
                    HistoryDealGetDouble(deal, DEAL_COMMISSION),
                    (datetime)HistoryDealGetInteger(deal, DEAL_TIME)
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
