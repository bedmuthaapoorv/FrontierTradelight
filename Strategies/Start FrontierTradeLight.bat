@echo off
REM Double-click entry point on Windows - runs the real launcher
REM ("Start FrontierTradeLight.ps1") in PowerShell with the execution
REM policy bypassed just for this process, so double-clicking in Explorer
REM works even on a machine with script execution locked down by default.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start FrontierTradeLight.ps1"
pause
