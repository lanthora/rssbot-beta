from rssmodule import RSS, RSSItem
if __name__ == "__main__":
    import feedparser
    rss = RSS()
    url = 'https://rsshub.app/github/stars/nierunjie/rssbot-beta'
    d = feedparser.parse(url)
    rss.title = d.feed.title
    rss.url = d.feed.title_detail.base
    _name = d.entries[0].title
    _link = d.entries[0].link
    rss.mark = RSSItem(name=_name, link=_link).get_mark()
    print(rss.mark)
