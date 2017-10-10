# coding: utf-8
from gevent import monkey
monkey.patch_all(thread=False)

import requests
import json
import re
import time
import gevent
import logging

from conf import *
from random import choice, random
from urllib import quote
from base64 import b64encode
from db import MongoHelper
from yundama import get_pin
from gevent.lock import RLock
from threadpool import ThreadPool, makeRequests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


import sys
reload(sys)
sys.setdefaultencoding('utf-8')


lock = RLock()
login_data = {
    # 'door': self.pin,
    'encoding': 'UTF-8',
    'entry': 'weibo',
    'from': '',
    'gateway': '1',
    'pagerefer': '',
    'prelt': '49',
    'qrcode_flag': 'false',
    'returntype': 'META',
    'savestate': '7',
    'servertime': int(time.time()),
    'server': 'miniblog',
    # 'sp': user['pwd'],
    'sr': '1366*768',
    # 'su': b64encode(user['name']),
    'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
    'useticket': '1',
    'vsnf': '1'
}
db_cookie = MongoHelper('cookie')
logger = logging.getLogger('weibo')


class AuthError(Exception): pass


class UnknownError(Exception): pass


def get_cookies(users):
    cookies = []
    if not db_cookie.select():
        logger.debug(u'数据库中没有cookie,准备爬去')
        if not users:
            logger.info(u'请在conf文件中添加微博用户')
            return
        # pool = ThreadPool(3)
        # reqs = makeRequests(get_cookie, users)
        # [pool.putRequest(req) for req in reqs]
        # pool.wait()
        greenlets = []
        for user in users:
            # get_cookie(user)
            greenlets.append(gevent.spawn(get_cookie, user))
            if len(greenlets) >= 5:
                gevent.joinall(greenlets)
                greenlets = []
        gevent.joinall(greenlets)
    else:
        logger.debug(u'数据库中有cookie,准备更新...')
        # 更新数据库中用户的cookie
        update_cookies()
    # 加查询条件防止有的cookie更新失败
    now = time.time()
    select_time = now - 12 * 60 * 60
    records = db_cookie.select({'time': {'$gt': select_time}})
    for record in records:
        cookies.append(record['cookie'])
    db_cookie.close()
    return cookies


def update_cookies():
    now = time.time()
    select_time = now - 12*60*60
    select_sql = {'time': {'$lte': select_time}}
    old_cookies = db_cookie.select(select_sql)
    if not old_cookies: return
    greenlets = []
    for cookie in old_cookies:
        user = [cookie['_id'], cookie['pwd']]
        # get_cookie(user)
        greenlets.append(gevent.spawn(get_cookie, user))
        if len(greenlets) >= greenlet_num:
            gevent.joinall(greenlets)
            greenlets = []
    gevent.joinall(greenlets)


def get_cookie(user, try_times=0):
    login_data.update(
        {
            'sp': user[1],
            'su': b64encode(user[0])
        }
    )
    session = requests.session()
    try:
        cookie = login(session, login_data)
        if not cookie: return
        record = {
            '_id': user[0],
            'pwd': user[1],
            'cookie': cookie,
            'time': time.time()
        }
        db_cookie.delete({'_id': user[0]})
        db_cookie.insert(record)
    except (AuthError, UnknownError):
        logger.info(u'用户为:'+user[0]+u'的账号有问题,请修改或删除')
    except Exception, e:
        logger.debug('in get_Cookie, user:'+user[0]+',except:'+str(e))
        try_times += 1
        if try_times >= 3:
            return
        get_cookie(user, try_times)


def login(session, data, headers={'User-Agent': choice(agents)}, error_time=0):
    url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
    login_res = session.post(url, data, headers=headers, verify=False, timeout=timeout)
    login_cont = login_res.content
    reason = re.search('reason=(.*?)"', login_cont)
    if reason:  # 登陆出现状况
        reason = reason.group(1)
        if quote('验证码'.encode('gbk')) in reason:
            error_time += 1
            if error_time >= 3: return
            lock.acquire()
            logger.debug(u'需要输入验证码')
            get_cap(session, pre_login(session, headers), headers)
            times = 0
            while True:
                pin = get_pin(dm_user[0], dm_user[1])
                times += 1
                if pin or times >= 2: break
            logger.debug(u'打码成功，准备二次登陆...'+pin)
            data.update({
                'door': pin
            })
            lock.release()
            return login(session, data, error_time=error_time)
        if quote('密码'.encode('gbk')) in reason:
            raise AuthError
        else:
            logger.debug('login_reason:'+reason)
            raise UnknownError
    else:  # 登录成功
        logger.debug(u'验证成功')
        # 但此时得到的cookie并不能登录进微博
        # 经抓包还需经过以下步骤
        # 从login的响应中获得cross_url
        # 从cross_res中获得随后需要的两个url
        cross_url = re.search('replace\("(.*?)"\)', login_cont, re.S).group(1)
        logger.debug('cross_url:'+cross_url)
        cross_res = session.get(cross_url, headers=headers, verify=False, timeout=timeout)
        login1 = re.search(r'"arrURL":\["(.*?)",', cross_res.content, re.S).group(1).replace('\\', '')
        login1 = login1 + "&callback=sinaSSOController.doCrossDomainCallBack&scriptId=ssoscript0&client=ssologin.js" \
            "(v1.4.19)&_="+str(time.time()*1000)
        logger.debug('login1_url:'+login1)
        login2 = re.search(r"replace\('(.*?)'\)", cross_res.content, re.S).group(1)
        logger.debug('login2_url:'+login2)
        session.get(login1, headers=headers, verify=False, timeout=timeout)
        session.get(login2, headers=headers, verify=False, timeout=timeout)
        logger.debug(u'所有登录验证完毕,获得cookie')
        logger.debug(u'cookie:'+str(session.cookies.get_dict()))
        return session.cookies.get_dict()


# 获取验证码所需信息得从该响应中获取
def pre_login(session, headers):
    url = 'https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack' \
          '&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_=' + str(time.time() * 1000)
    logger.debug('prelogin_url:'+url)
    res = session.get(url, headers=headers, verify=False, timeout=timeout)
    raw_data = res.content
    logger.debug('prelogin_res:'+raw_data)
    data = raw_data[raw_data.find('(')+1:-1]
    data = json.loads(data)
    return dict(data)


# 获取验证码
def get_cap(session, data, headers):
    pin_url = 'https://login.sina.com.cn/cgi/pin.php?r=%s&s=0&p=%s'
    url = pin_url % (int(random()*100000000), data.get('pcid', ''))
    logger.debug('pin_url:'+url)
    res = session.get(url, headers=headers, verify=False, timeout=timeout)
    with open('pin.png', 'wb') as f:
        f.write(res.content)
        # logger.debug(u'验证码保存至pin.png')


# 可在此调试，注意开启conf文件中的DEBUG模式
if __name__ == '__main__':
    print get_cookies(users)
