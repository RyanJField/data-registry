#!/bin/bash
cd ..
find . -path '*/migrations/*.py*' -not -path './venv/*' -not -name '__init__.py' -delete
rm db.sqlite3
python3 manage.py makemigrations custom_user
python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py graph_models data_management --arrow-shape crow -X "BaseModel,DataObject,DataObjectVersion" -E -o schema.dot
dot schema.dot -Tsvg -o static/images/schema.svg
python3 manage.py collectstatic --noinput > /dev/null 2>&1
python3 manage.py createsuperuser --noinput
