#!/bin/bash
# Deployment script for logwatch-ai
# Usage: sudo bash deploy.sh

set -e

echo "=========================================="
echo "logwatch-ai Deployment Script"
echo "=========================================="

# Configuration
PROJECT_DIR="/opt/logwatch-with-ai"
PYTHON_VERSION=3

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Step 1: Verify prerequisites
echo "[1/7] Checking prerequisites..."
command -v logwatch >/dev/null 2>&1 || { echo "logwatch is not installed. Please run: apt-get install logwatch"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is not installed."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "pip3 is not installed."; exit 1; }

# Step 2: Install Python dependencies
echo "[2/7] Installing Python dependencies..."
pip3 install -r "$PROJECT_DIR/requirements.txt"

# Step 3: Create directory structure
echo "[3/7] Creating directory structure..."
mkdir -p "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR"

# Step 4: Copy configuration files
echo "[4/7] Installing configuration files..."
cp "$PROJECT_DIR/config/logwatch-ai.cron" /etc/cron.d/logwatch-ai
chmod 644 /etc/cron.d/logwatch-ai

cp "$PROJECT_DIR/config/logwatch-ai.logrotate" /etc/logrotate.d/logwatch-ai
chmod 644 /etc/logrotate.d/logwatch-ai

# Step 5: Set file permissions
echo "[5/7] Setting file permissions..."
chmod 755 "$PROJECT_DIR/src/main.py"
chmod 644 "$PROJECT_DIR/src"/*.py
chmod 755 "$PROJECT_DIR"

# Step 6: Create log directories
echo "[6/7] Creating log directories..."
mkdir -p /var/log
touch /var/log/logwatch-ai.log
chmod 640 /var/log/logwatch-ai.log

# Step 7: Verify configuration
echo "[7/7] Verifying installation..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Please copy .env.example to .env and configure:"
    echo "   cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
    echo "   nano $PROJECT_DIR/.env"
else
    echo "✓ .env file found"
fi

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure environment variables:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Test the script manually:"
echo "   cd $PROJECT_DIR"
echo "   source .env"
echo "   python3 src/main.py"
echo ""
echo "3. Verify Cron job:"
echo "   cat /etc/cron.d/logwatch-ai"
echo ""
echo "4. View logs:"
echo "   tail -f /var/log/logwatch-ai.log"
echo ""
