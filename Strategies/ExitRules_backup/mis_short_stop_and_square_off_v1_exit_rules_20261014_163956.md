# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: MIS Short Stop and Square-off v1
Applies To: Momentum Loser Intraday Short v1 (a SHORT, INTRADAY strategy).
Do not pair it with a long or swing entry strategy.
Timeframe: Intraday - uses the entry day's HIGH (explicitly allowed here)

---

## Position

This is a SHORT position opened at the entry day's open (`entry_price`) and
always closed the same day. `future_df` contains only the entry day.

---

## Exit Rules

### Rule 1: Stop-Loss Above Entry (ExitReason "SL")

- `ATR = ATR(14)` computed from `signal_history_df` (the day before entry),
  using pandas_ta `ta.atr(high, low, close, length=14)`, last value.
- `stop = entry_price + 1.0 * ATR`
- If the entry day's HIGH (`future_df["high"].iloc[0]`) is greater than or
  equal to `stop`, the stop was hit: exit on the entry date at
  `ExitPrice = stop`, `ExitReason = "SL"`.

With daily bars we can't know whether the high came before or after the
day's fall, so a touched stop is always assumed to have been hit
(pessimistic).

### Otherwise

Return None. The backtester then squares the position off at the entry
day's close (ExitReason "SquareOff"), as MIS requires.

If ATR can't be computed (too little history), return None.
