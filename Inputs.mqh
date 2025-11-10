//+------------------------------------------------------------------+
//|                                                      Inputs.mqh  |
//|                      Inputs for News Analyzer Expert Advisor    |
//+------------------------------------------------------------------+
#ifndef NEWS_ANALYZER_INPUTS_MQH
#define NEWS_ANALYZER_INPUTS_MQH

// Mode selector for this EA
enum ModeEnum { Sender, Receiver };
input ModeEnum Mode = Sender;      // Mode (Sender/Receiver)

// Strategy selector
enum StrategyEnum { S1=1, S2=2, S3=3, S4=4, S5=5 };

// Identification and risk settings
input int ID = 1;                  // Unique identifier
input int Multiplier = 1;          // Multiplier
input int Risk = 1;                // Risk
input StrategyEnum StrategyID = S2;  // Strategy

// Existing inputs
input int PrintInterval = 5;       // Print interval in seconds
input bool PrintOnTick = false;    // Print on every tick (can be noisy)

// Testing mode toggle
input bool TestingMode = false;    // Enable testing mode logic
// Server sending
input bool   SendToServer = true;   // Enable HTTP POST sending (default true)
input string ServerIP     = "127.0.0.1"; // Server IP or hostname
input int    ServerPort   = 5000;        // Server port

#endif // NEWS_ANALYZER_INPUTS_MQH
