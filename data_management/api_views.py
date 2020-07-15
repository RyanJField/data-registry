from copy import deepcopy
import fnmatch

from django import forms
from django_filters import filters
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import renderer_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, permissions, views, renderers, mixins, exceptions, status
from rest_framework.response import Response
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend, filterset
from django_filters import constants
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from . import models, serializers
from .prov import generate_prov_document, serialize_prov_document


class JPEGRenderer(renderers.BaseRenderer):
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class SVGRenderer(renderers.BaseRenderer):
    media_type = 'image/svg+xml'
    format = 'svg'
    charset = None
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class XMLRenderer(renderers.BaseRenderer):
    media_type = 'text/xml'
    format = 'xml'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProvnRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'provn'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


@renderer_classes([renderers.BrowsableAPIRenderer, renderers.JSONRenderer, JPEGRenderer, SVGRenderer, XMLRenderer, ProvnRenderer])
class ProvReportView(views.APIView):

    def get(self, request, pk, format=None):
        model_output = get_object_or_404(models.ModelOutput, pk=pk)
        doc = generate_prov_document(model_output)
        value = serialize_prov_document(doc, request.accepted_renderer.format)
        return Response(value)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username']


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class APIIntegrityError(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'integrity_error'


class RegexFilter(filters.Filter):
    def __init__(self, *args, **kwargs):
        kwargs['lookup_expr'] = 'regex'
        super().__init__(*args, **kwargs)
    field_class = forms.CharField


class GlobFilter(filters.Filter):
    def __init__(self, *args, **kwargs):
        kwargs['lookup_expr'] = 'glob'
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in constants.EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        regex_value = '\\A' + fnmatch.translate(value).replace('?s:', '')
        lookup = '%s__regex' % (self.field_name,)
        qs = self.get_method(qs)(**{lookup: regex_value})
        return qs

    field_class = forms.CharField


class CustomFilterSet(filterset.FilterSet):
    FILTER_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
    FILTER_DEFAULTS.update({
        models.NameField: {'filter_class': GlobFilter},
    })


class CustomDjangoFilterBackend(DjangoFilterBackend):
    default_filter_set = CustomFilterSet


class BaseViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    Base class for all model API views. Allows for GET to retrieve lists of objects and single object, and
    POST to create a new object.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [CustomDjangoFilterBackend]
    # lookup_field = 'name'

    def get_queryset(self):
        return self.model.objects.all()

    def perform_create(self, serializer):
        try:
            serializer.save(updated_by=self.request.user)
        except IntegrityError as ex:
            raise APIIntegrityError(str(ex))

    def perform_update(self, serializer):
        try:
            serializer.save(updated_by=self.request.user)
        except IntegrityError as ex:
            raise APIIntegrityError(str(ex))


for name, cls in models.all_models.items():
    data = {
        'model': cls,
        'serializer_class': getattr(serializers, name + 'Serializer'),
        'filterset_fields': cls.FILTERSET_FIELDS,
    }
    globals()[name + "ViewSet"] = type(name + "ViewSet", (BaseViewSet,), data)

