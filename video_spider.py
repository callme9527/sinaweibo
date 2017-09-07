# -*- coding:utf-8 -*-
__author__ = '9527'
# 微博的视频页面是最多10页
# 每访问一页时会加载15个视频，而后会ajax加载2次。 构造地址时的主要参数是mid即微博的ID！
import re
import sys
import json
import time
import gevent
import requests
from random import choice
from urllib import unquote
from bs4 import BeautifulSoup
from config import agents
from gevent import monkey
monkey.patch_all(thread=False)
reload(sys)
sys.setdefaultencoding('utf-8')
try:
    import cPickle as pickle
except ImportError:
    import pickle


class VideoSpider(object):
    # 解析出视频信息
    def parser(self, html, wb_q):
        if not html: return
        soup = BeautifulSoup(html, 'html.parser')
        videos = soup.find_all('div', {'action-type': 'feed_list_item'})
        # print 'size:' + str(len(videos))
        if not videos: return
        for video in videos:
            # print video
            mid = video.get('mid', u'')  # 微博id
            if mid in self.mids:
                if videos.index(video) < len(videos)-1:
                    continue
                return mid
            # 获取发布者信息
            author_info = video.find('div', {'class': 'WB_info'}).find('a')
            author_name = author_info.get('title', u'无')
            author_link = author_info.get('href', u'无')
            # 获取发布时间及发布设备
            wb_from = video.find('div', {'class': 'WB_from S_txt2'})
            wb_from = wb_from.find_all('a') if wb_from else None
            wb_time = u'无'
            wb_dev = u'无'
            if wb_from and len(wb_from) == 2:
                wb_time = wb_from[0].get('title')
                wb_dev = wb_from[1].string
            # 获取微博内容
            wb_text = video.find('div', {'node-type': 'feed_list_content'})
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
            # 微博的视频地址
            wb_video = video.find('li', {'node-type': "fl_h5_video"})
            wb_video = wb_video.get('action-data', '') if wb_video else None
            video_src = u'无'
            if wb_video:
                for item in wb_video.split('&'):
                    if 'video_src' in item:
                        video_src = 'http:' + unquote(item.split('=', 1)[1])
                        break

            wb_sta = u'原创'
            # 保存微博信息
            wb_info = {
                '_id': mid,
                'tag': wb_sta,
                'author_name': author_name,
                'author_link': author_link,
                'time': wb_time,
                'device': wb_dev,
                'cont': wb_cont,
                'video': video_src
            }
            # 是否为转发
            wb_expand = video.find('div', {'class': 'WB_feed_expand'})
            if wb_expand:  # 如果存在则为转发
                wb_sta = u'转发'
                wb_info['tag'] = wb_sta
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
                except Exception:
                    pass
                # 保存原微博信息
                wb_raw = {
                    'author_name': raw_author_name,
                    'author_link': raw_author_link,
                    'wb_cont': raw_wb_cont
                }
                wb_info['wb_raw'] = wb_raw
            print '微博信息:' + str(wb_info)
            wb_q.put_nowait(wb_info)
            self.mids.add(mid)
        return mid

    # 下载单页微博
    def download(self, headers, cookies, page_url, wb_q):
        try:
            res = requests.get(page_url, headers=headers, cookies=cookies, timeout=5)
            if res.status_code != 200: return
            #  微博视频的html在一个script中
            html = re.search('home/js/pl/content/homefeed/index.js.*?html":"(.*?)"}', res.content, re.S)
            html = html.group(1).replace('\\', '').replace('\r\n', '') if html else None
            #  得到最后一个微博的ID
            min_id = self.parser(html, wb_q)
            page_id = re.search('page=([0-9]+)', page_url, re.S).group(1)
            end_id = re.search('end_id=([0-9]+)', page_url, re.S).group(1)
            #  构造ajax__url
            ajax_url = 'http://weibo.com/aj/mblog/fsearch?ajwvr=6&pre_page=%s&page=%s&end_id=%s&min_id=%s' \
            '&is_video=1&pagebar=%d&__rnd=%d'
            #  一共有两次ajax请求
            for i in range(2):
                if not min_id: break
                rnd = int(time.time() * 1000)
                ajax_url = ajax_url % (page_id, page_id, end_id, min_id, i, rnd)
                res = requests.get(ajax_url, headers=headers, cookies=cookies, timeout=5)
                if res.status_code != 200: return
                html = dict(json.loads(res.content)).get('data', '')
                min_id = self.parser(html, wb_q)
        except:
            print u'网络不佳'

    # 异步下载全部微博
    def downloads(self, cookie_q, wb_q):
        # 将所有微博的ID保存，避免下载重复微博
        self.mids = set()
        try:
            with open('mid.txt', 'r') as f:
                for line in f:
                    self.mids.add(line.strip('\n'))
                print u'读取old_spider微博ID over.'
        except: pass

        while True:
            item = cookie_q.get()
            if item == 'end':
                wb_q.put_nowait('end')
                print u'所有cookie抓取微博完毕.'
                with open('mid.txt', 'w') as f:
                    f.write('\n'.join(list(self.mids)))
                print u'所有微博ID写入mid.txt.'
                return
            uid = item[0]  # 用户ID
            cookies = item[1]  # 用户cookies
            video_url = 'https://weibo.com/'
            if uid.isdigit():
                video_url = video_url + 'u/%s/home?is_video=1' % uid
            else:
                video_url = video_url + '%s/home?is_video=1' % uid
            # print video_url
            print u'爬取视频...'
            headers = {
                'User-Agent': choice(agents)
            }
            try:
                res = requests.get(video_url, headers=headers, cookies=cookies, verify=False)
            except Exception, e:
                print str(e)
                print u'网络状况不佳，抓取失败'
                continue
            if res.status_code != 200: continue

            mid = re.search('mid=.*?([0-9]+)', res.content).group(1)  # 第一个微博ID
            #  因为微博视频最多10页，图方便直接构造了10个greenlet，如果页面不存在直接跳过.
            greenlets = []
            for i in range(1, 11):
                page_url = video_url + '&end_id=%s&pre_page=1&page=%d&pids=Pl_Content_HomeFeed' % (mid, i)
                greenlet = gevent.spawn(self.download, headers, cookies, page_url, wb_q)
                greenlets.append(greenlet)
            gevent.joinall(greenlets)
            print '用户id为%s的微博视频已经爬取完毕.' % uid

