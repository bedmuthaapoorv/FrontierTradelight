"""Read-only view of a screener/sell-screener report CSV, the same files
tabs/results.py and tabs/sell.py already read in the Streamlit app - no new
logic, just serialization. Parameterized so /results (stock_report.csv) and
/sell-report (sell_report.csv) share one implementation.
"""

import os

import pandas as pd
from fastapi import APIRouter


def make_report_router(*, prefix, path):
    router = APIRouter(prefix=prefix)

    @router.get("")
    def get_report():
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return {"columns": [], "rows": []}

        df = pd.read_csv(path)
        # NaN (missing Details columns on failed rows) isn't valid JSON.
        # astype(object) first: assigning None into a still-float64 column
        # silently reverts it back to NaN instead of keeping None.
        df = df.astype(object).where(pd.notnull(df), None)
        return {"columns": list(df.columns), "rows": df.to_dict("records")}

    return router
