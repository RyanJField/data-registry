#!/bin/bash
cd ..
find . -path '*/migrations/*.py*' -not -path './venv/*' -not -name '__init__.py' -delete
rm db.sqlite3
python3 manage.py makemigrations custom_user
python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser --noinput
