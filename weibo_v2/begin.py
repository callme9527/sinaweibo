# -*- coding:utf-8 -*-
__author__ = '9527'
import sys
from multiprocessing import Process, Queue
from cookie import CookieSpider
from wb_store import StoreSpider
from wb_download import Downloader
from getopt import getopt


def usage():
    print '''
    -h or --help: for help
    -t or --tag: write the tag you want crawl. eg: all, video, pic, music, article
    '''
    sys.exit()

if __name__ == '__main__':
    _tag = 'all'
    choice = ['all', 'video', 'pic', 'music', 'article', '全部', '视频', '图片', '音乐', '文章' ]
    opts, args = getopt(sys.argv[1:], 'ht:', ['help', 'tag='])
    for o, v in opts:
        if o in ['-h', '--help']:
            usage()
        if o in ['-t', '--tag']:
            v = v.lower()
            if v in choice: tag = v
        else:
            usage()
    if not tag:
        tag = _tag
        print u'未输入tag，默认爬取微博分类->全部'
    c_q = Queue()
    wb_q = Queue()
    c_s = CookieSpider()
    d_p = Process(target=Downloader, args=(tag, c_q, wb_q))
    s_p = Process(target=StoreSpider, args=(tag, wb_q))
    d_p.start()
    s_p.start()
    c_s.get_cookies(c_q)
    d_p.join()
    s_p.join()
    print u'所有进程执行完毕！Perfect!'