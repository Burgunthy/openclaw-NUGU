#!/bin/bash

# NUGU + OpenClaw + Home Assistant Integration Setup Script
# This script helps you set up the project

set -e

echo "=========================================="
echo "NUGU + OpenClaw + HA Integration Setup"
echo "=========================================="
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Detect OS
OS="$(uname -s)"
echo "Detected OS: $OS"

# Create necessary directories
echo "Creating directories..."
mkdir -p webhook-server/logs
mkdir -p screenshots
mkdir -p openclaw/skills

# Check Python version
echo ""
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "Python version: $PYTHON_VERSION"

    # Check if version is 3.9 or higher
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        echo "Warning: Python 3.9 or higher is recommended."
    fi
else
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
cd webhook-server
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Generate secure token
echo ""
echo "Generating secure token..."
TOKEN=$(openssl rand -hex 32)
echo "Generated token: $TOKEN"
echo ""
echo "IMPORTANT: Save this token! You'll need it for configuration."
echo "Token: $TOKEN" > .token
chmod 600 .token

# Update config files with generated token
echo ""
echo "Updating configuration files..."
sed -i.bak "s/YOUR_OPENCLAW_TOKEN/$TOKEN/g" webhook-server/config.yml
sed -i.bak "s/YOUR_SECURE_TOKEN_HERE/$TOKEN/g" openclaw/config.yml

# Prompt for network configuration
echo ""
echo "=========================================="
echo "Network Configuration"
echo "=========================================="
echo ""
echo "Please enter the following information:"
read -p "Home Assistant IP (default: 192.168.1.100): " HA_IP
HA_IP=${HA_IP:-192.168.1.100}

read -p "OpenClaw PC IP (default: 192.168.1.200): " OC_IP
OC_IP=${OC_IP:-192.168.1.200}

read -p "Home Assistant Port (default: 8123): " HA_PORT
HA_PORT=${HA_PORT:-8123}

# Update config files with IPs
sed -i.bak "s/192.168.1.100/$HA_IP/g" webhook-server/config.yml
sed -i.bak "s/192.168.1.100/$HA_IP/g" home-assistant/configuration.yaml
sed -i.bak "s/192.168.1.200/$OC_IP/g" webhook-server/config.yml
sed -i.bak "s/192.168.1.200/$OC_IP/g" home-assistant/configuration.yaml
sed -i.bak "s/8123/$HA_PORT/g" webhook-server/config.yml
sed -i.bak "s/8123/$HA_PORT/g" home-assistant/configuration.yaml

# Clean up backup files
rm -f webhook-server/config.yml.bak
rm -f openclaw/config.yml.bak
rm -f home-assistant/configuration.yaml.bak

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy openclaw/config.yml to ~/.openclaw/config.yml on your OpenClaw PC"
echo "2. Copy home-assistant/*.yaml to your Home Assistant configuration"
echo "3. Update Home Assistant files with your HA Long-Lived Access Token"
echo "4. Run: cd webhook-server && source venv/bin/activate && python app.py"
echo "5. Or use Docker: docker-compose up -d"
echo ""
echo "For detailed instructions, see docs/SETUP.md"
