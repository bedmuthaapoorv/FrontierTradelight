"""Generic file CRUD + backup/restore router for a markdown strategy file
(rules.md, exit_rules.md). Parameterized by path/backup_dir/suffix so both
Rules and (later) Sell's exit-strategy editor can mount their own instance
of the same routes without duplicating logic - mirrors how
`ui_helpers.strategy_editor`/`backup_restore_section` are shared by both
tabs in the Streamlit app.

None of the underlying read/write/backup logic is reimplemented here -
this only wraps `backup_utils.py` and plain file IO in HTTP handlers.
"""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backup_utils import backup_markdown, delete_backup, group_backups, list_backups, rename_backup


class FileContent(BaseModel):
    content: str


class RenameRequest(BaseModel):
    new_name: str


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def make_markdown_router(*, prefix, path, backup_dir, backup_suffix):
    router = APIRouter(prefix=prefix)

    @router.get("")
    def get_file():
        if not os.path.exists(path):
            return {"content": ""}
        return {"content": _read_text(path)}

    @router.put("")
    def put_file(body: FileContent):
        """Backs up the current content (if non-empty) before overwriting,
        same as ui_helpers.save_with_backup."""
        if os.path.exists(path):
            previous = _read_text(path)
            backup_name = None
            if previous.strip():
                backup_name = backup_markdown(previous, backup_dir, backup_suffix)
        else:
            backup_name = None

        _write_text(path, body.content)
        return {"content": body.content, "backed_up_as": backup_name}

    @router.get("/backups")
    def get_backups():
        return group_backups(list_backups(backup_dir))

    @router.get("/backups/{filename}")
    def get_backup(filename: str):
        backup_path = os.path.join(backup_dir, filename)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup not found")
        return {"content": _read_text(backup_path)}

    @router.post("/backups/{filename}/restore")
    def restore_backup(filename: str):
        """Backs up the current live file (if it differs), then overwrites
        it with the chosen backup's content - same as
        ui_helpers.backup_restore_section's overwrite button."""
        backup_path = os.path.join(backup_dir, filename)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup not found")

        backup_content = _read_text(backup_path)
        backed_up_as = None
        if os.path.exists(path):
            current_content = _read_text(path)
            if current_content.strip() and current_content != backup_content:
                backed_up_as = backup_markdown(current_content, backup_dir, backup_suffix)

        _write_text(path, backup_content)
        return {"content": backup_content, "backed_up_as": backed_up_as}

    @router.post("/backups/{filename}/rename")
    def rename(filename: str, body: RenameRequest):
        result = rename_backup(backup_dir, filename, body.new_name)
        if result is None:
            raise HTTPException(status_code=400, detail="Invalid name or backup not found")
        return {"filename": result}

    @router.delete("/backups/{filename}")
    def delete(filename: str):
        backup_path = os.path.join(backup_dir, filename)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup not found")
        delete_backup(backup_dir, filename)
        return {"status": "deleted"}

    return router
