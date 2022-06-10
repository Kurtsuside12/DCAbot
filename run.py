#importing libraries
from audioop import avg
from distutils.command.config import config
import ccxt
import schedule
import time
import threading
from config import *
from decimal import *
from telegram import Update, ForceReply, message
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
counter = 0
currentprice = None
orderIdAvgBuyPrice = {}
avgBuyPrice = None
perc = None
som = 0
start_wallet = None
counter = 1
totalquantity = 0
startquantity = quantity
startdcabound = dcabound
startsellbound = sellbound
walletEmpty = False

exchange_class = getattr(ccxt, exchange)
exchange = exchange_class({
    'apiKey': api_key,
    'secret': api_key_secret,
    'enableRateLimit': True,
           # 'headers': {
      #  'FTX-SUBACCOUNT': f'{sub_account}'
    }
)

def createOrder():
    global perc
    global som
    global avgBuyPrice
    global startquantity
    global startdcabound
    global startsellbound
    global sellbound
    global walletEmpty
    global dcabound
    global quantity
    global totalquantity
    global counter
    global start_wallet

    if len(orderIdAvgBuyPrice) > counter:
        if (sellbound / 1.1**len(orderIdAvgBuyPrice)) > 0.12:
            sellbound = startsellbound
            sellbound = sellbound / 1.1**len(orderIdAvgBuyPrice)
        else: pass
        if len(orderIdAvgBuyPrice) > counter:
            dcabound = startdcabound
            dcabound = dcabound * 1.1**len(orderIdAvgBuyPrice)
        counter +=1


    print(f"{len(orderIdAvgBuyPrice)}, {counter}")
    getPercDiff()
    

    if len(orderIdAvgBuyPrice) == 0:
        print("First buy order...")
        start_wallet = getBalance()
        neworder = exchange.createOrder(symbol,"market","buy",quantity)
        time.sleep(2)
        getAvgPrice(neworder['info']['id'])
        sendMessage(f"Entering first trade on pair {symbol}, start quantity is {quantity}")
    elif perc > sellbound:
        neworder = exchange.createOrder(symbol,"market","sell",totalquantity)
        end_wallet = getBalance()
        sendMessage(f"Sold {totalquantity} for pair {symbol}, profit is {Decimal(end_wallet) - Decimal(start_wallet)}")
        orderIdAvgBuyPrice.clear()
        totalquantity = 0
        som = 0
        counter = 1
        dcabound = startdcabound
        sellbound = startsellbound
        quantity = startquantity
        walletEmpty = False if walletEmpty == True else False
    elif perc < dcabound:
        try:
            quantity = totalquantity
            neworder = exchange.createOrder(symbol,"market","buy",quantity)
            sendMessage(f"DCA bought {quantity} for pair {symbol}\nWB:{round(getBalance())}\nABP:{round(avgBuyPrice)}\nIm trying to save your ass bitch!!!")
            time.sleep(2)
            getAvgPrice(neworder['info']['id'])
        except Exception as e: 
            print(e)
            print("Probably wallet is empty....")
            if walletEmpty == False:
                sendMessage("Wallet is empty, please enable margin or deposit more funds")
                walletEmpty = True
            
            

    else: 
        print(f"Nothing to do.. perc is {perc}, sellbound = {sellbound}, dcabound = {dcabound}")
        

        
    
        
            


def getAvgPrice(orderid):
    global som
    global avgBuyPrice
    global totalquantity
    order = exchange.fetchOrder(orderid)
    orderIdAvgBuyPrice[orderid] = float(order['info']['avgFillPrice'])
    totalquantity += float(order['info']['filledSize'])

    currentBoughtQuantity = order['info']['filledSize']
    avgBuyPrice = order['info']['avgFillPrice']

    print(f"avgbuyprice = {avgBuyPrice}, currentboughtq={currentBoughtQuantity}")

    for x in orderIdAvgBuyPrice.values():
        print(x)
    som += Decimal(currentBoughtQuantity) * Decimal(avgBuyPrice) 
    avgBuyPrice = Decimal(som/Decimal(totalquantity))
    print(f"De som is  {som}")
    print(f"De gemiddelde prijs is {avgBuyPrice}")
    
    
    time.sleep(2)
    
    

def getPercDiff():
    global currentprice
    global avgBuyPrice
    global perc
    try:
        getCurrentPrice()
        print(f"Currentprice is {currentprice}, avgBuyPrice is {avgBuyPrice}")
        perc = ((currentprice - avgBuyPrice)/((currentprice+avgBuyPrice)/2))*100
        print(perc)
    except Exception as e: print(e)

slower = len(orderIdAvgBuyPrice)+1


def job():
    global totalquantity
    global slower
    slower = len(orderIdAvgBuyPrice)+1
    try:
        print(orderIdAvgBuyPrice)
        createOrder()
        print(f"total is {totalquantity}")
    except Exception as e: print(e)


def getCurrentPrice():
    global currentprice
    ticker = exchange.fetch_ticker(symbol)
    currentprice = Decimal((float(ticker['ask']) + float(ticker['bid'])) / 2)
   
    
def getBalance():
    try:
        balance = exchange.fetchBalance()['USD']['free']
        print(str(balance))
        return str(balance)
    except Exception as e: print(e)

def sendMessage(tekst) -> None:
    try:
        updater = Updater(token=tg_token, use_context=True)
        updater.bot.send_message(chat_id=tg_chat_id,text=tekst)
    except Exception as e: print(e)


def getInfo(update: Update, context: CallbackContext) -> None:
    global perc
    global dcabound
    global sellbound
    sendMessage(f"Percentage difference is {round(perc,2)}, current sellbound is {round(sellbound,2)}, current dca bound is {round(dcabound,2)}")
    



def main() -> None:
    """Start the bot."""
    updater = Updater(token=tg_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("info", getInfo))

    updater.start_polling()
    updater.bot.send_message(chat_id=tg_chat_id,text=f'Telegram bot started succesfully!!')

        
     







try:
    threading.Thread(target=job()).start() #start bot thread
    if tg_enabled == True:
        threading.Thread(target=main()).start() #start TG bot thread
except Exception as e: print(e)








schedule.every(slower*1).seconds.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)