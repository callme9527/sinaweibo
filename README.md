# requests爬取新浪微博
多进程异步爬取新浪微博下的各项微博，目前已完成对账号下视频的爬取，以后会对图片，音乐等爬取，并完善程序。希望大家批评指导！

### 环境
**Windows** *python2.7*

### 所需库
以下库可以通过pip下载
- **requests** 请求URL并获取响应
- **bs4** 解析响应
- **gevent** 异步
- **pymongo** 操作mongo数据库

### 使用
下载压缩包解压，切换到该文件夹下，在config.py中的users中加入要爬取的账号（name为用户名，pwd为密码）,**python begin.py**即可<br/>
开始爬取，爬取期间需要自己输入验证码.

### 详情
**使用多进程加异步的方式爬取微博**<br/>
因为是爬取个人账号相应标签下（eg: 视频）的微博，所以需要登录。在cookie.py中采取异步获取cookie.<br/>
在video_spider.py中主要对视频页面进行异步下载和解析.<br/>
在video_store.py中将爬取到的视频信息保存至mongo中.<br/>

### 说明
本爬虫只是用于个人的学习，未来会加入代理ip，人工打码以及更多微博的爬取.希望大家可以多多指导改进.<br/>

---
## 更新
添加了对图片，音乐，文章以及全部等分类微博的爬取。
### 使用
**python begin.py -t 分类名（tag）**，分类名可以为：['all', 'video', 'pic', 'music', 'article', '全部', '视频', '图片', '音乐', '文章' ]
### 说明
接下来会增加ip代理，并对关注者和粉丝信息及微博进行爬取的功能！

---
## 更新至v3
多进程抓取信息和存储信息,主要模块如下:
### 1.cookie（in cookie.py）
使用gevent异步获取cookie，并加入了云打码识别验证码. 账号需在conf.py下配置,抓取结果存入mongodb。
### 2.抓取信息（in handle.py）
多线程抓取微博，用户以及待爬url信息.在各个线程中加入gevent爬取相应信息.
### 3.存储信息 (in store.py)
多线程存储微博和用户信息.
### 运行结果
![](https://github.com/callme9527/sinaweibo/tree/master/weibo_v3/pic/wb.png)
![](https://github.com/callme9527/sinaweibo/tree/master/weibo_v3/pic/wb2.png)
![](https://github.com/callme9527/sinaweibo/tree/master/weibo_v3/pic/info.png)


