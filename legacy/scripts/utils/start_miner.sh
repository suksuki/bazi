#!/bin/bash
# Startup script for Antigravity Miner Service (The "Yin" System)
# This service handles background tasks: Video downloading, Theory mining, and Model training.

echo "Starting Antigravity Miner Service..."
echo "Log file: miner.log"

# Ensure virtualenv is active if possible (heuristic)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run in background with nohup, or foreground if requested?
# User might want to see output. Let's run in foreground for now or use &
# But typically a service runs in background.
# "Make it an independent application".

python3 service/miner_app.py
