#!/usr/bin/env python3

from datetime import datetime
from typing import Optional


class Media:
    contenturl: str = ""
    contenttype: str = ""
    contentmedium: str = ""
    descriptiontype: str = ""
    copyright: str = ""

    def __init__(self, media):
        self.contenturl: str = media.get(key="url")
        self.contenttype: str = media.get(key="type")
        self.contentmedium: str = media.get(key="medium")


class Item:
    title: str = ""
    link: str = ""
    description: str = ""
    guid: str = ""
    pubdate: datetime = datetime.fromtimestamp(0)
    media: Optional[Media] = None

    def __init__(self, item, mediatag=""):
        self.title: str = "" if (x := list(filter(lambda x: (x.tag == "title"), item))) == [] else x[0].text  # fmt: skip
        self.link: str = "" if (x := list(filter(lambda x: (x.tag == "link"), item))) == [] else x[0].text  # fmt: skip
        self.description: str = "" if (x := list(filter(lambda x: (x.tag == "description"), item))) == [] else x[0].text  # fmt: skip
        self.guid: str = "" if (x := list(filter(lambda x: (x.tag == "guid"), item))) == [] else x[0].text  # fmt: skip
        self.pubdate: datetime = datetime.strptime(
            list(filter(lambda x: (x.tag == "pubDate"), item))[0].text,
            "%a, %d %b %Y %H:%M:%S %z",
        )
        self.media: Optional[Media] = None if (x := list(filter(lambda x: (x.tag == mediatag), item))) == [] else Media(x[0])  # fmt: skip
