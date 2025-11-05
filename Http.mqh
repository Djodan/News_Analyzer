//+------------------------------------------------------------------+
//|                                                       Http.mqh   |
//|                Simple HTTP helpers for News Analyzer            |
//+------------------------------------------------------------------+
#ifndef NEWS_ANALYZER_HTTP_MQH
#define NEWS_ANALYZER_HTTP_MQH

// Perform a POST request. Returns HTTP code. resultBody/resultHeaders are outputs.
int HttpPost(const string url, const string headers, const string body, const int timeout,
             string &resultBody, string &resultHeaders)
{
   // Prepare body buffer with exact length
   char data[];
   int len = StringLen(body);
   ArrayResize(data, len);
   StringToCharArray(body, data, 0, len);
   // Result buffers
   char result[];
   string hdrs = "";
   int code = WebRequest("POST", url, headers, timeout, data, result, hdrs);
   resultBody = CharArrayToString(result);
   resultHeaders = hdrs;
   return code;
}

// Perform a GET request. Returns HTTP code. resultBody/resultHeaders are outputs.
int HttpGet(const string url, const string headers, const int timeout,
            string &resultBody, string &resultHeaders)
{
   // Empty payload for GET
   char empty[]; ArrayResize(empty,0);
   char result[];
   string hdrs = "";
   int code = WebRequest("GET", url, headers, timeout, empty, result, hdrs);
   resultBody = CharArrayToString(result);
   resultHeaders = hdrs;
   return code;
}

//+------------------------------------------------------------------+
//| Send trade outcome notification to Python server                |
//| Called when a trade closes at TP or SL                          |
//+------------------------------------------------------------------+
bool SendTradeOutcome(string symbol, string outcome, string serverIP, int serverPort)
{
   // Build JSON payload
   string payload = "{\"symbol\":\"" + symbol + "\",\"outcome\":\"" + outcome + "\"}";
   
   // Prepare buffer
   char post_data[];
   int payload_len = StringLen(payload);
   ArrayResize(post_data, payload_len);
   StringToCharArray(payload, post_data, 0, payload_len);
   
   // Build headers
   string host_hdr = serverIP + ":" + IntegerToString(serverPort);
   string headers =
      "Host: " + host_hdr + "\r\n" +
      "Content-Type: application/json\r\n" +
      "Accept: application/json\r\n" +
      "Connection: close\r\n" +
      "Content-Length: " + IntegerToString(payload_len) + "\r\n";
   
   // Build URL
   string url = "http://" + serverIP + ":" + IntegerToString(serverPort) + "/trade_outcome";
   
   // Send request
   string respBody, respHdrs;
   int timeout = 5000;
   int code = HttpPost(url, headers, payload, timeout, respBody, respHdrs);
   
   if(code == 200)
   {
      Print("Trade outcome sent: ", symbol, " -> ", outcome, " (NID tracking updated)");
      return true;
   }
   else
   {
      Print("Failed to send trade outcome: code=", code, " symbol=", symbol, " outcome=", outcome);
      return false;
   }
}

#endif // NEWS_ANALYZER_HTTP_MQH

