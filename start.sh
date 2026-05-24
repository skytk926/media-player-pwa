#!/bin/bash
cd "$(dirname "$0")"
pkill -f "python3 server.py" 2>/dev/null
pkill -f cloudflared 2>/dev/null
echo "Starting server..."
python3 server.py &
sleep 3
echo "Starting tunnel..."
/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8900 2>&1 | while read line; do
  echo "$line" | grep -o 'https://[^ ]*\.trycloudflare\.com' | while read url; do
    echo ""
    echo ">>> Tunnel URL: $url <<<"
    echo ""
  done
done
