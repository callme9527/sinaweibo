# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/10/7 15:53'

from db import MongoHelper


class Validater(object):
    def __init__(self):
        self.collect_info = MongoHelper('info')
        self.collect_wb = MongoHelper('wb')

    def validate_nums(self, p_id, now_nums):
        crawl_info = False
        query = {'page_id': p_id}
        info = self.collect_info.select(query)
        if len(info) == 0:
            wb_num = now_nums[2]
            crawl_info = True
        else:
            old_nums = info[0]['follow_num'], info[0]['fans_num'], info[0]['wb_num']
            if old_nums != tuple(now_nums):
                self.collect_info.update(query, {'follow_num': now_nums[0], 'fans_num': now_nums[1], 'wb_num': now_nums[2]})
            wb_num = now_nums[2]-old_nums[2] if now_nums[2] - old_nums[2] > 0 else 0
        return crawl_info, wb_num

    def validate_wb(self, mid):
        query = {'mid': mid}
        wb = self.collect_wb.select(query)
        if wb: return True
        return False

    def validate_info(self, uid):
        query = {'uid': uid}


# if __name__ == '__main__':
#     v = Validater()
#     print v.validate_nums('12544684', (0, 0, 2))
