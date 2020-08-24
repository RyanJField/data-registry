import os

from django.shortcuts import render, HttpResponse
from django.views import generic
from django.utils.text import camel_case_to_spaces
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.authtoken.models import Token

from collections import namedtuple

from . import models


def index(request):
    """
    Default view showing tables of the database objects, divided into Data Products, External Objects and Code Repo
    Releases.
    """
    objects = models.Object.objects.filter(~Q(updated_by__username = 'Test'))
    data_products = objects.filter(data_product__isnull=False)
    external_objects = objects.filter(external_object__isnull=False)
    code_repo_release = objects.filter(code_repo_release__isnull=False)

    ObjectData = namedtuple('object', 'name display_name count doc')
    object_data = [
        ObjectData('objects', 'Object', objects.count(), models.Object.__doc__)
    ]
    issues = models.Issue.objects.filter(~Q(updated_by__username = 'Test'))
    ctx = {
        'objects': object_data,
        'issues': issues,
        'data_products': data_products,
        'external_objects': external_objects,
        'code_repo_release': code_repo_release,
    }
    return render(request, 'data_management/index.html', ctx)


def get_token(request):
    """
    Generate a new API access token for the User.
    """
    user_model = get_user_model()
    user_name = request.user.username
    user = user_model.objects.get_by_natural_key(user_name)
    Token.objects.filter(user=user).delete()
    token = Token.objects.get_or_create(user=user)
    return HttpResponse('Your token is: %s' % token[0])


def revoke_token(request):
    """
    Revoke an existing API access token for the User.
    """
    user_model = get_user_model()
    user_name = request.user.username
    user = user_model.objects.get_by_natural_key(user_name)
    Token.objects.filter(user=user).delete()
    return HttpResponse('Your token has been deleted')


class BaseListView(generic.ListView):
    """
    Base class for views for displaying a table of the database objects.
    """
    context_object_name = 'objects'
    template_name = 'data_management/object_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model_name.lower()
        context['display_name'] = camel_case_to_spaces(self.model_name) + 's'
        return context


class BaseDetailView(generic.DetailView):
    """
    Base class for views for displaying details about a specific database object.
    """
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_name'] = self.model_name.lower() + 's'
        context['list_display_name'] = camel_case_to_spaces(self.model_name) + 's'
        context['model_name'] = self.model_name.lower()
        return context


# Generate ListView and DetailView classes for each model that subclasses DataObject
for name, cls in models.all_models.items():
    data = {'model': cls, 'model_name': name}
    globals()[name + "ListView"] = type(name + "ListView", (BaseListView,), data)
    globals()[name + "DetailView"] = type(name + "DetailView", (BaseDetailView,), data)


class IssueListView(generic.ListView):
    """
    View for displaying all Issues.
    """
    model = models.Issue
    context_object_name = 'issues'


class IssueDetailView(generic.DetailView):
    """
    View for displaying details about a specific Issue.
    """
    model = models.Issue


def docs(request, name):
    with open(os.path.join('docs', name)) as file:
        text = file.read()
    ctx = {
        'text': text
    }
    return render(request, 'data_management/docs.html', ctx)


def doc_index(request):
    with open('docs/index.md') as file:
        text = file.read()
    ctx = {
        'text': text
    }
    return render(request, 'data_management/docs.html', ctx)
