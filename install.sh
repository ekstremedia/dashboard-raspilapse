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

# Update Apache site config to proxy to Flask (except static files and CGI)
echo "Updating Apache configuration..."
sudo tee /etc/apache2/sites-available/raspilapse-dashboard.conf > /dev/null << 'EOF'
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    <Directory /var/www/html>
        Options FollowSymLinks ExecCGI
        AllowOverride None
        Require all granted
        AddHandler cgi-script .cgi
    </Directory>

    # Static files served directly by Apache
    ProxyPass /status.jpg !

    # CGI scripts handled by Apache
    ProxyPassMatch ^/.*\.cgi$ !

    <LocationMatch "^/gallery/image/">
        ProxyPass !
    </LocationMatch>
    Alias /gallery/image /var/www/html/images

    <LocationMatch "^/videos/file/">
        ProxyPass !
    </LocationMatch>
    Alias /videos/file /var/www/html/videos

    # Everything else goes to Flask
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
EOF

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
echo "The old index.html has been replaced by the dashboard."
echo "Static files (images/videos) are still served by Apache."
