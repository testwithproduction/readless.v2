from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDateEdit,
    QComboBox,
    QTextEdit,
    QLabel,
)
from PySide6.QtCore import QDate, Qt
from datetime import datetime, timedelta
from core.feed_manager import FeedManager


class DigestTab(QWidget):
    def __init__(self, feed_manager: FeedManager):
        super().__init__()
        self.feed_manager = feed_manager
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Date range selection
        date_layout = QHBoxLayout()

        # Start date picker
        from_label = QLabel("From:")
        date_layout.addWidget(from_label)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)

        # End date picker
        to_label = QLabel("To:")
        date_layout.addWidget(to_label)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)

        # Preset date ranges
        self.preset_dates = QComboBox()
        self.preset_dates.addItems(
            ["Custom", "Last Day", "Last 7 Days", "Last 30 Days"]
        )
        self.preset_dates.currentIndexChanged.connect(self.update_date_range)
        date_layout.addWidget(self.preset_dates)

        main_layout.addLayout(date_layout)

        # Generate and Export buttons
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Digest")
        self.generate_btn.clicked.connect(self.generate_digest)
        button_layout.addWidget(self.generate_btn)

        self.export_btn = QPushButton("Export Markdown")
        self.export_btn.clicked.connect(self.export_markdown)
        button_layout.addWidget(self.export_btn)
        main_layout.addLayout(button_layout)

        # Markdown display
        self.markdown_view = QTextEdit()
        self.markdown_view.setReadOnly(True)
        main_layout.addWidget(self.markdown_view)

        self.setLayout(main_layout)

    def export_markdown(self):
        from PySide6.QtWidgets import QFileDialog

        markdown = self.markdown_view.toMarkdown()
        if not markdown:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown File", "", "Markdown Files (*.md);;All Files (*)"
        )
        if file_name:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(markdown)

    def update_date_range(self, index):
        today = QDate.currentDate()
        if index == 1:  # Last Day
            self.start_date.setDate(today.addDays(-1))
            self.end_date.setDate(today)
        elif index == 2:  # Last 7 Days
            self.start_date.setDate(today.addDays(-7))
            self.end_date.setDate(today)
        elif index == 3:  # Last 30 Days
            self.start_date.setDate(today.addDays(-30))
            self.end_date.setDate(today)

    def generate_digest(self):
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()

        # Get entries from database
        entries = self.feed_manager.get_entries_by_date_range(start_date, end_date)

        # Group entries by category
        categories = {}
        for entry in entries:
            category = entry.get("category", "Uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(entry)

        from bs4 import BeautifulSoup

        # Generate markdown
        # Generate markdown with specified header levels
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        markdown = f"# RSS Digest from {start_date_str} to {end_date_str}\n\n"
        for category, entries in categories.items():
            markdown += f"## {category}\n\n"
            for entry in entries:
                markdown += f'### [{entry["title"]}]({entry["link"]})\n'
                if entry.get("description"):
                    # Use BeautifulSoup to remove HTML tags from description
                    soup = BeautifulSoup(entry["description"], "html.parser")
                    clean_description = soup.get_text()
                    markdown += f"{clean_description}\n"
            markdown += "\n"

        self.markdown_view.setMarkdown(markdown)
