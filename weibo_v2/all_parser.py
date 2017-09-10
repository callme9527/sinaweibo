# -*- coding:utf-8 -*-
__author__ = '9527'
from bs4 import BeautifulSoup
from urllib import unquote


class AllParser(object):
    def parse(self, html, wb_q, mids, uid):
        if not html: return
        soup = BeautifulSoup(html, 'html.parser')
        wbs = soup.find_all('div', {'action-type': 'feed_list_item'})
        # print 'size:' + str(len(wbs))
        if not wbs: return
        for wb in wbs:
            wb_info = {}
            wb_info['tag'] = u'待定'
            mid = wb.get('mid', u'')  # 微博id
            if mid in mids:
                if wbs.index(wb) < len(wbs)-1:
                    continue
                return mid
            # 获取发布者信息
            author_info = wb.find('div', {'class': 'WB_info'}).find('a')
            author_name = author_info.get('title', u'无')
            author_link = author_info.get('href', u'无')
            # 获取发布时间及发布设备
            wb_from = wb.find('div', {'class': 'WB_from S_txt2'})
            wb_from = wb_from.find_all('a') if wb_from else None
            wb_time = u'无'
            wb_dev = u'无'
            if wb_from and len(wb_from) == 2:
                wb_time = wb_from[0].get('title')
                wb_dev = wb_from[1].string
            # 获取微博内容
            wb_text = wb.find('div', {'node-type': 'feed_list_content'})
            wb_cont = u'无'
            if wb_text and wb_text.stripped_strings:
                wb_music = {}
                # 包含音乐
                urls = wb_text.find_all('a', {'action-type': 'feed_list_url'})
                for url in urls:
                    try:
                        if url.find('i').string == 'K':
                            wb_music['name'] = url.get('title', '')  # 音乐名
                            wb_music['href'] = url.get('href', '')  # 音乐地址
                            wb_info['music'] = wb_music
                            wb['tag'] = 'music'
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
            # 微博中多个图片情况
            imgs = wb.find('ul', {'node-type': 'fl_pic_list'})
            imgs = imgs.find_all('li') if imgs else None
            if imgs:
                imgs_list = []
                for img in imgs:
                    img_src = img.find('img').get('src')
                    imgs_list.append('http:'+img_src)
                wb_info['img'] = imgs_list
                wb_info['tag'] = 'pic'
            # 微博只有单张图片情况
            img = wb.find('li', {'action-type': 'feed_list_media_img'})
            img_src = img.find('img').get('src', '') if img else ''
            if img_src:
                wb_info['img'] = 'http:'+img_src
                wb_info['tag'] = 'pic'
            # 微博中有视频时
            video = wb.find('li', {'node-type': "fl_h5_video"})
            video = video.get('action-data', '') if video else None
            if video:
                for item in video.split('&'):
                    if 'video_src' in item:
                        video_src = 'http:' + unquote(item.split('=', 1)[-1])
                        wb_info['video'] = video_src
                        wb_info['tag'] = 'video'
                        break
            # 微博有文章时
            wb_media = wb.find('div', {'class': 'media_box'})
            article_soup = wb_media.find('div', {'action-type': 'widget_articleLayer'}) if wb_media else None
            wb_article = article_soup.get('action-data', '') if article_soup else ''
            item = wb_article.split('=', 1)[-1] if wb_article else ''
            article_src = 'http:'+unquote(item) if item else u''
            # 文章的介绍
            article_cont_soup = article_soup.find('div', {'class': 'WB_feed_spec_cont'}) if article_soup else None
            if article_cont_soup:
                conts = []
                try:
                    for cont in article_cont_soup.stripped_strings:
                        conts.append(cont.replace('rn', '').strip())
                    article_cont = ''.join(conts)
                    wb_info['article'] = {
                        'cont': article_cont,
                        'src': article_src
                    }
                    wb_info['tag'] = 'article'
                except: pass

            wb_sta = u'原创'
            # 保存微博信息
            wb_info.update({
                '_id': mid,
                'uid': uid,
                'sta': wb_sta,
                'author_name': author_name,
                'author_link': 'https://weibo.com'+author_link,
                'time': wb_time,
                'device': wb_dev,
                'cont': wb_cont
            })
            # 是否为转发
            wb_expand = wb.find('div', {'class': 'WB_feed_expand'})
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
                except: pass
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