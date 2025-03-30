import click
import json
from core.feed_manager import FeedManager

feed_manager = FeedManager()


@click.group()
def feed():
    """Manage RSS feeds"""
    pass


@feed.command()
@click.argument("url")
def add(url):
    """Add a new RSS feed"""
    if feed_manager.add_feed(url):
        click.echo(f"Successfully added feed: {url}")
    else:
        click.echo(f"Failed to add feed: {url}")


@feed.command()
def fetch():
    """Fetch all feed entries"""
    feeds = feed_manager.get_feeds()
    if not feeds:
        click.echo("No feeds available")
        return

    total_entries = 0
    for feed in feeds:
        if not feed["enabled"]:
            continue
        try:
            success, entry_count = feed_manager.refresh_feed(feed["url"])
            if success:
                total_entries += entry_count
                click.echo(f"Fetched {entry_count} new entries from {feed['title']}")
            else:
                click.echo(f"Failed to fetch feed {feed['title']}")
        except Exception as e:
            click.echo(f"Failed to fetch feed {feed['title']}: {str(e)}")

    if total_entries > 0:
        click.echo(f"\nSuccessfully fetched {total_entries} new entries in total")
    else:
        click.echo("No new entries found")


@feed.command()
def list():
    """List all feeds"""
    feeds = feed_manager.get_feeds()
    if feeds:
        click.echo("\nAvailable feeds:")
        for feed in feeds:
            status = "enabled" if feed["enabled"] else "disabled"
            click.echo(f"- {feed['title']} ({feed['url']}) [{status}]")
    else:
        click.echo("No feeds available")


@feed.command()
@click.argument("url")
def remove(url):
    """Remove a feed"""
    if feed_manager.remove_feed(url):
        click.echo(f"Successfully removed feed: {url}")
    else:
        click.echo(f"Failed to remove feed: {url}")


@feed.command()
@click.argument("file_path", type=click.Path(exists=True))
def import_from_file(file_path):
    """Import feeds from a JSON file"""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict) or "feeds" not in data:
            click.echo("Error: Invalid JSON format. File must contain a 'feeds' array.")
            return

        success_count = 0
        fail_count = 0

        for feed in data["feeds"]:
            if not isinstance(feed, dict) or "url" not in feed:
                click.echo(f"Skipping invalid feed entry: {feed}")
                fail_count += 1
                continue

            if feed_manager.add_feed(feed["url"]):
                success_count += 1
                click.echo(f"Successfully added feed: {feed['url']}")
            else:
                fail_count += 1
                click.echo(f"Failed to add feed: {feed['url']}")

        click.echo(
            f"\nImport complete: {success_count} feeds added, {fail_count} failed"
        )
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON file format")
    except Exception as e:
        click.echo(f"Error: Failed to import feeds - {str(e)}")


@feed.command()
@click.argument("days", type=int)
def backdate(days):
    """Backdate all feeds' last_updated field by specified number of days and remove entries after the new date.

    Args:
        days: Number of days to backdate
    """
    if feed_manager.backdate_feeds(days):
        click.echo(f"Successfully backdated feeds by {days} days")
    else:
        click.echo(f"Failed to backdate feeds by {days} days")
