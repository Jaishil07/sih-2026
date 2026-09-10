#!/bin/bash
set -e

echo "Pulling latest code..."
git pull origin develop

echo "Activating virtualenv and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Running migrations and collecting static files..."
python manage.py migrate
python manage.py collectstatic --noinput

echo "Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "Update complete!"
