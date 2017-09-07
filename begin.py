# -*- coding:utf-8 -*-
__author__ = '9527'
from multiprocessing import Process, Queue
from cookie import CookieSpider
from video_spider import VideoSpider
from video_store import StoreSpder


def main():
    c_q = Queue()
    wb_q = Queue()
    c_s = CookieSpider()
    v_s = VideoSpider()
    s_s = StoreSpder()
    v_p = Process(target=v_s.downloads, args=(c_q, wb_q))
    s_p = Process(target=s_s.store, args=(wb_q,))
    v_p.start()
    s_p.start()
    c_s.get_cookies(c_q)
    v_p.join()
    s_p.join()
    print 'over'


if __name__ == '__main__':
    main()