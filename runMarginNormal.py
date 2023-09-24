from ast import Pass
from tkinter.colorchooser import askcolor
from Wick.wickChaser import MM
import Wick.data as d
from email import message
from tkinter import EXCEPTION
from traceback import print_tb
from requests import Request, Session, Response
from threading import Thread
import _thread
import json
import websocket
import time, math
from binance.spot import Spot 
import requests
import threading
import pandas as pd
client = Spot(key=d.nanceSubApi, secret=d.secretSubApi)
listenKey = client.new_isolated_margin_listen_key("BTCUSDT")
key = listenKey["listenKey"]
#print(client.account())

lastTradedPrice = None
previousTradedPrice = None
cancelBidId = None
cancelAskId = None
stopMargin = 65
bidAskMargin = 8
limitBidAskMargin = 10
amountToBidAskBtc = 0.1
stopLossTakenOut = False
btcusdt = "BTCUSDT"
timerOn = False
lastRecordedStopMargin = 65
lastRecordedBidAskMargin = 8
lastRecordedLimitBidAskMargin = 10
lastPivotAtr = None

def wwma(values, n):
            """
            J. Welles Wilder's EMA 
            """
            return values.ewm(alpha=1/n, adjust=False).mean()
def atr(df, n=14):
    global latestAtr, secondLastAtr
    data = df.copy()
    high = data["high"]
    low = data["low"]
    close = data["close"]
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = wwma(tr, n)
    latestAtr = float(atr[499])
    secondLastAtr = float(atr[498])
    time.sleep(15)
def  getAtr():
    global lastPivotAtr, latestAtr, secondLastAtr, stopMargin, bidAskMargin, limitBidAskMargin, stopLossTakenOut, filledPrice, filledSide, filledQuantity, priceToBid, bidToStop, stopLimitbid, priceToAsk, askToStop, stopLimitask, lastRecordedStopMargin, lastRecordedBidAskMargin, lastRecordedLimitBidAskMargin
    while True:
        klines = client.klines(symbol="BTCUSDT", interval="1m", limit=500)
        open = []
        high = []
        low = []
        close = []
        for line in klines:
            open.append(float(line[1]))
            high.append(float(line[2]))
            low.append(float(line[3]))
            close.append(float(line[4]))
        myColumns = ["open", "high", "low", "close"]
        df = pd.DataFrame(list(zip(open, high, low, close)),columns=myColumns)
        
        atr(df=df)
        if latestAtr <= 7:
            lastRecordedStopMargin = 65
            lastRecordedBidAskMargin = 8
            lastRecordedLimitBidAskMargin = 10
            stopMargin = 120
            bidAskMargin = 20
            limitBidAskMargin = 20
        if 7 < latestAtr <= 12:
            if lastRecordedStopMargin == None:
                lastRecordedStopMargin = stopMargin
                lastRecordedBidAskMargin = bidAskMargin
                lastRecordedLimitBidAskMargin = limitBidAskMargin
            stopMargin = 65
            bidAskMargin = 8
            limitBidAskMargin = 10
        if 12 < latestAtr <= 19:
            if lastRecordedStopMargin != None:
                stopMargin = lastRecordedStopMargin
                bidAskMargin = lastRecordedBidAskMargin
                limitBidAskMargin = lastRecordedLimitBidAskMargin
            lastRecordedStopMargin = None
            lastRecordedBidAskMargin = None
            lastRecordedLimitBidAskMargin = None
        if 19 < latestAtr <= 25:
            if lastRecordedStopMargin == None:
                lastRecordedStopMargin = stopMargin
                lastRecordedBidAskMargin = bidAskMargin
                lastRecordedLimitBidAskMargin = limitBidAskMargin
            stopMargin = 90
            bidAskMargin = 12
            limitBidAskMargin = 12
        if 25 < latestAtr <= 35:
            lastRecordedStopMargin = 65
            lastRecordedBidAskMargin = 8
            lastRecordedLimitBidAskMargin = 10
            stopMargin = 120
            bidAskMargin = 20
            limitBidAskMargin = 16
        if 35 < latestAtr:
            lastRecordedStopMargin = 65
            lastRecordedBidAskMargin = 8
            lastRecordedLimitBidAskMargin = 10
            stopMargin = 200
            bidAskMargin = 35
            limitBidAskMargin = 43
def vegaDecrease():
    global stopMargin, bidAskMargin, limitBidAskMargin, stopLossTakenOut, filledPrice, filledSide, filledQuantity, priceToBid, bidToStop, stopLimitbid, priceToAsk, askToStop, stopLimitask
    if stopMargin > 65:
        stopMargin -= 15
    if bidAskMargin > 8:
        bidAskMargin -= 2
    if limitBidAskMargin > 10:
        limitBidAskMargin -= 2
def vegaIncrease():
    global stopMargin, bidAskMargin, limitBidAskMargin, stopLossTakenOut, filledPrice, filledSide, filledQuantity, priceToBid, bidToStop, stopLimitbid, priceToAsk, askToStop, stopLimitask
    if stopMargin < 190:
        stopMargin += 45
    if bidAskMargin < 20:
        bidAskMargin += 4
    if limitBidAskMargin < 22:
        limitBidAskMargin += 4
def wsBidAskOpen(ws):
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params":
            [
                "btcusdt@trade",
            ],
        "id": 1
    }

    ws.send(json.dumps(subscribe_message))
    print("opened")
def wsBidAskMessage(ws, message):
    global jsonMessage, lastTradedPrice, previousTradedPrice, cancelBidId, cancelAskId
    jsonMessage = json.loads(message)
    lastTradedPrice = round(float(jsonMessage['p']))    
def wsTradesThread(*args):
    socket = "wss://stream.binance.com:9443/ws"
    ws = websocket.WebSocketApp(socket, on_open=wsBidAskOpen, on_message=wsBidAskMessage)
    ws.run_forever(ping_interval=15, ping_payload=str({'op': 'ping'}))
def wsUserData(ws, message):
    global stopMargin, bidAskMargin, limitBidAskMargin, stopLossTakenOut, filledPrice, filledSide, filledQuantity, priceToBid, bidToStop, stopLimitbid, priceToAsk, askToStop, stopLimitask, timerOn
    jsonMessage = json.loads(message)
    print(jsonMessage)
    if jsonMessage["e"] == "executionReport":
        if jsonMessage["x"] == "TRADE":
            if jsonMessage["X"] == "FILLED":
                if jsonMessage["o"] == "LIMIT":
                    filledPrice = round(float(jsonMessage["L"]))
                    filledSide = jsonMessage["S"]
                    filledQuantity = float(jsonMessage["z"])
                    priceToBid = filledPrice - limitBidAskMargin
                    bidToStop = filledPrice + stopMargin
                    stopLimitbid = bidToStop + 20
                    priceToAsk = filledPrice + limitBidAskMargin
                    askToStop = filledPrice - stopMargin
                    stopLimitask = askToStop - 20
                    if filledSide == "SELL":
                        btcusdtbidParams = {
                        'symbol': 'BTCUSDT',
                        'side': 'BUY',
                        'quantity': filledQuantity,
                        'price': priceToBid,
                        'stopPrice': bidToStop,
                        'stopLimitPrice': stopLimitbid,
                        'stopLimitTimeInForce': 'GTC',
                        'isIsolated': 'TRUE',
                        }
                        #symbol='BTCUSDT', side='BUY', quantity=filledQuantity, price=priceToBid, stopPrice=bidToStop
                        try:
                            oco1 = client.new_margin_oco_order(**btcusdtbidParams)
                        except Exception as e:
                            print(e)
                            oco1 = client.new_margin_oco_order(**btcusdtbidParams)
                            pass
                        #print(oco1)
                    if filledSide == "BUY":
                        btcusdtaskParams = {
                        'symbol': 'BTCUSDT',
                        'side': 'SELL',
                        'quantity': filledQuantity,
                        'price': priceToAsk,
                        'stopPrice': askToStop,
                        'stopLimitPrice': stopLimitask,
                        'stopLimitTimeInForce': 'GTC',
                        'isIsolated': 'TRUE',
                        }
                        #symbol='BTCUSDT', side='BUY', quantity=filledQuantity, price=priceToBid, stopPrice=bidToStop
                        try:
                            oco2 = client.new_margin_oco_order(**btcusdtaskParams)
                            #print(oco2)
                        except Exception as e:
                            print(e)
                            oco2 = client.new_margin_oco_order(**btcusdtaskParams)
                            pass
                if jsonMessage["o"] == "LIMIT_MAKER":
                    threading.Thread(target=vegaDecrease).start()
                if jsonMessage["o"] == "STOP_LOSS_LIMIT":
                    threading.Thread(target=vegaIncrease).start()
def wsUserDataThread(*args):
    socket = f"wss://stream.binance.com:9443/ws/{key}"
    ws = websocket.WebSocketApp(socket, on_message=wsUserData)
    ws.run_forever(ping_interval=15, ping_payload=str({'op': 'ping'}))    
def keepAlive(*args):
    time.sleep(1800)
    client.renew_isolated_margin_listen_key()
#def atr(*args):
#    global stopMargin, bidAskMargin
#    try:
#        url = f"https://www.alphavantage.co/query?function=ATR&symbol=BTCUSD&interval=1min&time_period=4&apikey={d.alphaVantage2}"
#        r = requests.get(url)
#        data = r.json()
#        lastRefresh = data['Meta Data']['3: Last Refreshed']
#        atr = float(data['Technical Analysis: ATR'][lastRefresh[:-3]]['ATR'])
#        if atr >= 40:
#            stopMargin = 100
#            bidAskMargin = 8
#        else:
#            stopMargin = 55
#            bidAskMargin = 8
#    except Exception as e:
#        print(e)
#        pass
#    time.sleep(60)

        

    print(atr>50)
def checkForNakedPositions():
    while True:
        accountInfo = client.isolated_margin_account(symbols="BTCUSDT")
        for asset in accountInfo["assets"]:
            if asset['baseAsset']["asset"] == "BTC":
                freeBtc = float(asset["baseAsset"]["free"])
                if freeBtc > 0.23:
                    amountToMarketSell = round(freeBtc - 0.2, 3)
                    btcusdtMarketSell = {
                        'symbol': 'BTCUSDT',
                        'side': 'SELL',
                        'type': 'MARKET',
                        'quantity': amountToMarketSell,
                        'isIsolated': 'TRUE',
                    }
                    try:
                        response6 = client.new_margin_order(**btcusdtMarketSell)
                    except Exception as e:
                        print(e)
                        pass
            if asset['quoteAsset']["asset"] == "USDT":
                freeUsdt = float(asset["quoteAsset"]["free"])
                if freeUsdt > 4500:
                    excessAmount = round(freeUsdt - 4000)
                    amountToMarketBuy = round(excessAmount / lastTradedPrice, 3)
                    btcusdtMarketBuy = {
                        'symbol': 'BTCUSDT',
                        'side': 'BUY',
                        'type': 'MARKET',
                        'quantity': amountToMarketBuy,
                        'isIsolated': 'TRUE',
                    }
                    try:
                        response7 = client.new_margin_order(**btcusdtMarketBuy)
                    except Exception as e:
                        print(e)
                        pass
        time.sleep(15)

_thread.start_new_thread(wsTradesThread, ())
_thread.start_new_thread(wsUserDataThread, ())
_thread.start_new_thread(keepAlive, ())
_thread.start_new_thread(checkForNakedPositions, ())
_thread.start_new_thread(getAtr, ())


def bid():
    global priceToBid, priceToAsk, amountToBidAskBtc
    btcusdtbidParams = {
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'type': 'LIMIT',
            'timeInForce': 'FOK',
            'quantity': amountToBidAskBtc,
            'price': priceToBid,
            'isIsolated': 'TRUE',
        }
    try:
        response1 = client.new_margin_order(**btcusdtbidParams)
        #cancelBidId = response1["orderId"]
        #print(response1)
    except Exception as e:
        print(e)
        pass
def ask():
    global priceToBid, priceToAsk, amountToBidAskBtc
    btcusdtaskParams = {
            'symbol': 'BTCUSDT',
            'side': 'SELL',
            'type': 'LIMIT',
            'timeInForce': 'FOK',
            'quantity': amountToBidAskBtc,
            'price': priceToAsk,
            'isIsolated': 'TRUE',
        }
    try:
        response2 = client.new_margin_order(**btcusdtaskParams)
        #cancelAskId = response2["orderId"]
        #print(response2)
    except Exception as e:
        print(e)
        pass
            
while True:
    try:
        ##if lastTradedPrice != previousTradedPrice:
        #previousTradedPrice = lastTradedPrice
        priceToBid = lastTradedPrice - bidAskMargin
        priceToAsk = lastTradedPrice + bidAskMargin
        time.sleep(0.4)
        threading.Thread(target=bid).start()
        threading.Thread(target=ask).start()
        print(stopMargin, bidAskMargin, limitBidAskMargin)       
    except Exception as e:
            print(e)
            pass
    