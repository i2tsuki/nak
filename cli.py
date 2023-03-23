#!/usr/bin/env python3

import click
from add import add


@click.group()
def cli():
    pass


cli.add_command(add)

if __name__ == "__main__":
    cli()
