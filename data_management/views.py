from configparser import ConfigParser
import os

from django.http import HttpResponseNotFound
from django.shortcuts import render, HttpResponse, redirect
from django.views import generic
from django.utils.text import camel_case_to_spaces
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.authtoken.models import Token

from collections import namedtuple

from . import models
from . import object_storage
from . import settings

def index(request):
    """
    Default view showing tables of the database objects, divided into Data Products, External Objects and Code Repo
    Releases.
    """
    data_products = models.Object.objects.filter(data_product__isnull=False)
    external_objects = models.Object.objects.filter(external_object__isnull=False)
    code_repo_release = models.Object.objects.filter(code_repo_release__isnull=False)

    ObjectData = namedtuple('object', 'name display_name count doc')
    object_data = [
        ObjectData('objects', 'Object', models.Object.objects.count(), models.Object.__doc__)
    ]
    issues = models.Issue.objects.all()
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

def get_data(request, name):
    check = True

    try:
        storage_root = models.StorageRoot.objects.get(Q(name=settings.CONFIG['STORAGE_ROOT']))
        location = models.StorageLocation.objects.get(Q(storage_root=storage_root) & Q(path=name))
        object = models.Object.objects.get(storage_location=location)
    except Exception:
        check = None
    else:
        if object.metadata:
            try:
                keyvalue = object.metadata.get(Q(key='accessibility'))
            except Exception:
                pass
            else:
                if not request.user.is_authenticated and keyvalue.value == 'private':
                    check = False

    if check is None:
        return HttpResponseNotFound()
    elif not check:
        return HttpResponse(status=403)

    return redirect(object_storage.create_url(name, 'GET'))

def data_product(request, namespace, data_product_name, version):
    """
    Redirect to the URL of a file given the namespace, data product name and version
    """
    try:
        namespace = models.Namespace.objects.get(Q(name=namespace))
        data_product = models.DataProduct.objects.get(Q(name=data_product_name) & Q(namespace=namespace) & Q(version=version))
    except Exception:
        return HttpResponseNotFound()

    if not data_product.object.storage_location:
        return HttpResponseNotFound()

    if 'root' in request.GET:
        return HttpResponse(data_product.object.storage_location.storage_root.root)

    return redirect(data_product.object.storage_location.full_uri())

def external_object(request, doi, title, version):
    """
    Redirect to the URL of a file given the DOI or unique name, title and version
    """
    # Even if the user specified "doi://" the server will only see "doi:/"
    doi = doi.replace('doi:/', 'doi://')

    # Find external object
    try:
        external_object = models.ExternalObject.objects.get(Q(doi_or_unique_name=doi) & Q(title=title) & Q(version=version))
    except Exception:
        return HttpResponseNotFound()

    if 'source' not in request.GET:
        # Return storage location, if it exists
        try:
            url = external_object.object.storage_location.full_uri()
        except Exception:
            pass
        else:
            if 'root' in request.GET:
                return HttpResponse(external_object.object.storage_location.storage_root.root)
            return redirect(url)

        # Return website of original_store, if it exists
        try:
            url = external_object.original_store.full_uri()
        except Exception:
            pass
        else:
            if 'root' in request.GET:
                return HttpResponse(external_object.original_store.storage_root.root)
            return redirect(url)

        # External object exists but there is no StorageLocation or original_store
        return HttpResponse(status=204)

    try:
        url = external_object.source.website
    except Exception:
        pass
    else:
        if 'root' in request.GET:
            return HttpResponse(status=204)
        return redirect(url)

    return HttpResponse(status=204)

