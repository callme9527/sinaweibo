# -*- coding:utf-8 -*-
__author__ = '9527'
import sys
import pymongo
reload(sys)
sys.setdefaultencoding('utf-8')


class StoreSpder(object):
    def __init__(self):
        pass

    def con_db(self):
        self.datas = []
        self.client = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db = self.client['spider']
        self.collection = self.db['wb_video']

    def store(self, wb_q):
        self.con_db()
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
                with open('error_store.txt', 'a')as f:
                    f.write('[*]error:'+str(e)+'\n'+str(self.datas)+'\n\n')

    def store_end(self):
        if len(self.datas) > 0:
            self.collection.insert_many(self.datas)
        self.client.close()
