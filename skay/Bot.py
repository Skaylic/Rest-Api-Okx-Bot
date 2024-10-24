import os
from time import sleep, strftime
import logging
from skay.Okx import Okx
from skay.DataBase import DataBase
from skay.Models import Orders


logger = logging.getLogger('SkayBot')
db = DataBase().set_db()


class Bot(Okx):

    def __init__(self):
        super(Bot, self).__init__()
        self.bot_mane = os.getenv('BOT_MANE')
        self.min = float(os.getenv("MIN"))
        self.max = float(os.getenv("MAX"))
        self.percent = float(os.getenv("PERCENT"))
        self.grid = []
        self.grid_px = 0.0
        self.to_buy = 0
        self.position_px = 0.0

    def check(self):
        if not self.instruments:
            self.getInstruments()
        self.getKline()
        self.grid_positions()

    def grid_positions(self):
        x = self.min
        while x <= self.max:
            x += (x * self.percent / 100)
            self.grid.append(x)

    def array_grid(self, a, val):
        self.grid_px = round(min([x for x in a if x > val] or [None]), 9)
        return self

    def is_position(self):
        mrx = float(self.kline['close'] - (self.kline['close'] * self.percent / 100))
        _ord = (db.query(Orders).filter(Orders.side == 'Buy', Orders.px <= mrx, Orders.is_active == True)
                .order_by(Orders.px).first())
        if _ord:
            return _ord
        _ord = db.query(Orders).filter(Orders.side == 'Buy', Orders.grid_px == self.grid_px,
                                       Orders.is_active == True).first()
        if _ord:
            return None
        else:
            return False

    def check_qty(self):
        if self.qty / self.kline['close'] < self.min_qty:
            self.qty = self.min_qty * self.kline['close']
        return self

    def save_order(self, order, active=True):
        _ord = Orders(
            ordId=order.get('orderId'),
            cTime=strftime('%Y%m%d%H%M%S'),
            sz=order.get('cumExecQty'),
            px=order.get('avgPrice'),
            grid_px=self.grid_px,
            profit=order.get('profit'),
            fee=order.get('cumExecFee'),
            feeCcy=order.get('feeCcy'),
            side=order.get('side'),
            instId=order.get('instId'),
            is_active=active,
            instType=order.get('instType'),
            state=order.get('state'),
            tgtCcy=order.get('tgtCcy'),
            tag=self.bot_mane,
        )
        db.add(_ord)
        db.commit()
        logger.info(_ord)
        return _ord

    def start(self):
        logger.info(f"The {os.getenv('BOT_NAME')} is started!")
        while True:
            self.check()
            if len(self.kline) > 0:
                self.array_grid(self.grid, self.kline['close'])
                pos = self.is_position()
                if self.kline['close'] > self.kline['open'] and self.to_buy == 0:
                    self.position_px = self.grid_px
                    self.to_buy = 1
                    logger.info(f"{strftime('%d.%m.%Y %H:%M:%S')}: Order: {pos}, MarkPx: {self.kline['close']}, GridPx: {self.grid_px}")
                elif self.kline['close'] < self.kline['open'] and self.to_buy == 1:
                    self.to_buy = 0
                    logger.info(f"{strftime('%d.%m.%Y %H:%M:%S')}: Order: {pos}, MarkPx: {self.kline['close']}, GridPx: {self.grid_px}")
                if pos and self.balance[self.baseCcy] > pos.sz and self.order is None:
                    self.sendTicker(side='sell', qty=pos.sz - round(pos.fee, 2))
                elif pos and self.balance[self.baseCcy] < pos.sz and self.order is None:
                    self.sendTicker(side='buy', tag=strftime('%Y%m%d%H%M%S'))
                elif (pos is False and self.to_buy == 1 and self.kline['close'] > self.position_px and
                      self.balance[self.quoteCcy] > self.qty and self.order is None):
                    self.position_px = self.grid_px
                    self.sendTicker(side='buy')
                if self.order and self.order['orderId'] == self.orderId:
                    if self.order['tag'] == self.bot_mane and self.order['side'] == "sell":
                        self.save_order(self.order, active=False)
                        self.orderId = None
                        self.order = None
                        pos.cTime = strftime('%Y%m%d%H%M%S')
                        pos.is_active = False
                        db.commit()
                    elif self.order['tag'] == self.bot_mane and self.order['side'] == "buy":
                        self.save_order(self.order, active=True)
                        self.orderId = None
                        self.order = None
                    else:
                        self.save_order(self.order, active=False)
                        self.orderId = None
                        self.order = None
            sleep(10)
