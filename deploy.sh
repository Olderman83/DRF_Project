#!/bin/bash

set -e

echo "Starting deployment..."

cd /opt/lms

echo "Pulling latest changes..."
git pull origin main

echo "Stopping containers..."
docker-compose down

echo "Rebuilding containers..."
docker-compose build

echo "Starting containers..."
docker-compose up -d

echo "Running migrations..."
docker-compose exec -T web python manage.py migrate

echo "Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo "Restarting services..."
docker-compose restart web celery celery-beat

echo "Deployment completed successfully!"
