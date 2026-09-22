"""Fund paperwork storage - agreements, investor statements, compliance
filings, tax records the user uploads for the fund. Entirely separate from
the backtest engine and from fund_manager_utils.py's NAV/units accounting:
this is just file storage + metadata, never read by any NAV/AUM
calculation.

Each uploaded file is saved on disk under FUND_DOCUMENTS_DIR named by its own
generated doc id (never the original filename - avoids path-traversal and
collisions), with metadata (original name, category, date, notes) kept in a
CSV alongside it, the same "CSV as the record, id assigned at creation"
pattern used elsewhere in this app (e.g. backup filenames)."""

import os
import uuid

import pandas as pd

from constants import FUND_DOCUMENTS_DIR, FUND_DOCUMENTS_META_PATH

META_COLUMNS = ["ID", "Name", "Category", "Date", "SizeBytes", "StoredFilename", "Notes"]

CATEGORIES = ["Agreement", "Statement", "Compliance", "Tax", "Other"]

# Only document formats this tool is meant for - never anything executable.
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".png", ".jpg", ".jpeg"}
MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB, matches the design's stated limit


def _load_meta() -> pd.DataFrame:
    if not os.path.exists(FUND_DOCUMENTS_META_PATH) or os.path.getsize(FUND_DOCUMENTS_META_PATH) == 0:
        return pd.DataFrame(columns=META_COLUMNS)
    return pd.read_csv(FUND_DOCUMENTS_META_PATH, keep_default_na=False)


def _save_meta(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(FUND_DOCUMENTS_META_PATH), exist_ok=True)
    df.to_csv(FUND_DOCUMENTS_META_PATH, index=False)


def list_documents() -> list[dict]:
    df = _load_meta()
    if df.empty:
        return []
    df = df.sort_values("Date", ascending=False)
    return [
        {
            "id": row["ID"],
            "name": row["Name"],
            "category": row["Category"],
            "date": row["Date"],
            "size_bytes": int(row["SizeBytes"]),
            "notes": row["Notes"],
        }
        for _, row in df.iterrows()
    ]


def add_document(file_bytes: bytes, original_filename: str, category: str, doc_date: str, notes: str = "") -> dict:
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"status": "error", "message": f"Unsupported file type {ext or '(none)'}."}
    if len(file_bytes) > MAX_SIZE_BYTES:
        return {"status": "error", "message": f"File too large ({len(file_bytes) / 1_048_576:.1f} MB, limit 25 MB)."}
    if category not in CATEGORIES:
        return {"status": "error", "message": f"Category must be one of {', '.join(CATEGORIES)}."}
    if not original_filename.strip():
        return {"status": "error", "message": "File must have a name."}

    doc_id = uuid.uuid4().hex
    stored_filename = f"{doc_id}{ext}"
    os.makedirs(FUND_DOCUMENTS_DIR, exist_ok=True)
    with open(os.path.join(FUND_DOCUMENTS_DIR, stored_filename), "wb") as f:
        f.write(file_bytes)

    df = _load_meta()
    new_row = pd.DataFrame([{
        "ID": doc_id,
        "Name": original_filename,
        "Category": category,
        "Date": doc_date,
        "SizeBytes": len(file_bytes),
        "StoredFilename": stored_filename,
        "Notes": notes,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    _save_meta(df)

    return {
        "status": "ok",
        "document": {
            "id": doc_id,
            "name": original_filename,
            "category": category,
            "date": doc_date,
            "size_bytes": len(file_bytes),
            "notes": notes,
        },
    }


def get_document_file(doc_id: str) -> tuple[str, str] | None:
    """Returns (absolute_path, original_filename) for a download, or None if
    the doc id doesn't exist or its file is missing on disk."""
    df = _load_meta()
    match = df[df["ID"] == doc_id]
    if match.empty:
        return None
    row = match.iloc[0]
    path = os.path.join(FUND_DOCUMENTS_DIR, row["StoredFilename"])
    if not os.path.exists(path):
        return None
    return path, row["Name"]


def remove_document(doc_id: str) -> dict:
    df = _load_meta()
    match = df[df["ID"] == doc_id]
    if match.empty:
        return {"status": "error", "message": "Document not found."}
    stored_filename = match.iloc[0]["StoredFilename"]
    path = os.path.join(FUND_DOCUMENTS_DIR, stored_filename)
    if os.path.exists(path):
        os.remove(path)
    df = df[df["ID"] != doc_id]
    _save_meta(df)
    return {"status": "ok"}
