#!/usr/bin/env python3

import json
import requests


# Target class represents the media lists that this script scrapes.
class Target:
    rss = {}

    def __init__(self, file="target.json"):
        with open(file=file, mode="r") as f:
            self.target = json.load(f)


if __name__ == "__main__":
    target = Target()
    for url in Target.rss.values():
        r = requests.get(url=url)
