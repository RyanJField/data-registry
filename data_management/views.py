from django.shortcuts import render
from django.views import generic
from django.utils.text import camel_case_to_spaces
from collections import namedtuple

from . import models


def index(request):
    ObjectData = namedtuple('object', 'name display_name count doc')
    object_models = models.all_object_models
    object_data = []
    for (model_name, model_cls) in sorted(object_models.items()):
        count = getattr(models, model_name).objects.count()
        name = model_name.lower() + 's'
        display_name = camel_case_to_spaces(model_name)
        doc = model_cls.__doc__
        object_data.append(ObjectData(name, display_name, count, doc))
    issues = models.Issue.objects.all()
    return render(request, 'data_management/index.html', {'objects': object_data, 'issues': issues})


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
