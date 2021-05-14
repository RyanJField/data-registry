python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py graph_models data_management --arrow-shape crow -X "BaseModel,DataObject,DataObjectVersion" -E -o schema.dot
dot schema.dot -Tsvg -o static/images/schema.svg
dot schema.dot -Tpng -o static/images/schema.png
