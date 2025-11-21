#!/bin/sh
echo "Starting hostmanager " && uv run python hostmanager.py &
echo "Starting web interface " && uv run python app.py
