# -*- coding:utf-8 -*-
__author__ = '9527'
from urllib import unquote
from bs4 import BeautifulSoup


class ArticleParser(object):
    def parse(self, html, wb_q, mids, uid):
        if not html: return
        soup = BeautifulSoup(html, 'lxml')
        articles = soup.find_all('div', {'action-type': 'feed_list_item'})
        # print 'size:' + str(len(articles))
        if not articles: return
        for article in articles:
            # print article
            mid = article.get('mid', u'')  # 微博id
            if mid in mids:
                if articles.index(article) < len(articles)-1:
                    continue
                return mid
            # 获取发布者信息
            author_info = article.find('div', {'class': 'WB_info'}).find('a')
            author_name = author_info.get('title', u'无')
            author_link = author_info.get('href', u'无')
            # 获取发布时间及发布设备
            wb_from = article.find('div', {'class': 'WB_from S_txt2'})
            wb_from = wb_from.find_all('a') if wb_from else None
            wb_time = u'无'
            wb_dev = u'无'
            if wb_from and len(wb_from) == 2:
                wb_time = wb_from[0].get('title')
                wb_dev = wb_from[1].string
            # 获取微博内容
            wb_text = article.find('div', {'node-type': 'feed_list_content'})
            wb_cont = u'无'
            if wb_text and wb_text.stripped_strings:
                # print wb_text.stripped_strings
                conts = []
                try:
                    for cont in wb_text.stripped_strings:
                        conts.append(cont.replace('rn', '').strip())
                except StopIteration: pass
                wb_cont = ''.join(conts)
            # 微博的文章地址
            article_media = article.find('div', {'class': 'media_box'})
            wb_article_soup = article_media.find('div', {'action-type': 'widget_articleLayer'}) if article_media else None
            wb_article = wb_article_soup.get('action-data', '') if wb_article_soup else ''
            item = wb_article.split('=', 1)[1] if wb_article else ''
            article_src = 'http:'+unquote(item) if item else u'无'
            #  文章的介绍
            article_cont_soup = wb_article_soup.find('div', {'class': 'WB_feed_spec_cont'}) if wb_article_soup else None
            article_cont = u'无'
            if article_cont_soup:
                conts = []
                try:
                    for cont in article_cont_soup.stripped_strings:
                        conts.append(cont.replace('rn', '').strip())
                    article_cont = ''.join(conts)
                except: pass
            wb_sta = u'原创'
            # 保存微博信息
            wb_info = {
                '_id': mid,
                'uid': uid,
                'tag': 'article',
                'sta': wb_sta,
                'author_name': author_name,
                'author_link': 'https://weibo.com'+author_link,
                'time': wb_time,
                'device': wb_dev,
                'cont': wb_cont,
                'article': article_src,
                'article_cont': article_cont
            }
            # 是否为转发
            wb_expand = article.find('div', {'class': 'WB_feed_expand'})
            if wb_expand:  # 如果存在则为转发
                wb_sta = u'转发'
                wb_info['sta'] = wb_sta
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
        