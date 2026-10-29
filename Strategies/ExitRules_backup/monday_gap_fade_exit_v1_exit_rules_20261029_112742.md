# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: Monday Gap Fade Exit v1
Applies To: Monday Gap Fade Short v1 (a SHORT, INTRADAY strategy).
Do not pair it with a long or swing entry strategy.
Timeframe: Intraday - uses the entry day's OPEN and HIGH (explicitly allowed here)

---

## Position

This is a SHORT position opened at the entry day's open (`entry_price`) and
always closed the same day. `future_df` contains only the entry day.
`signal_history_df` ends on the signal day (the Friday).

---

## Exit Rules

Evaluate in this order.

### Rule 0: Entry Condition Not Met (ExitReason "NoEntry")

The trade only exists if Monday gaps up. Let:

- `signal_date` = the date of the last row of `signal_history_df`
- `signal_close` = the last close in `signal_history_df`
- `entry_day` = the date of `future_df`'s first row

Compare calendar dates (use `pd.Timestamp(x).date()`), not timestamps.

If (`entry_day` - `signal_date`) is not exactly 3 calendar days (i.e. the
entry is not the Monday right after a normal weekend), OR
`entry_price < 1.01 * signal_close`:
    return {"ExitDate": future_df.index[0], "ExitPrice": entry_price,
            "ExitReason": "NoEntry"}

The backtester drops "NoEntry" trades entirely.

### Rule 1: Stop-Loss Above Entry (ExitReason "SL")

- `stop = entry_price * 1.05`
- If the entry day's HIGH (`future_df["high"].iloc[0]`) is greater than or
  equal to `stop`, exit on the entry date at `ExitPrice = stop`,
  `ExitReason = "SL"`.

There is no profit target, so a touched stop is always a real stop-out,
whatever the order of the day's moves.

### Otherwise

Return None. The backtester then squares the position off at the entry
day's close (ExitReason "SquareOff"), as MIS requires.

Do not raise; return None on any missing data.
