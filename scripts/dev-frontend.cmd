@echo off
setlocal
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "NODE_DIR=%ROOT%\.tools\node"
set "PATH=%NODE_DIR%;%PATH%"
cd /d "%ROOT%\frontend"
"%NODE_DIR%\npm.cmd" run dev -- --hostname 127.0.0.1 --port 3000
