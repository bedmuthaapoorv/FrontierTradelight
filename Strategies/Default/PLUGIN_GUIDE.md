# How to Create a Plugin (Tab) for Frontier TradeLight

Every tab you see in the app - Rules, Run, Results, Sell, Backtest - is a
self-contained plugin: one file in `tabs/`, discovered automatically by
`app.py`. Adding a new tab means adding a new file, not editing a shared
list that everyone else is also editing - that's what keeps two people's
tabs from colliding when merging forks.

---

## The contract

A plugin is any `tabs/your_module.py` that defines:

```python
TITLE = "Your Tab Name"   # required - shown as the tab label

def render():             # required - called with your tab active
    ...
```

That's the whole interface. `tabs/__init__.py`'s `discover_tabs()` imports
every `.py` file in `tabs/` (skipping ones starting with `_`), checks each
has `TITLE` and `render`, and raises immediately if either is missing - so
a broken plugin fails loudly at startup, not silently at click-time.

### Optional: ORDER

```python
ORDER = 45   # default is 100 if omitted
```

Tabs are sorted left-to-right by `(ORDER, TITLE)`. Current tabs use
`10, 20, 30, 40, 50` - spaced out on purpose so you can slot a new tab
in between (e.g. `ORDER = 25` to land between Run and Results) without
renumbering anyone else's plugin. If you don't care where your tab lands,
just omit `ORDER` and it'll land at the end.

---

## Minimal example

```python
# tabs/watchlist.py
"""One-line description of what this tab does."""

import streamlit as st

TITLE = "Watchlist"
ORDER = 45


def render():
    st.subheader("My Watchlist")
    st.write("Nothing here yet.")
```

Drop that file in `tabs/`, restart the app, and a "Watchlist" tab appears
between Run and Results - no other file touched.

---

## What's available to you

### From `ui_helpers.py`

Shared patterns already used by the built-in tabs - reach for these before
writing your own version of the same thing:

| Function | Use it for |
|---|---|
| `read_text(path)` / `write_text(path, content)` | UTF-8 file I/O (plain `open()` breaks on ₹ and other non-ASCII on Windows) |
| `run_script(script_name, args=None)` | Run a `.py` script in `Default/` as a subprocess, streaming its stdout live into the page |
| `run_script_with_feedback(button_label, script_name, spinner_text, success_text)` | A button that runs a script with a spinner + success/error message - the common case |
| `show_guide(filename, expander_label)` | Render a markdown guide file inside a collapsed `st.expander` |
| `nonempty_csv_exists(path)` | `os.path.exists(path) and os.path.getsize(path) > 0` - guards against `pd.errors.EmptyDataError` on a 0-byte CSV |
| `load_into_session(session_key, path)` | Load a file's contents into `st.session_state` once, on first render |
| `save_with_backup(path, backup_dir, suffix, backup_label, new_content, session_key)` | Back up a file's current contents, then overwrite it |
| `strategy_editor(...)` / `backup_restore_section(...)` | The full edit/save/restore workflow used by the Rules and Sell tabs - reach for these if your plugin edits + backs up a markdown file the same way |

### From `constants.py`

All the project's file paths (`APP_DIR`, `RULES_PATH`, `EXIT_RULES_PATH`,
`BACKTEST_TRADES_PATH`, `HOLDINGS_PATH`, etc.) - import what you need
rather than hardcoding paths. If your plugin introduces a new persistent
file, add its path here rather than inlining a string in your module.

### From `strings.py`

Longer UI copy (captions, help text, warnings) lives here, not inline in
tab code, so `tabs/*.py` stays focused on layout/logic. If your plugin has
a caption longer than a short one-liner, add a constant here and reference
it - keeps the pattern consistent with every other tab.

### `st.session_state`

Shared globally across all tabs (that's how Streamlit works - there's no
way to sandbox it per-plugin). Prefix your keys with something specific to
your plugin (e.g. `watchlist_df`, not `df`) to avoid colliding with another
tab's session state.

---

## Conventions to follow

- **One file, one tab.** If your tab needs multiple sections, use private
  helper functions within your module (see `tabs/backtest.py` or
  `tabs/sell.py` for examples of a tab broken into
  `render_config()` / `render_run_controls()` / etc., all called from the
  top-level `render()`).
- **Don't import from another `tabs/*.py` module.** If two tabs need to
  share logic, that logic belongs in `ui_helpers.py`, not in one tab
  importing from another - keeps plugins independent and mergeable.
- **New persistent files are gitignored by default for generated data.**
  If your plugin writes a CSV/log that's per-user runtime output (not
  something to commit), add it to `.gitignore` alongside the existing
  `stock_report.csv`, `backtest_trades.csv`, etc.
- **A subprocess script, not inline logic, for anything slow or
  NSE-fetching.** The existing tabs never fetch data or run a backtest
  inline in the Streamlit process - they shell out to a dedicated `.py`
  script via `run_script()`/`run_script_with_feedback()`, so the UI stays
  responsive and the same script is independently testable from the CLI.

---

## Testing your plugin

```bash
streamlit run app.py
```

or use the `stock-screener-ui` launch config
(`.claude/launch.json`) if you're working with Claude Code. If your
plugin's `TITLE`/`render()` contract is broken, `discover_tabs()` raises an
`AttributeError` immediately on startup, naming the offending module - fix
and rerun.
