# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/10/5 21:41'

import logging

from conf import *
from time import sleep
from Queue import Empty
from db import MongoHelper
from threading import Thread


logger = logging.getLogger('weibo')


def store_wb(wb_q):
    wb_num = 0
    wbs = []
    collect = MongoHelper('wb')
    while True:
        try:
            if len(wbs) >= 45:
                collect.insert_many(wbs)
                wb_num += len(wbs)
                logger.debug(u'存储了' + str(wb_num) + u'条微博了')
                wbs = []
            wb = wb_q.get_nowait()
            # logger.debug('get wbs:'+str(wb))
            if wb == 'end':
                if len(wbs) > 0:
                    collect.insert_many(wbs)
                    wb_num += len(wbs)
                    logger.debug(u'存储微博完毕,共' + str(wb_num) + u'条微博.')
                break
            wbs.extend(wb)
        except Empty:
            sleep(1)
        except Exception, e:
            logger.debug('in store_wb:'+str(e))


def store_info(info_q):
    info_num = 0
    infos = []
    collect = MongoHelper('info')
    while True:
        try:
            if len(infos) >= 10:
                collect.insert_many(infos)
                infos = []
                info_num += 10
                logger.debug(u'存储了' + str(info_num) + u'条用户信息了')
            info = info_q.get_nowait()
            if info == 'end':
                if len(infos) > 0:
                    collect.insert_many(infos)
                    info_num += len(infos)
                logger.debug(u'存储用户信息完毕,共' + str(info_num) + u'条.')
                break
            infos.append(info)
        except Empty:
            sleep(1)
        except Exception, e:
            logger.debug('in store_info:' + str(e))


def store(wb_q, info_q):
    wb_t = Thread(target=store_wb, args=(wb_q,))
    info_t = Thread(target=store_info, args=(info_q,))
    wb_t.start()
    info_t.start()
    wb_t.join()
    info_t.join()

