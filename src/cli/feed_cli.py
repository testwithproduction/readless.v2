#!/usr/bin/env python3

import sys
from pathlib import Path
import click

sys.path.append(str(Path(__file__).parent.parent))

from cli.feed_commands import feed
from cli.category_commands import category


@click.group()
def cli():
    """ReadLess CLI - RSS Feed Manager"""
    pass


cli.add_command(feed)
cli.add_command(category)

if __name__ == "__main__":
    cli()
