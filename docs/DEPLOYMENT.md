# Deployment Guide for Tracy E-Learning System

This document provides instructions for deploying the Tracy E-Learning System to a production environment.

## Prerequisites

- A server running Linux (Ubuntu/Debian recommended)
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Nginx
- Domain name (optional, but recommended)
- SSL certificate (strongly recommended for production)

## Step 1: Set Up the Server

### Update the system
```bash
sudo apt update
sudo apt upgrade -y
```

### Install required packages
```bash
sudo apt install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl
```

### Set up PostgreSQL database
```bash
sudo -u postgres psql
```

In the PostgreSQL shell:
```sql
CREATE DATABASE tracy_lms;
CREATE USER tracy_user WITH PASSWORD 'secure_password';
ALTER ROLE tracy_user SET client_encoding TO 'utf8';
ALTER ROLE tracy_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tracy_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE tracy_lms TO tracy_user;
\q
```

## Step 2: Clone and Configure the Application

### Create a directory for the application
```bash
mkdir -p /var/www/tracy_lms
cd /var/www/tracy_lms
```

### Clone the repository
```bash
git clone <repository-url> .
```

### Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install requirements
```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Create a production settings file
Create a file called `production_settings.py` in the `elearning_system` folder:

```python
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tracy_lms',
        'USER': 'tracy_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
```

### Collect static files
```bash
python manage.py collectstatic
```

### Apply migrations
```bash
python manage.py migrate
```

### Create a superuser
```bash
python manage.py createsuperuser
```

## Step 3: Configure Gunicorn

### Create a systemd service file
```bash
sudo nano /etc/systemd/system/tracy_lms.service
```

Add the following content:
```
[Unit]
Description=Tracy LMS Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/tracy_lms
ExecStart=/var/www/tracy_lms/venv/bin/gunicorn --workers 3 --bind unix:/var/www/tracy_lms/tracy_lms.sock elearning_system.wsgi:application --env DJANGO_SETTINGS_MODULE=elearning_system.production_settings

[Install]
WantedBy=multi-user.target
```

### Set proper permissions
```bash
sudo chown -R www-data:www-data /var/www/tracy_lms
```

### Start and enable the service
```bash
sudo systemctl start tracy_lms
sudo systemctl enable tracy_lms
```

## Step 4: Configure Nginx

### Create an Nginx server block
```bash
sudo nano /etc/nginx/sites-available/tracy_lms
```

Add the following content:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/tracy_lms/static/;
    }

    location /media/ {
        alias /var/www/tracy_lms/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/tracy_lms/tracy_lms.sock;
    }
}
```

### Enable the server block
```bash
sudo ln -s /etc/nginx/sites-available/tracy_lms /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: Secure with SSL (Let's Encrypt)

### Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain and install SSL certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to complete the SSL setup.

### Set up automatic renewal
Certbot creates a cron job for renewal by default, but you can verify it:
```bash
sudo systemctl status certbot.timer
```

## Step 6: Logging and Monitoring

### Configure logging
Update the production settings file to include detailed logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/tracy_lms/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

Create the log directory:
```bash
sudo mkdir -p /var/log/tracy_lms
sudo chown www-data:www-data /var/log/tracy_lms
```

### Set up database backups
Create a backup script:
```bash
sudo nano /usr/local/bin/backup_tracy_db.sh
```

Add the following content:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/tracy_lms"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR
pg_dump tracy_lms -U tracy_user > $BACKUP_DIR/tracy_lms_$TIMESTAMP.sql
find $BACKUP_DIR -type f -mtime +7 -name "tracy_lms_*.sql" -delete
```

Make it executable and set up a daily cron job:
```bash
sudo chmod +x /usr/local/bin/backup_tracy_db.sh
sudo crontab -e
```

Add the following line:
```
0 2 * * * /usr/local/bin/backup_tracy_db.sh
```

## Step 7: Final Steps

### Test the deployment
1. Visit your domain in a web browser
2. Verify that HTTPS is working correctly
3. Test login functionality 
4. Test course creation and enrollment

### Set up monitoring (optional)
Consider setting up monitoring with tools like:
- Prometheus + Grafana
- New Relic
- Datadog

### Performance tuning
Adjust Gunicorn workers based on server resources:
```
workers = (2 x CPU cores) + 1
```

### Firewall configuration
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## Troubleshooting

### Check application logs
```bash
sudo tail -f /var/log/tracy_lms/django.log
```

### Check Nginx logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Gunicorn service
```bash
sudo systemctl status tracy_lms
sudo journalctl -u tracy_lms
```

### Database issues
```bash
sudo -u postgres psql -d tracy_lms
```

## Updates and Maintenance

### Deploying updates
```bash
cd /var/www/tracy_lms
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart tracy_lms
```

### Backup before major changes
```bash
sudo -u postgres pg_dump tracy_lms > /var/backups/tracy_lms_pre_update.sql
tar -czf /var/backups/tracy_lms_files_pre_update.tar.gz /var/www/tracy_lms
```

This deployment guide covers the essential steps for deploying the Tracy E-Learning System in a production environment. Adjust the configuration according to your specific requirements and server setup.
