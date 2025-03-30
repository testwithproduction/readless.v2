from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QTextBrowser,
    QLabel,
    QMenu,
    QComboBox,
)
from PySide6.QtCore import Qt


class AllEntriesTab(QWidget):
    def __init__(self, feed_manager):
        super().__init__()
        self.feed_manager = feed_manager
        layout = QVBoxLayout(self)

        # Article list and content splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Article tree panel
        tree_panel = QWidget()
        tree_layout = QVBoxLayout(tree_panel)
        self.article_tree = QTreeWidget()
        self.article_tree.setHeaderLabels(["Articles"])
        self.article_tree.setSelectionMode(
            QTreeWidget.ExtendedSelection
        )  # Enable multi-selection
        self.article_tree.currentItemChanged.connect(self.show_article_content)
        self.article_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.article_tree.customContextMenuRequested.connect(self.show_context_menu)
        tree_layout.addWidget(QLabel("Articles by Category"))
        tree_layout.addWidget(self.article_tree)

        # Content panel
        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        self.content_view = QTextBrowser()
        content_layout.addWidget(QLabel("Content"))
        content_layout.addWidget(self.content_view)

        # Add panels to splitter
        splitter.addWidget(tree_panel)
        splitter.addWidget(content_panel)
        splitter.setSizes([400, 600])

        self.refresh_articles()

    def refresh_articles(self):
        self.article_tree.clear()
        categories = self.feed_manager.get_categories()
        articles = self.feed_manager.get_all_articles()

        # Create category items
        category_items = {}
        for category in categories:
            category_item = QTreeWidgetItem([category])
            self.article_tree.addTopLevelItem(category_item)
            category_items[category] = category_item

        # Add articles under their categories
        for article in articles:
            category = self.feed_manager.get_entry_category(article["link"])
            article_item = QTreeWidgetItem(
                [f"{article['feed_title']} - {article['title']}"]
            )
            article_item.setData(0, Qt.UserRole, article)
            if category in category_items:
                category_items[category].addChild(article_item)

        self.article_tree.expandAll()

    def show_article_content(self, current, previous):
        if not current or not current.data(0, Qt.UserRole):
            return

        article = current.data(0, Qt.UserRole)
        content = f"<h2>{article['title']}</h2>"
        content += f"<p><i>From: {article['feed_title']}</i></p>"
        if article["published"]:
            content += f"<p><i>Published: {article['published']}</i></p>"
        content += f"<p><a href=\"{article['link']}\">Original Article</a></p>"
        content += f"<div>{article['content']}</div>"

        self.content_view.setHtml(content)

    def show_context_menu(self, position):
        selected_items = self.article_tree.selectedItems()
        valid_items = [item for item in selected_items if item.data(0, Qt.UserRole)]

        if not valid_items:
            return

        menu = QMenu()
        change_category = menu.addMenu("Change Category")

        # Add category options in sorted order
        categories = self.feed_manager.get_categories()
        sorted_categories = ["Uncategorized"] + sorted(
            cat for cat in categories if cat != "Uncategorized"
        )

        for category in sorted_categories:
            action = change_category.addAction(category)
            action.triggered.connect(
                lambda checked, c=category: self.change_articles_category(
                    valid_items, c
                )
            )

        menu.exec_(self.article_tree.viewport().mapToGlobal(position))

    def change_articles_category(self, items, new_category):
        success = True
        for item in items:
            article = item.data(0, Qt.UserRole)
            if not self.feed_manager.set_entry_category(article["link"], new_category):
                success = False
        if success:
            self.refresh_articles()
