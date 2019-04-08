from vnpy.app.cta_strategy.NewStrategyBody import StrategyBody
import vnpy.app.cta_strategy.Util as util
import time
sbs = [
    StrategyBody(security='600025'),
    StrategyBody(security='600161'),
    StrategyBody(security='600153'),
]
while True:
    nowTimeString = util.getYMDHMS()
    for sb in sbs:
        sb.handleOneTick(nowTimeString)
        time.sleep(1)
        print('['+util.getYMDHMS()+' - '+sb.security+']: looping...')



# now = util.getYMDHMS()
# timeArr = util.getTimeSerialBySecurity(starttime='2019-04-02 09:30:00', count=30000, periodSec=59, security='TA8888.XZCE')
# for nowTimeString in timeArr:
#     if nowTimeString > now:
#         exit()
#     for sb in sbs:
#         sb.handleOneTick(nowTimeString)

# timeArr = util.getTimeSerialBySecurity(starttime=startTime, count=5000, periodSec=59, security=sb.security)
# for nowTimeString in timeArr:
#     sb.handleOneTick(nowTimeString)