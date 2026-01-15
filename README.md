# Raspilapse Dashboard

A web dashboard for managing the [Raspilapse](https://github.com/your-repo/raspilapse) timelapse system on Raspberry Pi.

## Features

- **Live View** - Latest captured image with auto-refresh and quick stats
- **Timelapse Generator** - Generate timelapse videos with customizable options
- **Config Editor** - Edit raspilapse configuration with validation and backups
- **Image Gallery** - Browse captured images by date
- **Video Library** - View and download generated timelapses
- **System Status** - Monitor CPU, memory, disk usage, and service status
- **Log Viewer** - View raspilapse logs in real-time

## Requirements

- Raspberry Pi (tested on Pi 4/5)
- Raspilapse installed at `/home/pi/raspilapse/`
- Apache2 web server
- Python 3.9+

## Installation

### 1. Clone the repository

```bash
cd /home/pi
git clone https://github.com/your-repo/dashboard-raspilapse.git
cd dashboard-raspilapse
```

### 2. Run the install script

```bash
chmod +x install.sh
./install.sh
```

This will:
- Create a Python virtual environment
- Install dependencies (Flask, Gunicorn, PyYAML)
- Enable Apache proxy modules
- Configure Apache to serve the dashboard
- Install and enable the systemd service

### 3. Start the services

```bash
sudo systemctl start raspilapse-dashboard
sudo systemctl restart apache2
```

### 4. Access the dashboard

Open your browser and go to:
```
http://<your-pi-ip>/
```

## Manual Installation

If you prefer to install manually:

### Create virtual environment and install dependencies

```bash
cd /home/pi/dashboard-raspilapse
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn pyyaml
```

### Create logs directory

```bash
mkdir -p logs
```

### Enable Apache modules

```bash
sudo a2enmod proxy proxy_http
```

### Create Apache site configuration

```bash
sudo nano /etc/apache2/sites-available/raspilapse-dashboard.conf
```

Add the following content:

```apache
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    <Directory /var/www/html>
        Options FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    # Static files served directly by Apache
    ProxyPass /status.jpg !

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
```

### Enable the site

```bash
sudo a2dissite 000-default.conf
sudo a2ensite raspilapse-dashboard.conf
sudo systemctl reload apache2
```

### Install systemd service

```bash
sudo cp systemd/raspilapse-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspilapse-dashboard
sudo systemctl start raspilapse-dashboard
```

## Configuration

The dashboard expects raspilapse to be installed at `/home/pi/raspilapse/`. If your installation is different, edit `app/config.py`:

```python
RASPILAPSE_ROOT = '/home/pi/raspilapse'
RASPILAPSE_CONFIG = '/home/pi/raspilapse/config/config.yml'
RASPILAPSE_LOGS = '/home/pi/raspilapse/logs'
IMAGES_DIR = '/var/www/html/images'
VIDEOS_DIR = '/var/www/html/videos'
STATUS_IMAGE = '/var/www/html/status.jpg'
```

## Usage

### Generating Timelapses

1. Go to the **Timelapse** page
2. Set start and end times
3. Choose options (HD, Hardware encoding, Slitscan, etc.)
4. Click **Generate Timelapse**

The dashboard enforces single-instance execution - you cannot start a new timelapse if one is already running or if ffmpeg is active.

### Editing Configuration

1. Go to the **Config** page
2. Edit the YAML configuration
3. Click **Validate** to check for errors
4. Click **Save** to apply changes

A backup is automatically created before each save. You can restore previous backups using the **Backups** button.

## Development

To run in development mode:

```bash
cd /home/pi/dashboard-raspilapse
source venv/bin/activate
python run.py
```

The development server runs on `http://0.0.0.0:5000` with debug mode enabled.

## Service Management

```bash
# Check status
sudo systemctl status raspilapse-dashboard

# View logs
journalctl -u raspilapse-dashboard -f

# Restart
sudo systemctl restart raspilapse-dashboard

# Stop
sudo systemctl stop raspilapse-dashboard
```

## Troubleshooting

### Dashboard not loading

1. Check if the service is running:
   ```bash
   sudo systemctl status raspilapse-dashboard
   ```

2. Check Apache error logs:
   ```bash
   sudo tail -f /var/log/apache2/error.log
   ```

3. Check dashboard logs:
   ```bash
   tail -f /home/pi/dashboard-raspilapse/logs/error.log
   ```

### Permission errors on /videos or /images

Make sure Apache has the correct configuration and the proxy modules are enabled:
```bash
sudo a2enmod proxy proxy_http
sudo systemctl restart apache2
```

### Timelapse won't start

The dashboard checks for running `ffmpeg` or `make_timelapse.py` processes. Check if any are running:
```bash
pgrep -f ffmpeg
pgrep -f make_timelapse.py
```

## License

MIT License
