from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.utils.decorators import classonlymethod
from django.utils.text import camel_case_to_spaces
from collections import namedtuple
from rest_framework import viewsets, permissions, mixins, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import Group
from custom_user.models import User


from . import models, serializers
#from .serializers import UserSerializer, GroupSerializer, ModelSerializer

def index(request):
    ObjectCount = namedtuple('object', 'name display_name count')
    model_names = models.all_object_models
    object_counts = []
    for model_name in model_names:
        count = getattr(models, model_name).objects.count()
        name = model_name.lower() + 's'
        display_name = camel_case_to_spaces(model_name)
        object_counts.append(ObjectCount(name, display_name, count))
    issues = models.Issue.objects.all()
    return render(request, 'data_management/index.html', { 'objects': object_counts, 'issues': issues })


class BaseListView(generic.ListView):
    context_object_name = 'objects'
    template_name = 'data_management/object_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model_name.lower()
        context['display_name'] = camel_case_to_spaces(self.model_name) + 's'
        return context

class BaseDetailView(generic.DetailView):
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_name'] = self.model_name.lower() + 's'
        context['list_display_name'] = camel_case_to_spaces(self.model_name) + 's'
        context['model_name'] = self.model_name.lower()
        return context

# Generate ListView and DetailView classes for each model that subclasses DataObject
for name, cls in models.all_object_models.items():
    data = {'model': cls, 'model_name': name}
    globals()[name + "ListView"] = type(name + "ListView", (BaseListView,), data)
    globals()[name + "DetailView"] = type(name + "DetailView", (BaseDetailView,), data)

class IssueListView(generic.ListView):
    model = models.Issue
    context_object_name = 'issues'
    
class IssueDetailView(generic.DetailView):
    model = models.Issue

