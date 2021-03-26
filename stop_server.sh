ps -ef | grep ".scrc/manage.py runserver" | grep -v grep | awk '{print $2}' | xargs kill
