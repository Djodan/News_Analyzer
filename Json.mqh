//+------------------------------------------------------------------+
//|                                                       Json.mqh   |
//|                JSON helpers and payload builders                |
//+------------------------------------------------------------------+
#ifndef NEWS_ANALYZER_JSON_MQH
#define NEWS_ANALYZER_JSON_MQH

#include "GlobalVariables.mqh"
#include "Inputs.mqh"

string JsonEscape(const string s)
{
   string out="";
   for(int i=0;i<StringLen(s);i++)
   {
      ushort c=StringGetCharacter(s,i);
      if(c=='"') out+="\\\"";
      else if(c=='\\') out+="\\\\";
      else if(c=='\n') out+="\\n";
      else if(c=='\r') out+="\\r";
      else if(c=='\t') out+="\\t";
      else out+=StringSubstr(s,i,1);
   }
   return out;
}

string FormatISO8601(datetime dt)
{
   MqlDateTime mdt;
   TimeToStruct(dt, mdt);
   string iso = StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",
      mdt.year, mdt.mon, mdt.day, mdt.hour, mdt.min, mdt.sec);
   return iso;
}

string BuildPayload()
{
   string json = "{";
   json += "\"id\":"+IntegerToString(ID)+",";
   json += "\"mode\":\"" + (Mode==Sender?"Sender":"Receiver") + "\",";
   json += "\"timestamp\":\"" + FormatISO8601(TimeCurrent()) + "\",";

   // Open positions
   json += "\"open\":[";
   int n = ArraySize(openTickets);
   for(int i=0;i<n;i++)
   {
      if(i>0) json+=",";
      json+="{";
      json+="\"ticket\":"+IntegerToString((long)openTickets[i])+",";
      json+="\"symbol\":\""+JsonEscape(openSymbols[i])+"\",";
      json+="\"type\":"+IntegerToString((int)openTypes[i])+",";
      json+="\"volume\":"+DoubleToString(openVolumes[i],2)+",";
      json+="\"openPrice\":"+DoubleToString(openOpenPrices[i],_Digits)+",";
      json+="\"price\":"+DoubleToString(openCurrentPrices[i],_Digits)+",";
      json+="\"sl\":"+DoubleToString(openSLs[i],_Digits)+",";
      json+="\"tp\":"+DoubleToString(openTPs[i],_Digits)+",";
      json+="\"openTime\":\""+FormatISO8601(openOpenTimes[i])+"\",";
      json+="\"magic\":"+IntegerToString((int)openMagics[i])+",";
      json+="\"comment\":\""+JsonEscape(openComments[i])+"\"";
      json+="}";
   }
   json += "],";
   
   // Symbols currently open - list of unique symbols
   json += "\"symbolsCurrentlyOpen\":[";
   string uniqueSymbols[];
   int uniqueCount = 0;
   ArrayResize(uniqueSymbols, 0);
   
   // Extract unique symbols from open positions
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
   
   // Build JSON array of symbols
   for(int i=0; i<uniqueCount; i++)
   {
      if(i>0) json+=",";
      json+="\""+JsonEscape(uniqueSymbols[i])+"\"";
   }
   json += "],";

   // Closed offline
   json += "\"closed_offline\":[";
   n = ArraySize(closedOfflineDeals);
   for(int i=0;i<n;i++)
   {
      if(i>0) json+=",";
      json+="{";
      json+="\"deal\":"+IntegerToString((long)closedOfflineDeals[i])+",";
      json+="\"symbol\":\""+JsonEscape(closedOfflineSymbols[i])+"\",";
      json+="\"type\":"+IntegerToString((int)closedOfflineTypes[i])+",";
      json+="\"volume\":"+DoubleToString(closedOfflineVolumes[i],2)+",";
      json+="\"openPrice\":"+DoubleToString(closedOfflineOpenPrices[i],_Digits)+",";
      json+="\"closePrice\":"+DoubleToString(closedOfflineClosePrices[i],_Digits)+",";
      json+="\"profit\":"+DoubleToString(closedOfflineProfits[i],2)+",";
      json+="\"swap\":"+DoubleToString(closedOfflineSwaps[i],2)+",";
      json+="\"commission\":"+DoubleToString(closedOfflineCommissions[i],2)+",";
      json+="\"closeTime\":"+IntegerToString((int)closedOfflineCloseTimes[i])+"";
      json+="}";
   }
   json += "],";

   // Closed online
   json += "\"closed_online\":[";
   n = ArraySize(closedOnlineDeals);
   for(int i=0;i<n;i++)
   {
      if(i>0) json+=",";
      json+="{";
      json+="\"deal\":"+IntegerToString((long)closedOnlineDeals[i])+",";
      json+="\"symbol\":\""+JsonEscape(closedOnlineSymbols[i])+"\",";
      json+="\"type\":"+IntegerToString((int)closedOnlineTypes[i])+",";
      json+="\"volume\":"+DoubleToString(closedOnlineVolumes[i],2)+",";
      json+="\"openPrice\":"+DoubleToString(closedOnlineOpenPrices[i],_Digits)+",";
      json+="\"closePrice\":"+DoubleToString(closedOnlineClosePrices[i],_Digits)+",";
      json+="\"profit\":"+DoubleToString(closedOnlineProfits[i],2)+",";
      json+="\"swap\":"+DoubleToString(closedOnlineSwaps[i],2)+",";
      json+="\"commission\":"+DoubleToString(closedOnlineCommissions[i],2)+",";
      json+="\"closeTime\":"+IntegerToString((int)closedOnlineCloseTimes[i])+"";
      json+="}";
   }
   json += "]";

   json += "}";
   return json;
}

//+------------------------------------------------------------------+
//| Build Packet B - Account Info (balance, equity)                  |
//+------------------------------------------------------------------+
string BuildPacket_B_AccountInfo()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   string json = "{";
   json += "\"packetType\":\"B\",";
   json += "\"id\":"+IntegerToString(ID)+",";
   json += "\"timestamp\":\"" + FormatISO8601(TimeCurrent()) + "\",";
   json += "\"balance\":" + DoubleToString(balance, 2) + ",";
   json += "\"equity\":" + DoubleToString(equity, 2);
   json += "}";
   
   return json;
}

//+------------------------------------------------------------------+
//| Helper: Get ATR value and format symbol data                     |
//+------------------------------------------------------------------+
string FormatSymbolData(string symbol, int atrHandle)
{
   // Get current prices
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   
   // Calculate spread in pips
   double spreadPoints = (ask - bid) / point;
   double spread = spreadPoints;
   if(digits == 3 || digits == 5) spread = spreadPoints / 10.0; // Convert to pips for 3/5 digit pairs
   
   // Get ATR value (14-period on current timeframe)
   double atrBuffer[];
   ArraySetAsSeries(atrBuffer, true);
   double atr = 0.0;
   
   if(atrHandle != INVALID_HANDLE)
   {
      if(CopyBuffer(atrHandle, 0, 0, 1, atrBuffer) > 0)
      {
         atr = atrBuffer[0];
         // Convert ATR to pips
         if(digits == 3 || digits == 5)
            atr = atr / (point * 10.0);
         else
            atr = atr / point;
      }
   }
   
   // Alert if ATR is 0 (pair not loaded or no data) - only if ATRalert input is enabled
   if(ATRalert && atr == 0.0 && bid == 0.0)
   {
      Alert("WARNING: ", symbol, " has not been loaded - ATR is 0 and no price data available!");
   }
   
   // Build JSON object for this symbol
   string json = "{";
   json += "\"symbol\":\"" + symbol + "\",";
   json += "\"atr\":" + DoubleToString(atr, 1) + ",";
   json += "\"spread\":" + DoubleToString(spread, 1) + ",";
   json += "\"bid\":" + DoubleToString(bid, digits) + ",";
   json += "\"ask\":" + DoubleToString(ask, digits);
   json += "}";
   
   return json;
}

//+------------------------------------------------------------------+
//| Build Packet C - Symbol Data (ATR, spread, prices for 29 pairs)  |
//+------------------------------------------------------------------+
string BuildPacket_C_SymbolData()
{
   string json = "{";
   json += "\"packetType\":\"C\",";
   json += "\"id\":"+IntegerToString(ID)+",";
   json += "\"timestamp\":\"" + FormatISO8601(TimeCurrent()) + "\",";
   json += "\"symbols\":[";
   
   // Add all 29 currency pairs (28 forex + 1 crypto)
   json += FormatSymbolData("AUDCAD", g_atrHandle_AUDCAD) + ",";
   json += FormatSymbolData("AUDJPY", g_atrHandle_AUDJPY) + ",";
   json += FormatSymbolData("AUDUSD", g_atrHandle_AUDUSD) + ",";
   json += FormatSymbolData("AUDCHF", g_atrHandle_AUDCHF) + ",";
   json += FormatSymbolData("AUDNZD", g_atrHandle_AUDNZD) + ",";
   json += FormatSymbolData("CADJPY", g_atrHandle_CADJPY) + ",";
   json += FormatSymbolData("CADCHF", g_atrHandle_CADCHF) + ",";
   json += FormatSymbolData("EURAUD", g_atrHandle_EURAUD) + ",";
   json += FormatSymbolData("EURCAD", g_atrHandle_EURCAD) + ",";
   json += FormatSymbolData("EURCHF", g_atrHandle_EURCHF) + ",";
   json += FormatSymbolData("EURGBP", g_atrHandle_EURGBP) + ",";
   json += FormatSymbolData("EURJPY", g_atrHandle_EURJPY) + ",";
   json += FormatSymbolData("EURNZD", g_atrHandle_EURNZD) + ",";
   json += FormatSymbolData("EURUSD", g_atrHandle_EURUSD) + ",";
   json += FormatSymbolData("GBPAUD", g_atrHandle_GBPAUD) + ",";
   json += FormatSymbolData("GBPCAD", g_atrHandle_GBPCAD) + ",";
   json += FormatSymbolData("GBPCHF", g_atrHandle_GBPCHF) + ",";
   json += FormatSymbolData("GBPJPY", g_atrHandle_GBPJPY) + ",";
   json += FormatSymbolData("GBPNZD", g_atrHandle_GBPNZD) + ",";
   json += FormatSymbolData("GBPUSD", g_atrHandle_GBPUSD) + ",";
   json += FormatSymbolData("NZDCAD", g_atrHandle_NZDCAD) + ",";
   json += FormatSymbolData("NZDCHF", g_atrHandle_NZDCHF) + ",";
   json += FormatSymbolData("NZDJPY", g_atrHandle_NZDJPY) + ",";
   json += FormatSymbolData("NZDUSD", g_atrHandle_NZDUSD) + ",";
   json += FormatSymbolData("USDCAD", g_atrHandle_USDCAD) + ",";
   json += FormatSymbolData("USDCHF", g_atrHandle_USDCHF) + ",";
   json += FormatSymbolData("USDJPY", g_atrHandle_USDJPY) + ",";
   json += FormatSymbolData("CHFJPY", g_atrHandle_CHFJPY) + ",";
   json += FormatSymbolData("BITCOIN", g_atrHandle_BITCOIN);
   
   json += "]}";
   
   return json;
}

//+------------------------------------------------------------------+
//| Build Packet D - Position Analytics (MAE/MFE every 5s)           |
//+------------------------------------------------------------------+
string BuildPacket_D_PositionAnalytics()
{
   string json = "{";
   json += "\"packetType\":\"D\",";
   json += "\"id\":"+IntegerToString(ID)+",";
   json += "\"timestamp\":\"" + FormatISO8601(TimeCurrent()) + "\",";
   json += "\"positions\":[";
   
   int count = ArraySize(openTickets);
   datetime currentTime = TimeCurrent();
   
   for(int i = 0; i < count; i++)
   {
      if(i > 0) json += ",";
      
      // Get current price for unrealized P&L calculation
      double currentPrice = openCurrentPrices[i];
      double openPrice = openOpenPrices[i];
      int digits = (int)SymbolInfoInteger(openSymbols[i], SYMBOL_DIGITS);
      double point = SymbolInfoDouble(openSymbols[i], SYMBOL_POINT);
      
      // Calculate pip difference (handles 3/5 digit pairs)
      double pipMultiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;
      double pipDiff = 0.0;
      
      if(openTypes[i] == POSITION_TYPE_BUY)
         pipDiff = (currentPrice - openPrice) / point / pipMultiplier;
      else
         pipDiff = (openPrice - currentPrice) / point / pipMultiplier;
      
      // Calculate unrealized P&L (simplified - actual calculation needs contract size)
      double unrealizedPnL = pipDiff * openVolumes[i] * 10.0; // Rough estimate
      
      // Get MAE/MFE (already tracked in arrays)
      double mae = (i < ArraySize(openMAE)) ? openMAE[i] : 0.0;
      double mfe = (i < ArraySize(openMFE)) ? openMFE[i] : 0.0;
      
      // Calculate seconds open
      int secondsOpen = (int)(currentTime - openOpenTimes[i]);
      
      json += "{";
      json += "\"ticket\":" + IntegerToString((long)openTickets[i]) + ",";
      json += "\"symbol\":\"" + openSymbols[i] + "\",";
      json += "\"currentPrice\":" + DoubleToString(currentPrice, digits) + ",";
      json += "\"unrealizedPnL\":" + DoubleToString(unrealizedPnL, 2) + ",";
      json += "\"mae\":" + DoubleToString(mae, 1) + ",";
      json += "\"mfe\":" + DoubleToString(mfe, 1) + ",";
      json += "\"secondsOpen\":" + IntegerToString(secondsOpen);
      json += "}";
   }
   
   json += "]}";
   
   return json;
}

//+------------------------------------------------------------------+
//| Build Packet E - Close Details (immediate on trade close)        |
//+------------------------------------------------------------------+
string BuildPacket_E_CloseDetails(
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
   double mfe,
   string close_reason="Unknown",
   int strategy_id=2)
{
   // Calculate additional metrics
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double pipMultiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;
   
   // Calculate pip gain
   double pipGain = 0.0;
   if(type == POSITION_TYPE_BUY)
      pipGain = (closePrice - openPrice) / point / pipMultiplier;
   else
      pipGain = (openPrice - closePrice) / point / pipMultiplier;
   
   // Calculate duration in seconds
   int duration = (int)(closeTime - openTime);
   
   // Build JSON
   string json = "{";
   json += "\"packetType\":\"E\",";
   json += "\"id\":"+IntegerToString(ID)+",";
   json += "\"timestamp\":\"" + FormatISO8601(TimeCurrent()) + "\",";
   json += "\"trade\":{";
   json += "\"ticket\":" + IntegerToString((long)ticket) + ",";
   json += "\"symbol\":\"" + symbol + "\",";
   json += "\"type\":" + IntegerToString(type) + ",";
   json += "\"volume\":" + DoubleToString(volume, 2) + ",";
   json += "\"openPrice\":" + DoubleToString(openPrice, digits) + ",";
   json += "\"closePrice\":" + DoubleToString(closePrice, digits) + ",";
   json += "\"openTime\":\"" + FormatISO8601(openTime) + "\",";
   json += "\"closeTime\":\"" + FormatISO8601(closeTime) + "\",";
   json += "\"profit\":" + DoubleToString(profit, 2) + ",";
   json += "\"swap\":" + DoubleToString(swap, 2) + ",";
   json += "\"commission\":" + DoubleToString(commission, 2) + ",";
   json += "\"mae\":" + DoubleToString(mae, 1) + ",";
   json += "\"mfe\":" + DoubleToString(mfe, 1) + ",";
   json += "\"pipGain\":" + DoubleToString(pipGain, 1) + ",";
   json += "\"duration\":" + IntegerToString(duration) + ",";
   json += "\"close_reason\":\"" + close_reason + "\",";
   json += "\"strategy\":\"S" + IntegerToString(strategy_id) + "\"";
   json += "}}";
   
   return json;
}

#endif // NEWS_ANALYZER_JSON_MQH
//+------------------------------------------------------------------+
//|                    Simple JSON extract helpers                  |
//+------------------------------------------------------------------+

// Extract a string value by key: returns true if found
bool JsonGetString(const string body, const string key, string &out)
{
   string patt = "\"" + key + "\"";
   int p = StringFind(body, patt);
   if(p < 0) return false;
   int c = StringFind(body, ":", p);
   if(c < 0) return false;
   int i = c + 1;
   // skip whitespace
   while(i < StringLen(body) && (StringGetCharacter(body,i)==' ' || StringGetCharacter(body,i)=='\t' || StringGetCharacter(body,i)=='\n' || StringGetCharacter(body,i)=='\r')) i++;
   if(i >= StringLen(body)) return false;
   if(StringGetCharacter(body,i)!='"') return false;
   int start = i + 1;
   int end = StringFind(body, "\"", start);
   if(end < 0) return false;
   out = StringSubstr(body, start, end - start);
   return true;
}

// Extract a numeric value by key into double
bool JsonGetNumber(const string body, const string key, double &out)
{
   string patt = "\"" + key + "\"";
   int p = StringFind(body, patt);
   if(p < 0) return false;
   int c = StringFind(body, ":", p);
   if(c < 0) return false;
   int i = c + 1;
   // skip whitespace
   while(i < StringLen(body) && (StringGetCharacter(body,i)==' ' || StringGetCharacter(body,i)=='\t' || StringGetCharacter(body,i)=='\n' || StringGetCharacter(body,i)=='\r')) i++;
   if(i >= StringLen(body)) return false;
   int j = i;
   // read until comma or closing brace
   while(j < StringLen(body))
   {
      ushort ch = StringGetCharacter(body,j);
      if(ch==',' || ch=='}') break;
      j++;
   }
   string num = StringSubstr(body, i, j - i);
   // trim possible quotes
   if(StringLen(num) > 0 && StringGetCharacter(num,0)=='"')
      num = StringSubstr(num,1);
   if(StringLen(num) > 0 && StringGetCharacter(num,StringLen(num)-1)=='"')
      num = StringSubstr(num,0,StringLen(num)-1);
   // trim whitespace by reference
   StringTrimLeft(num);
   StringTrimRight(num);
   out = StringToDouble(num);
   return true;
}

// Extract a numeric value by key into long
bool JsonGetInteger(const string body, const string key, long &out)
{
   double d=0.0;
   if(!JsonGetNumber(body, key, d)) return false;
   out = (long)d;
   return true;
}
