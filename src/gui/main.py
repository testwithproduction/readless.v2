#!/usr/bin/env python
import sys
import os
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
)
from PySide6.QtGui import QIcon
from all_entries_tab import AllEntriesTab
from feed_sources_tab import FeedSourcesTab
from categories_tab import CategoriesTab
from core.feed_manager import FeedManager


class RSSReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReadLess - RSS Reader")
        self.setMinimumSize(1000, 600)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "icon.svg")
        self.setWindowIcon(QIcon(icon_path))

        # Initialize feed manager
        self.feed_manager = FeedManager()

        # Set window to maximized state
        self.showMaximized()

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.all_entries_tab = AllEntriesTab(self.feed_manager)
        self.feed_sources_tab = FeedSourcesTab(self.feed_manager)
        self.categories_tab = CategoriesTab(self.feed_manager)

        # Add tabs
        self.tab_widget.addTab(self.all_entries_tab, "All Entries")
        self.tab_widget.addTab(self.feed_sources_tab, "Feed Sources")
        self.tab_widget.addTab(self.categories_tab, "Categories")

        # Connect tab signals
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        # Refresh the current tab's content
        current_tab = self.tab_widget.widget(index)
        if hasattr(current_tab, "refresh_feed_list"):
            current_tab.refresh_feed_list()
        elif hasattr(current_tab, "refresh_articles"):
            current_tab.refresh_articles()
        elif hasattr(current_tab, "refresh_lists"):
            current_tab.refresh_lists()


def main():
    app = QApplication(sys.argv)
    window = RSSReader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
