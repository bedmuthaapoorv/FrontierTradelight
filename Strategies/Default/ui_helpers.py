"""Shared Streamlit helpers used by tabs/*.py plugins.

Kept separate from any single tab so plugins stay self-contained: a new
tab module only needs to import from here, never reach into another tab's
file, which is what keeps merging in someone else's tabs/*.py additions
low-conflict.
"""

import os

import streamlit as st

from backup_utils import backup_markdown, list_backups
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


def strategy_editor(*, session_key, path, guide_filename, guide_label, backup_dir,
                     backup_suffix, backup_label, text_area_label, text_area_height,
                     save_button_label, save_success_message, no_backups_caption):
    """Renders the edit/save/restore workflow shared by rules.md and exit_rules.md."""
    show_guide(guide_filename, guide_label)
    load_into_session(session_key, path)

    edited = st.text_area(
        text_area_label,
        value=st.session_state[session_key],
        height=text_area_height,
        label_visibility="collapsed",
    )

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

    if show_in_expander:
        st.code(backup_content, language="markdown")
    else:
        with st.expander(f"Preview {selected_backup}"):
            st.code(backup_content, language="markdown")

    if st.button(f"{overwrite_label_prefix} {selected_backup}"):
        current_content = read_text(path)
        if current_content.strip() and current_content != backup_content:
            backup_name = backup_markdown(current_content, backup_dir, backup_suffix)
            st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

        write_text(path, backup_content)
        st.session_state[session_key] = backup_content
        st.success(f"{success_message_prefix} {selected_backup}")
        st.rerun()
