# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/10/6 16:54'

import re
import logging

from validate import Validater
from bs4 import BeautifulSoup
from urllib import unquote
from conf import *


logger = logging.getLogger('weibo')
validater = Validater()


class Parser(object):
    # 解析首页获得关注，粉丝，微博数
    @ staticmethod
    def parse_index(html):
        tds = re.findall(r'<strong.*?>(\d+)</strong><span.*?</span>', html.replace('\\', ''), re.S)
        if not tds or len(tds) != 3:
            logger.debug(u'解析关注，粉丝，微博数的方式错误.')
            return
        return [int(td) for td in tds]

    @ staticmethod
    def parse_wb(html, uid):
        if not html: return
        soup = BeautifulSoup(html, 'html.parser')
        wbs = soup.find_all('div', {'action-type': 'feed_list_item'})
        if not wbs:
            logger.debug('wb页面结构变化')
            return
        wb_list = []
        for wb in wbs:
            wb_info = {}
            wb_info['uid'] = uid
            wb_info['tag'] = u'luan_bb'
            mid = wb.get('mid', u'')  # 微博id
            if validater.validate_wb(mid):
                logger.debug(u'存在微博:'+mid)
                continue  # 存在该微博
            # 获取发布者信息
            author_info = wb.find('div', {'class': 'WB_info'}).find('a')
            author_name = author_info.string if author_info.string else u'无'
            author_link = author_info.get('href', u'无')
            # 获取发布时间及发布设备
            wb_from = wb.find('div', {'class': 'WB_from S_txt2'})
            wb_from = wb_from.find_all('a') if wb_from else None
            wb_time = u'无'
            wb_dev = u'无'
            if wb_from and len(wb_from) == 2:
                wb_time = float(wb_from[0].get('date')) / 1000
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
                    except:
                        pass
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
                    imgs_list.append('http:' + img_src)
                wb_info['img'] = imgs_list
                wb_info['tag'] = 'pic'
            # 微博只有单张图片情况
            img = wb.find('li', {'action-type': 'feed_list_media_img'})
            img_src = img.find('img').get('src', '') if img else ''
            if img_src:
                wb_info['img'] = 'http:' + img_src
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
            article_src = 'http:' + unquote(item) if item else u''
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
                except:
                    pass
            wb_sta = u'原创'
            # 保存微博信息
            wb_info.update({
                'mid': mid,
                'sta': wb_sta,
                'author_name': author_name,
                'author_link': 'https://weibo.com' + author_link,
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
                except:
                    pass
                # 保存原微博信息
                wb_raw = {
                    'author_name': raw_author_name,
                    'author_link': 'https://weibo.com' + raw_author_link,
                    'wb_cont': raw_wb_cont
                }
                wb_info['wb_raw'] = wb_raw
            print u'微博信息:' + str(wb_info)
            wb_list.append(wb_info)
        return wb_list

    @ staticmethod
    def parse_relate(html):
        try:
            urls = re.findall('<a\sclass="S_txt1".*?href="(.*?)\?refer', html.replace('\\', ''))
            return urls
        except Exception as e:
            logger.debug('in parse_relate:'+str(e))

    @ staticmethod
    def parse_info(cont):
        if not cont: return
        try:
            uid = re.search("CONFIG\['oid'\]='(.*?)'", cont).group(1)
            page_id = re.search("CONFIG\['page_id'\]='(.*?)'", cont).group(1)
            nick = re.search("CONFIG\['onick'\]='(.*?)'", cont).group(1).decode('utf-8')
            domain = re.search("CONFIG\['domain'\]='(.*?)'", cont).group(1)
            location = re.search("CONFIG\['location'\]='(.*?)'", cont).group(1)
            level = re.search("微博等级(\d+)", cont).group(1)
            nums = re.findall(r'<strong.*?>(\d+)</strong><span.*?</span>', cont.replace('\\', ''), re.S)
            if len(nums) != 3: nums = [0, 0, 0]
            info = {
                'uid': uid,
                'page_id': page_id,
                'nick': nick,
                'domain': domain,
                'location': location,
                'level': level,
                'follow_num': int(nums[0]),
                'fans_num': int(nums[1]),
                'wb_num': int(nums[2])
            }
            cont = re.search('PCD_text_b.css.*?"html":"(.*?)"}', cont, re.S)
            if cont:
                cont = cont.group(1)
                cont = cont.replace('\\t', '').replace('\\n', '').replace('\\r', '').replace('\\', '')
                soup = BeautifulSoup(cont, 'lxml')
                parts = soup.find_all('div', {'class': 'WB_cardwrap S_bg2'})
                if parts:
                    for part in parts:
                        name = part.find('div', {'class': 'obj_name'}).string
                        name = u'其他信息' if not name else name
                        options = {}
                        li_s = part.find_all('li', {'class': 'li_1 clearfix'})
                        if not li_s:
                            cont_soup = part.find('div', {'class': 'WB_innerwrap'})
                            conts = ''.join([cont for cont in cont_soup.stripped_strings])
                            options['cont'] = conts
                        else:
                            for li in li_s:
                                v = [s for s in li.stripped_strings]
                                v = ','.join(v)
                                v_a = li.find_all('a')
                                for a in v_a:
                                    a_cont = ''.join([s for s in a.stripped_strings]).strip()
                                    a_href = a.get('href')
                                    if not a_cont or not a_href: continue
                                    v = v.replace(a_cont, a_cont + '(' + a_href + ')')
                                k, v = v.split('：', 1)
                                options[k] = v.lstrip(',')
                        info[name] = options
            print u'用户信息:' + str(info)
            return info
        except Exception, e:
            logger.debug('in parse_info, except:'+ str(e))
