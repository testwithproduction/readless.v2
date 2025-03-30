import feedparser
import sqlite3
from datetime import datetime
import pytz
from typing import List, Dict
from .database import Database


class FeedManager:
    def __init__(self):
        self.db = Database()
        self.feeds = {feed["url"]: feed for feed in self.get_feeds()}

    def add_feed(self, url: str) -> bool:
        """Add a new RSS feed and fetch its initial content."""
        try:
            feed_data = feedparser.parse(url)
            if feed_data.get("bozo", 1) == 1:  # Feed parsing error
                return False

            feed_title = feed_data.feed.get("title", url)
            feed = {
                "title": feed_title,
                "url": url,
                "last_updated": datetime.now(pytz.UTC),
                "enabled": True,
                "entries": [],
            }

            # Prepare entries
            for entry in feed_data.entries:
                article = {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "description": entry.get("description", ""),
                    "published": entry.get("published", ""),
                    "content": (
                        entry.get("content", [{"value": ""}])[0]["value"]
                        if "content" in entry
                        else entry.get("description", "")
                    ),
                }
                feed["entries"].append(article)

            return self.db.add_feed(feed)
        except Exception:
            return False

    def remove_feed(self, url: str) -> None:
        """Remove a feed and its articles."""
        self.db.remove_feed(url)

    def get_feeds(self) -> List[Dict]:
        """Get list of all feeds."""
        return self.db.get_feeds()

    def get_articles(self, feed_url: str) -> List[Dict]:
        """Get articles for a specific feed."""
        return self.db.get_feed_entries(feed_url)

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
        if old_name == "Uncategorized":
            return False

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get the IDs of the categories
                cursor.execute("SELECT id FROM categories WHERE name = ?", (old_name,))
                old_category = cursor.fetchone()
                if not old_category:
                    return False

                # Add new category
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (new_name,))
                new_category_id = cursor.lastrowid

                # Update entries to use new category
                cursor.execute(
                    "UPDATE entries SET category_id = ? WHERE category_id = ?",
                    (new_category_id, old_category["id"]),
                )

                # Delete old category
                cursor.execute(
                    "DELETE FROM categories WHERE id = ?", (old_category["id"],)
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def set_entry_category(self, entry_link: str, category: str) -> bool:
        """Set category for a feed entry."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get category ID
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
                category_data = cursor.fetchone()
                if not category_data:
                    return False

                # Update entry's category
                cursor.execute(
                    "UPDATE entries SET category_id = ? WHERE link = ?",
                    (category_data["id"], entry_link),
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def get_entry_category(self, entry_link: str) -> str:
        """Get category for a feed entry."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.name
                FROM entries e
                JOIN categories c ON e.category_id = c.id
                WHERE e.link = ?
                """,
                (entry_link,),
            )
            result = cursor.fetchone()
            return result["name"] if result else "Uncategorized"

    def get_all_articles(self) -> List[Dict]:
        """Get all articles from enabled feeds."""
        all_articles = []
        for url, feed in self.feeds.items():
            if feed["enabled"]:
                articles = self.get_articles(url)
                for article in articles:
                    article["feed_title"] = feed["title"]
                all_articles.extend(articles)
        return all_articles

    def refresh_feed(self, url: str) -> bool:
        """Refresh articles for a specific feed."""
        if url not in self.feeds:
            return False
        return self.add_feed(url)  # Re-fetch and update articles

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
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.title, e.link, e.description, c.name as category
                FROM entries e
                JOIN categories c ON e.category_id = c.id
                WHERE e.published BETWEEN ? AND ?
                ORDER BY e.published DESC
                """,
                (start_date, end_date),
            )
            return [dict(row) for row in cursor.fetchall()]

    def set_read_status(self, entry_links: str | List[str], is_read: bool) -> bool:
        """Set read status for one or multiple feed entries."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            try:
                if isinstance(entry_links, str):
                    cursor.execute(
                        "UPDATE entries SET is_read = ? WHERE link = ?",
                        (1 if is_read else 0, entry_links),
                    )
                else:
                    cursor.executemany(
                        "UPDATE entries SET is_read = ? WHERE link = ?",
                        [(1 if is_read else 0, link) for link in entry_links],
                    )
                conn.commit()
                return True
            except sqlite3.Error:
                return False
