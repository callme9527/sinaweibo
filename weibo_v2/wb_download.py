# -*- coding:utf-8 -*-
__author__ = '9527'
# 微博的视频页面是最多10页
# 每访问一页时会加载15个微博，而后会ajax加载2次。 构造地址时的主要参数是mid即微博的ID！
import traceback
import re
import sys
import json
import time
import gevent
import requests
from random import choice
from config import agents, types
from gevent import monkey
monkey.patch_all(thread=False)
from video_parser import VideoParser
from pic_parser import PicParser
from article_parser import ArticleParser
from music_parser import MusicParser
from all_parser import AllParser
reload(sys)
sys.setdefaultencoding('utf-8')
try:
    import cPickle as pickle
except ImportError:
    import pickle


class Downloader(object):
    def __init__(self, tag, cookie_q, wb_q):
        self.headers = {
            'User-Agent': choice(agents)
        }
        self.mids = set()
        self.type = types[tag]
        self.tag = tag
        self.mids_file = 'mids_'+tag+'.txt'
        self.parser = eval(tag.title()+'Parser()')
        self.cookie_q = cookie_q
        self.wb_q = wb_q
        self.downloads()

    # 下载单页微博
    def download(self, cookies, page_url):
        try:
            res = requests.get(page_url, headers=self.headers, cookies=cookies, timeout=5)
            if res.status_code != 200: return
            #  微博的html在一个script中
            html = re.search('home/js/pl/content/homefeed/index.js.*?html":"(.*?)"}', res.content, re.S)
            html = html.group(1).replace('\\', '').replace('\r\n', '') if html else None
            #  获得用户ID插入数据库，方便数据库查询
            uid = re.search('weibo.com/(.*?)/home', page_url, re.S).group(1)
            uid = uid.split('/')[-1] if 'u' in uid else uid
            #  得到最后一个微博的ID，调用相应分类的解析方法
            min_id = self.parser.parse(html, self.wb_q, self.mids, uid)
            #  获取微博的页码pageid，第一个微博的ID即endid
            page_id = re.search('&page=([0-9]+)', page_url, re.S).group(1)
            end_id = re.search('end_id=([0-9]+)', page_url, re.S).group(1)
            #  一共有两次ajax请求
            for i in range(2):
                if not min_id: break
                #  构造ajax__url
                ajax_url = 'http://weibo.com/aj/mblog/fsearch?ajwvr=6&pre_page=%s&page=%s&end_id=%s&min_id=%s' \
                           '&is_' + self.tag + '=1&pagebar=%d&__rnd=%s'
                rnd = int(time.time() * 1000)
                ajax_url = ajax_url % (page_id, page_id, end_id, min_id, i, rnd)
                res = requests.get(ajax_url, headers=self.headers, cookies=cookies, timeout=5)
                if res.status_code != 200: return
                html = dict(json.loads(res.content)).get('data', '')
                min_id = self.parser.parse(html, self.wb_q, self.mids, uid)
        except:
            print u'网络不佳'
            # print traceback.print_exc()

    # 异步下载全部微博
    def downloads(self):
        # 将所有微博的ID保存，避免下载重复微博
        try:
            with open(self.mids_file, 'r') as f:
                for line in f:
                    self.mids.add(line.strip('\n'))
                print u'读取以前爬取微博ID完毕.'
        except: pass

        while True:
            item = self.cookie_q.get()
            if item == 'end':
                self.wb_q.put_nowait('end')
                print u'所有cookie抓取微博完毕.'
                with open(self.mids_file, 'w') as f:
                    f.write('\n'.join(list(self.mids)))
                print u'所有微博ID写入mid_%s.txt.' % self.tag
                return
            uid = item[0]  # 用户ID
            cookies = item[1]  # 用户cookies
            tag_url = 'https://weibo.com/'
            if uid.isdigit():
                tag_url = tag_url + 'u/%s/home?is_%s=1' % (uid, self.tag)
            else:
                tag_url = tag_url + '%s/home?is_%s=1' % (uid, self.tag)
            # print tag_url
            print u'用户id为%s的微博(分类->%s)已经开始爬取.'% (uid, self.type)
            print u'爬取微博分类->%s...' % self.type
            try:
                res = requests.get(tag_url, headers=self.headers, cookies=cookies, verify=False)
            except:
                print u'网络状况不佳，抓取失败'
                continue
            if res.status_code != 200: continue

            mid = re.search('mid=.*?([0-9]+)', res.content).group(1)  # 第一个微博ID
            #  因为微博最多10页，图方便直接构造了10个greenlet，如果页面不存在直接跳过.
            greenlets = []
            for i in range(1, 11):
                page_url = tag_url + '&end_id=%s&pre_page=2&page=%d&pids=Pl_Content_HomeFeed' % (mid, i)
                greenlet = gevent.spawn(self.download, cookies, page_url)
                greenlets.append(greenlet)
            gevent.joinall(greenlets)
            print u'用户id为%s的微博(分类->%s)已经爬取完毕.' % (uid, self.type)

