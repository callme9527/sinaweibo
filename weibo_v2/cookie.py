# -*- coding:utf-8 -*-
__author__ = '9527'
import re
import sys
import json
import time
import gevent
import requests
from random import random, choice
from urllib import quote
from bs4 import BeautifulSoup
from base64 import b64encode
from config import agents, prelogin_url, login_url, pin_url, coroutine_num, users
from gevent import monkey
from PIL import Image
monkey.patch_all(thread=False)
reload(sys)
sys.setdefaultencoding('utf-8')
try:
    import cPickle as pickle
except ImportError:
    import pickle


# 验证码错误异常
class PinError(Exception):
    def __init__(self):
        super(Exception, self).__init__()


# 用户密码错误异常
class AccessError(Exception):
    def __init__(self):
        super(Exception, self).__init__()


class CookieSpider(object):
    def __init__(self):
        self.error_times = 0
        self.cookies = []

    # cookie是否需要更新
    def _need_update(self):
        with open('cookie.txt', 'rb') as f:
            cookies = pickle.load(f)
        now = time.time()
        with open('time.txt', 'r') as f:
            data = f.read()
        if not data or (now-float(data)) > 24*60*60 or not cookies: return True
        return False

    # 异步获取多个cookie
    def get_cookies(self, cookie_q):
        try:
            if not self._need_update():
                print u'cookie未过期,准备加载...'
                with open('cookie.txt', 'rb') as f:
                    cookies_ = pickle.load(f)
                    # print cookies_
                for item in cookies_:
                    # print u'获得cookie：'+ str(item)+'\n'
                    cookie_q.put(item)
                cookie_q.put('end')
                # print u'cookie over！'
                return
        except:
            print u'time.txt 文件不存在，需要更新cookie'

        with open('time.txt', 'w') as f:
            f.write(str(time.time()))
        print u'准备抓取cookie...'
        for _ in range(coroutine_num):
            users.insert(0, 'end')
        greenlets = [gevent.spawn(self.get_cookie, users.pop(), cookie_q) for _ in range(coroutine_num)]
        gevent.joinall(greenlets)
        print u'抓取cookie完毕.'
        cookie_q.put('end')
        cookie_q.close()
        with open('cookie.txt', 'wb') as f:
            pickle.dump(self.cookies, f)
            print u'cookies保存完毕'
        return

    # 获取单个cookie
    def get_cookie(self, user, cookie_q):
        try:
            if user == 'end':  return
            headers = {
                'User-Agent': choice(agents)
            }
            print headers
            item = None
            session = requests.session()
            data = self.pre_login(session, headers)
            self.get_pin(session, headers, data)
            img = Image.open('pin.png')
            img.show()
            self.pin = raw_input(u'请查看pin.png输入验证码:')
            item = self.login(session, headers, user)
        except PinError:
            print u'验证码错误...'
            self.get_cookie(user, cookie_q)
        except AccessError:
            print u'用户密码错误,保存错误信息'
            with open('error_users.txt', 'a') as f:
                f.write('用户或密码错误:'+str(user)+'\n')
        except Exception, e:
            print str(e)
            self.error_times += 1
            if self.error_times > 2:
                print u'程序怕是要被你搞炸了...'
                with open('error_users.txt', 'a') as f:
                    f.write('网络状况不佳:'+ str(user) + '\n')
                return
            self.get_cookie(user, cookie_q)
        if not item or not item[0]: return
        # print u'getcookie:' + str(item)
        cookie_q.put(item)
        # print u'put cookie to q'
        self.cookies.append(item)

    # 获取验证码所需信息得从该响应中获取
    def pre_login(self, session, headers):
        url = prelogin_url % (time.time() * 1000)
        # print u'preurl:' + url + '\n'
        res = session.get(url, headers=headers, verify=False, timeout=5)
        raw_data = res.content
        # print raw_data
        data = raw_data[raw_data.find('(')+1:-1]
        # print data
        data = json.loads(data)
        return dict(data)

    # 获取验证码
    def get_pin(self, session, headers, data):
        url = pin_url % (int(random()*100000000), data.get('pcid', ''))
        # print 'pinurl:'+url+'\n'
        res = session.get(url, headers=headers, verify=False, timeout=5)
        with open('pin.png', 'wb') as f:
            f.write(res.content)
            print u'验证码保存至pin.png'

    # 登录
    def login(self, session, headers, user):
        post_data = {
            'door': self.pin,
            'encoding': 'UTF-8',
            'entry': 'weibo',
            'from': '',
            'gateway': '1',
            'pagerefer': '',
            'prelt': '103908',
            # 'pwencode': 'rsa2',
            'qrcode_flag': 'false',
            'returntype': 'META',
            'savestate': '7',
            'servertime': int(time.time()),
            'server': 'miniblog',
            'sp': user['pwd'],
            'sr': '1366*768',
            'su': b64encode(user['name']),
            'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'useticket': '1',
            'vsnf': '1'
        }
        res = session.post(login_url, data=post_data, headers=headers, verify=False, timeout=5)
        # print res.status_code
        # print res.content
        raw_data = res.content
        # 从响应中获取登录结果
        soup = BeautifulSoup(raw_data, 'html.parser', from_encoding='gbk')
        url = soup.find('meta', {'http-equiv': 'refresh'}).get('content').split(';', 1)[-1].split('=', 1)[-1].strip("'")
        # 验证码错误
        if quote(u'验证码'.encode('gbk')) in url:
            raise PinError
        # 密码错误
        if quote(u'密码'.encode('gbk')) in url:
            raise AccessError
        # 登陆成功后的cookies并不是我们所要的cookie
        # 微博会继续访问以下网址，最后的cookie才是我们所要的
        # print u'login得到的cookies:' + str(session.cookies.get_dict())
        # print u'从login中得到的url:\n' + url
        # 访问该网址得到随后的第一次登录网址login1
        res = session.get(url, headers=headers, verify=False)
        # print u'经过crossdomain后，cookies变为:' + str(session.cookies.get_dict())
        login1 = re.search(r'"arrURL":\["(.*?)",', res.content, re.S).group(1).replace('\\', '')
        # print login1 + '\n'
        login1 = login1 + "&callback=sinaSSOController.doCrossDomainCallBack&scriptId=ssoscript0&client=ssologin.js" \
                          "(v1.4.19)&_=1504181581334"
        res1 = session.get(login1, headers=headers, verify=False, timeout=5)
        # print u'login1_res' + res1.content + '\n'
        # print u'login1得到的cookies:' + str(session.cookies.get_dict())
        # 从login1的响应中获取login2网址
        index1 = res1.content.find(u'{')
        data = res1.content[index1: -4]
        # print u'data:' + data
        user_id = dict(json.loads(data)).get('userinfo', {}).get('uniqueid', '')
        login2 = re.search(r"replace\('(.*?)'\)", res.content, re.S).group(1)
        # print 'login2:' + login2 + '\n'
        # 访问login2得到最终cookie
        res2 = session.get(login2, headers=headers, verify=False, timeout=5)
        # print u'login2_res' + res2.content + '\n'
        # print u'login2得到的cookies:' + str(session.cookies.get_dict())
        return user_id, session.cookies.get_dict()


# 可以在此进行调试
# if __name__ == '__main__':
#     c_s = CookieSpider()
#     from multiprocessing import Queue
#     c_q = Queue()
#     c_s.get_cookie(user={'name': 'xxx', 'pwd': 'xxx'}, cookie_q=c_q)

