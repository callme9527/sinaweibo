# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/10/6 15:35'

import logging
import requests
from conf import *
from time import sleep
from random import choice
from cookie import get_cookies
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


logger = logging.getLogger('weibo')


class CodeError(Exception): pass


class Downloader(object):
    def __init__(self):
        self.count = 1
        self.cookies = get_cookies(users)
        self.agents = agents
        self.timeout = timeout
        self.try_max = try_max

    def download(self, url, try_times=1):
        headers = {
            'User-Agent': choice(self.agents)
        }
        cookies = choice(self.cookies)
        # logger.info('cookie:'+str(cookies))
        try:
            res = requests.get(url, headers=headers, cookies=cookies, timeout=timeout, allow_redirects=False)
            # 账号少的话，太频繁容易出现账号异常
            sleep(0.5)
            if res.status_code == 200:
                logger.debug('download('+str(try_times)+'):'+url+'('+str(self.count)+')-->OK')
                self.count += 1
                return res
            logger.debug('download('+str(try_times)+'):'+url+'('+str(self.count)+')-->error_httpcode:'
                         +str(res.status_code)+',res_cont:'+res.content)
            raise CodeError
        except Exception, e:
            logger.debug('download('+str(try_times)+'):'+url+',exception:'+str(e))
            if try_times >= self.try_max:
                logger.warning('download:'+url+': Max Try,Still Fail.')
                return
            try_times += 1
            self.download(url, try_times)

# if __name__ == '__main__':
#     downloader = Downloader()
#     res = downloader.download('http://weibo.com/mayday')
#     print res.content
#     downloader.download('http://www.baidu.com')

