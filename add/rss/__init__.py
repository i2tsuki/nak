#!/usr/bin/env python3

from .feed import Item  # noqa
from .marker import Marker

from lxml import etree
from pytion import Notion
from pytion.models import Block, Page, RichTextArray, LinkTo
import click

from typing import Dict, List, Iterable, Iterator, Union
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
    ago: int = 0,
) -> Union[str, List[Item]]:
    articles: List[Item] = []

    start: datetime = datetime.combine(date.today(), datetime.min.time()) - timedelta(days=ago)

    for channel in tree:
        if channel.tag == "channel":
            if (title_element := list(filter(lambda x: (x.tag == "title"), channel))) != []:
                title: str = title_element[0].text or ""
            else:
                sys.stderr.write("invalid rss format\n")
                sys.exit(1)
            items: Iterator = filter(lambda x: (x.tag == "item"), channel)
            for item in items:
                i: Item = Item(item)
                if i.pubdate.timestamp() > start.timestamp() and (i.title not in marker.obj[title]):
                    articles.append(i)
        else:
            sys.stderr.write("invalid rss format\n")
            sys.exit(1)

    return title, articles


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
@click.option(
    "--no-catch-up",
    is_flag=True,
    default=False,
    required=False,
    type=bool,
    help="Do not show catch-up images."
)
@click.option(
    "--items",
    nargs=1,
    default=20,
    required=False,
    type=int,
    help="Number of the output items."
)
def rss(select, from_days, no_mixed, no_catch_up):
    """Add RSS Feed content to Notion."""
    now: datetime = datetime.now()
    marker = Marker(file="marker.json")

    target: Target = Target()

    no: Notion = Notion(token=os.environ["NOTION_TOKEN"])
    page: Page = no.pages.get(target.page_id)

    articles: List[Item] = []
    target.select(channel_title=select)

    for feed in target.rss:
        resp: requests.Response = requests.get(url=target.rss[feed])
        tree: Iterable[etree._Element] = etree.fromstring(resp.content)
        title, rss_articles = get_rss_articles(tree=tree, marker=marker, ago=from_days)
        for article in rss_articles:
            article.metadata = {"feed_title": title}
        articles.extend(
            sorted(
                rss_articles,
                key=lambda x: x.pubdate,
            )
        )
    if not no_mixed:        
        articles = sorted(articles, key=lambda x: x.pubdate)           

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

    for item in articles:
        print(f"[{item.title}]({item.link})")
        print(item.description)
        if item.media and item.media.contenttype.startswith("image"):
            print(f"([{item.media.contenturl}]{item.media.contenturl})")

        if not no_catch_up and item.media and item.media.contenttype.startswith("image"):
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

        # Mark an item in Marker
        # When a title is not include in the `marker.obj` dict
        if title not in marker.obj:
            marker.obj[item.metadata["feed_title"]] = {}
        marker.obj[item.metadata["feed_title"]][item.title] = {}

    page.block_append(blocks=blocks)

    marker.update()
