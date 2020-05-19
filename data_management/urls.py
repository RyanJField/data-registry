from django.urls import path
from django.utils.text import camel_case_to_spaces

from . import views
from .models import all_object_models

urlpatterns = [
    path('', views.index, name='index'),
    path('issue/', views.IssueListView.as_view(), name='issues'),
    path('issue/<int:pk>', views.IssueDetailView.as_view(), name='issue')
]

for name in all_object_models:
    url_name = camel_case_to_spaces(name).replace(' ', '_')
    urlpatterns.append(path(url_name + '/<int:pk>', getattr(views, name + 'DetailView').as_view(), name=name.lower()))
    urlpatterns.append(path(url_name + '/', getattr(views, name + 'ListView').as_view(), name=name.lower() + 's')) 
