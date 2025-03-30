import sqlite3
import os
from datetime import datetime
import pytz
from typing import List, Dict, Optional, Any


class Database:
    def __init__(self):
        self.db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "readless.db"
        )
        self._init_db()

    # Database initialization methods
    def _init_db(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create categories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """
            )

            # Create feeds table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    last_updated TIMESTAMP,
                    enabled BOOLEAN DEFAULT 1
                )
            """
            )

            # Create entries table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    description TEXT,
                    content TEXT,
                    published TEXT,
                    category_id INTEGER DEFAULT 1,
                    is_read BOOLEAN DEFAULT 0,
                    FOREIGN KEY (feed_id) REFERENCES feeds (id),
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            """
            )

            # Insert default category if it doesn't exist
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Uncategorized",)
            )

            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory set to dict."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        return conn

    # Feed operations
    def add_feed(self, feed_data: Dict[str, Any]) -> bool:
        """Add a new feed and its entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Insert feed
                cursor.execute(
                    """
                    INSERT INTO feeds (url, title, last_updated, enabled)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        feed_data["url"],
                        feed_data["title"],
                        feed_data["last_updated"].isoformat(),
                        feed_data["enabled"],
                    ),
                )

                feed_id = cursor.lastrowid

                # Get default category ID (Uncategorized)
                cursor.execute("SELECT id FROM categories WHERE name = 'Uncategorized'")
                default_category = cursor.fetchone()

                # Insert entries
                for entry in feed_data.get("entries", []):
                    cursor.execute(
                        """
                        INSERT INTO entries 
                        (feed_id, title, link, description, content, published, category_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            feed_id,
                            entry["title"],
                            entry["link"],
                            entry.get("description", ""),
                            entry.get("content", ""),
                            entry.get("published", ""),
                            default_category["id"],
                        ),
                    )

                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def get_feeds(self) -> List[Dict[str, Any]]:
        """Get all feeds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM feeds")
            feeds = cursor.fetchall()
            for feed in feeds:
                feed["last_updated"] = datetime.fromisoformat(feed["last_updated"])
            return feeds

    def update_feed(self, url: str, updates: Dict[str, Any]) -> bool:
        """Update feed properties."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                update_fields = []
                params = []

                if "title" in updates:
                    update_fields.append("title = ?")
                    params.append(updates["title"])
                if "enabled" in updates:
                    update_fields.append("enabled = ?")
                    params.append(updates["enabled"])
                if "last_updated" in updates:
                    update_fields.append("last_updated = ?")
                    params.append(updates["last_updated"].isoformat())

                if update_fields:
                    params.append(url)
                    cursor.execute(
                        f"UPDATE feeds SET {', '.join(update_fields)} WHERE url = ?",
                        params,
                    )
                    conn.commit()
                return True
        except sqlite3.Error:
            return False

    def remove_feed(self, url: str) -> bool:
        """Remove a feed and all its entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM feeds WHERE url = ?", (url,))
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    # Category operations
    def get_categories(self) -> List[str]:
        """Get all category names."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories")
            return [row["name"] for row in cursor.fetchall()]

    def add_category(self, name: str) -> bool:
        """Add a new category."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                return True
        except sqlite3.IntegrityError:
            return False

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category.

        Args:
            old_name: The current name of the category
            new_name: The new name for the category

        Returns:
            bool: True if successful, False otherwise
        """
        if old_name == "Uncategorized":
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE categories SET name = ? WHERE name = ?",
                    (new_name, old_name),
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def remove_category(self, name: str) -> bool:
        """Remove a category and update associated entries to Uncategorized."""
        if name == "Uncategorized":
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get the IDs of the categories
                cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
                category = cursor.fetchone()
                if not category:
                    return False

                cursor.execute("SELECT id FROM categories WHERE name = 'Uncategorized'")
                uncategorized = cursor.fetchone()

                # Update entries to use Uncategorized category
                cursor.execute(
                    "UPDATE entries SET category_id = ? WHERE category_id = ?",
                    (uncategorized["id"], category["id"]),
                )

                # Delete the category
                cursor.execute("DELETE FROM categories WHERE id = ?", (category["id"],))
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def get_entry_category(self, entry_link: str) -> str:
        """Get category for a feed entry."""
        with self._get_connection() as conn:
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

    def set_entry_category(self, entry_link: str, category: str) -> bool:
        """Set category for a feed entry."""
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
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

    def set_entry_read_status(
        self, entry_links: str | List[str], is_read: bool
    ) -> bool:
        """Set read status for one or multiple feed entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
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

    def remove_entries_after_date(self, feed_url: str, date: datetime) -> bool:
        """Remove entries from a feed that are published after the specified date.

        Args:
            feed_url: The URL of the feed
            date: The cutoff date

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM entries
                    WHERE feed_id = (SELECT id FROM feeds WHERE url = ?)
                    AND published > ?
                    """,
                    (feed_url, date.isoformat()),
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def get_feed_entries(self, feed_url: str) -> List[Dict[str, Any]]:
        """Get all entries for a specific feed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*
                FROM entries e
                JOIN feeds f ON e.feed_id = f.id
                WHERE f.url = ? AND f.enabled = 1
            """,
                (feed_url,),
            )
            return cursor.fetchall()
