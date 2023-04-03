#!/usr/bin/env python3

from .feed import Item  # noqa
from .marker import Marker

from lxml import etree
from pytion import Notion
from pytion.models import Block, Page, RichTextArray, LinkTo
import click

from typing import Dict, List, Iterable, Iterator
from datetime import date, datetime, timedelta
import json
import os
import requests
import sys


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

@click.command()
@click.option("--select", nargs=1, default="", required=False, type=str, help="Select RSS Feed.")
# Parameter for output since how many day ago
@click.option(
    "--from-days",
    nargs=1,
    default=3,
    required=False,
    type=int,
    help="Output since how many days ago.",
)
# Not mix each RSS feed or not
@click.option(
    "--no-mixed",
    is_flag=True,
    default=False,
    required=False,
    type=bool,
    help="Do not mix articles for each RSS feed.",
)
def rss(select, from_days, no_mixed):
    """Add RSS Feed content to Notion."""
    now: datetime = datetime.now()
    marker = Marker(file="marker.json")

    target: Target = Target()

    no: Notion = Notion(token=os.environ["NOTION_TOKEN"])
    page: Page = no.pages.get(target.page_id)

    rss_articles: List[Item] = []
    target.select(channel_title=select)

    for feed in target.rss:
        resp: requests.Response = requests.get(url=target.rss[feed])
        tree: Iterable[etree._Element] = etree.fromstring(resp.content)
        articles: List[Item] = get_rss_articles(tree=tree, marker=marker, ago=from_days)
        rss_articles.extend(articles)

    if not no_mixed:
        rss_articles = sorted(rss_articles, key=lambda x: x.pubdate)

    print(f"Last updated: {now:%Y-%m-%d %H:%M:%S}")
    blocks: List[Block] = []
    blocks.extend(
        [
            Block.create(
                RichTextArray(
                    [{"type": "plain_text", "plain_text": f"Last updated: {now:%Y-%m-%d %H:%M:%S}"}]
                )
            )
        ]
    )

    for item in rss_articles:
        print(f"[{item.title}]({item.link})")
        print(item.description)
        if item.media and item.media.contenttype.startswith("image"):
            print(f"([{item.media.contenturl}]{item.media.contenturl})")

        if item.media and item.media.contenttype.startswith("image"):
            b: Block = Block(
                type="image",
                parent=LinkTo(),
                image={
                    "caption": [
                        {
                            "type": "text",
                            "text": {"content": item.title, "link": {"url": item.link}},
                            "plain_text": item.title,
                            "href": item.link,
                        }
                    ],
                    "type": "external",
                    "external": {"url": item.media.contenturl},
                },
            )
            blocks.extend(
                [
                    b,
                    Block.create(
                        RichTextArray([{"type": "plain_text", "plain_text": item.description}])
                    ),
                ]
            )
        else:
            array: List[Dict[str, str]] = [
                {"type": "plain_text", "plain_text": item.title, "href": item.link},
                {"type": "plain_text", "plain_text": "\n"},
                {"type": "plain_text", "plain_text": item.description},
            ]
            blocks.extend([Block.create(RichTextArray(array))])
    page.block_append(blocks=blocks)

    marker.update()
