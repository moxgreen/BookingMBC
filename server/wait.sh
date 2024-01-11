#!/bin/sh

echo Hello
while ! nc -z db 3306 ; do
    echo "Waiting for the MySQL Server"
    sleep 3
done
python manage.py makemigrations
python manage.py migrate
export PYTHONMALLOC=debug
gunicorn --bind 0.0.0.0:8001 BookingMBC.wsgi