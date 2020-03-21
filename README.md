# RSSBot-beta

## 样例

[Telgram RSS Bot](https://t.me/BRSSBot)

## 特性

- [ ] 标题正则表达式匹配推送机制
- [x] 控制订阅数量:管理员可以设置机器人的开放程度，防止恶意使用，必要情况下可以设置非管理员不可使用
- [x] 重命名标题:有些RSS的标题显示不友好，可自定义名称
- [x] 添加状态标记:使用▫️和▪进行标记，多次获取内容失败自动设置为不活跃，(任意用户)再次订阅并通过状态检查后重新推送
- [x] 负载均衡:请求均匀分布，避免在某一时刻出现大量网络请求的情况

## 特别说明

如果刷新时，某个订阅中的内容完全发生了改变，内容上无法与上次的刷新结果匹配，则认为此次异常，不进行推送操作。
出现这种现象可能的情况是，该订阅内容更新的频率过高。可以缩短BOT默认的刷新间隔尝试解决这个问题。
可在INFO级别的rss.log中查看是否出现上述情况。


## 命令

```html
<!--订阅--> 

/sub https://www.solidot.org/index.rss

已订阅: 最新更新 – Solidot

<!--显示所有订阅--> 

/rss

你的订阅:  
▫️最新更新 – Solidot

<!--重命名--> 

/rename https://www.solidot.org/index.rss Solidot

别名已更新为: Solidot

<!--退订--> 

/unsub https://www.solidot.org/index.rss

已退订: 最新更新 – Solidot

```

## 配置

在项目根目录创建名为`conf.ini`的文件，并填入以下配置

```ini
[default]
# 从BotFather获取的token
token=your-token

# 同一个RSS刷新时间间隔，单位为秒。RSS的刷新平均分布到这段时间间隔中。例如，存在两个订阅，则分别在0时刻和150时刻刷新
freq=300

# RSS源可能出现不可获取的情况，连续多次不可获取后，暂停该RSS的推送，并提醒订阅者检查该RSS，此处设置的是最多允许连续出错的次数
errorlimit=60

# /start 的回复内容
startmsg=<a href="https://github.com/lanthora/rssbot-beta/blob/master/README.md">README</a>

# 管理员，用于权限控制，值为username
admin=lanthora

# 非管理员可订阅的数量，设置为0则仅管理员可用
sublimit=10

# 日志级别，ERROR/非ERROR
loglevel=ERROR
```


