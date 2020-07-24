from copy import deepcopy
import fnmatch

from django import forms, db
from django.http import HttpResponseBadRequest, JsonResponse
from django_filters import filters
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import APIException
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


class BadQuery(APIException):
    status_code = 400
    default_code = 'bad_query'


class JPEGRenderer(renderers.BaseRenderer):
    """
    Custom rendered for returning JPEG images.
    """
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class SVGRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning SVG images.
    """
    media_type = 'image/svg+xml'
    format = 'svg'
    charset = None
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class XMLRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning XML data.
    """
    media_type = 'text/xml'
    format = 'xml'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProvnRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning PROV-N data (as defined in https://www.w3.org/TR/2013/REC-prov-n-20130430/).
    """
    media_type = 'text/plain'
    format = 'provn'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class TextRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning plain text data.
    """
    media_type = 'text/plain'
    format = 'text'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data['text']


@renderer_classes([
    renderers.BrowsableAPIRenderer, renderers.JSONRenderer, JPEGRenderer, SVGRenderer, XMLRenderer, ProvnRenderer
])
class ProvReportView(views.APIView):
    """
    API view for returning a PROV report for a CodeRun.

    This report can be returned as JSON (default) or JPEG, SVG, XML or PROV-N using the custom renderers.
    """

    def get(self, request, pk, format=None):
        code_run = get_object_or_404(models.CodeRun, pk=pk)
        doc = generate_prov_document(code_run)
        value = serialize_prov_document(doc, request.accepted_renderer.format)
        return Response(value)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API views (GET only) for the User model.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username']

    def list(self, request, *args, **kwargs):
        if set(request.query_params.keys()) - {'username'}:
            raise BadQuery(detail='Invalid query arguments, only query arguments [username] are allowed')
        return super().list(request, *args, **kwargs)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API views (GET only) for the Group model.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if request.query_params.keys():
            raise BadQuery(detail='Invalid query arguments, no query arguments are allowed')
        return super().list(request, *args, **kwargs)


class APIIntegrityError(exceptions.APIException):
    """
    API error to be returned if there is a database unique constraint failure, i.e. due to trying to add a duplicate
    entry.
    """
    status_code = status.HTTP_409_CONFLICT
    default_code = 'integrity_error'


class RegexFilter(filters.Filter):
    """
    Custom API filter which can be used to add regex filtering to a field.
    """
    def __init__(self, *args, **kwargs):
        kwargs['lookup_expr'] = 'regex'
        super().__init__(*args, **kwargs)
    field_class = forms.CharField


class GlobFilter(filters.Filter):
    """
    Custom API filter which can be used to add Unix glob style pattern matching to a field.
    """
    def __init__(self, *args, **kwargs):
        kwargs['lookup_expr'] = 'glob'
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in constants.EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        # The regex generated by fnmatch is not compatible with PostgreSQL so we need to do remove the ?s: characters
        # and we also add a \A at the start so that it matches on the entire string.
        regex_value = '\\A' + fnmatch.translate(value).replace('?s:', '')
        lookup = '%s__regex' % (self.field_name,)
        qs = self.get_method(qs)(**{lookup: regex_value})
        return qs

    field_class = forms.CharField


class CustomFilterSet(filterset.FilterSet):
    """
    Custom filters which we use to add glob filtering to all NameField fields.
    """
    FILTER_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
    FILTER_DEFAULTS.update({
        models.NameField: {'filter_class': GlobFilter},
        db.models.OneToOneField: {'filter_class': filters.NumberFilter},
        db.models.ForeignKey: {'filter_class': filters.NumberFilter},
    })


class CustomDjangoFilterBackend(DjangoFilterBackend):
    """
    Custom filtering backend which we use to add the CustomFilterSet filtering.
    """
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

    def list(self, request, *args, **kwargs):
        if set(request.query_params.keys()) - set(self.model.FILTERSET_FIELDS + ('page',)):
            args = ', '.join(self.model.FILTERSET_FIELDS + ('page',))
            raise BadQuery(detail='Invalid query arguments, only query arguments [%s] are allowed' % args)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()

    def perform_create(self, serializer):
        """
        Customising the create to add the current user as the models updated_by.
        """
        try:
            serializer.save(updated_by=self.request.user)
        except IntegrityError as ex:
            raise APIIntegrityError(str(ex))

    def perform_update(self, serializer):
        """
        Customising the update to add the current user as the models updated_by.
        """
        try:
            serializer.save(updated_by=self.request.user)
        except IntegrityError as ex:
            raise APIIntegrityError(str(ex))


for name, cls in models.all_models.items():
    data = {
        'model': cls,
        'serializer_class': getattr(serializers, name + 'Serializer'),
        'filterset_fields': cls.FILTERSET_FIELDS,
        '__doc__': cls.__doc__,
    }
    if name == 'TextFile':
        data['renderer_classes'] = BaseViewSet.renderer_classes + [TextRenderer]
    globals()[name + "ViewSet"] = type(name + "ViewSet", (BaseViewSet,), data)

