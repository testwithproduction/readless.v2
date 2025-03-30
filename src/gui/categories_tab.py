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
)
from PySide6.QtCore import Qt


class CategoriesTab(QWidget):
    def __init__(self, feed_manager):
        super().__init__()
        self.feed_manager = feed_manager
        layout = QVBoxLayout(self)

        # Category list and management
        category_list_layout = QVBoxLayout()
        category_list_layout.addWidget(QLabel("Categories"))
        self.category_list = QListWidget()
        category_list_layout.addWidget(self.category_list)

        # Category management buttons
        category_buttons = QHBoxLayout()
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Category name")
        add_category_button = QPushButton("+")
        add_category_button.clicked.connect(self.add_category)
        edit_category_button = QPushButton("Edit")
        edit_category_button.clicked.connect(self.edit_category)
        remove_category_button = QPushButton("-")
        remove_category_button.clicked.connect(self.remove_category)

        category_buttons.addWidget(self.category_input)
        category_buttons.addWidget(add_category_button)
        category_buttons.addWidget(edit_category_button)
        category_buttons.addWidget(remove_category_button)
        category_list_layout.addLayout(category_buttons)

        layout.addLayout(category_list_layout)
        self.refresh_categories()

    def add_category(self):
        category = self.category_input.text().strip()
        if not category:
            return

        if self.feed_manager.add_category(category):
            self.category_input.clear()
            self.refresh_categories()
        else:
            QMessageBox.warning(self, "Error", "Category already exists.")

    def edit_category(self):
        current_item = self.category_list.currentItem()
        if not current_item or current_item.text() == "Uncategorized":
            return

        new_name = self.category_input.text().strip()
        if not new_name:
            return

        if self.feed_manager.rename_category(current_item.text(), new_name):
            self.category_input.clear()
            self.refresh_categories()
        else:
            QMessageBox.warning(self, "Error", "Failed to rename category.")

    def remove_category(self):
        current_item = self.category_list.currentItem()
        if not current_item or current_item.text() == "Uncategorized":
            return

        if (
            QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete category '{current_item.text()}'?"
                "\nAll entries will be moved to Uncategorized.",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            if self.feed_manager.remove_category(current_item.text()):
                self.refresh_categories()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove category.")

    def refresh_categories(self):
        self.category_list.clear()
        categories = self.feed_manager.get_categories()

        # Ensure 'Uncategorized' is first, then sort other categories
        sorted_categories = ["Uncategorized"] + sorted(
            cat for cat in categories if cat != "Uncategorized"
        )

        for category in sorted_categories:
            self.category_list.addItem(category)
