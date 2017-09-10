# -*- coding:utf-8 -*-
__author__ = '9527'
import sys
import pymongo
reload(sys)
sys.setdefaultencoding('utf-8')


class StoreSpider(object):
    def __init__(self, tag, wb_q):
        self.datas = []
        self.client = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db = self.client['spider']
        self.collection = self.db['wb_'+tag]
        self.store(wb_q)

    def store(self, wb_q):
        while True:
            try:
                wb = wb_q.get()
                if wb == 'end':
                    self.store_end()
                    return
                self.datas.append(wb)
                if len(self.datas) >= 30:
                    self.collection.insert_many(self.datas)
                    self.datas = []
            except Exception, e:
                print str(e)

    def store_end(self):
        if len(self.datas) > 0:
            self.collection.insert_many(self.datas)
        self.client.close()
