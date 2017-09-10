# -*- coding:utf-8 -*-
__author__ = '9527'
from bs4 import BeautifulSoup


class PicParser(object):
    def parse(self, html, wb_q, mids, uid):
        if not html: return
        soup = BeautifulSoup(html, 'html.parser')
        pics = soup.find_all('div', {'action-type': 'feed_list_item'})
        # print 'size:' + str(len(pics))
        if not pics: return
        for pic in pics:
            # print pic
            mid = pic.get('mid', u'')  # 微博id
            if mid in mids:
                if pics.index(pic) < len(pics) - 1:
                    continue
                return mid
            # 获取发布者信息
            author_info = pic.find('div', {'class': 'WB_info'}).find('a')
            author_name = author_info.get('title', u'无')
            author_link = author_info.get('href', u'无')
            # 获取发布时间及发布设备
            wb_from = pic.find('div', {'class': 'WB_from S_txt2'})
            wb_from = wb_from.find_all('a') if wb_from else None
            wb_time = u'无'
            wb_dev = u'无'
            if wb_from and len(wb_from) == 2:
                wb_time = wb_from[0].get('title')
                wb_dev = wb_from[1].string
            # 获取微博内容
            wb_text = pic.find('div', {'node-type': 'feed_list_content'})
            wb_cont = u'无'
            if wb_text and wb_text.stripped_strings:
                # print wb_text.stripped_strings
                conts = []
                try:
                    for cont in wb_text.stripped_strings:
                        conts.append(cont.replace('rn', '').strip())
                except StopIteration:
                    pass
                wb_cont = ''.join(conts).strip()
            # 微博的图片地址
            imgs = []
            wb_pics = pic.find('ul', {'node-type': 'fl_pic_list'})
            wb_pics = wb_pics.find_all('li') if wb_pics else None
            if wb_pics:
                for wb_pic in wb_pics:
                    img = wb_pic.find('img')
                    img = 'http:' + img.get('src') if img else u'无'
                    imgs.append(img)
            else:
                wb_pic = pic.find('li', {'action-type': 'feed_list_media_img'})
                img = 'http:'+wb_pic.find('img').get('src') if wb_pic else ''
                imgs.append(img)
            wb_sta = u'原创'
            # 保存微博信息
            wb_info = {
                '_id': mid,
                'uid': uid,
                'tag': 'pic',
                'sta': wb_sta,
                'author_name': author_name,
                'author_link': 'https://weibo.com' + author_link,
                'time': wb_time,
                'device': wb_dev,
                'cont': wb_cont,
                'pic': imgs
            }
            # 是否为转发
            wb_expand = pic.find('div', {'class': 'WB_feed_expand'})
            if wb_expand:  # 如果存在则为转发
                wb_sta = u'转发'
                wb_info['tag'] = wb_sta
                # 原作者信息
                raw_author_info = wb_expand.find('div', {'class': 'WB_info'})
                raw_author_info = raw_author_info.find('a') if raw_author_info else None
                raw_author_name = raw_author_info.get('title', u'无') if raw_author_info else u'无'
                raw_author_link = raw_author_info.get('href', u'无') if raw_author_info else u'无'
                # 原微博内容
                raw_wb_text = wb_expand.find('div', {'class': 'WB_text'})
                raw_wb_cont = u'无'
                try:
                    raw_conts = []
                    for raw_cont in raw_wb_text.stripped_strings:
                        raw_conts.append(raw_cont.replace('rn', '').strip())
                    raw_wb_cont = ''.join(raw_conts)
                except Exception:
                    pass
                # 保存原微博信息
                wb_raw = {
                    'author_name': raw_author_name,
                    'author_link': 'https://weibo.com' + raw_author_link,
                    'wb_cont': raw_wb_cont
                }
                wb_info['wb_raw'] = wb_raw
            print u'微博信息:' + str(wb_info)
            wb_q.put_nowait(wb_info)
            mids.add(mid)
        return mid

