#!/usr/bin/env python3

from datetime import datetime


class Item:
    title = ""
    link = ""
    description = ""
    guid = ""
    pubdate = datetime.fromtimestamp(0)
    media = None

    def __init__(self, item, mediatag=""):
        self.title = "" if (x := list(filter(lambda x: (x.tag == "title"), item))) == [] else x[0].text  # fmt: skip
        self.link = "" if (x := list(filter(lambda x: (x.tag == "link"), item))) == [] else x[0].text  # fmt: skip
        self.description = "" if (x := list(filter(lambda x: (x.tag == "description"), item))) == [] else x[0].text  # fmt: skip
        self.guid = "" if (x := list(filter(lambda x: (x.tag == "guid"), item))) == [] else x[0].text  # fmt: skip
        self.pubdate = datetime.strptime(
            list(filter(lambda x: (x.tag == "pubDate"), item))[0].text,
            "%a, %d %b %Y %H:%M:%S %z",
        )
        self.media = None if (x := list(filter(lambda x: (x.tag == mediatag), item))) == [] else Media(x[0])  # fmt: skip


class Media:
    contenturl = ""
    contenttype = ""
    contentmedium = ""
    descriptiontype = ""
    copyright = ""

    def __init__(self, media):
        self.contenturl = media.get(key="url")
        self.contenttype = media.get(key="type")
        self.contentmedium = media.get(key="medium")
