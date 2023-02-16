#!/usr/bin/env python3

from rss import Item

from lxml import etree

from datetime import date, datetime, timedelta
import json
import requests
import sys


# Parameter for output since how many day ago
ago = 3


# Target class represents the media lists that this script scrapes.
class Target:
    rss = {}

    def __init__(self, file="target.json"):
        with open(file=file, mode="r") as f:
            self.rss = json.load(f)


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
                sys.exit(1)
        for item in rssitems:
            now = datetime.combine(date.today(), datetime.min.time()) - timedelta(
                days=ago
            )
            if item.pubdate.timestamp() > now.timestamp():
                print(f"### [{item.title}]({item.link})")
                print(item.description)
