#!/bin/bash
set -e

# setup.sh - Automated Production Deployment Suite for AWS EC2 (Ubuntu 24.04 LTS)
echo "Starting setup..."

# 1. Swapfile creation (2GB) for t2.micro
if [ ! -f /swapfile ]; then
    echo "Creating 2GB swapfile..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 2. Package installation
echo "Installing system packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx sqlite3 curl

# 3. Virtualenv setup
echo "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# 4. Migration & Collectstatic & Seed Data
echo "Running Django setup..."
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data || echo "Seed data might have already been created."

# 5. Service deployment
echo "Deploying services..."
sudo cp deploy/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

sudo cp deploy/nginx.conf /etc/nginx/sites-available/sih
if [ ! -L /etc/nginx/sites-enabled/sih ]; then
    sudo ln -s /etc/nginx/sites-available/sih /etc/nginx/sites-enabled/
fi
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
sudo systemctl enable nginx

# Give www-data access to the gunicorn socket and static files
sudo chown -R ubuntu:www-data /home/ubuntu/sih-2026
sudo chmod -R 755 /home/ubuntu/sih-2026

echo "Setup complete! Application should be running."
