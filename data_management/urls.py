from django.urls import path, include
from django.utils.text import camel_case_to_spaces
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import views
from .models import all_object_models

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('', include(router.urls)),
    path('issue/', views.IssueListView.as_view(), name='issues'),
    path('issue/<int:pk>', views.IssueDetailView.as_view(), name='issue'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

#urlpatterns = format_suffix_patterns(urlpatterns)

for name in all_object_models:
    url_name = camel_case_to_spaces(name).replace(' ', '_')
    urlpatterns.append(path(url_name + '/<int:pk>', getattr(views, name + 'DetailView').as_view(), name=name.lower()))
    urlpatterns.append(path(url_name + 's/', getattr(views, name + 'ListView').as_view(), name=name.lower() + 's')) 
    urlpatterns.append(path('api/' + url_name + 's/', getattr(views, name + 'List').as_view()))
    urlpatterns.append(path('api/' + url_name + '/<int:pk>', getattr(views, name + 'Detail').as_view()))
