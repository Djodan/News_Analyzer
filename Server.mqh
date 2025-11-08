//+------------------------------------------------------------------+
//|                                                      Server.mqh  |
//|           HTTP communication for News Analyzer                  |
//+------------------------------------------------------------------+
#ifndef NEWS_ANALYZER_SERVER_MQH
#define NEWS_ANALYZER_SERVER_MQH

// Uses globals/inputs
#include "Inputs.mqh"
#include "GlobalVariables.mqh"
#include "Json.mqh"
#include "Http.mqh"
#include "Trades.mqh"

// JSON building moved to Json.mqh (BuildPayload, JsonEscape)

//+------------------------------------------------------------------+
//| Server Disconnect Detection and Auto-Reset                      |
//+------------------------------------------------------------------+

// Global flag to track if we've already performed auto-reset
bool g_ServerDisconnected = false;

// Check if error indicates server disconnection
bool IsServerDisconnectionError(int httpCode, int lastError)
{
   // HTTP error codes that indicate disconnection
   // 1001 = custom error from HttpPost/HttpGet
   // 4006 = ERR_NO_CONNECTION
   // 0 = sometimes indicates connection refused
   
   if(httpCode == 1001 && lastError == 4006)
      return true;
   
   if(httpCode == 0 && (lastError == 4006 || lastError == 5203))
      return true; // 5203 = ERR_CANNOT_CONNECT
   
   // Additional common network errors
   if(lastError == 4014) return true; // ERR_FUNCTION_NOT_CONFIRMED
   if(lastError == 5203) return true; // Cannot connect to server
   
   return false;
}

// Auto-reset function: close all positions and clear tracking arrays
void PerformAutoReset()
{
   if(g_ServerDisconnected)
      return; // Already performed reset
   
   g_ServerDisconnected = true;
   
   // Print("========================================");
   // Print("SERVER DISCONNECTED - PERFORMING AUTO-RESET");
   // Print("========================================");
   
   // Close all open positions
   int positionsClosed = 0;
   int openCount = ArraySize(openTickets);
   
   if(openCount > 0)
   {
      // Print("Closing ", openCount, " open position(s)...");
      
      // Create a copy of tickets to avoid array modification during iteration
      ulong ticketsCopy[];
      ArrayResize(ticketsCopy, openCount);
      ArrayCopy(ticketsCopy, openTickets, 0, 0, openCount);
      
      for(int i = 0; i < openCount; i++)
      {
         ulong ticket = ticketsCopy[i];
         string symbol = "";
         long ptype = 0;
         double pvol = 0.0;
         
         if(SelectPositionByTicket(ticket, symbol, ptype, pvol))
         {
            string typeStr = (ptype == POSITION_TYPE_BUY) ? "BUY" : "SELL";
            // Print("  Closing position: Ticket=", ticket, " Symbol=", symbol, " Type=", typeStr, " Volume=", DoubleToString(pvol, 2));
            
            if(ClosePositionByTicket(ticket, 0.0))
            {
               positionsClosed++;
               // Print("  >> Position closed successfully");
            }
            else
            {
               // Print("  >> Failed to close position");
            }
         }
      }
      
      // Print("Closed ", positionsClosed, "/", openCount, " position(s)");
   }
   else
   {
      // Print("No open positions to close");
   }
   
   // Reset all tracking arrays
   // Print("Resetting internal tracking variables...");
   
   // Open trades arrays
   ArrayResize(openTickets, 0);
   ArrayResize(openSymbols, 0);
   ArrayResize(openTypes, 0);
   ArrayResize(openVolumes, 0);
   ArrayResize(openOpenPrices, 0);
   ArrayResize(openCurrentPrices, 0);
   ArrayResize(openSLs, 0);
   ArrayResize(openTPs, 0);
   ArrayResize(openOpenTimes, 0);
   ArrayResize(openMagics, 0);
   ArrayResize(openComments, 0);
   
   // Closed offline arrays
   ArrayResize(closedOfflineDeals, 0);
   ArrayResize(closedOfflineSymbols, 0);
   ArrayResize(closedOfflineTypes, 0);
   ArrayResize(closedOfflineVolumes, 0);
   ArrayResize(closedOfflineOpenPrices, 0);
   ArrayResize(closedOfflineClosePrices, 0);
   ArrayResize(closedOfflineProfits, 0);
   ArrayResize(closedOfflineSwaps, 0);
   ArrayResize(closedOfflineCommissions, 0);
   ArrayResize(closedOfflineCloseTimes, 0);
   
   // Closed online arrays
   ArrayResize(closedOnlineDeals, 0);
   ArrayResize(closedOnlineSymbols, 0);
   ArrayResize(closedOnlineTypes, 0);
   ArrayResize(closedOnlineVolumes, 0);
   ArrayResize(closedOnlineOpenPrices, 0);
   ArrayResize(closedOnlineClosePrices, 0);
   ArrayResize(closedOnlineProfits, 0);
   ArrayResize(closedOnlineSwaps, 0);
   ArrayResize(closedOnlineCommissions, 0);
   ArrayResize(closedOnlineCloseTimes, 0);
   
   // Print("All tracking arrays cleared");
   // Print("========================================");
   // Print("AUTO-RESET COMPLETE");
   // Print("Server can be restarted without manual EA removal");
   // Print("========================================");
}

// Reset the disconnected flag to allow reconnection
void ResetServerConnectionFlag()
{
   if(g_ServerDisconnected)
   {
      // Print("Resetting server connection flag - ready for reconnection");
      g_ServerDisconnected = false;
   }
}

// Optional: quick GET /health connectivity probe
void HealthCheck()
{
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/health";
   string host_hdr = ServerIP + ":" + IntegerToString(ServerPort);
   string headers =
      "Host: " + host_hdr + "\r\n" +
      "Accept: */*\r\n" +
      "Connection: close\r\n";
   // WebRequest requires a char array for data; use empty array for GET
   char empty[]; ArrayResize(empty,0);
   string body, hdrs;
   int timeout = 5000;
   int code = HttpGet(url, headers, timeout, body, hdrs);
   // Print("HealthCheck GET ", url, " -> code=", code, " hdr=", hdrs, " body=", body);
}

// Fetch message from server and print to Experts tab
void FetchAndPrintMessage()
{
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/message";
   string host_hdr = ServerIP + ":" + IntegerToString(ServerPort);
   string headers =
      "Host: " + host_hdr + "\r\n" +
      "Accept: application/json\r\n" +
      "Connection: close\r\n";
   // Empty payload for GET
   char empty[]; ArrayResize(empty,0);
   string body, hdrs;
   int timeout = 5000;
   int code = HttpGet(url, headers, timeout, body, hdrs);
   if(code==200)
   {
      // Extract simple {"message":"..."}
      int p = StringFind(body, "\"message\":");
      if(p>=0)
      {
         int start = StringFind(body, "\"", p+10);
         int end = (start>=0) ? StringFind(body, "\"", start+1) : -1;
         if(start>=0 && end>start)
         {
            string msg = StringSubstr(body, start+1, end-start-1);
            // Print("Server message: ", msg);
         }
      }
   }
   else
   {
   // Print("FetchAndPrintMessage FAILED code=", code, " hdr=", hdrs);
   }
}

bool SendArrays()
{
   if(!SendToServer) return true; // disabled

   string payload = BuildPayload();
   
   // DEBUG: Print payload to terminal to verify data
   Print("=== PACKET A - TRADE_STATE DEBUG ===");
   Print("Payload length: ", StringLen(payload), " bytes");
   Print("First 500 chars: ", StringSubstr(payload, 0, MathMin(500, StringLen(payload))));
   if(StringLen(payload) > 500)
      Print("Last 200 chars: ", StringSubstr(payload, StringLen(payload)-200, 200));
   Print("=====================================");
   
   // Build exact-length byte buffer (avoid trailing NULs)
   char post_data[];
   int payload_len = StringLen(payload);
   ArrayResize(post_data, payload_len);
   StringToCharArray(payload, post_data, 0, payload_len);

   string host_hdr = ServerIP + ":" + IntegerToString(ServerPort);
   string headers =
      "Host: " + host_hdr + "\r\n" +
      "Content-Type: application/json\r\n" +
      "Accept: */*\r\n" +
      "Connection: close\r\n" +
      "Content-Length: " + IntegerToString(payload_len) + "\r\n";
   // Build URL from IP + Port
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/";
   
   // Build list of unique symbols currently open
   string uniqueSymbols[];
   int uniqueCount = 0;
   ArrayResize(uniqueSymbols, 0);
   for(int i=0; i<ArraySize(openSymbols); i++)
   {
      bool found = false;
      for(int j=0; j<uniqueCount; j++)
      {
         if(uniqueSymbols[j] == openSymbols[i])
         {
            found = true;
            break;
         }
      }
      if(!found)
      {
         ArrayResize(uniqueSymbols, uniqueCount + 1);
         uniqueSymbols[uniqueCount] = openSymbols[i];
         uniqueCount++;
      }
   }
   
   // Format symbols list for printing
   string symbolsList = "";
   for(int i=0; i<uniqueCount; i++)
   {
      if(i>0) symbolsList += ", ";
      symbolsList += uniqueSymbols[i];
   }
   if(symbolsList == "") symbolsList = "None";
   
   // Print("Client: [", IntegerToString(ID), "] - Sending snapshot with ", ArraySize(openTickets), " open trades");
   // Print("  Symbols Currently Open: [", symbolsList, "]");
   
   int timeout = 15000;
   string respBody, respHdrs;
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   if(code!=200)
   {
      int lastErr = GetLastError();
      // Print("SendArrays FAILED: code=", code, " lastError=", lastErr);
      // Print("Tip: Ensure Tools > Options > Expert Advisors > Allow WebRequest includes ", url);
      
      // Check if this is a server disconnection error
      if(IsServerDisconnectionError(code, lastErr))
      {
         // Print("Detected server disconnection - triggering auto-reset");
         PerformAutoReset();
      }
      else
      {
         // Probe connectivity to help debug
         HealthCheck();
      }
      return false;
   }
   // Print("Server: Response OK");
   
   // Reset disconnection flag on successful connection
   ResetServerConnectionFlag();
   
   return true;
}

#define NEWS_ANALYZER_STATE_DO_NOTHING 0
#define NEWS_ANALYZER_STATE_OPEN_BUY   1
#define NEWS_ANALYZER_STATE_OPEN_SELL  2
#define NEWS_ANALYZER_STATE_CLOSE_TRADE 3
double _NormalizeVolume(string symbol, double vol)
{
   double minVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double step   = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   if(step<=0.0) step = 0.01;
   if(vol < minVol) vol = minVol;
   if(vol > maxVol) vol = maxVol;
   double steps = MathFloor(vol/step);
   vol = steps*step;
   if(vol < minVol) vol = minVol;
   return vol;
}

// Poll the server for a command for this EA's ID and execute it
bool ProcessServerCommand()
{
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/command/" + IntegerToString(ID);
   string host_hdr = ServerIP + ":" + IntegerToString(ServerPort);
   string headers =
      "Host: " + host_hdr + "\r\n" +
      "Accept: application/json\r\n" +
      "Connection: close\r\n";
   char empty[]; ArrayResize(empty,0);
   string body, hdrs;
   int timeout = 5000;
   int code = HttpGet(url, headers, timeout, body, hdrs);
   if(code != 200)
   {
      int lastErr = GetLastError();
      
      // Check if this is a server disconnection error
      if(IsServerDisconnectionError(code, lastErr))
      {
         // Print("ProcessServerCommand: Detected server disconnection - triggering auto-reset");
         PerformAutoReset();
      }
      
      return false;
   }

   long state = 0;
   if(!JsonGetInteger(body, "state", state))
      return false;

   // Reset disconnection flag on successful connection
   ResetServerConnectionFlag();

   string cmdId = "";
   JsonGetString(body, "cmdId", cmdId);
   
   // Print received command
   if(state != NEWS_ANALYZER_STATE_DO_NOTHING)
   {
      string stateStr = (state==NEWS_ANALYZER_STATE_OPEN_BUY ? "OPEN BUY" : 
                         state==NEWS_ANALYZER_STATE_OPEN_SELL ? "OPEN SELL" :
                         state==NEWS_ANALYZER_STATE_CLOSE_TRADE ? "CLOSE TRADE" : "UNKNOWN");
      Print("[MT5-RECV] Server: Command received - state=", (int)state, " (", stateStr, ") cmdId=", cmdId);
   }

   bool success = true;
   string details = "";

   if(state == NEWS_ANALYZER_STATE_DO_NOTHING)
   {
      success = true;
      details = "{\"message\":\"noop\"}";
   }
   else if(state == NEWS_ANALYZER_STATE_OPEN_BUY || state == NEWS_ANALYZER_STATE_OPEN_SELL)
   {
      string symbol = Symbol();
      double vol = 0.0;
      string comment = "";
      JsonGetString(body, "symbol", symbol);
      JsonGetNumber(body, "volume", vol);
      JsonGetString(body, "comment", comment);
      // Optional: absolute SL/TP or pip distances
      double absSL = 0.0, absTP = 0.0;
      double slPips = 0.0, tpPips = 0.0;
      JsonGetNumber(body, "sl", absSL);
      JsonGetNumber(body, "tp", absTP);
      JsonGetNumber(body, "slPips", slPips);
      JsonGetNumber(body, "tpPips", tpPips);

      // Compute SL/TP if pip distances provided
      // First, ensure the symbol is selected and prices are available
      if(!SymbolSelect(symbol, true))
      {
         Print("[MT5-WARN] Could not select symbol ", symbol, " in Market Watch");
      }
      
      // Refresh symbol data
      MqlTick tick;
      SymbolInfoTick(symbol, tick);
      
      double pt = SymbolInfoDouble(symbol, SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      double pip = pt;
      if(digits==3 || digits==5) pip = pt*10.0; // common pip definition for 3/5-digit symbols

      double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      
      // Debug: Print pip calculation values
      Print("[MT5-DEBUG] symbol=", symbol, " ask=", ask, " bid=", bid, " point=", pt, " digits=", digits, " pip=", pip);
      Print("[MT5-DEBUG] slPips=", slPips, " tpPips=", tpPips);
      Print("[MT5-DEBUG] absSL (from JSON)=", absSL, " absTP (from JSON)=", absTP);
      
      // Validate that we have valid prices
      if(ask <= 0.0 || bid <= 0.0)
      {
         Print("[MT5-ERROR] Invalid prices for ", symbol, " - ask=", ask, " bid=", bid);
         success = false;
         details = "{\"retcode\":10018,\"message\":\"Invalid symbol prices - symbol may not be available\"}";
      }
      else
      {
         if(absSL==0.0 && MathAbs(slPips)>0.0)
         {
            if(state==NEWS_ANALYZER_STATE_OPEN_BUY) absSL = ask - MathAbs(slPips) * pip; else absSL = bid + MathAbs(slPips) * pip;
         }
         if(absTP==0.0 && MathAbs(tpPips)>0.0)
         {
            if(state==NEWS_ANALYZER_STATE_OPEN_BUY) absTP = ask + MathAbs(tpPips) * pip; else absTP = bid - MathAbs(tpPips) * pip;
         }
         
         // Normalize SL/TP to symbol's tick size
         if(absSL > 0.0) absSL = NormalizeDouble(absSL, digits);
         if(absTP > 0.0) absTP = NormalizeDouble(absTP, digits);
         
         // Debug: Print calculated SL/TP
         Print("[MT5-DEBUG] Calculated absSL=", absSL, " absTP=", absTP);

         vol = _NormalizeVolume(symbol, vol);
         bool placed = (state==NEWS_ANALYZER_STATE_OPEN_BUY)
            ? trade.Buy(vol, symbol, 0.0, absSL, absTP, comment)
            : trade.Sell(vol, symbol, 0.0, absSL, absTP, comment);
         long rc = (long)trade.ResultRetcode();
         string rdesc = trade.ResultRetcodeDescription();
         double exe_price = trade.ResultPrice();
         success = placed && (rc==TRADE_RETCODE_DONE || rc==TRADE_RETCODE_PLACED);
         string typestr = (state==NEWS_ANALYZER_STATE_OPEN_BUY) ? "BUY" : "SELL";
         int sd = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
         string jvol = DoubleToString(vol, 2);
         string jsl = DoubleToString(absSL, sd);
         string jpaid = DoubleToString(exe_price, sd);
         string jtp = DoubleToString(absTP, sd);
         if(placed)
         {
            Print("[MT5-SUCCESS] TRADE PLACED: ", typestr, " ", symbol, " Vol=", jvol, " Price=", jpaid, " TP=", jtp, " SL=", jsl, " Retcode=", (int)rc, " ", rdesc);
         }
         else
         {
            Print("[MT5-FAILED] TRADE FAILED: ", typestr, " ", symbol, " Vol=", jvol, " Retcode=", (int)rc, " ", rdesc);
         }
         details = "{"+
            "\"retcode\":" + IntegerToString((int)rc) + ","+
            "\"message\":\"" + JsonEscape(rdesc) + "\","+
            "\"symbol\":\"" + symbol + "\","+
            "\"type\":\"" + typestr + "\","+
            "\"volume\":" + jvol + ","+
            "\"paid\":" + jpaid + ","+
            "\"sl\":" + jsl + ","+
            "\"tp\":" + jtp +
         "}";
      }
   }
   else if(state == NEWS_ANALYZER_STATE_CLOSE_TRADE)
   {
      long ticket = 0;
      string symbol = "";
      double vol = 0.0;
   long sideType = -1; // 0 BUY, 1 SELL (optional)
      JsonGetInteger(body, "ticket", ticket);
      JsonGetString(body, "symbol", symbol);
      JsonGetNumber(body, "volume", vol);
   JsonGetInteger(body, "type", sideType);
      bool closed = false;
      if(ticket>0)
      {
         // Print ticket and detected type before closing
         string sym2=""; long ptype=0; double pvol=0.0;
         if(SelectPositionByTicket((ulong)ticket, sym2, ptype, pvol))
         {
            string tstr = (ptype==POSITION_TYPE_BUY ? "BUY" : "SELL");
            string vstr = DoubleToString((vol>0.0?vol:pvol), 2);
            // Print("CLOSING: ticket=", (long)ticket, " type=", tstr, " symbol=", sym2, " vol=", vstr);
         }
         closed = ClosePositionByTicket((ulong)ticket, vol);
      }
      else if(symbol!="")
      {
         // find first ticket with that symbol and optional side filter
         for(int i=0;i<ArraySize(openTickets);++i)
         {
            if(openSymbols[i]==symbol && (sideType<0 || openTypes[i]==sideType))
            {
               string tstr = (openTypes[i]==POSITION_TYPE_BUY ? "BUY" : "SELL");
               string vstr2 = DoubleToString((vol>0.0?vol:openVolumes[i]), 2);
               // Print("CLOSING: ticket=", (long)openTickets[i], " type=", tstr, " symbol=", openSymbols[i], " vol=", vstr2);
               closed = ClosePositionByTicket(openTickets[i], vol);
               if(closed) break;
            }
         }
      }
      success = closed;
      details = closed ? "{\"message\":\"closed\"}" : "{\"message\":\"close_failed\"}";
   }

   // ACK back if we have a cmdId
   if(cmdId!="")
   {
      string ack_url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/ack/" + IntegerToString(ID);
      string payload = "{\"cmdId\":\"" + cmdId + "\",\"success\":" + (success?"true":"false") + ",\"details\":" + details + "}";

      // build headers with content length
      int payload_len = StringLen(payload);
      char post_data[]; ArrayResize(post_data, payload_len); StringToCharArray(payload, post_data, 0, payload_len);
      string ack_headers =
         "Host: " + host_hdr + "\r\n" +
         "Content-Type: application/json\r\n" +
         "Accept: */*\r\n" +
         "Connection: close\r\n" +
         "Content-Length: " + IntegerToString(payload_len) + "\r\n";
      string respBody, respHdrs;
      int ack_code = HttpPost(ack_url, ack_headers, payload, 5000, respBody, respHdrs);
      // Print("Client: [", IntegerToString(ID), "] - Sent ACK cmdId=", cmdId, " success=", (success?"true":"false"));
   }

   return success;
}

//+------------------------------------------------------------------+
//| Send Packet B - Account Info (with change detection)             |
//| Sends every 30-60s OR when balance/equity changes                |
//+------------------------------------------------------------------+
bool SendPacket_B()
{
   // Get current account data
   double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   datetime currentTime = TimeCurrent();
   
   // Calculate time since last send
   int secondsSinceLastSend = (int)(currentTime - g_lastAccountPacketTime);
   
   // Check if we should send:
   // 1. Balance changed
   // 2. Equity changed
   // 3. 60+ seconds elapsed since last send
   bool balanceChanged = (MathAbs(currentBalance - g_lastBalanceSent) > 0.01);
   bool equityChanged = (MathAbs(currentEquity - g_lastEquitySent) > 0.01);
   bool timeElapsed = (secondsSinceLastSend >= 60);
   
   // Must be at least 30 seconds since last send
   if(secondsSinceLastSend < 30)
      return false;
   
   // Send if any condition met
   if(!balanceChanged && !equityChanged && !timeElapsed)
      return false;
   
   // Build and send packet
   string payload = BuildPacket_B_AccountInfo();
   
   string headers = "Content-Type: application/json\r\n";
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/";
   int timeout = 5000;
   string respBody, respHdrs;
   
   Print("=== PACKET B - ACCOUNT_INFO DEBUG ===");
   Print("Balance: ", DoubleToString(currentBalance, 2), " (changed: ", (balanceChanged?"YES":"NO"), ")");
   Print("Equity: ", DoubleToString(currentEquity, 2), " (changed: ", (equityChanged?"YES":"NO"), ")");
   Print("Time since last: ", secondsSinceLastSend, "s");
   Print("Payload: ", payload);
   Print("=====================================");
   
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   
   if(code == 200)
   {
      // Update tracking variables
      g_lastBalanceSent = currentBalance;
      g_lastEquitySent = currentEquity;
      g_lastAccountPacketTime = currentTime;
      return true;
   }
   else
   {
      // Print("Packet B send failed: code=", code);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Send Packet C - Symbol Data (ATR, spread, prices)                |
//| Sends every 30 seconds                                            |
//+------------------------------------------------------------------+
bool SendPacket_C()
{
   datetime currentTime = TimeCurrent();
   int secondsSinceLastSend = (int)(currentTime - g_lastSymbolPacketTime);
   
   // Send every 30 seconds
   if(secondsSinceLastSend < 30)
      return false;
   
   // Build and send packet
   string payload = BuildPacket_C_SymbolData();
   
   string headers = "Content-Type: application/json\r\n";
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/";
   int timeout = 5000;
   string respBody, respHdrs;
   
   Print("=== PACKET C - SYMBOL_DATA DEBUG ===");
   Print("Payload length: ", StringLen(payload), " bytes");
   Print("First 300 chars: ", StringSubstr(payload, 0, MathMin(300, StringLen(payload))));
   if(StringLen(payload) > 300)
      Print("Last 100 chars: ", StringSubstr(payload, StringLen(payload)-100, 100));
   Print("=====================================");
   
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   
   if(code == 200)
   {
      g_lastSymbolPacketTime = currentTime;
      return true;
   }
   else
   {
      // Print("Packet C send failed: code=", code);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Update MAE/MFE for all open positions                            |
//+------------------------------------------------------------------+
void UpdateMAE_MFE()
{
   int count = ArraySize(openTickets);
   
   // Ensure arrays are sized correctly
   if(ArraySize(openMAE) != count) ArrayResize(openMAE, count);
   if(ArraySize(openMFE) != count) ArrayResize(openMFE, count);
   
   for(int i = 0; i < count; i++)
   {
      double currentPrice = openCurrentPrices[i];
      double openPrice = openOpenPrices[i];
      double point = SymbolInfoDouble(openSymbols[i], SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(openSymbols[i], SYMBOL_DIGITS);
      
      // Calculate pip difference
      double pipMultiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;
      double pipDiff = 0.0;
      
      if(openTypes[i] == POSITION_TYPE_BUY)
         pipDiff = (currentPrice - openPrice) / point / pipMultiplier;
      else
         pipDiff = (openPrice - currentPrice) / point / pipMultiplier;
      
      // Update MAE (worst loss in pips - negative number)
      if(pipDiff < openMAE[i])
         openMAE[i] = pipDiff;
      
      // Update MFE (best profit in pips - positive number)
      if(pipDiff > openMFE[i])
         openMFE[i] = pipDiff;
   }
}

//+------------------------------------------------------------------+
//| Send Packet D - Position Analytics (MAE/MFE every 5s)            |
//+------------------------------------------------------------------+
bool SendPacket_D()
{
   // Only send if we have open positions
   int positionCount = ArraySize(openTickets);
   if(positionCount == 0)
      return false;
   
   datetime currentTime = TimeCurrent();
   int secondsSinceLastSend = (int)(currentTime - g_lastAnalyticsPacketTime);
   
   // Send every 5 seconds
   if(secondsSinceLastSend < 5)
      return false;
   
   // Update MAE/MFE before building packet
   UpdateMAE_MFE();
   
   // Build and send packet
   string payload = BuildPacket_D_PositionAnalytics();
   
   string headers = "Content-Type: application/json\r\n";
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/";
   int timeout = 5000;
   string respBody, respHdrs;
   
   Print("=== PACKET D - POSITION_ANALYTICS DEBUG ===");
   Print("Open positions: ", positionCount);
   Print("Payload length: ", StringLen(payload), " bytes");
   Print("Payload: ", payload);
   Print("===========================================");
   
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   
   if(code == 200)
   {
      g_lastAnalyticsPacketTime = currentTime;
      return true;
   }
   else
   {
      // Print("Packet D send failed: code=", code);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Send Packet E - Close Details (immediate on trade close)         |
//+------------------------------------------------------------------+
bool SendPacket_E(
   ulong ticket,
   string symbol,
   long type,
   double volume,
   double openPrice,
   double closePrice,
   datetime openTime,
   datetime closeTime,
   double profit,
   double swap,
   double commission,
   double mae,
   double mfe)
{
   // Build packet with all trade details
   string payload = BuildPacket_E_CloseDetails(
      ticket, symbol, type, volume,
      openPrice, closePrice,
      openTime, closeTime,
      profit, swap, commission,
      mae, mfe
   );
   
   string headers = "Content-Type: application/json\r\n";
   string url = "http://" + ServerIP + ":" + IntegerToString(ServerPort) + "/";
   int timeout = 5000;
   string respBody, respHdrs;
   
   Print("=== PACKET E - CLOSE_DETAILS DEBUG ===");
   Print("Trade closed: Ticket=", (long)ticket, " Symbol=", symbol);
   Print("Profit: ", DoubleToString(profit, 2), " MAE: ", DoubleToString(mae, 1), " MFE: ", DoubleToString(mfe, 1));
   Print("Payload length: ", StringLen(payload), " bytes");
   Print("Payload: ", payload);
   Print("======================================");
   
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   
   if(code == 200)
   {
      return true;
   }
   else
   {
      // Print("Packet E send failed: code=", code);
      return false;
   }
}

#endif