#!/usr/bin/env python3

from pytion import Notion
from pytion.models import Page

import click
import os


@click.command()
@click.option("--page-id", nargs=1, default="", required=False, type=str, help="Page ID.")
def wc(page_id: str):
    "Print newline, word, and byte counts for Notion."
    no: Notion = Notion(token=os.environ["NOTION_TOKEN"])
    page: Page = no.pages.get(page_id)
    doc: str = page.get_block_children().obj.__str__()
    line: int = doc.count("\n")
    word: int = len(doc)
    byte: int = len(doc.encode("utf-8"))
    print(f"{line}\t{word}\t{byte}\t{page_id}")
