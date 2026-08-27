"""Edit rules.md and load previously backed-up strategies."""

import streamlit as st

import strings
from constants import BACKUP_DIR, RULES_PATH
from ui_helpers import backup_restore_modal, strategy_editor

TITLE = "Rules"
ORDER = 10


def render():
    st.subheader("Edit rules.md")

    strategy_editor(
        session_key="rules_content",
        path=RULES_PATH,
        guide_filename="RULES_GUIDE.md",
        guide_label="New to rules.md? Read the guide",
        backup_dir=BACKUP_DIR,
        backup_suffix="rules",
        backup_label="Rules_backup",
        text_area_label="Strategy rules",
        text_area_height=600,
        save_button_label="Save rules.md",
        save_success_message="Saved rules.md",
        no_backups_caption=strings.NO_RULES_BACKUPS_CAPTION,
    )

    st.divider()

    backup_restore_modal(
        modal_title="Load a previous strategy",
        open_button_label="Load a previous strategy",
        path=RULES_PATH,
        backup_dir=BACKUP_DIR,
        backup_suffix="rules",
        backup_label="Rules_backup",
        session_key="rules_content",
        no_backups_caption=strings.NO_RULES_BACKUPS_CAPTION,
        selectbox_label="Choose a backed-up strategy",
        overwrite_label_prefix="Overwrite rules.md with",
        success_message_prefix="rules.md overwritten with",
    )
