# RSSBot-beta

![asd](docs/rssbot.svg)

## Command

|CMD|Description|
|:-|:-|
|sub url|Subscribe to an RSS feed|
|unsub url|Unsubscribe from an RSS|
|rss|Show your subscribed RSS|


## Configuration

```ini
[default]
# Token obtained from BotFather
token=your-token
# Update interval in seconds
freq=300
# Error limit, over it will trigger error handling
errorlimit=60
# Click "Start" to display the content, support html
startmsg=<a href="https://github.com/nierunjie/rssbot-beta">README</a>
# Administrator id, your telegram username
admin=lanthora
# The number of non-administrators can subscribe
sublimit=10
# Database related parameters
dbname=rss.db
sqlfile=rss.sql
```
