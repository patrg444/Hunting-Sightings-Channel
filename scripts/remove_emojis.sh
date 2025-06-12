#!/bin/bash

echo "Running emoji removal script..."
echo

# Make sure we're in the project root
cd "$(dirname "$0")/.."

# Run the Python script
python3 scripts/remove_emojis.py

echo
echo "Emoji removal complete!"
