import feedparser
from datetime import datetime, timedelta
import pytz
from typing import List, Dict
from .database import Database


class FeedManager:
    def __init__(self):
        self.db = Database()
        self.feeds = {feed["url"]: feed for feed in self.get_feeds()}

    # Feed-related operations
    def add_feed(self, url: str) -> bool:
        """Add a new RSS feed without fetching initial content."""
        try:
            # Validate feed and get title
            feed_data = feedparser.parse(url)
            if feed_data.get("bozo", 1) == 1:
                return False

            title = feed_data.feed.get("title", url)

            feed = {
                "title": title,
                "url": url,
                "last_updated": datetime(1970, 1, 1, tzinfo=pytz.UTC),
                "enabled": True,
                "entries": [],
            }
            return self.db.add_feed(feed)
        except Exception:
            return False

    def remove_feed(self, url: str) -> None:
        """Remove a feed and its articles."""
        self.db.remove_feed(url)

    def get_feeds(self) -> List[Dict]:
        """Get list of all feeds."""
        return self.db.get_feeds()

    def toggle_feed_status(self, url: str) -> bool:
        """Toggle feed enabled/disabled status."""
        feeds = self.db.get_feeds()
        feed = next((f for f in feeds if f["url"] == url), None)
        if not feed:
            return False
        return self.db.update_feed(url, {"enabled": not feed["enabled"]})

    def update_feed_title(self, url: str, new_title: str) -> bool:
        """Update the title of a feed."""
        return self.db.update_feed(url, {"title": new_title})

    def refresh_feed(self, url: str) -> tuple[bool, int]:
        """Refresh articles for a specific feed, skipping old entries."""
        if url not in self.feeds:
            return False, 0

        # Get last update time
        last_updated = self.feeds[url].get("last_updated")
        if not last_updated:
            success = self.add_feed(url)
            return success, 0 if not success else len(self.feeds[url]["entries"])

        # Parse new feed data
        feed_data = feedparser.parse(url)
        if feed_data.get("bozo", 1) == 1:
            return False, 0

        # Prepare new entries
        new_entries = []
        for entry in feed_data.entries:
            published = entry.get("published", "")
            if published:
                try:
                    entry_date = datetime.strptime(
                        published, "%a, %d %b %Y %H:%M:%S %z"
                    )
                    if entry_date > last_updated:
                        article = {
                            "title": entry.get("title", "No title"),
                            "link": entry.get("link", ""),
                            "description": entry.get("description", ""),
                            "published": published,
                            "content": (
                                entry.get("content", [{"value": ""}])[0]["value"]
                                if "content" in entry
                                else entry.get("description", "")
                            ),
                        }
                        new_entries.append(article)
                except ValueError:
                    continue

        # Update feed with new entries
        if new_entries:
            feed = self.feeds[url].copy()
            feed["entries"] = new_entries
            feed["last_updated"] = datetime.now(pytz.UTC)
            return self.db.update_feed(url, feed), len(new_entries)
        return True, 0

    # Category-related operations
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        return self.db.get_categories()

    def add_category(self, category: str) -> bool:
        """Add a new category."""
        return self.db.add_category(category)

    def remove_category(self, category: str) -> bool:
        """Remove a category and move its entries to Uncategorized."""
        return self.db.remove_category(category)

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category."""
        return self.db.rename_category(old_name, new_name)

    # Entry-related operations
    def get_entries(self, feed_url: str) -> List[Dict]:
        """Get entries for a specific feed."""
        return self.db.get_feed_entries(feed_url)

    def get_all_entries(self) -> List[Dict]:
        """Get all entries from enabled feeds."""
        all_entries = []
        for url, feed in self.feeds.items():
            if feed["enabled"]:
                entries = self.get_entries(url)
                for entry in entries:
                    entry["feed_title"] = feed["title"]
                all_entries.extend(entries)
        return all_entries

    def set_entry_category(self, entry_link: str, category: str) -> bool:
        """Set category for a feed entry."""
        return self.db.set_entry_category(entry_link, category)

    def get_entry_category(self, entry_link: str) -> str:
        """Get category for a feed entry."""
        return self.db.get_entry_category(entry_link)

    def get_entries_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Get entries between specified dates.

        Args:
            start_date: Start date of the range
            end_date: End date of the range

        Returns:
            List of entries with title, link, description, and category
        """
        return self.db.get_entries_by_date_range(start_date, end_date)

    def set_entry_read_status(
        self, entry_links: str | List[str], is_read: bool
    ) -> bool:
        """Set read status for one or multiple feed entries."""
        return self.db.set_entry_read_status(entry_links, is_read)

    def backdate_feeds(self, days: int) -> bool:
        """Backdate all feeds' last_updated field by specified number of days and remove entries after the new date.

        Args:
            days: Number of days to backdate

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate new date
            new_date = datetime.now(pytz.UTC) - timedelta(days=days)

            # Get all feeds
            feeds = self.get_feeds()
            if not feeds:
                return False

            # Update each feed
            for feed in feeds:
                # Update last_updated field
                self.db.update_feed(feed["url"], {"last_updated": new_date})

                # Remove entries after new date
                self.db.remove_entries_after_date(feed["url"], new_date)

            return True
        except Exception:
            return False
