from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from data_management import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class for serializing the User model.
    """
    class Meta:
        model = get_user_model()
        fields = ['url', 'username', 'full_name', 'email', 'orgs']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class for serializing the Group model.
    """
    class Meta:
        model = Group
        fields = ['url', 'name']


class BaseSerializer(serializers.HyperlinkedModelSerializer):
    """
    Base class for serializing the data management objects.

    Serializes all the defined fields on the model as well as any non-database field or method specified in the models
    EXTRA_DISPLAY_FIELDS.
    """
    class Meta:
        model = models.BaseModel
        fields = '__all__'

    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)
        return expanded_fields + list(self.Meta.model.EXTRA_DISPLAY_FIELDS)


class IssueSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Issue


for name, cls in models.all_models.items():
    if name == 'Issue':
        continue
    meta_cls = type('Meta', (BaseSerializer.Meta,), {'model': cls, 'read_only_fields': cls.EXTRA_DISPLAY_FIELDS})
    data = {'Meta': meta_cls}
    globals()[name + "Serializer"] = type(name + "Serializer", (BaseSerializer,), data)
