"""Backup/restore helpers for rules.md and exit_rules.md, shared by app.py."""

import os
import re
from datetime import datetime


def strategy_slug(content, name_field="Strategy Name"):
    """Turn a rules.md/exit_rules.md's declared name into a backup filename.

    We want backup files named after the strategy (e.g. "breakout_momentum_v6"),
    not a meaningless timestamp, so past versions are easy to recognize in the
    UI's restore dropdown. This reads the "<name_field>: ..." line from the
    file's content and converts it to a lowercase, underscore-separated slug.
    If no such line is present, falls back to a timestamp so we always get a
    usable filename.
    """
    match = re.search(rf"{re.escape(name_field)}:\s*(.+)", content)
    declared_name = match.group(1).strip() if match else ""
    slug = re.sub(r"[^a-z0-9]+", "_", declared_name.lower()).strip("_")
    return slug or datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_markdown(content, backup_dir, suffix, name_field="Strategy Name"):
    """Save the given markdown content into backup_dir, keyed by the name
    declared in name_field plus a timestamp, so each save gets its own
    distinct, dated backup file instead of overwriting the last one."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{strategy_slug(content, name_field=name_field)}_{suffix}_{timestamp}.md"
    with open(os.path.join(backup_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def list_backups(backup_dir):
    if not os.path.isdir(backup_dir):
        return []
    return sorted(f for f in os.listdir(backup_dir) if f.endswith(".md"))
