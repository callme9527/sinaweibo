# -*- coding:utf-8 -*-
import httplib, mimetypes, urlparse, json, time


class YDMHttp:
    apiurl = 'http://api.yundama.com/api.php'

    username = ''
    password = ''
    appid = ''
    appkey = ''

    def __init__(self, username, password, appid, appkey):
        self.username = username
        self.password = password
        self.appid = str(appid)
        self.appkey = appkey

    def request(self, fields, files=[]):
        try:
            response = post_url(self.apiurl, fields, files)
            response = json.loads(response)
        except Exception as e:
            response = None
        return response

    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['balance']
        else:
            return -9001

    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['uid']
        else:
            return -9001

    def upload(self, filename, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        file = {'file': filename}
        response = self.request(data, file)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    def result(self, cid):
        data = {'method': 'result', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'cid': str(cid)}
        response = self.request(data)
        return response and response['text'] or ''

    def decode(self, filename, codetype, timeout):
        cid = self.upload(filename, codetype, timeout)
        if (cid > 0):
            for i in range(0, timeout):
                result = self.result(cid)
                if (result != ''):
                    return cid, result
                else:
                    time.sleep(1)
            return -3003, ''
        else:
            return cid, ''


######################################################################

def post_url(url, fields, files=[]):
    urlparts = urlparse.urlsplit(url)
    return post_multipart(urlparts[1], urlparts[2], fields, files)


def post_multipart(host, selector, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('Host', host)
    h.putheader('Content-Type', content_type)
    h.putheader('Content-Length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()


def encode_multipart_formdata(fields, files=[]):
    BOUNDARY = 'WebKitFormBoundaryJKrptX8yPbuAJLBQ'
    CRLF = '\r\n'
    L = []
    for field in fields:
        key = field
        value = fields[key]
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for field in files:
        key = field
        filepath = files[key]
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filepath))
        L.append('Content-Type: %s' % get_content_type(filepath))
        L.append('')
        L.append(open(filepath, 'rb').read())
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


######################################################################
def get_pin(user, pwd):
    # 用户名
    username = user

    # 密码
    password = pwd

    # 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
    appid = 3988

    # 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！
    appkey = 'f3d2ac1c2068e1ca6ae183c90217a96b'

    # 图片文件
    filename = 'pin.png'

    # 验证码类型，# 例：1005表示5位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
    codetype = 1005

    # 超时时间，秒
    timeout = 20

    # 初始化
    yundama = YDMHttp(username, password, appid, appkey)

    # 登陆云打码
    uid = yundama.login()
    print u'云打码用户uid: %s' % uid

    # 查询余额
    balance = yundama.balance()
    print u'账号余额: %s' % balance

    # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
    cid, result = yundama.decode(filename, codetype, timeout)
    return result

######################################################################


if __name__ == '__main__':
    user = 'xxx'
    pwd = 'xxx'
    print get_pin(user, pwd)