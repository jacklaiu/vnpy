# coding: utf-8

import jqdatasdk
import talib
import numpy as np
import time
import vnpy.app.cta_strategy.Util as Util
from vnpy.app.cta_strategy.SmtpClient import SmtpClient as smtp

lastaccesstimestampObj = {'lastaccesstimestamp': None}
frequency = '30m'
dfMap = {}
securities = ['RB8888.XSGE', 'ZN8888.XSGE']

to0100_securies_str = 'ZN'

def refreshAdvancedData(security, nowTimeString=None):
    jqdatasdk.auth('13268108673', 'king20110713')
    newRow = None
    newIndex = None
    df = None
    if dfMap is None:
        exit()
    if security not in dfMap.keys():
        dfMap.setdefault(security, df)
    else:
        df = dfMap.get(security)

    if df is None:
        try:
            df = jqdatasdk.get_price(
                security=security,
                count=300,
                end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
                frequency=frequency,
                fields=['close', 'open', 'high', 'low', 'volume']
            )
        except:
            smtp.sendMail(subject=security + ': refreshAdvancedData初始化数据错误！', content='')
    else:
        try:
            newDf = jqdatasdk.get_price(
                security=security,
                count=1,
                end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
                frequency=frequency,
                fields=['close', 'open', 'high', 'low', 'volume']
            )
            newIndex = newDf.index.tolist()[0]
            newRow = newDf.loc[newIndex]
        except:
            try:
                time.sleep(5)
                jqdatasdk.auth('13268108673', 'king20110713')
                newDf = jqdatasdk.get_price(
                    security=security,
                    count=1,
                    end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
                    frequency=frequency,
                    fields=['close', 'open', 'high', 'low', 'volume']
                )
                newIndex = newDf.index.tolist()[0]
                newRow = newDf.loc[newIndex]
            except:
                pass

    if newRow is not None:
        df.loc[newIndex] = newRow
    close = [float(x) for x in df['close']]
    df['RSI9'] = talib.RSI(np.array(close), timeperiod=9)
    df.drop([df.index.tolist()[0]], inplace=True)

    dfMap[security] = df

def getVolumeArrow(df, indexList):
    count = 0
    i = indexList.__len__() - 1
    flagVolume = df.loc[indexList[i], 'volume']
    i = i - 1
    while i >= 0:
        volume = df.loc[indexList[i], 'volume']
        if flagVolume > volume:
            count = count + 1
        else:
            break
        i = i - 1
    return count

def isTradeTime(security=None, nowTimeString=None):
    pre = security[0:2]
    hm = nowTimeString[-8:-3]
    if pre in to0100_securies_str and ('01:00' <= hm < '09:00' or '10:15' <= hm < '10:30' or '11:30' <= hm < '13:30' or '15:00' <= hm < '21:00'):
        return False
    elif '00:00' <= hm < '09:00' or '10:15' <= hm < '10:30' or '11:30' <= hm < '13:30' or '15:00' <= hm < '21:00' or '23:00' <= hm <= '23:59':
        return False
    else:
        return True

def notify(security, nowTimeString):
    if security in dfMap.keys():
        df = dfMap[security]
        if df is None:
            return
        indexList = df.index.tolist()
        vac = getVolumeArrow(df=df, indexList=indexList)
        print('['+security+': '+nowTimeString+']: VAC' + str(vac))

def loop(nowTimeString):
    ts = Util.string2timestamp(str(nowTimeString))
    lastaccesstimestamp = lastaccesstimestampObj['lastaccesstimestamp']
    if lastaccesstimestamp is None:
        lastaccesstimestampObj['lastaccesstimestamp'] = ts
    if lastaccesstimestamp is None or (ts - lastaccesstimestamp) > (int(frequency[0:-1]) * 58):
        for security in securities:
            if isTradeTime(security=security, nowTimeString=nowTimeString) is False:
                continue
            refreshAdvancedData(security=security, nowTimeString=nowTimeString)
            notify(security, nowTimeString)
            lastaccesstimestampObj['lastaccesstimestamp'] = ts

def main():
    while True:
        nowTimeString = Util.getYMDHMS()
        if Util.isFutureTradingTime(nowTimeString=nowTimeString) is False:
            time.sleep(58)
            continue
        loop(nowTimeString=nowTimeString)
        time.sleep(4)

def test():
    ts = Util.getTimeSerial(starttime='2019-05-08 08:30:00', count=20000, periodSec=58)
    for nowTimeString in ts:
        if Util.isFutureTradingTime(nowTimeString=nowTimeString) is False:
            continue
        loop(nowTimeString)

test()
