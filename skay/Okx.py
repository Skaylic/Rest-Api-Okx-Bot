import os
import logging

from okx.PublicData import PublicAPI
from okx.MarketData import MarketAPI
from okx.Account import AccountAPI
from okx.Trade import TradeAPI

logger = logging.getLogger('SkayBot')


class Okx:

    def __init__(self):
        logger.info(f"The {os.getenv('BOT_NAME')} loaded!")
        self.params = dict(
            domain='https://www.okx.com',
            api_key=os.environ.get('API_KEY', '1'),
            api_secret_key=os.environ.get('SECRET_KEY', '1'),
            passphrase=os.environ.get('PASSPHRASE', '1'),
            flag=os.getenv('IS_DEMO', '1'),
            debug=False
        )
        self.symbol = os.getenv('SYMBOL')
        self.interval = os.getenv('INTERVAL')
        self.qty = float(os.getenv('QTY'))
        self.instruments = None
        self.min_qty = 0.0
        self.baseCcy = ''
        self.quoteCcy = ''
        self.status = ''
        self.kline = {}
        self.balance = {}
        self.orderId = False
        self.order = False

    def getResponse(self, data):
        if data['code'] == '0':
            return data['data'][0]
        else:
            logging.debug(data)

    def getInstruments(self):
        res = PublicAPI(**self.params).get_instruments(instType="SPOT", instId=self.symbol)
        data = self.getResponse(res)
        self.instruments = data
        self.min_qty = float(data['minSz'])
        self.baseCcy = data['baseCcy']
        self.quoteCcy = data['quoteCcy']
        self.status = data['state']
        return self

    def getKline(self):
        res = MarketAPI(**self.params).get_candlesticks(instId=self.symbol, bar=self.interval, limit=1)
        data = self.getResponse(res)
        self.kline = {"open": float(data[1]), "close": float(data[4])}
        return self

    def getBalance(self):
        res = AccountAPI(**self.params).get_account_balance(ccy=f"{self.quoteCcy},{self.baseCcy}")
        data = self.getResponse(res)['details']
        for i in data:
            if i['ccy'] == self.baseCcy:
                self.balance[self.baseCcy] = float(i['cashBal'])
            elif i['ccy'] == self.quoteCcy:
                self.balance[self.quoteCcy] = float(i['cashBal'])
        return self

    def sendTicker(self, qty: float, side="buy", tag='Bot3'):
        res = TradeAPI(**self.params).place_order(
            instId=self.symbol,
            tdMode="cash",
            ordType="market",
            tgtCcy="quote_ccy",
            side=side,
            sz=qty,
            px=self.kline['close'],
            tag=tag
        )
        data = self.getResponse(res)
        self.orderId = data['ordId']
        return self

    def getOrderDetails(self):
        res = TradeAPI(**self.params).get_order(instId=self.symbol, ordId=self.orderId)
        data = self.getResponse(res)
        self.order = data
        return self
