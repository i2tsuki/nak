#!/usr/bin/env python3

from rss import Item

from lxml import etree

from typing import Dict, List, Iterator, Iterable
from datetime import date, datetime, timedelta
import json
import requests
import sys


# Parameter for output since how many day ago
ago: int = 3


# Target class represents the media lists that this script scrapes.
class Target:
    rss: Dict[str, str] = {}

    def __init__(self, file="target.json"):
        with open(file=file, mode="r") as f:
            self.rss = json.load(f)


if __name__ == "__main__":
    target = Target()
    for url in target.rss.values():
        rssitems: List[Item] = []
        resp: requests.Response = requests.get(url=url)
        tree: Iterable[etree._Element] = etree.fromstring(resp.content)
        for channel in tree:
            if channel.tag == "channel":
                items: Iterator = filter(lambda x: (x.tag == "item"), channel)
                for i in items:
                    rssitems.append(Item(i))
            else:
                sys.stderr.write("invalid rss format\n")
                sys.exit(1)
        for item in rssitems:
            now: datetime = datetime.combine(date.today(), datetime.min.time()) - timedelta(
                days=ago
            )
            if item.pubdate.timestamp() > now.timestamp():
                print(f"### [{item.title}]({item.link})")
                print(item.description)
