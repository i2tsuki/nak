#!/usr/bin/env python3

import click
from pytion import setup_logging

from add import add


@click.group()
@click.option(
    "--debug/--no-debug", is_flag=True, default=False, help="Output verbose logs for debugging."
)
def cli(debug):
    if debug:
        setup_logging(level="debug", to_console=True, filename="pytion.log")


cli.add_command(add)

if __name__ == "__main__":
    cli()
