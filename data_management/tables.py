from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from . import models


def data_product_table_data(request):
    size = int(request.GET.get('limit', 25))
    offset = int(request.GET.get('offset', 25))
    search = request.GET.get('search', None)
    sort = request.GET.get('sort', '') or 'name'
    order = request.GET.get('order', '') or 'asc'
    sign = '-' if order == 'desc' else ''
    all_objects = models.DataProduct.objects.all().order_by(sign + sort)
    if search:
        all_objects = all_objects.filter(
            Q(namespace__name__contains=search) |
            Q(name__contains=search) |
            Q(version__contains=search)
        )
    paginator = Paginator(all_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse({
        'total': all_objects.count(),
        'rows': [
            {
                'namespace': str(obj.namespace),
                'name': obj.name,
                'version': obj.version,
            } for obj in page_objects
        ],
    })


def external_objects_table_data(request):
    size = int(request.GET.get('limit', 25))
    offset = int(request.GET.get('offset', 25))
    search = request.GET.get('search', None)
    sort = request.GET.get('sort', '') or 'doi_or_unique_name'
    order = request.GET.get('order', '') or 'asc'
    sign = '-' if order == 'desc' else ''
    all_objects = models.ExternalObject.objects.all().order_by(sign + sort)
    if search:
        all_objects = all_objects.filter(
            Q(source__name__contains=search) |
            Q(doi_or_unique_name__contains=search) |
            Q(release_date__contains=search) |
            Q(title__contains=search) |
            Q(version__contains=search)
        )
    paginator = Paginator(all_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse({
        'rows': [
            {
                'source': str(obj.source),
                'doi_or_unique_name': obj.doi_or_unique_name,
                'release_date': str(obj.release_date),
                'title': obj.title,
                'version': obj.version,
            } for obj in page_objects
        ],
    })


def code_repo_release_table_data(request):
    size = int(request.GET.get('limit', 25))
    offset = int(request.GET.get('offset', 25))
    search = request.GET.get('search', None)
    sort = request.GET.get('sort', '') or 'name'
    order = request.GET.get('order', '') or 'asc'
    sign = '-' if order == 'desc' else ''
    all_objects = models.CodeRepoRelease.objects.all().order_by(sign + sort)
    if search:
        all_objects = all_objects.filter(
            Q(name__contains=search) |
            Q(version__contains=search) |
            Q(website__contains=search)
        )
    paginator = Paginator(all_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse({
        'rows': [
            {
                'name': obj.name,
                'version': obj.version,
                'website': obj.website,
            } for obj in page_objects
        ],
    })
