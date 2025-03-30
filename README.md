# ReadLess - A Modern RSS Reader

ReadLess is a modern RSS reader application that provides both a graphical user interface (GUI) and command-line interface (CLI) for managing and reading your RSS feeds efficiently.

## Features

- **Dual Interface**: Choose between a modern GUI or powerful CLI
- **Feed Management**: Add, remove, and organize RSS feeds
- **Category Organization**: Group feeds into categories for better organization
- **Multi-selection Support**: Efficiently manage multiple feeds or entries at once
- **Cross-platform**: Works on various operating systems

## Installation

ReadLess requires Python 3.8 or higher. You can install it using pip:

```bash
pip install .
```

### Dependencies

The project automatically handles the following dependencies:

- PySide6 (>=6.6.0) - For the GUI interface
- feedparser (>=6.0.10) - For parsing RSS feeds
- requests (>=2.31.0) - For fetching feed content
- pytz (>=2023.3) - For timezone handling
- click (>=8.1.0) - For CLI interface

## Usage

### GUI Interface

To start the graphical interface:

```bash
python -m src.gui.main
```

The GUI provides three main tabs:
- Feed Sources: Manage your RSS feed subscriptions
- Categories: Organize feeds into categories
- All Entries: Read and manage feed entries

### CLI Interface

ReadLess provides a command-line interface for feed management:

```bash
python -m src.cli.feed_cli
```

Available commands:
- Feed management commands
- Category organization commands

Use the `--help` option with any command to see detailed usage instructions:

```bash
python -m src.cli.feed_cli --help
```

## Development

To set up the development environment:

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

Development tools include:
- pytest for testing
- black for code formatting
- flake8 for linting

## License

This project is licensed under the terms of the LICENSE file included in the repository.