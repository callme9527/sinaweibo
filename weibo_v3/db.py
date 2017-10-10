# -*- coding:utf-8 -*-
__author__ = '9527'

import pymongo


class MongoHelper(object):
    def __init__(self, collect):
        self.client = pymongo.MongoClient('mongodb://localhost:27017')
        db = self.client['weibo']
        self.collect = db[collect]

    def select(self, sql=''):
        if sql:
            return list(self.collect.find(sql))
        return list(self.collect.find())

    def insert(self, sql=''):
        if not sql: return
        self.collect.insert(sql)

    def insert_many(self, sql=''):
        if not sql: return
        self.collect.insert_many(sql)

    def update(self, query='', set=''):
        if not query or not set: return
        self.collect.update(query, {'$set': set})

    def delete(self, query=''):
        if not query:
            self.collect.remove()
            return
        self.collect.remove(query)

    def close(self):
        self.client.close()
