#: encoding: utf8
import requests

class SmtpClient():

    def __init__(self, enable=False):
        self.enable = enable

    def sendMail(self, subject, content, receivers='jacklaiu@163.com'):
        if self.enable is False:
            return
        try:
            url = 'http://107.182.31.161:64210/smtpclient/sendHtml?subject=' + subject + '&content=' + content + '&receivers=' + receivers
            print("@@@@@@@@@@@@@->subject: " + subject + " content: " + content)
            requests.get(url)
        except:
            pass
