import click
from core.feed_manager import FeedManager

feed_manager = FeedManager()


@click.group()
def category():
    """Manage feed categories"""
    pass


@category.command()
def list():
    """List all categories"""
    categories = feed_manager.get_categories()
    if categories:
        click.echo("\nAvailable categories:")
        for category in categories:
            click.echo(f"- {category}")
    else:
        click.echo("No categories available")


@category.command()
@click.argument("name")
def add(name):
    """Add a new category"""
    if feed_manager.add_category(name):
        click.echo(f"Successfully added category: {name}")
    else:
        click.echo(f"Failed to add category: {name}")


@category.command()
@click.argument("name")
def remove(name):
    """Remove a category and move its entries to Uncategorized"""
    if name.lower() == "uncategorized":
        click.echo("Cannot remove the Uncategorized category")
        return
    if feed_manager.remove_category(name):
        click.echo(f"Successfully removed category: {name}")
    else:
        click.echo(f"Failed to remove category: {name}")


@category.command()
@click.argument("file_path", type=click.Path(exists=True))
def import_from_file(file_path):
    """Import categories from a file"""
    try:
        with open(file_path, "r") as f:
            categories = [line.strip() for line in f if line.strip()]

        success_count = 0
        for category in categories:
            if feed_manager.add_category(category):
                success_count += 1

        if success_count > 0:
            click.echo(f"Successfully imported {success_count} categories")
            if success_count < len(categories):
                click.echo(
                    f"Note: {len(categories) - success_count} categories were skipped (already exist or invalid)"
                )
        else:
            click.echo("No new categories were imported")
    except Exception as e:
        click.echo(f"Failed to import categories: {str(e)}")
