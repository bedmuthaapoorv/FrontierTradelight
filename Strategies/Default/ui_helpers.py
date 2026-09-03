"""Shared Streamlit helpers used by tabs/*.py plugins.

Kept separate from any single tab so plugins stay self-contained: a new
tab module only needs to import from here, never reach into another tab's
file, which is what keeps merging in someone else's tabs/*.py additions
low-conflict.
"""

import os

import streamlit as st

from backup_utils import backup_markdown, delete_backup, group_backups, list_backups, rename_backup
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
    """Loads path's content into session_state[session_key] the first time,
    and re-syncs it whenever the file's on-disk mtime has moved since the
    last load - so a change made outside this app session (a direct edit,
    another script, restoring the file from git) shows up on the next
    rerun instead of staying invisible until the whole Streamlit process
    is restarted. Only compares mtime (not content) so this stays cheap on
    every rerun. Note: if the file changes externally while you have
    unsaved edits in the text area, this will overwrite them - external
    changes winning is the safer default here since a stale editor has
    been the recurring problem, not clobbered in-progress edits."""
    mtime_key = f"{session_key}_mtime"
    current_mtime = os.path.getmtime(path)
    if session_key not in st.session_state or st.session_state.get(mtime_key) != current_mtime:
        set_markdown_session_content(session_key, read_text(path))
        st.session_state[mtime_key] = current_mtime


def write_and_sync(path, content, session_key):
    """Writes content to path, then updates session_state (both the plain
    key and the text_area's own widget key - see set_markdown_session_content)
    and the mtime load_into_session tracks, so this app's own write doesn't
    look like an external change that needs re-syncing on the next rerun."""
    write_text(path, content)
    set_markdown_session_content(session_key, content)
    st.session_state[f"{session_key}_mtime"] = os.path.getmtime(path)


def save_with_backup(path, backup_dir, suffix, backup_label, new_content, session_key):
    """Back up the file's current contents, then overwrite it with new_content."""
    previous_content = read_text(path)
    if previous_content.strip():
        backup_name = backup_markdown(previous_content, backup_dir, suffix)
        st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

    write_and_sync(path, new_content, session_key)


def set_markdown_session_content(session_key, content):
    """Sets st.session_state[session_key] AND the underlying text_area
    widget's own state (editable_markdown's `key=f"{session_key}_textarea"`).

    Once a keyed widget has rendered once, Streamlit ignores any `value=`
    passed to it on later reruns and uses the widget's own session_state
    entry instead - so overwriting only session_state[session_key] (e.g.
    after restoring a backup) silently fails to update the visible text
    area; it keeps showing whatever it last rendered. Any code path that
    replaces a markdown file's content wholesale (not via the user typing
    into the text area itself) must go through this, not a plain
    `st.session_state[session_key] = content` assignment.
    """
    st.session_state[session_key] = content
    st.session_state[f"{session_key}_textarea"] = content


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
                            overwrite_label_prefix, success_message_prefix):
    backups = list_backups(backup_dir)
    if not backups:
        st.caption(no_backups_caption)
        return

    search = st.text_input(
        "Search backups", key=f"{backup_dir}_search", placeholder="Filter by name...",
    )
    if search:
        backups = [f for f in backups if search.lower() in f.lower()]
        if not backups:
            st.caption(f"No backups match '{search}'.")
            return

    groups = group_backups(backups)
    selected_group = st.selectbox(
        selectbox_label, list(groups.keys()), format_func=lambda g: g.replace("_", " ").title(),
    )
    versions = groups[selected_group]

    if len(versions) > 1:
        selected_backup = st.selectbox(f"Version ({len(versions)} saved)", versions)
    else:
        selected_backup = versions[0]

    backup_content = read_text(os.path.join(backup_dir, selected_backup))
    preview_key = f"{backup_dir}_{selected_backup}_preview"

    # Note: no st.rerun() here. This section runs inside an st.dialog whose
    # opening is gated behind `if st.button(open_button_label)` in the
    # parent scope (see backup_restore_modal below). Calling st.rerun()
    # forces a full top-to-bottom script rerun, and on that rerun the
    # open button's return value is False again - so the gate fails and
    # the dialog silently closes instead of showing the success message.
    # Letting Streamlit's normal automatic rerun (triggered by the button
    # click itself) run its course keeps the dialog open.
    if st.button(f"{overwrite_label_prefix} {selected_backup}"):
        current_content = read_text(path)
        if current_content.strip() and current_content != backup_content:
            backup_name = backup_markdown(current_content, backup_dir, backup_suffix)
            st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

        write_and_sync(path, backup_content, session_key)
        st.success(f"{success_message_prefix} {selected_backup}")

    with st.expander(f"Preview {selected_backup}", expanded=False):
        raw_or_rendered_preview(backup_content, key=preview_key)

    manage_backup_file(backup_dir, selected_backup)


def backup_restore_modal(*, modal_title, open_button_label, **section_kwargs):
    """Opens the backup/restore workflow (backup_restore_section) in a
    modal dialog instead of an inline expander, so browsing old strategy
    versions doesn't push the rest of the tab's content down/compete for
    space with the editor above it."""
    if st.button(open_button_label):
        _open_backup_dialog(modal_title, section_kwargs)


def _open_backup_dialog(modal_title, section_kwargs):
    @st.dialog(modal_title)
    def _dialog():
        backup_restore_section(**section_kwargs)

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

    with delete_col:
        with st.popover("Delete"):
            st.caption(f"Permanently delete {selected_backup}? This cannot be undone.")
            if st.button("Confirm delete", key=f"{backup_dir}_{selected_backup}_delete_confirm"):
                delete_backup(backup_dir, selected_backup)
                st.success(f"Deleted {selected_backup}")
