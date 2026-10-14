"""Streams a script's stdout to the frontend as it runs, one line per
chunk, ending with an __EXIT_CODE__ marker line - the same
Popen(stdout=PIPE, stderr=STDOUT, text=True) pattern ui_helpers.run_script
already uses for the Streamlit app, just streamed over HTTP instead of
written into st.empty().
"""

import subprocess
import sys
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from constants import APP_DIR

router = APIRouter(prefix="/jobs")


def _stream_script(script_name: str) -> Iterator[str]:
    process = subprocess.Popen(
        [sys.executable, script_name],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        yield line if line.endswith("\n") else line + "\n"
    process.wait()
    yield f"__EXIT_CODE__:{process.returncode}\n"


@router.post("/generate-screener")
def generate_screener():
    return StreamingResponse(_stream_script("generate_screener.py"), media_type="text/plain")


@router.post("/run-screener")
def run_screener():
    return StreamingResponse(_stream_script("stock_screener.py"), media_type="text/plain")


@router.post("/generate-exit-strategy")
def generate_exit_strategy():
    return StreamingResponse(_stream_script("generate_exit_strategy.py"), media_type="text/plain")


@router.post("/check-exit-signals")
def check_exit_signals():
    return StreamingResponse(_stream_script("sell_screener.py"), media_type="text/plain")


@router.post("/fetch-fundamentals")
def fetch_fundamentals():
    return StreamingResponse(_stream_script("fetch_fundamentals.py"), media_type="text/plain")
