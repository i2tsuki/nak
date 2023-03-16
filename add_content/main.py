#!/usr/bin/env python3

from rss import Item
from marker import Marker

from lxml import etree
from pytion import Notion
from pytion.models import Page, Block, RichText, RichTextArray

from typing import Dict, List, Iterator, Iterable
from datetime import date, datetime, timedelta
import argparse
import json
import os
import requests
import sys


# Override RichText.get()
def rich_text_get(self):
    """
    Text type supported only
    """
    href = None
    link = None
    if self.href:
        link = {"url": self.href}
        href = self.href
    return {
        "type": "text",
        "text": {"content": self.plain_text, "link": link},
        # "annotations": self.annotations,
        # "plain_text": self.plain_text,
        "href": href,
    }


RichText.get = rich_text_get


# Target class represents the media lists that this script scrapes.
class Target:
    rss: Dict[str, str] = {}

    def __init__(self, file="target.json"):
        with open(file=file, mode="r") as f:
            target = json.load(f)
            self.rss: Dict[str, str] = target["RSS Feed"]
            self.page_id: str = target["Notion"]["Page ID"]

    def select(self, channel_title=""):
        if channel_title != "":
            self.rss = {channel_title: self.rss[channel_title]}


def get_rss_articles(
    tree: Iterable[etree._Element] = iter([]),
    marker: Marker = Marker(),
    ago: int = 3,
) -> List[Item]:
    articles: List[Item] = []

    start: datetime = datetime.combine(date.today(), datetime.min.time()) - timedelta(days=ago)

    for channel in tree:
        if channel.tag == "channel":
            if (title_element := list(filter(lambda x: (x.tag == "title"), channel))) != []:
                title: str = title_element[0].text or ""
                # When a title is not include in the `marker.obj` dict
                if title not in marker.obj:
                    marker.obj[title] = {}
            else:
                sys.stderr.write("invalid rss format\n")
                sys.exit(1)
            items: Iterator = filter(lambda x: (x.tag == "item"), channel)
            for item in items:
                i: Item = Item(item)
                if i.pubdate.timestamp() > start.timestamp() and (i.title not in marker.obj[title]):
                    marker.obj[title][i.title] = {}
                    articles.append(i)
        else:
            sys.stderr.write("invalid rss format\n")
            sys.exit(1)

    return articles


def parse_args() -> argparse.Namespace:
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
    args.from_days = int(args.from_days[0])
    return args


def main():
    now: datetime.Datetime = datetime.now()
    marker = Marker(file="marker.json")
    
    args: argparse.Namespace = parse_args()
    target: Target = Target()

    no: Notion = Notion(token=os.environ["NOTION_TOKEN"])
    page: Page = no.pages.get(target.page_id)

    rss_articles: List[Item] = []
    target.select(channel_title=args.select[0])

    for feed in target.rss:
        resp: requests.Response = requests.get(url=target.rss[feed])
        tree: Iterable[etree._Element] = etree.fromstring(resp.content)
        articles: List[Item] = get_rss_articles(
            tree=tree, marker=marker, ago=args.from_days
        )
        rss_articles.extend(articles)

    no_mixed: bool = False
    if not no_mixed:
        rss_articles = sorted(rss_articles, key=lambda x: x.pubdate)

    print(f"Last updated: {now:%Y-%m-%d %H:%M:%S}")
    page.block_append(
        block=Block.create(
            RichTextArray(
                [{"type": "plain_text", "plain_text": f"Last updated: {now:%Y-%m-%d %H:%M:%S}"}]
            )
        )
    )

    blocks: List[Block] = []
    for item in rss_articles:
        print(f"[{item.title}]({item.link})")
        print(item.description)
        array: List[Dict[str, str]] = [
            {"type": "plain_text", "plain_text": item.title, "href": item.link},
            {"type": "plain_text", "plain_text": "\n"},
            {"type": "plain_text", "plain_text": item.description},
        ]
        blocks.extend([Block.create(RichTextArray(array))])
    page.block_append(blocks=blocks)

    marker.update()

if __name__ == "__main__":
    main()
