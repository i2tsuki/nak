#!/usr/bin/env python3

from rss import Item

from lxml import etree

from typing import Any, Dict, List, Iterator, Iterable
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


def print_rss_items(
    tree: Iterable[etree._Element] = None, marker: Dict[str, Any] = {}, ago: int = 3
) -> Dict[str, Any]:
    for channel in tree:
        if channel.tag == "channel":
            if (
                title_element := list(filter(lambda x: (x.tag == "title"), channel))
            ) != []:
                title: str = title_element[0].text
            else:
                sys.stderr.write("invalid rss format\n")
                sys.exit(1)
            items: Iterator = filter(lambda x: (x.tag == "item"), channel)
            for i in items:
                rssitems.append(Item(i))
        else:
            sys.stderr.write("invalid rss format\n")
            sys.exit(1)

    if title not in marker:
        marker[title] = {}

    for item in rssitems:
        now: datetime = datetime.combine(date.today(), datetime.min.time()) - timedelta(
            days=ago
        )
        if item.pubdate.timestamp() > now.timestamp():
            if item.title not in marker[title]:
                print(f"### [{item.title}]({item.link})")
                print(item.description)
                marker[title][item.title] = {}

    return marker


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

    with open(file="marker.json", mode="r") as f:
        marker = json.load(f)

    target = Target()
    if args.select[0] == "":
        for feed in target.rss:
            url: str = target.rss[feed]
            rssitems: List[Item] = []
            resp: requests.Response = requests.get(url=url)
            tree: Iterable[etree._Element] = etree.fromstring(resp.content)
            print_rss_items(tree=tree, marker=marker, ago=args.from_days)
    else:
        url: str = target.rss[args.select[0]]
        rssitems: List[Item] = []
        resp: requests.Response = requests.get(url=url)
        tree: Iterable[etree._Element] = etree.fromstring(resp.content)
        print_rss_items(tree=tree, marker=marker, ago=args.from_days)

    with open(file="marker.json", mode="w") as f:
        json.dump(obj=marker, fp=f)
