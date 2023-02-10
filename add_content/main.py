#!/usr/bin/env python3

from lxml import etree

from datetime import datetime
import json
import requests
import sys


# Target class represents the media lists that this script scrapes.
class Target:
    rss = {}

    def __init__(self, file="target.json"):
        with open(file=file, mode="r") as f:
            self.rss = json.load(f)


class Item:
    title = ""
    link = ""
    description = ""
    guid = ""
    pubdate = datetime.fromtimestamp(0)

    def __init__(self, item):
        self.title = list(filter(lambda x: (x.tag == "title"), item))[0].text
        self.link = list(filter(lambda x: (x.tag == "link"), item))[0].text
        self.description = list(filter(lambda x: (x.tag == "description"), item))[0].text
        self.guid = list(filter(lambda x: (x.tag == "description"), item))[0].text
        self.pubdate = list(filter(lambda x: (x.tag == "pubDate"), item))[0].text


if __name__ == "__main__":
    target = Target()
    for url in target.rss.values():
        rssitems = []
        resp = requests.get(url=url)
        tree = etree.fromstring(resp.content)
        for channel in tree:
            if channel.tag == "channel":
                items = filter(lambda x: (x.tag == "item"), channel)
                for item in items:
                    rssitems.append(Item(item))
            else:
                sys.stderr.write("invalid rss format\n")
        for item in rssitems:
            print(f"### {item.title}")
            print(item.description)
