# -*- coding:utf-8 -*-
__author__ = '9527'
from urllib import unquote
from bs4 import BeautifulSoup


class MusicParser(object):
    def parse(self, html, wb_q, mids, uid):
        if not html: return
        soup = BeautifulSoup(html, 'html.parser')
        musics = soup.find_all('div', {'action-type': 'feed_list_item'})
        # print 'size:' + str(len(musics))
        if not musics: return
        for music in musics:
            # print music
            wb_info = {}
            mid = music.get('mid', u'')  # 微博id
            if mid in mids:
                if musics.index(music) < len(musics)-1:
                    continue
                return mid
            # 获取发布者信息
            author_info = music.find('div', {'class': 'WB_info'}).find('a')
            author_name = author_info.get('title', u'无')
            author_link = author_info.get('href', u'无')
            # 获取发布时间及发布设备
            wb_from = music.find('div', {'class': 'WB_from S_txt2'})
            wb_from = wb_from.find_all('a') if wb_from else None
            wb_time = u'无'
            wb_dev = u'无'
            if wb_from and len(wb_from) == 2:
                wb_time = wb_from[0].get('title')
                wb_dev = wb_from[1].string
            # 获取微博内容
            wb_text = music.find('div', {'node-type': 'feed_list_content'})
            wb_cont = u'无'
            if wb_text and wb_text.stripped_strings:
                wb_music = {}
                # 获取音乐地址
                urls = wb_text.find_all('a', {'action-type': 'feed_list_url'})
                for url in urls:
                    try:
                        if url.find('i').string == 'K':
                            wb_music['name'] = url.get('title', '')  # 音乐名
                            wb_music['href'] = url.get('href', '')  # 音乐地址
                            wb_info['music'] = wb_music
                            break
                    except: pass
                # 获取微博文字内容
                conts = []
                try:
                    for cont in wb_text.stripped_strings:
                        conts.append(cont.replace('rn', '').strip())
                except StopIteration:
                    pass
                wb_cont = ''.join(conts).strip()
            # 获取微博中图片
            imgs = music.find('ul', {'node-type': 'fl_pic_list'})
            imgs = imgs.find_all('li') if imgs else None
            if imgs:
                imgs_list = []
                for img in imgs:
                    img_src = img.find('img').get('src')
                    imgs_list.append('http:'+img_src)
                wb_info['img'] = imgs_list
            wb_sta = u'原创'
            # 保存微博信息
            wb_info.update({
                '_id': mid,
                'uid': uid,
                'tag': 'music',
                'sta': wb_sta,
                'author_name': author_name,
                'author_link': 'https://weibo.com'+author_link,
                'time': wb_time,
                'device': wb_dev,
                'cont': wb_cont
            })
            # 是否为转发
            wb_expand = music.find('div', {'class': 'WB_feed_expand'})
            if wb_expand:  # 如果存在则为转发
                wb_sta = u'转发'
                wb_info['sta'] = wb_sta
                # 原作者信息
                raw_author_info = wb_expand.find('div', {'class': 'WB_info'})
                raw_author_info = raw_author_info.find('a') if raw_author_info else None
                raw_author_name = raw_author_info.get('title', u'无') if raw_author_info else u'无'
                raw_author_link = raw_author_info.get('href', u'无') if raw_author_info else u'无'
                # 原微博内容
                raw_wb_text = wb_expand.find('div', {'node-type': 'feed_list_reason'})
                raw_wb_cont = u'无'
                try:
                    raw_conts = []
                    for raw_cont in raw_wb_text.stripped_strings:
                        raw_conts.append(raw_cont.replace('rn', '').strip())
                    raw_wb_cont = ''.join(raw_conts)
                except Exception, e:
                    pass
                # 保存原微博信息
                wb_raw = {
                    'author_name': raw_author_name,
                    'author_link': 'https://weibo.com'+raw_author_link,
                    'wb_cont': raw_wb_cont
                }
                wb_info['wb_raw'] = wb_raw
            print u'微博信息:' + str(wb_info)
            wb_q.put_nowait(wb_info)
            mids.add(mid)
        return mid