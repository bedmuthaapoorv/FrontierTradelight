"""Backup/restore helpers for rules.md and exit_rules.md, shared by app.py."""

import os
import re
from datetime import datetime


def declared_strategy_name(content, name_field="Strategy Name"):
    """Reads the "<name_field>: ..." line from a rules.md/exit_rules.md's
    content (e.g. "Breakout Momentum v6"). Returns "" if no such line is
    present."""
    match = re.search(rf"{re.escape(name_field)}:\s*(.+)", content)
    return match.group(1).strip() if match else ""


def strategy_slug(content, name_field="Strategy Name"):
    """Turn a rules.md/exit_rules.md's declared name into a backup filename.

    We want backup files named after the strategy (e.g. "breakout_momentum_v6"),
    not a meaningless timestamp, so past versions are easy to recognize in the
    UI's restore dropdown. This reads the "<name_field>: ..." line from the
    file's content and converts it to a lowercase, underscore-separated slug.
    If no such line is present, falls back to a timestamp so we always get a
    usable filename.
    """
    declared_name = declared_strategy_name(content, name_field=name_field)
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


def group_backups(backups):
    """Groups backup filenames by the strategy name they were saved under,
    collapsing the many timestamped versions of the same strategy into one
    entry so the restore UI doesn't show a huge flat list. A file that was
    manually renamed (so it no longer ends in the auto-generated
    "_YYYYMMDD_HHMMSS.md" suffix) becomes its own single-item group.

    Returns a dict of group_label -> [filenames], newest version first,
    sorted by group label.
    """
    groups = {}
    for filename in backups:
        match = re.match(r"^(.*)_\d{8}_\d{6}\.md$", filename)
        key = match.group(1) if match else os.path.splitext(filename)[0]
        groups.setdefault(key, []).append(filename)

    for versions in groups.values():
        versions.sort(reverse=True)

    return dict(sorted(groups.items()))


def delete_backup(backup_dir, filename):
    """Permanently removes a backup file. Callers are responsible for
    confirming with the user first - this has no undo."""
    path = os.path.join(backup_dir, filename)
    if os.path.exists(path):
        os.remove(path)


def rename_backup(backup_dir, old_filename, new_name):
    """Renames a backup file to new_name (a bare name, without the .md
    extension - this always adds it). Returns the final filename actually
    used, or None if old_filename doesn't exist or new_name is empty.

    If a file with the target name already exists, appends a numeric
    suffix rather than silently overwriting it.
    """
    if not new_name.strip():
        return None

    old_path = os.path.join(backup_dir, old_filename)
    if not os.path.exists(old_path):
        return None

    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", new_name.strip()).strip("_")
    if not safe_name:
        return None

    new_filename = f"{safe_name}.md"
    candidate = new_filename
    counter = 2
    while os.path.exists(os.path.join(backup_dir, candidate)) and candidate != old_filename:
        candidate = f"{safe_name}_{counter}.md"
        counter += 1

    new_path = os.path.join(backup_dir, candidate)
    os.rename(old_path, new_path)
    return candidate
