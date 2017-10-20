# -*- coding:utf-8 -*-
__author__ = '9527'

from gevent import monkey, sleep
monkey.patch_all(thread=False)

import re
import ast
import json
import gevent
import logging

from conf import *
from Queue import Empty
from store import store
from parse import Parser
from threading import Thread
from validate import Validater
from download import Downloader
from multiprocessing import Process, Queue
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.setrecursionlimit(100000)


def start_handler(url_q, wb_q, info_q):
    handler = Handler(url_q, wb_q, info_q)
    handler.handle_url()


logger = logging.getLogger('weibo')


def log(func):
    def wrap(*args, **kwargs):
        logger.debug(func.__name__+' start..')
        func(*args, **kwargs)
        logger.debug(func.__name__+' stop.')
    return wrap


class Handler(object):
    def __init__(self, url_q, wb_q, info_q):
        self.url_count = 1
        self.handle_urls = set()
        self.url_suf = 'http://weibo.com'
        self.url_q = url_q
        self.wb_q = wb_q
        self.info_q = info_q
        self.downloader = Downloader()
        self.validater = Validater()

    def oninit(self, url):
        url = self.url_suf + url
        res = self.downloader.download(url)
        if not res: return
        cont = res.content
        uid = re.search("CONFIG\['oid'\]='(.*?)'", cont).group(1)
        nick = re.search("CONFIG\['onick'\]='(.*?)'", cont).group(1).decode('utf-8')
        # ajax 请求微博时要用
        page_id = re.search("CONFIG\['page_id'\]='(.*?)'", cont).group(1)
        domain = re.search("CONFIG\['domain'\]='(.*?)'", cont).group(1)
        location = re.search("CONFIG\['location'\]='(.*?)'", cont).group(1)
        nums = Parser.parse_index(cont)
        if not nums: return
        follow_num, fans_num, wb_num = nums
        # 验证该用户关注粉丝微博数是否变化
        # 如变化更新信息，微博变化则需要爬取更新的微博
        # 该方法返回需要爬取的微博数
        crawl_info, wb_num = self.validater.validate_nums(page_id, nums)
        self.crawl_info = crawl_info
        return {
            'uid': uid,
            'page_id': page_id,
            'nick': nick,
            'domain': domain,
            'location': location,
            'follow_num': int(follow_num),
            'fans_num': int(fans_num),
            'wb_num': int(wb_num)
        }

    def handle_url(self):
        while True:
            try:
                url = self.url_q.get()
                if url == 'end':
                    self.wb_q.put_nowait('end')
                    self.info_q.put_nowait('end')
                    print 'crawl over'
                    break
                if url in self.handle_urls: continue
                self.args = args = self.oninit(url)
                if not args: continue
                # wb_t = Thread(target=self.get_wb)
                # url_t = Thread(target=self.get_url)
                # wb_t.start()
                # url_t.start()
                # wb_t.join()
                # info_t = Thread(target=self.get_info)
                # info_t.start()
                # url_t.join()
                # info_t.join()

                greenlets = []
                greenlets.append(gevent.spawn(self.get_wb))
                greenlets.append(gevent.spawn(self.get_url))
                greenlets.append(gevent.spawn(self.get_info))
                gevent.joinall(greenlets)

                self.handle_urls.add(url)
            except Empty:
                sleep(1)
            except Exception, e:
                logger.debug('error in handle_url:' + str(e))

    @log
    def get_wb(self):
        wb_num = self.args.get('wb_num', 0)
        print u'微博数:'+str(wb_num)
        if not wb_num: return
        page_count = wb_num / 45 if wb_num % 45 == 0 else wb_num / 45 + 1
        domain = self.args['domain']
        page_id = self.args['page_id']
        greenlets = []
        ajax_url = 'http://weibo.com/p/aj/v6/mblog/mbloglist?domain=%s&page=%d&pagebar=%d&id=%s&pre_page=%d'
        for id in range(1, page_count+1):
            url_p = self.url_suf + '/p/' + page_id + '?page=' + str(id)
            ajax_url1 = ajax_url % (domain, id, 0, page_id, id)
            ajax_url2 = ajax_url % (domain, id, 1, page_id, id)
            greenlets.append(gevent.spawn(self.handle_wb_url, url_p))
            greenlets.append(gevent.spawn(self.handle_wb_url, ajax_url1))
            greenlets.append(gevent.spawn(self.handle_wb_url, ajax_url2))
            if len(greenlets) >= greenlet_num:
                gevent.joinall(greenlets)
                greenlets = []
        gevent.joinall(greenlets)

    @log
    def get_url(self):
        p_id = self.args['page_id']
        follow_num = self.args['follow_num']
        fans_num = self.args['fans_num']
        raw_follow = follow_num / 20
        raw_fans = fans_num / 20
        follow_page_num = min(raw_follow, 5) if follow_num % 20 == 0 else min(raw_follow+1, 5)
        fans_page_num = min(fans_num/20, 5) if fans_num % 20 == 0 else min(raw_fans+1, 5)
        logger.debug('follow:'+str(follow_page_num)+',fans:'+str(fans_page_num))
        suf = self.url_suf+'/p/'+p_id+'/follow'
        follow_g = [gevent.spawn(self.handle_relate_url, suf+'?page='+str(i+1)) for i in range(follow_page_num)]
        fans_g = [gevent.spawn(self.handle_relate_url, suf+'?relate=fans&page='+str(i+1)) for i in range(fans_page_num)]
        greenlets = follow_g + fans_g
        gevent.joinall(greenlets)

    @log
    def get_info(self):
        if not self.crawl_info: return
        url = self.url_suf + '/p/' + self.args['page_id'] + '/info'
        self.handle_info_url(url)

    def handle_wb_url(self, url):
        try:
            res = self.downloader.download(url)
            if not res or not res.content:
                logger.debug('改url:'+url+'无微博内容')
                return
            # logger.debug('wb_html:'+res.content)
            if 'mbloglist' in url:
                data = re.search('"data":"(.*?)"}', res.content, re.S)
                data = data.group(1) if data else ''
                html = data.replace('\\r', '').replace('\\n', '').replace('\\t', '').replace('\\', '').strip()
                # print html
            else:
                html = re.search('js/pl/content/homeFeed/index.js.*?html":"(.*?)"}', res.content, re.S)
                if not html: return
                html = html.group(1).replace('\\t', '').replace('\\n', '').replace('\\r', '').replace('\\', '')
            if not html:
                logger.debug(u'该url:' + url + u'无微博信息')
                return
            wbs = Parser.parse_wb(html, self.args['uid'])
            if not wbs: return
            self.wb_q.put_nowait(wbs)
            # print (self.wb_q.qsize())
        except Exception, e:
            logger.warning('error in hand_wb_url:'+str(e)+u',url为:'+url)

    def handle_relate_url(self, url):
        res = self.downloader.download(url)
        if not res: return
        urls = Parser.parse_relate(res.content)
        if not urls: return
        for url in urls:
            if self.url_count >= user_num:
                self.url_q.put_nowait('end')
                return
            self.url_q.put_nowait(url)
            self.url_count += 1

    def handle_info_url(self, url):
        res = self.downloader.download(url)
        if not res:
            url = url.replace('info', 'about')
            res = self.downloader.download(url)
            if not res: return
        info = Parser.parse_info(res.content)
        if info: self.info_q.put_nowait(info)


if __name__ == '__main__':
    url_q = Queue()
    url_q.put_nowait(index_url)
    wb_q = Queue()
    info_q = Queue()
    p1 = Process(target=start_handler, args=(url_q, wb_q, info_q))
    p2 = Process(target=store, args=(wb_q, info_q))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print 'all_over'
