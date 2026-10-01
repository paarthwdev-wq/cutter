@echo off
title Telegram AI Video Clipper
cd /d "%~dp0"
set PYTHONPATH=.
python telegram_clipper\main.py
pause
