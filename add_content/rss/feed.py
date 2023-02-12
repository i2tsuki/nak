#!/usr/bin/env python3

from datetime import datetime


class Item:
    title = ""
    link = ""
    description = ""
    guid = ""
    pubdate = datetime.fromtimestamp(0)

    def __init__(self, item):
        self.title = list(filter(lambda x: (x.tag == "title"), item))[0].text
        self.link = list(filter(lambda x: (x.tag == "link"), item))[0].text
        self.description = list(filter(lambda x: (x.tag == "description"), item))[
            0
        ].text
        self.guid = list(filter(lambda x: (x.tag == "description"), item))[0].text
        self.pubdate = datetime.strptime(
            list(filter(lambda x: (x.tag == "pubDate"), item))[0].text,
            "%a, %d %b %Y %H:%M:%S %z",
        )
