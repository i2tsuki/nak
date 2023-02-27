#!/usr/bin/env python3

from rss import Item
from marker import Marker

from lxml import etree

from typing import Dict, List, Iterator, Iterable
from datetime import date, datetime, timedelta
import argparse
import json
import requests
import sys


# Target class represents the media lists that this script scrapes.
class Target:
    rss: Dict[str, str] = {}

    def __init__(self, file="target.json"):
        with open(file=file, mode="r") as f:
            self.rss = json.load(f)


def get_rss_articles(
    tree: Iterable[etree._Element] = None, marker: Marker = None, ago: int = 3
) -> List[Item]:
    articles: List[Item] = []

    start: datetime = datetime.combine(date.today(), datetime.min.time()) - timedelta(
        days=ago
    )

    for channel in tree:
        if channel.tag == "channel":
            if (
                title_element := list(filter(lambda x: (x.tag == "title"), channel))
            ) != []:
                title: str = title_element[0].text
                # When a title is not include in the `marker.obj` dict
                if title not in marker.obj:
                    marker.obj[title] = {}
            else:
                sys.stderr.write("invalid rss format\n")
                sys.exit(1)
            items: Iterator = filter(lambda x: (x.tag == "item"), channel)
            for item in items:
                i: Item = Item(item)
                if i.pubdate.timestamp() > start.timestamp() and (
                    i.title not in marker.obj[title]
                ):
                    marker.obj[title][i.title] = {}
                    articles.append(i)
        else:
            sys.stderr.write("invalid rss format\n")
            sys.exit(1)

    marker.update()
    return articles


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="rssnotion",
        description="Add RSS Feed content to Notion.",
    )
    parser.add_argument(
        "--select",
        action="store",
        dest="select",
        help="RSS feed selector",
        metavar="--select",
        nargs=1,
        required=False,
        default=[""],
    )
    # Parameter for output since how many day ago
    parser.add_argument(
        "--from-days",
        action="store",
        dest="from_days",
        help="Output since how many days ago",
        metavar="--from-days",
        nargs=1,
        required=False,
        default=[3],
    )
    args: argparse.Namespace = parser.parse_args()
    args.from_days: int = int(args.from_days[0])

    marker: Marker = Marker(file="marker.json")

    target = Target()
    if args.select[0] == "":
        for feed in target.rss:
            url: str = target.rss[feed]
            resp: requests.Response = requests.get(url=url)
            tree: Iterable[etree._Element] = etree.fromstring(resp.content)
            articles: List[Item] = get_rss_articles(
                tree=tree, marker=marker, ago=args.from_days
            )
            for item in articles:
                print(f"[{item.title}]({item.link})")
                print(item.description)

    else:
        url: str = target.rss[args.select[0]]
        resp: requests.Response = requests.get(url=url)
        tree: Iterable[etree._Element] = etree.fromstring(resp.content)
        get_rss_articles(tree=tree, marker=marker, ago=args.from_days)
        articles: List[Item] = get_rss_articles(
            tree=tree, marker=marker, ago=args.from_days
        )
        for item in articles:
            print(f"[{item.title}]({item.link})")
            print(item.description)
