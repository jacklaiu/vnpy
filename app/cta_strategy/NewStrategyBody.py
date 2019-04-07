import jqdatasdk
import talib
import numpy as np
import time
from pandas import DataFrame
from functools import reduce
import vnpy.app.cta_strategy.Util as Util
from vnpy.trader.object import TradeData
from vnpy.app.cta_strategy.SmtpClient import SmtpClient as smtp

class StrategyBody():

    def __init__(self, security=None, frequency='28m', onlyDuo=0, onlyKon=0, trade_position=1, trader=None, enableSendMessage=False,
                 adx_edge=30, real_open_rate=0.2, cond_er=0.4, cond_before_er=1.2, cond_after_er=0.8, fast_ema=6, slow_ema=23):
        self.jqAcc = '13268108673'
        self.jqPwd = 'king20110713'
        jqdatasdk.auth(self.jqAcc, self.jqPwd)

        self.smtp = smtp(enable=enableSendMessage)
        self.enableSendMessage = enableSendMessage

        self.markTreses = False
        self.cond_er = cond_er
        self.cond_before_er = cond_before_er
        self.cond_after_er = cond_after_er
        self.adx_timeperiod = 4
        self.real_open_rate = real_open_rate
        self.adx_edge = adx_edge
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema

        # in loop mess
        self.df = None
        self.position = 0
        self.force_waiting_count = 0
        self.open = 0
        self.clearRates = []
        self.open_after_next_change = False
        self.real_open = 0
        self.nowTimeString = None
        self.closes = []
        self.price = 0
        self.ADXs = []
        self.adx = 0
        self.status = 'STILL'
        self.pricePosi = 0
        self.cfn_count = 0
        self.pricePosis = None
        self.lastaccesstimestamp = None
        self.lastrefreshYmdHms = None
        self.tick = None
        self.lastTick = None

        self.security = security
        self.frequency = frequency
        self.onlyDuo = onlyDuo
        self.onlyKon = onlyKon
        self.trade_position = trade_position
        self.trader = trader

        self.runningStock = False
        self.real_open_rate_below = 0
        if Util.isStock(security=self.security) is True:
            self.cond_er = 2
            self.cond_before_er = 4
            self.cond_after_er = 3
            self.real_open_rate = 2
            self.real_open_rate_below = 8
            self.onlyDuo = 1
            self.onlyKon = 0
            self.frequency = '17m'
            self.runningStock = True
            self.security = Util.acJQ_StockName(security)
            self.write_log(words='Stock-------------------------------------------Loading...')
        else:
            self.write_log(words='Future-------------------------------------------Loading...')

    def write_log(self, words=None):
        if self.nowTimeString is None:
            nts = 'YYYY-MM-DD HH:mm:ss'
        else:
            nts = self.nowTimeString
        words = "[" + nts + " - " + self.security + ']：' + words
        print(words)
        Util.log(words)
        if self.trader is not None:
            self.trader.write_log(words)
        if self.enableSendMessage is True:
            try:
                if "Still Holding" in words and self.runningStock is True:
                    return
                self.smtp.sendMail(subject=words, content=words, receivers='jacklaiu@163.com')
            except:
                pass

    def getPricePosiArray(self):
        indexList = self.df[self.df.EMA60 == self.df.EMA60].index.tolist()
        pricePositions = []
        for index in indexList:
            emafast = self.df.loc[index, 'EMAF']
            emas = sorted(
                # [ema5, self.df.loc[index, 'EMA10'], self.df.loc[index, 'EMA20'], self.df.loc[index, 'EMA40'], self.df.loc[index, 'EMA60']],
                [emafast, self.df.loc[index, 'EMAS']],
                reverse=True)
            pricePosi = 0
            for ema in emas:
                if ema == emafast:
                    break
                pricePosi = pricePosi + 1
            pricePositions.append(pricePosi)
        return pricePositions

    def isChangeTo(self):
        pps = self.pricePosis
        nowPricePosi = pps[-1]
        prePricePosi = pps[-2]
        if nowPricePosi != prePricePosi and nowPricePosi == 0:
            return "UP"
        elif nowPricePosi != prePricePosi and nowPricePosi == 1:
            return "DOWN"
        else:
            return "STILL"

    def isChangeToDOWN(self):
        pps = self.pricePosis
        nowPricePosi = pps[-1]
        prePricePosi = pps[-2]
        if nowPricePosi != prePricePosi and nowPricePosi == 1:
            return True
        else:
            return False

    def changeFromNowCount(self):
        pps = self.pricePosis
        pricePositions = pps[-200:]
        pre = None
        i = pricePositions.__len__() - 1
        count = 0
        while i > 0:
            pricePosition = pricePositions[i]
            if pre is None:
                pre = pricePosition
            elif pre is not None:
                if pre != pricePosition:
                    break
            count = count + 1
            i = i - 1
        return count

    def getOpen2CloseRates(self):
        opens = [float(x) for x in self.df['open']]
        closes = [float(x) for x in self.df['close']]
        arr = []
        i = 0
        for open in opens:
            close = closes[i]
            rate = Util.getRate(open, close)
            i = i + 1
            arr.append(rate)
        return arr

    def getNearMaxClosePrice(self, preCount=0):
        pricePositions = self.pricePosis
        indexList = self.df[self.df.EMA60 == self.df.EMA60].index.tolist()
        if preCount > 0:
            pricePositions = pricePositions[0:-preCount - 1]
            indexList = indexList[0:-preCount - 1]
        closes = []
        for index in indexList:
            closes.append(self.df.loc[index, 'close'])
        i = pricePositions.__len__() - 1
        nowPricePosition = pricePositions[-1]
        while (i - 1) > 0:
            pp = pricePositions[i - 1]
            if pp == nowPricePosition:
                i = i - 1
            else:
                break
        closes = closes[i:]
        if nowPricePosition == 0:
            maxClose = max(closes)
            return maxClose
        return None

    def getNearMinClosePrice(self, preCount=0):
        pricePositions = self.pricePosis
        indexList = self.df[self.df.EMA60 == self.df.EMA60].index.tolist()
        if preCount > 0:
            pricePositions = pricePositions[0:-preCount - 1]
            indexList = indexList[0:-preCount - 1]
        closes = []
        for index in indexList:
            closes.append(self.df.loc[index, 'close'])
        i = pricePositions.__len__() - 1
        nowPricePosition = pricePositions[-1]
        while (i - 1) > 0:
            pp = pricePositions[i - 1]
            if pp == nowPricePosition:
                i = i - 1
            else:
                break
        closes = closes[i:]
        if nowPricePosition == 0:
            pass
        else:
            return min(closes)
        return None

    def getNowEarningRate(self, preCount=0):
        pricePositions = self.pricePosis
        indexList = self.df[self.df.EMA60 == self.df.EMA60].index.tolist()
        if preCount > 0:
            pricePositions = pricePositions[0:-preCount - 1]
            indexList = indexList[0:-preCount - 1]
        closes = []
        for index in indexList:
            closes.append(self.df.loc[index, 'close'])
        i = pricePositions.__len__() - 1
        nowPricePosition = pricePositions[-1]
        while (i - 1) > 0:
            pp = pricePositions[i - 1]
            if pp == nowPricePosition:
                i = i - 1
            else:
                break
        closes = closes[i:]
        isDouing = self.getNearMaxClosePrice() is not None
        startPrice = closes[0]
        nowPrice = closes[-1]
        if isDouing is True:
            return Util.getRate(startPrice, nowPrice)
        else:
            return Util.getRate(nowPrice, startPrice)

    def getDangerRate(self, preCount=0):
        indexList = self.df[self.df.EMA60 == self.df.EMA60].index.tolist()
        if preCount > 0:
            indexList = indexList[0:-preCount - 1]
        nowPrice = self.df.loc[indexList[-1], 'close']
        maxClosePrice = self.getNearMaxClosePrice(preCount)
        minClosePrice = self.getNearMinClosePrice(preCount)
        if maxClosePrice is not None:
            rate = Util.getRate(fromPrice=maxClosePrice, toPrice=nowPrice)
        else:
            rate = Util.getRate(fromPrice=nowPrice, toPrice=minClosePrice)
        return rate

    def getAdvancedData(self, nowTimeString=None):
        newRow = None
        newIndex = None
        if self.df is None:
            try:
                self.df = jqdatasdk.get_price(
                    security=self.security,
                    count=500,
                    end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
                    frequency=self.frequency,
                    fields=['close', 'open', 'high', 'low']
                )
            except:
                self.smtp.sendMail(subject=self.security + ': getAdvancedData初始化数据错误！', content='')
        else:
            try:
                newDf = jqdatasdk.get_price(
                    security=self.security,
                    count=1,
                    end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
                    frequency=self.frequency,
                    fields=['close', 'open', 'high', 'low']
                )
                newIndex = newDf.index.tolist()[0]
                newRow = newDf.loc[newIndex]
            except:
                try :
                    time.sleep(5)
                    jqdatasdk.auth(self.jqAcc, self.jqPwd)
                    newDf = jqdatasdk.get_price(
                        security=self.security,
                        count=1,
                        end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
                        frequency=self.frequency,
                        fields=['close', 'open', 'high', 'low']
                    )
                    newIndex = newDf.index.tolist()[0]
                    newRow = newDf.loc[newIndex]
                except:
                    data = {
                        'open': [self.lastTick.last_price],
                        'close': [self.tick.last_price],
                        'high': [self.tick.last_price],
                        'low': [self.lastTick.last_price]
                    }
                    newDf = DataFrame(data=data, index=[Util.string2Datetime(nowTimeString[0:nowTimeString.rindex(':') + 1] + '30')])
                    self.smtp.sendMail(subject=self.security + ': 注意：从tick中拿了一帧数据', content=str(data))
                    newIndex = newDf.index.tolist()[0]
                    newRow = newDf.loc[newIndex]

        if newRow is not None:
            self.df.loc[newIndex] = newRow
        close = [float(x) for x in self.df['close']]
        high = [float(x) for x in self.df['high']]
        low = [float(x) for x in self.df['low']]
        self.df['EMA5'] = talib.EMA(np.array(close), timeperiod=5)
        self.df['EMA10'] = talib.EMA(np.array(close), timeperiod=10)
        self.df['EMA20'] = talib.EMA(np.array(close), timeperiod=20)
        self.df['EMA40'] = talib.EMA(np.array(close), timeperiod=40)
        self.df['EMA60'] = talib.EMA(np.array(close), timeperiod=60)
        self.df['EMAF'] = talib.EMA(np.array(close), timeperiod=self.fast_ema)
        self.df['EMAS'] = talib.EMA(np.array(close), timeperiod=self.slow_ema)
        self.df['ADX'] = talib.ADX(np.array(high), np.array(low), np.array(close), timeperiod=self.adx_timeperiod)
        self.df.drop([self.df.index.tolist()[0]], inplace=True)

    def setPosition(self, position):
        self.position = position
    def setOpen(self, open):
        self.open = open
    def setReal_Open(self, real_open):
        self.real_open = real_open

    def handleSTILL(self, earningRate, dangerRate):
        # 趋势持续
        if self.status != 'STILL':
            return
        # 止损止盈平仓
        if self.position != 0 and (
                (earningRate <= self.cond_er and dangerRate < -self.cond_before_er) or
                (earningRate > self.cond_er and dangerRate < -self.cond_after_er)
        ):
            if self.real_open != 0 and self.real_open is not None:
                self.clearRates.append(round((1 + earningRate / 100), 4))
            else:
                self.clearRates.append(1)

            self.write_log(words='止损止盈平仓 ' + str(earningRate) + ' sum_rate:' + str(
                reduce(lambda x, y: x * y, self.clearRates)))

            if self.real_open > 0 and self.trader is not None:
                if self.position > 0:
                    self.trader.sell(float(self.tick.limit_down * 1.01), self.trade_position)
                    self.write_log(words='止损止盈平多仓')
                else:
                    self.trader.cover(float(self.tick.limit_up * 0.99), self.trade_position)
                    self.write_log(words='止损止盈平空仓')

            self.setPosition(position=0)
            self.setOpen(open=0)
            self.setReal_Open(real_open=0)
            self.open_after_next_change = False
        else:
            # 高位回落平仓后再此处等待，或瞬间变化时ADX条件不符合正在等待机会
            if self.position == 0:
                if self.open_after_next_change is False:
                    # 等到adx条件符合，开空仓
                    if self.pricePosi == 1 and (self.adx > self.adx_edge):
                        self.write_log(
                            words='平仓后再此处等待 adx条件符合，开空仓 Down Position' + ' adx:' + str(
                                self.adx))
                        # self.position = -1
                        self.setPosition(position=-1)
                        # self.open = self.price
                        self.setOpen(open=self.price)
                        dangerRate = 0
                    # 等到adx条件符合，开多仓
                    elif self.pricePosi == 0 and (self.adx > self.adx_edge):
                        self.write_log(
                            words='平仓后再此处等待 adx条件符合，开多仓 Up Position' + ' adx:' + str(
                                self.adx))
                        # self.position = 1
                        self.setPosition(position=1)
                        # self.open = self.price
                        self.setOpen(open=self.price)
                        dangerRate = 0
                    else:
                        self.write_log(
                            words="WAITING..." + ' close: ' + str(self.price))
                else:
                    self.write_log("WAITING..." + ' adx: ' + str(self.adx))
            # 持有多仓
            if self.position > 0:
                self.write_log(
                    words="Still Holding DUO..." + " dr:" + str(
                        dangerRate) + ' er:' + str(
                        earningRate) + ' adx:' + str(self.adx))

                if self.runningStock is True and earningRate < self.real_open_rate_below and earningRate > self.real_open_rate and self.real_open == 0 and self.onlyKon == 0:
                    self.setReal_Open(real_open=self.price)
                    self.write_log(words='正式做多：' + str(self.price))
                    self.write_log(words='正式做多：' + str(self.price))
                    self.write_log(words='正式做多：' + str(self.price))
                    if self.trader is not None:
                        self.trader.buy(float(self.tick.limit_up * 0.99), self.trade_position)
                        self.write_log(words='正式做多，交易完成')
                elif self.runningStock is False and earningRate > self.real_open_rate and self.real_open == 0 and self.onlyKon == 0:
                    self.setReal_Open(real_open=self.price)
                    self.write_log(words='正式做多：' + str(self.price))
                    self.write_log(words='正式做多：' + str(self.price))
                    self.write_log(words='正式做多：' + str(self.price))
                    if self.trader is not None:
                        self.trader.buy(float(self.tick.limit_up * 0.99), self.trade_position)
                        self.write_log(words='正式做多，交易完成')

            # 持有空仓
            if self.position < 0:
                self.write_log(
                    words="Still Holding KON..." + " dr:" + str(
                        dangerRate) + ' er:' + str(
                        earningRate) + ' adx:' + str(self.adx))
                if earningRate > self.real_open_rate and self.real_open == 0 and self.onlyDuo == 0:
                    self.setReal_Open(real_open=self.price)
                    self.write_log(words='正式做空：' + str(self.price))
                    self.write_log(words='正式做空：' + str(self.price))
                    self.write_log(words='正式做空：' + str(self.price))
                    if self.trader is not None:
                        self.trader.short(float(self.tick.limit_down * 1.01), self.trade_position)
                        self.write_log(words='正式做空，交易完成')

    def handleDOWN(self, earningRate, dangerRate):
        if self.status != "DOWN":
            return
        # 前个趋势还在持仓，而现在趋势反转，应该反手做空
        if self.position != 0:
            if self.real_open != 0:
                self.clearRates.append(round((1 + earningRate / 100), 4))
            else:
                self.clearRates.append(1)

            self.write_log(
                words='clear Position 转趋势平多仓 ------> ' + str(
                    earningRate) + ' r:' + str(
                    reduce(lambda x, y: x * y, self.clearRates)) + '!!! ----- !!!')

            if self.real_open > 0 and self.trader is not None:
                self.trader.sell(float(self.tick.limit_down * 1.01), self.trade_position)
                self.write_log(words='转趋势平多仓')

            if self.adx < self.adx_edge:
                force_waiting_count = 5

            self.setOpen(open=0)
            self.setReal_Open(real_open=0)
            self.setPosition(position=0)
        # -------------------------------------------------------------------
        # 变为Down瞬间，adx也符合要求，开空仓
        elif (self.adx > self.adx_edge and self.cfn_count < 10) and self.position == 0:
            self.write_log(
                words='变为Down瞬间，adx也符合要求，开空仓 Down Position' + ' adx:' + str(
                    self.adx))

            # self.position = -1
            self.setPosition(position=-1)
            # self.open = self.price
            self.setOpen(open=self.price)

        self.open_after_next_change = False

    def handleUP(self, earningRate, dangerRate):
        if self.status != "UP":
            return
        # 前个趋势还在持仓，而现在趋势反转，应该反手做多
        if self.position != 0:
            # self.position = 0
            self.setPosition(position=0)
            if self.real_open != 0:
                self.clearRates.append(round((1 + earningRate / 100), 4))
            else:
                self.clearRates.append(1)

            self.write_log(
                words='clear Position 转趋势平空仓 ------> ' + str(
                    earningRate) + ' r:' + str(
                    reduce(lambda x, y: x * y, self.clearRates)) + '!!! ----- !!!')

            if self.real_open > 0 and self.trader is not None:
                self.trader.cover(float(self.tick.limit_up * 0.99), self.trade_position)
                self.write_log(words='转趋势平空仓')

            if self.adx < self.adx_edge:
                force_waiting_count = 5

            self.setOpen(open=0)
            self.setReal_Open(real_open=0)
            self.setPosition(position=0)

        # -------------------------------------------------------------------
        # 变为Up瞬间，adx也符合要求，开多仓
        elif (self.adx > self.adx_edge and self.cfn_count < 10) and self.position == 0:
            self.write_log(
                words='变为Up瞬间，adx也符合要求，开多仓 Up Position' + ' adx:' + str(
                    self.adx))
            # self.position = 1
            self.setPosition(position=1)
            # self.open = self.price
            self.setOpen(open=self.price)
        self.open_after_next_change = False

    def isForceWaitting(self):
        if self.force_waiting_count > 0:
            self.force_waiting_count = self.force_waiting_count - 1
            self.write_log(words="ForceWaiting...")
            return True

    def getDynaticEarningRate(self):
        earningRate = 0
        if self.open is not None and self.open != 0:
            if self.pricePosis[-2] == 0:
                earningRate = Util.getRate(self.open, self.price)
            else:
                earningRate = Util.getRate(self.price, self.open)
        if self.real_open is not None and self.real_open != 0:
            if self.pricePosis[-2] == 0:
                earningRate = Util.getRate(self.real_open, self.price)
            else:
                earningRate = Util.getRate(self.price, self.real_open)
        return earningRate

    def refresh(self, nowTimeString):
        # （1）刷新dataframe
        self.getAdvancedData(nowTimeString=nowTimeString)
        # （1）计算pricePosi
        self.pricePosis = self.getPricePosiArray()
        self.pricePosi = self.pricePosis[-1]
        # （1）更新最新价格
        self.closes = [float(x) for x in self.df['close']]
        self.price = self.closes[-1]
        # （1）检查是否需要强制等待
        if self.isForceWaitting() is True:
            return
        # （1）算出现在状态，STILL/DOWN/UP
        self.status = self.isChangeTo()
        # （1）计算Adx
        self.ADXs = [float(x) for x in self.df[self.df.ADX == self.df.ADX]['ADX']][-200:]
        self.adx = self.ADXs[-1]
        # （1）计算cfn_count
        self.cfn_count = self.changeFromNowCount()

        self.lastrefreshYmdHms = nowTimeString

    def markLastTick(self, nowTimeString=None, tick:TradeData=None):
        if tick is None:
            return
        self.lastTick = tick

    def markTick(self, nowTimeString=None, tick:TradeData=None):
        if tick is None:
            return
        self.tick = tick

    def loop(self, nowTimeString=None):
        if nowTimeString > '2017-02-07 21:00:35':
            pass
        #（1）刷新数据
        self.refresh(nowTimeString)
        #（1）dangerRate的容忍度应该由earningRate决定，两个是正相关。能容忍利润做筹码，厌恶本金损失
        dangerRate = self.getDangerRate()
        #（1）earningRate，有real_open用real_open算，优先计算real_open
        earningRate = self.getDynaticEarningRate()

        self.handleSTILL(earningRate=earningRate, dangerRate=dangerRate)

        self.handleDOWN(earningRate=earningRate, dangerRate=dangerRate)

        self.handleUP(earningRate=earningRate, dangerRate=dangerRate)

        if self.clearRates.__len__() > 500:
            self.clearRates.pop(0)

    def isTradeTime(self, nowTimeString=None):
        hm = nowTimeString[-8:-3]
        if self.runningStock is True:
            if '00:00' <= hm < '09:30' or '11:30' <= hm < '13:00' or '15:00' <= hm <= '23:59' or Util.isOpen(nowTimeString) is False:
                return False
            else:
                return True
        else:
            if '00:00' <= hm < '09:00' or '10:15' <= hm < '10:30' or '11:30' <= hm < '13:30' or '15:00' <= hm < '21:00' or '23:00' <= hm <= '23:59':
                return False
            else:
                return True

    def handleOneTick(self, nowTimeString=None, tick=None):
        self.nowTimeString = nowTimeString
        if self.isTradeTime(nowTimeString=nowTimeString) is False:
            return
        ts = Util.string2timestamp(str(nowTimeString))
        if self.lastaccesstimestamp is None or (ts - self.lastaccesstimestamp) > (int(self.frequency[0:-1]) * 58):
            self.markTick(nowTimeString=nowTimeString, tick=tick)
            self.loop(nowTimeString=nowTimeString)
            self.markLastTick(nowTimeString=nowTimeString, tick=tick)
            self.lastaccesstimestamp = ts
            if self.trader is not None:
                self.trader.put_event()

