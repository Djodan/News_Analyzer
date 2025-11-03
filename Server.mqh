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
   
   Print("Client: [", IntegerToString(ID), "] - Sending snapshot with ", ArraySize(openTickets), " open trades");
   Print("  Symbols Currently Open: [", symbolsList, "]");
   
   int timeout = 15000;
   string respBody, respHdrs;
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   if(code!=200)
   {
      int lastErr = GetLastError();
      Print("SendArrays FAILED: code=", code, " lastError=", lastErr);
      Print("Tip: Ensure Tools > Options > Expert Advisors > Allow WebRequest includes ", url);
   // Probe connectivity to help debug
   HealthCheck();
      return false;
   }
   Print("Server: Response OK");
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
      return false;

   long state = 0;
   if(!JsonGetInteger(body, "state", state))
      return false;

   string cmdId = "";
   JsonGetString(body, "cmdId", cmdId);
   
   // Print received command
   if(state != NEWS_ANALYZER_STATE_DO_NOTHING)
   {
      string stateStr = (state==NEWS_ANALYZER_STATE_OPEN_BUY ? "OPEN BUY" : 
                         state==NEWS_ANALYZER_STATE_OPEN_SELL ? "OPEN SELL" :
                         state==NEWS_ANALYZER_STATE_CLOSE_TRADE ? "CLOSE TRADE" : "UNKNOWN");
      Print("Server: Command received - state=", (int)state, " (", stateStr, ") cmdId=", cmdId);
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
         Print("WARNING: Could not select symbol ", symbol, " in Market Watch");
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
      Print("DEBUG: symbol=", symbol, " ask=", ask, " bid=", bid, " point=", pt, " digits=", digits, " pip=", pip);
      Print("DEBUG: slPips=", slPips, " tpPips=", tpPips);
      Print("DEBUG: absSL (from JSON)=", absSL, " absTP (from JSON)=", absTP);
      
      // Validate that we have valid prices
      if(ask <= 0.0 || bid <= 0.0)
      {
         Print("ERROR: Invalid prices for ", symbol, " - ask=", ask, " bid=", bid);
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
         Print("DEBUG: Calculated absSL=", absSL, " absTP=", absTP);

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
            Print("TRADE PLACED: ", typestr, " ", symbol, " Vol=", jvol, " Price=", jpaid, " TP=", jtp, " SL=", jsl, " Retcode=", (int)rc, " ", rdesc);
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
            Print("CLOSING: ticket=", (long)ticket, " type=", tstr, " symbol=", sym2, " vol=", vstr);
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
               Print("CLOSING: ticket=", (long)openTickets[i], " type=", tstr, " symbol=", openSymbols[i], " vol=", vstr2);
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
      Print("Client: [", IntegerToString(ID), "] - Sent ACK cmdId=", cmdId, " success=", (success?"true":"false"));
   }

   return success;
}

#endif