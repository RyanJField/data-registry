from django.contrib.auth.models import Group
from custom_user.models import User
from rest_framework import serializers

from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class BaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Model
        fields = '__all__'

    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)
        return expanded_fields + list(self.Meta.model.fields)


for name, cls in models.all_models.items():
    data = {'Meta': type('Meta', (BaseSerializer.Meta,), {'model': cls})}
    globals()[name + "Serializer"] = type(name + "Serializer", (BaseSerializer,), data)

