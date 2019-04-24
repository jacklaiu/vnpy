#coding: utf8
import vnpy.app.cta_strategy.Util as util
import time

while True:
    f = open('C:/Users/Administrator/Desktop/SecurityTrans.txt')
    str = f.read()
    f.close()
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
        f1.write(ctps + '\n' + ctps + '\n' + jqs + '\n')
        print('[' + util.getYMDHMS() + ']: jqs: ' + jqs + ' ctps:' + ctps)
        f1.close()
    time.sleep(1)


