find . -path '*/migrations/*.py*' -not -path './venv/*' -not -name '__init__.py' -delete
rm db.sqlite3
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
python3 manage.py makemigrations custom_user
python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py createsuperuser --noinput
