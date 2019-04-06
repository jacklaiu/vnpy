from vnpy.app.cta_strategy.NewStrategyBody import StrategyBody
import vnpy.app.cta_strategy.Util as util

startTime = '2018-11-14 14:00:00'
name = 'jd8888'
jq_s_name = util.get_JQ_Format_name(name)
ctp_s_name = util.get_CTA_Format_name(name)
print(jq_s_name)
print(ctp_s_name)

sb = StrategyBody(security=jq_s_name, frequency='28m', onlyKon=1, cond_er=0.4, cond_before_er=0.8, cond_after_er=1.0)

timeArr = util.getTimeSerialBySecurity(starttime=startTime, count=10000, periodSec=59, security=sb.security)
for nowTimeString in timeArr:
    sb.handleOneTick(nowTimeString)


# from vnpy.app.cta_strategy.SmtpClient import SmtpClient
# smtp = SmtpClient(enable=True)
# smtp.sendMail(subject='hello jacklaiu', content='hello jacklaiu', receivers='jacklaiu@163.com')