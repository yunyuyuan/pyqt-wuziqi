from time import sleep
from json import load, dump
from re import match

with open('./config.json', encoding='utf-8') as fp:
    config = load(fp)

def save_config():
    with open('./config.json', 'w', encoding='utf-8') as fp:
        dump(config, fp, indent=4)

from requests import Session
import PyQt5.Qt as qt

session = Session()


class AsyncRequest(qt.QThread):
    def __init__(self, top, url, data, signal=None, req_id=0):
        super().__init__(top)
        self.top = top
        self.url = config['server']+url
        self.data = data
        self.signal = signal
        self.req_id = req_id

    def run(self):
        try:
            re = session.post(self.url, data=self.data).json()
            data = re
        except Exception as e:
            data = {'state': 'err', 'data': str(e)}
        if self.signal:
            self.signal.emit(data, self.req_id)
        self.exit()

def check_legal(s):
    return match(r'^[\u4E00-\u9FA5\w_]{1,16}$', s)
