#!/usr/bin/env python3

import json
import os


class Marker:
    file: str = ""
    obj = {}

    def __init__(self, file="marker.json"):
        self.file = file
        if not os.path.exists(file):
            with open(file=file, mode="w") as f:
                f.writelines("{}")
        with open(file=self.file, mode="r") as f:
            self.obj = json.load(f)

    def update(self):
        with open(file=self.file, mode="w") as f:
            json.dump(obj=self.obj, fp=f)
