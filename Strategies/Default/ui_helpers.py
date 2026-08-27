"""Shared Streamlit helpers used by tabs/*.py plugins.

Kept separate from any single tab so plugins stay self-contained: a new
tab module only needs to import from here, never reach into another tab's
file, which is what keeps merging in someone else's tabs/*.py additions
low-conflict.
"""

import os

import streamlit as st

from backup_utils import backup_markdown, delete_backup, list_backups, rename_backup
from constants import APP_DIR


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_script(script_name, args=None):
    """Run a script in Default/ and stream its output."""
    import subprocess
    import sys

    process = subprocess.Popen(
        [sys.executable, script_name, *(args or [])],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output_box = st.empty()
    lines = []
    for line in process.stdout:
        lines.append(line.rstrip())
        output_box.code("\n".join(lines[-200:]))
    process.wait()
    return process.returncode


def run_script_with_feedback(button_label, script_name, spinner_text, success_text):
    if st.button(button_label):
        with st.spinner(spinner_text):
            code = run_script(script_name)
        if code == 0:
            st.success(success_text)
        else:
            st.error(f"{script_name} exited with code {code}.")


def show_guide(filename, expander_label):
    guide_path = os.path.join(APP_DIR, filename)
    if os.path.exists(guide_path):
        with st.expander(expander_label):
            st.markdown(read_text(guide_path))


def nonempty_csv_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def load_into_session(session_key, path):
    if session_key not in st.session_state:
        st.session_state[session_key] = read_text(path)


def save_with_backup(path, backup_dir, suffix, backup_label, new_content, session_key):
    """Back up the file's current contents, then overwrite it with new_content."""
    previous_content = read_text(path)
    if previous_content.strip():
        backup_name = backup_markdown(previous_content, backup_dir, suffix)
        st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

    write_text(path, new_content)
    st.session_state[session_key] = new_content


def editable_markdown(session_key, text_area_label, text_area_height):
    """A Preview toggle sitting above the editor that swaps between an
    editable text_area and a read-only rendered Markdown view of the same
    content, in the same space (not both shown at once). Live edits are
    written back to st.session_state[session_key] on every rerun while in
    edit mode, so switching to preview and back doesn't lose in-progress
    typing."""
    show_preview = st.toggle("Preview", key=f"{session_key}_preview_toggle")

    if show_preview:
        with st.container(border=True, height=text_area_height):
            st.markdown(st.session_state[session_key])
        return st.session_state[session_key]

    edited = st.text_area(
        text_area_label,
        value=st.session_state[session_key],
        height=text_area_height,
        label_visibility="collapsed",
        key=f"{session_key}_textarea",
    )
    st.session_state[session_key] = edited
    return edited


def raw_or_rendered_preview(content, key):
    """A Preview toggle above a read-only markdown blob (e.g. a backup
    file) that swaps between the raw source (st.code) and its rendered
    form (st.markdown), in the same space."""
    show_preview = st.toggle("Preview", key=key)
    if show_preview:
        with st.container(border=True):
            st.markdown(content)
    else:
        st.code(content, language="markdown")


def strategy_editor(*, session_key, path, guide_filename, guide_label, backup_dir,
                     backup_suffix, backup_label, text_area_label, text_area_height,
                     save_button_label, save_success_message, no_backups_caption):
    """Renders the edit/save/restore workflow shared by rules.md and exit_rules.md."""
    show_guide(guide_filename, guide_label)
    load_into_session(session_key, path)

    edited = editable_markdown(session_key, text_area_label, text_area_height)

    if st.button(save_button_label):
        save_with_backup(path, backup_dir, backup_suffix, backup_label, edited, session_key)
        st.success(save_success_message)

    return edited


def backup_restore_section(*, path, backup_dir, backup_suffix, backup_label,
                            session_key, no_backups_caption, selectbox_label,
                            overwrite_label_prefix, success_message_prefix,
                            show_in_expander=False):
    backups = list_backups(backup_dir)
    if not backups:
        st.caption(no_backups_caption)
        return

    selected_backup = st.selectbox(selectbox_label, backups)
    backup_content = read_text(os.path.join(backup_dir, selected_backup))
    preview_key = f"{backup_dir}_{selected_backup}_preview"

    if st.button(f"{overwrite_label_prefix} {selected_backup}"):
        current_content = read_text(path)
        if current_content.strip() and current_content != backup_content:
            backup_name = backup_markdown(current_content, backup_dir, backup_suffix)
            st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

        write_text(path, backup_content)
        st.session_state[session_key] = backup_content
        st.success(f"{success_message_prefix} {selected_backup}")
        st.rerun()

    if show_in_expander:
        raw_or_rendered_preview(backup_content, key=preview_key)
    else:
        with st.expander(f"Preview {selected_backup}"):
            raw_or_rendered_preview(backup_content, key=preview_key)

    manage_backup_file(backup_dir, selected_backup)


def backup_restore_modal(*, modal_title, open_button_label, **section_kwargs):
    """Opens the backup/restore workflow (backup_restore_section) in a
    modal dialog instead of an inline expander, so browsing old strategy
    versions doesn't push the rest of the tab's content down/compete for
    space with the editor above it. Always renders the backup preview
    inline (not in its own nested expander) since it's already inside the
    dialog's own contained surface."""
    if st.button(open_button_label):
        _open_backup_dialog(modal_title, section_kwargs)


def _open_backup_dialog(modal_title, section_kwargs):
    @st.dialog(modal_title)
    def _dialog():
        backup_restore_section(**section_kwargs, show_in_expander=True)

    _dialog()


def manage_backup_file(backup_dir, selected_backup):
    """Rename or permanently delete a single backup file - does not touch
    the live rules.md/exit_rules.md, only the backup copy itself."""
    rename_col, delete_col = st.columns(2)

    with rename_col:
        with st.popover("Rename"):
            new_name = st.text_input(
                "New name (no extension)",
                value=os.path.splitext(selected_backup)[0],
                key=f"{backup_dir}_{selected_backup}_rename_input",
            )
            if st.button("Confirm rename", key=f"{backup_dir}_{selected_backup}_rename_confirm"):
                result = rename_backup(backup_dir, selected_backup, new_name)
                if result is None:
                    st.error("Enter a valid name first.")
                else:
                    st.success(f"Renamed to {result}")
                    st.rerun()

    with delete_col:
        with st.popover("Delete"):
            st.caption(f"Permanently delete {selected_backup}? This cannot be undone.")
            if st.button("Confirm delete", key=f"{backup_dir}_{selected_backup}_delete_confirm"):
                delete_backup(backup_dir, selected_backup)
                st.success(f"Deleted {selected_backup}")
                st.rerun()
