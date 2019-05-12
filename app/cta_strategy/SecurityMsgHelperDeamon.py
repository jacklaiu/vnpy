#coding: utf8
import vnpy.app.cta_strategy.Util as util
import time
import jqdatasdk
_str = str

def gatherFutureMessage(jqsecurity):
    nowTimeString = util.getYMDHMS()
    jqdatasdk.auth('13268108673', 'king20110713')
    df = jqdatasdk.get_price(
        security=jqsecurity,
        count=500,
        end_date=nowTimeString[0:nowTimeString.rindex(':') + 1] + '30',
        frequency='30m',
        fields=['close', 'open', 'high', 'low', 'volume']
    )
    indexList = df[df.close == df.close].index.tolist()
    i = indexList.__len__() - 1

    allva = []
    allpa_up = []
    allpa_down = []
    volumeArrowArr = []
    priceArrowArr_up = []
    priceArrowArr_down = []
    while i >= 0:
        d = indexList[i]
        datestr = _str(d) + ': '
        varrow = getVolumeArrow(df=df, indexList=indexList, i=i)
        parrow_up = getPriceArrowUp(df=df, indexList=indexList, i=i)
        parrow_down = getPriceArrowDown(df=df, indexList=indexList, i=i)
        if varrow > 10:
            volumeArrowArr.append(datestr + _str(varrow) + '\n')
            allva.append(datestr + "!" + _str(varrow) + "!" + '\n')
            i = i - 1
            continue
        if parrow_up > 100:
            priceArrowArr_up.append(datestr + _str(parrow_up) + '\n')
            allpa_up.append(datestr + "!||" + _str(parrow_up) + "||!" + '\n')
            i = i - 1
            continue
        if parrow_down > 100:
            priceArrowArr_down.append(datestr + _str(parrow_down) + '\n')
            allpa_down.append(datestr + "!||" + _str(parrow_down) + "||!" + '\n')
            i = i - 1
            continue
        allva.append(datestr + _str(varrow) + '\n')
        allpa_up.append(datestr + _str(parrow_up) + '\n')
        allpa_down.append(datestr + _str(parrow_down) + '\n')
        i = i - 1

    n0 = [_str(x) for x in allva]
    strs = "\n" + "###Volume Arrow: " + (_str(volumeArrowArr.__len__())) + ' >10 ---> ' + ('-'.join(n0)) + '\n\n'

    n1 = [_str(x) for x in allpa_up]
    strs = strs + "###Price Arrow_Up: " + (_str(priceArrowArr_up.__len__())) + ' >100 ---> ' + ('-'.join(n1)) + '\n\n'

    n2 = [_str(x) for x in allpa_down]
    strs = strs + "###Price Arrow_Down: " + (_str(priceArrowArr_down.__len__())) + ' >100 ---> ' + ('-'.join(n2)) + '\n\n'

    return strs

def getVolumeArrow(df, indexList, i):
    count = 0
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

def getPriceArrowUp(df, indexList, i):
    count = 0
    closeFlag = df.loc[indexList[i], 'close']
    i = i - 1
    while i >= 0:
        close = df.loc[indexList[i], 'close']
        if closeFlag > close:
            count = count + 1
        else:
            break
        i = i - 1
    return count

def getPriceArrowDown(df, indexList, i):
    count = 0
    closeFlag = df.loc[indexList[i], 'close']
    i = i - 1
    while i >= 0:
        close = df.loc[indexList[i], 'close']
        if closeFlag < close:
            count = count + 1
        else:
            break
        i = i - 1
    return count



while True:
    f = open('C:/Users/Administrator/Desktop/SecurityTrans.txt')
    str = f.read()
    f.close()
    if 'look' in str:
        str = str.replace('look', '')
        jqs = util.get_JQ_Format_name(str)
        time.sleep(1)
        f1 = open('C:/Users/Administrator/Desktop/SecurityTrans.txt', 'w')
        f1.write(jqs + '\n' + gatherFutureMessage(jqsecurity=jqs))
        f1.close()
        continue
    if str.__len__() == 0 or str.__len__() > 10:
        print('['+util.getYMDHMS()+']: watching...')
        time.sleep(1)
        continue
    print('[' + util.getYMDHMS() + ']: begin translating...')
    if str.__len__() <= 2:
        str = str + '2001'
    jqs = util.get_JQ_Format_name(str)
    time.sleep(1)
    ctps = util.get_CTA_Format_name(str)
    if jqs is not None and ctps is not None:
        f1 = open('C:/Users/Administrator/Desktop/SecurityTrans.txt', 'w')
        str = gatherFutureMessage(jqsecurity=jqs)
        f1.write(ctps + '\n' + ctps + '\n' + jqs + '\n' + str)
        print('[' + util.getYMDHMS() + ']: jqs: ' + jqs + ' ctps:' + ctps)
        f1.close()


    time.sleep(1)


