#!/usr/bin/env bash
set -e

PI_USER="admin"
PI_HOST="192.168.178.94"
REMOTE_DIR="/home/admin/discord-bot"

echo "=========================================="
echo "🚀 Deploying Discord Bot to Raspberry Pi..."
echo "=========================================="

# 1. Ensure remote directory exists
ssh -o StrictHostKeyChecking=no "${PI_USER}@${PI_HOST}" "mkdir -p ${REMOTE_DIR}"

# 2. Copy project files
echo "📦 Copying files to ${PI_HOST}:${REMOTE_DIR}..."
scp -o StrictHostKeyChecking=no main.py requirements.txt .env "${PI_USER}@${PI_HOST}:${REMOTE_DIR}/"

# 3. Setup virtualenv and install dependencies on Pi
echo "🐍 Setting up Python virtual environment and installing dependencies on Pi..."
ssh -o StrictHostKeyChecking=no "${PI_USER}@${PI_HOST}" "bash -s" << 'EOF'
set -e
cd /home/admin/discord-bot

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing requirements..."
./venv/bin/pip install -q -r requirements.txt

echo "Dependencies successfully installed."
EOF

# 4. Setup and configure systemd service
echo "⚙️ Setting up systemd service..."
ssh -o StrictHostKeyChecking=no "${PI_USER}@${PI_HOST}" "cat << 'SERVICE' > /tmp/discord-bot.service
[Unit]
Description=Raspberry Pi Discord Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/discord-bot
ExecStart=/home/admin/discord-bot/venv/bin/python3 /home/admin/discord-bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE
echo 'jonajona' | sudo -S mv /tmp/discord-bot.service /etc/systemd/system/discord-bot.service
echo 'jonajona' | sudo -S systemctl daemon-reload
echo 'jonajona' | sudo -S systemctl enable discord-bot.service
"

echo "=========================================="
echo "✅ Deployment completed successfully!"
echo "=========================================="
echo "Um den Bot zu starten oder neu zu starten:"
echo "  ssh admin@192.168.178.94 'sudo systemctl restart discord-bot'"
echo "Um die Live-Logs zu sehen:"
echo "  ssh admin@192.168.178.94 'journalctl -u discord-bot -f'"
echo "=========================================="
