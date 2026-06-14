#!/bin/bash
echo "========================================================"
echo "   Starting Auto TikTok Poster with Remote Access"
echo "========================================================"

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Apply patches
python3 patch_uploader.py >/dev/null 2>&1

# Start the dashboard in the background
echo "Starting Local Dashboard..."
nohup python3 app.py > bot_server.log 2>&1 &

echo ""
echo "========================================================"
echo "Bot is running in the background!"
echo "Generating your public internet URL..."
echo "========================================================"
echo ""
echo "Look for the URL ending in '.lhr.life' below."
echo "You can access that link from your phone anywhere in the world!"
echo ""

# Run the SSH tunnel
ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 nokey@localhost.run
