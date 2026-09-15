"""
names_store.py
Keeps the "Sent by" name list (used on the PDF export screen).
Once a name is saved, it stays in this list for future PDFs --
no need to type it again. User can add new names any time.
"""

import json
import os

NAMES_FILE = os.path.join(os.path.dirname(__file__), "sent_by_names.json")


def load_names() -> list:
    if not os.path.exists(NAMES_FILE):
        default = ["Vimlesh Patel"]
        save_names(default)
        return default
    with open(NAMES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_names(names: list) -> None:
    with open(NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, indent=2)


def add_name(new_name: str) -> list:
    """Add a new name to the saved list (only once shows the '+ Add new name' option)."""
    names = load_names()
    new_name = new_name.strip()
    if new_name and new_name not in names:
        names.append(new_name)
        save_names(names)
    return names
