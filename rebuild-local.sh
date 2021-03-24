find . -path '*/migrations/*.py*' -not -path './venv/*' -not -name '__init__.py' -delete
rm db.sqlite3
export SCRC_REGISTRY=local
python3 manage.py makemigrations custom_user
python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py createsuperuser --username admin
