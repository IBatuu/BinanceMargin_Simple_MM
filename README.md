# BinanceMargin_Simple_MM
The script is a simple market-making script for Binance Spot/Margin.

This script is more of a boilerplate than anything. It uses many parameters that can be changed and backtested. 

###Here is how it functions:

1) It connects to multiple two different WebSockets, one to get the live market feed and the other to get the live account feed and get all the fills and etc.
2) Script also have three separate infinite loops; one calculates the ATR (Average True Range) to gauge the volatility, and the other check for naked positions which can occur due to servers slacking over heavy volume and failing to send/record fills and thus doesn't trigger TP/SL orders, and the final one is to keep the WebSockets alive inline with the Binance Docs.
3) Script sends FOK(Fill-or-Kill) orders with certain parameters in an infinite loop. Once a fill is received, the script send the TP/SL orders and depending on the volatility and current active positions, adjusts the new parameters and sends new FOK orders

![image](https://github.com/IBatuu/BinanceMargin_Simple_MM/assets/78052559/f595d1ad-2a0d-4d4b-a8fa-688767641eed)
