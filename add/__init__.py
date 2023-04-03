#!/usr/bin/env python3

from .rss import rss

from pytion.models import Block, RichText, RichTextArray

import click

from typing import Any, Dict


# Override RichText.get()
def rich_text_get(self) -> Dict[str, Any]:
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
        "plain_text": self.plain_text,
        "href": href,
    }


RichText.get = rich_text_get


# Override Block.get()
def block_get(self, with_object_type: bool = False):  # noqa
    if self.type in [
        "paragraph",
        "quote",
        "heading_1",
        "heading_2",
        "heading_3",
        "to_do",
        "bulleted_list_item",
        "numbered_list_item",
        "toggle",
        "callout",
        "code",
        "child_database",
    ]:

        text = RichTextArray.create(self.text) if isinstance(self.text, str) else self.text

        # base content
        new_dict: Dict[str, Any] = {self.type: {"rich_text": text.get()}}

        # to_do type attrs
        if self.type == "to_do" and hasattr(self, "checked"):
            new_dict[self.type]["checked"] = self.checked

        # code type attrs
        elif self.type == "code":
            new_dict[self.type]["language"] = getattr(self, "language", "plain text")
            if hasattr(self, "caption"):
                new_dict[self.type]["caption"] = self.caption.get()

        # child_database type struct
        elif self.type == "child_database":
            new_dict = {self.type: {"title": str(text)}}

        # heading_X types attrs
        elif "heading" in self.type:
            if hasattr(self, "is_toggleable") and isinstance(self.is_toggleable, bool):
                new_dict[self.type]["is_toggleable"] = self.is_toggleable
            else:
                new_dict[self.type]["is_toggleable"] = False

        if with_object_type:
            new_dict["object"] = "block"
            new_dict["type"] = self.type
        return new_dict

    if self.type in ["image"]:
        if self.raw.get("parent"):
            self.raw.pop("parent")
        return self.raw
    return None


Block.get = block_get


@click.group()
def add():
    pass


add.add_command(rss)
