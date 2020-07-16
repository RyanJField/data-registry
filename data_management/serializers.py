from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['url', 'username', 'full_name', 'email', 'orgs']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class BaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.BaseModel
        fields = '__all__'

    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)
        return expanded_fields + list(self.Meta.model.EXTRA_DISPLAY_FIELDS)


class ObjectRelatedField(serializers.HyperlinkedRelatedField):
    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'pk': obj.pk
        }
        view_name = obj.__class__.__name__.lower()
        return reverse(view_name + '-detail', kwargs=url_kwargs, request=request, format=format)


class IssueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Issue
        fields = ('url', 'last_updated', 'updated_by', 'severity', 'description', 'object_issues', 'component_issues')
        read_only_fields = ('url', 'last_updated', 'updated_by')


for name, cls in models.all_models.items():
    if name == 'Issue':
        continue
    meta_cls = type('Meta', (BaseSerializer.Meta,), {'model': cls, 'read_only_fields': cls.EXTRA_DISPLAY_FIELDS})
    data = {'Meta': meta_cls}
    globals()[name + "Serializer"] = type(name + "Serializer", (BaseSerializer,), data)

