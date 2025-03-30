from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QListWidgetItem,
    QCheckBox,
    QDialog,
    QFormLayout,
)
from PySide6.QtCore import Qt


class FeedSourcesTab(QWidget):
    def __init__(self, feed_manager):
        super().__init__()
        self.feed_manager = feed_manager
        layout = QVBoxLayout(self)

        # Feed list
        feed_list_layout = QVBoxLayout()
        feed_list_layout.addWidget(QLabel("Feed Sources"))
        self.feed_list = QListWidget()
        feed_list_layout.addWidget(self.feed_list)

        # Feed management buttons
        feed_buttons = QHBoxLayout()
        self.feed_input = QLineEdit()
        self.feed_input.setPlaceholderText("Enter RSS feed URL")
        add_feed_button = QPushButton("+")
        add_feed_button.clicked.connect(self.add_feed)
        edit_feed_button = QPushButton("Edit")
        edit_feed_button.clicked.connect(self.edit_selected_feed)
        remove_feed_button = QPushButton("-")
        remove_feed_button.clicked.connect(self.delete_selected_feed)

        feed_buttons.addWidget(self.feed_input)
        feed_buttons.addWidget(add_feed_button)
        feed_buttons.addWidget(edit_feed_button)
        feed_buttons.addWidget(remove_feed_button)
        feed_list_layout.addLayout(feed_buttons)

        layout.addLayout(feed_list_layout)
        self.refresh_feed_list()

    def add_feed(self):
        url = self.feed_input.text().strip()
        if not url:
            return

        if self.feed_manager.add_feed(url):
            self.feed_input.clear()
            self.refresh_feed_list()
        else:
            QMessageBox.warning(
                self, "Error", "Failed to add feed. Please check the URL."
            )

    def refresh_feed_list(self):
        self.feed_list.clear()
        # Get and sort feeds by title
        feeds = sorted(self.feed_manager.get_feeds(), key=lambda x: x["title"].lower())
        for feed in feeds:
            item = QListWidgetItem(f"{feed['title']} ({feed['url']})")
            item.setData(Qt.UserRole, feed)
            if not feed["enabled"]:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.feed_list.addItem(item)

    def edit_selected_feed(self):
        current_item = self.feed_list.currentItem()
        if not current_item:
            return
        feed = current_item.data(Qt.UserRole)
        self.edit_feed(feed)

    def delete_selected_feed(self):
        current_item = self.feed_list.currentItem()
        if not current_item:
            return
        feed = current_item.data(Qt.UserRole)
        self.delete_feed(feed["url"])

    def toggle_feed(self, url):
        self.feed_manager.toggle_feed_status(url)

    def edit_feed(self, feed):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Feed")
        layout = QFormLayout(dialog)

        title_input = QLineEdit(feed["title"])
        url_input = QLineEdit(feed["url"])
        url_input.setReadOnly(True)  # URL cannot be changed

        layout.addRow("Title:", title_input)
        layout.addRow("URL:", url_input)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(
            lambda: self.save_feed_edit(feed["url"], title_input.text(), dialog)
        )
        cancel_btn.clicked.connect(dialog.reject)

        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        dialog.exec()

    def save_feed_edit(self, url, new_title, dialog):
        if self.feed_manager.update_feed_title(url, new_title):
            dialog.accept()
            self.refresh_feed_list()
        else:
            QMessageBox.warning(self, "Error", "Failed to update feed title.")

    def delete_feed(self, url):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this feed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.feed_manager.remove_feed(url)
            self.refresh_feed_list()
