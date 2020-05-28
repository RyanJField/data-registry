from django.urls import path, include
from django.utils.text import camel_case_to_spaces
from rest_framework import routers

from . import views, api_views, models

router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'groups', api_views.GroupViewSet)

for name in models.all_models:
    url_name = camel_case_to_spaces(name).replace(' ', '_')
    router.register(url_name, getattr(api_views, name + 'ViewSet'), basename=name.lower())

urlpatterns = [
    path('', views.index, name='index'),
    path('', include(router.urls)),
    path('issues/', views.IssueListView.as_view(), name='issues'),
    path('issue/<int:pk>', views.IssueDetailView.as_view(), name='issue'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include(router.urls)),
]


for name in models.all_object_models:
    url_name = camel_case_to_spaces(name).replace(' ', '_')
    urlpatterns.append(path(url_name + '/<int:pk>', getattr(views, name + 'DetailView').as_view(), name=name.lower()))
    urlpatterns.append(path(url_name + 's/', getattr(views, name + 'ListView').as_view(), name=name.lower() + 's')) 
