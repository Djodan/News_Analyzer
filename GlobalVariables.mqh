//+------------------------------------------------------------------+
//|                                               GlobalVariables.mqh|
//|                     Global/shared variables for News Analyzer EA |
//+------------------------------------------------------------------+
#ifndef NEWS_ANALYZER_GLOBALVARIABLES_MQH
#define NEWS_ANALYZER_GLOBALVARIABLES_MQH

#include <Trade\Trade.mqh>

// Trade object and timing
CTrade trade;                // Trade helper instance
datetime lastPrintTime = 0;  // Last print timestamp

// Global parallel arrays for tracking OPEN trades
ulong    openTickets[];
string   openSymbols[];
long     openTypes[];
double   openVolumes[];
double   openOpenPrices[];
double   openCurrentPrices[];
double   openSLs[];
double   openTPs[];
datetime openOpenTimes[];
long     openMagics[];
string   openComments[];

// MAE/MFE tracking for open positions (Packet D)
double   openMAE[];  // Maximum Adverse Excursion (worst drawdown in pips)
double   openMFE[];  // Maximum Favorable Excursion (best profit in pips)

// Global parallel arrays for tracking CLOSED trades (OFFLINE: from history)
ulong    closedOfflineDeals[];
string   closedOfflineSymbols[];
long     closedOfflineTypes[];
double   closedOfflineVolumes[];
double   closedOfflineOpenPrices[];
double   closedOfflineClosePrices[];
double   closedOfflineProfits[];
double   closedOfflineSwaps[];
double   closedOfflineCommissions[];
datetime closedOfflineCloseTimes[];

// Global parallel arrays for tracking CLOSED trades (ONLINE: while EA is alive)
ulong    closedOnlineDeals[];
string   closedOnlineSymbols[];
long     closedOnlineTypes[];
double   closedOnlineVolumes[];
double   closedOnlineOpenPrices[];
double   closedOnlineClosePrices[];
double   closedOnlineProfits[];
double   closedOnlineSwaps[];
double   closedOnlineCommissions[];
datetime closedOnlineCloseTimes[];

//+------------------------------------------------------------------+
//| Packet B Tracking Variables (Account Info)                       |
//+------------------------------------------------------------------+
double   g_lastBalanceSent = 0.0;     // Last balance value sent in Packet B
double   g_lastEquitySent = 0.0;      // Last equity value sent in Packet B
datetime g_lastAccountPacketTime = 0; // Last time Packet B was sent

//+------------------------------------------------------------------+
//| Packet C Variables (Symbol Data with ATR)                        |
//+------------------------------------------------------------------+
// ATR indicator handles for all 28 currency pairs
int g_atrHandle_AUDCAD = INVALID_HANDLE;
int g_atrHandle_AUDJPY = INVALID_HANDLE;
int g_atrHandle_AUDUSD = INVALID_HANDLE;
int g_atrHandle_AUDCHF = INVALID_HANDLE;
int g_atrHandle_AUDNZD = INVALID_HANDLE;
int g_atrHandle_CADJPY = INVALID_HANDLE;
int g_atrHandle_CADCHF = INVALID_HANDLE;
int g_atrHandle_EURAUD = INVALID_HANDLE;
int g_atrHandle_EURCAD = INVALID_HANDLE;
int g_atrHandle_EURCHF = INVALID_HANDLE;
int g_atrHandle_EURGBP = INVALID_HANDLE;
int g_atrHandle_EURJPY = INVALID_HANDLE;
int g_atrHandle_EURNZD = INVALID_HANDLE;
int g_atrHandle_EURUSD = INVALID_HANDLE;
int g_atrHandle_GBPAUD = INVALID_HANDLE;
int g_atrHandle_GBPCAD = INVALID_HANDLE;
int g_atrHandle_GBPCHF = INVALID_HANDLE;
int g_atrHandle_GBPJPY = INVALID_HANDLE;
int g_atrHandle_GBPNZD = INVALID_HANDLE;
int g_atrHandle_GBPUSD = INVALID_HANDLE;
int g_atrHandle_NZDCAD = INVALID_HANDLE;
int g_atrHandle_NZDCHF = INVALID_HANDLE;
int g_atrHandle_NZDJPY = INVALID_HANDLE;
int g_atrHandle_NZDUSD = INVALID_HANDLE;
int g_atrHandle_USDCAD = INVALID_HANDLE;
int g_atrHandle_USDCHF = INVALID_HANDLE;
int g_atrHandle_USDJPY = INVALID_HANDLE;
int g_atrHandle_CHFJPY = INVALID_HANDLE;

datetime g_lastSymbolPacketTime = 0;  // Last time Packet C was sent

//+------------------------------------------------------------------+
//| Packet D Variables (Position Analytics - MAE/MFE)                |
//+------------------------------------------------------------------+
datetime g_lastAnalyticsPacketTime = 0;  // Last time Packet D was sent

#endif // NEWS_ANALYZER_GLOBALVARIABLES_MQH
