from configparser import ConfigParser
from copy import deepcopy
import fnmatch
from hashlib import sha1
import hmac
import time

from django import forms, db
from django_filters import filters
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, permissions, views, renderers, mixins, exceptions, status
from rest_framework.response import Response
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend, filterset
from django_filters import constants
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, HttpResponse, redirect
from django.db.models import Q

from data_management import models
from data_management.rest import serializers
from data_management.prov import generate_prov_document, serialize_prov_document


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
        if set(request.query_params.keys()) - {'username', 'cursor', 'format'}:
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
        if set(request.query_params.keys()) - {'cursor', 'format'}:
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
        if self.model.FILTERSET_FIELDS == '__all__':
            filterset_fields = self.model.field_names() + ('cursor', 'format')
        else:
            filterset_fields = self.model.FILTERSET_FIELDS + ('cursor', 'format')
        if set(request.query_params.keys()) - set(filterset_fields):
            args = ', '.join(filterset_fields)
            raise BadQuery(detail='Invalid query arguments, only query arguments [%s] are allowed' % args)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Customising the create method to raise a 409 on uniqueness validation failing.
        """
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as ex:
            name = list(ex.detail.keys())[0]
            if ex.detail[name][0].code == 'unique':
                raise APIIntegrityError('Field ' + name + ' must be unique')
            else:
                raise ex

    def perform_create(self, serializer):
        """
        Customising the save method to add the current user as the models updated_by.
        """
        try:
            return serializer.save(updated_by=self.request.user)
        except IntegrityError as ex:
            raise APIIntegrityError(str(ex))


class ObjectStorageView(views.APIView):
    """
    API views allowing users to upload and download data from object storage
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def __init__(self, *args, **kwargs):
        self.config = ConfigParser()
        self.config.read('/home/ubuntu/config.ini')
        super().__init__(*args, **kwargs)

    def create_url(self, path, method):
        expiry_time = int(time.time()) + int(self.config['storage']['duration'])
        path = '/v1/' + self.config['storage']['bucket'] + '/' + path
        if method == 'GET':
            hmac_body = '%s\n%s\n%s' % ('GET', expiry_time, path)
        elif method == 'PUT':
            hmac_body = '%s\n%s\n%s' % ('PUT', expiry_time, path)
        sig = hmac.new(self.config['storage']['key'].encode('utf-8'), hmac_body.encode('utf-8'), sha1).hexdigest()
        return '%s%s?temp_url_sig=%s&temp_url_expires=%d' % (self.config['storage']['url'], path, sig, expiry_time)

    def get(self, request, name):
        check = self.check_object_permissions(name)
        if check is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        elif not check:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return redirect(self.create_url(name, 'GET'))

    def post(self, request, name):
        url = self.create_url(name, 'PUT')
        return HttpResponse(url)

    def check_object_permissions(self, name):
        try:
            storage_root = models.StorageRoot.objects.get(Q(name=self.config['storage']['storage_root']))
        except Exception:
            return None

        try:
            location = models.StorageLocation.objects.get(Q(storage_root=storage_root) & Q(path=name))
        except Exception:
            return None

        try:
            object = models.Object.objects.get(storage_location=location)
        except Exception:
            return None

        return True

class IssueViewSet(BaseViewSet, mixins.UpdateModelMixin):
    model = models.Issue
    serializer_class = serializers.IssueSerializer
    filterset_fields = models.Issue.FILTERSET_FIELDS
    __doc__ = models.Issue.__doc__

    def create(self, request, *args, **kwargs):
        if 'object_issues' not in request.data:
            request.data['object_issues'] = []
        if 'component_issues' not in request.data:
            request.data['component_issues'] = []
        return super().create(request, *args, **kwargs)


for name, cls in models.all_models.items():
    if name == 'Issue':
        continue
    data = {
        'model': cls,
        'serializer_class': getattr(serializers, name + 'Serializer'),
        'filterset_fields': cls.FILTERSET_FIELDS,
        '__doc__': cls.__doc__,
    }
    if name == 'TextFile':
        data['renderer_classes'] = BaseViewSet.renderer_classes + [TextRenderer]
    globals()[name + "ViewSet"] = type(name + "ViewSet", (BaseViewSet,), data)

