#!/bin/bash
# Installation script for Raspilapse Dashboard

set -e

echo "=== Raspilapse Dashboard Installation ==="

cd /home/pi/dashboard-raspilapse

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install flask gunicorn pyyaml

# Make run.py executable
chmod +x run.py

# Enable Apache modules
echo "Enabling Apache modules..."
sudo a2enmod proxy proxy_http cgid

# Install Apache configuration
echo "Installing Apache configuration..."
sudo cp apache/raspilapse-dashboard.conf /etc/apache2/sites-available/

# Disable default site and enable dashboard site
sudo a2dissite 000-default.conf 2>/dev/null || true
sudo a2ensite raspilapse-dashboard.conf

# Install systemd service
echo "Installing systemd service..."
sudo cp systemd/raspilapse-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspilapse-dashboard

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start the dashboard:"
echo "  sudo systemctl start raspilapse-dashboard"
echo "  sudo systemctl restart apache2"
echo ""
echo "Dashboard will be available at: http://$(hostname)/"
echo ""
echo "For development, run:"
echo "  source venv/bin/activate && python run.py"
echo ""
echo "Static HTML files (tablet.html, etc) are still served by Apache."
echo "Static files (images/videos) are still served by Apache."
