# -*- coding:utf-8 -*-
__author__ = '9527'


from store import store
from conf import index_url
from handler import start_handler
from multiprocessing import Process, Queue


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
