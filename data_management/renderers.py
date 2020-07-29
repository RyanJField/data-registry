from rest_framework import renderers, serializers
from rest_framework.utils.field_mapping import ClassLookupDict


class HTMLFormRenderer(renderers.HTMLFormRenderer):
    default_style = ClassLookupDict({
        serializers.Field: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.EmailField: {
            'base_template': 'input.html',
            'input_type': 'email'
        },
        serializers.URLField: {
            'base_template': 'input.html',
            'input_type': 'url'
        },
        serializers.IntegerField: {
            'base_template': 'input.html',
            'input_type': 'number'
        },
        serializers.FloatField: {
            'base_template': 'input.html',
            'input_type': 'number'
        },
        serializers.DateTimeField: {
            'base_template': 'input.html',
            'input_type': 'datetime-local'
        },
        serializers.DateField: {
            'base_template': 'input.html',
            'input_type': 'date'
        },
        serializers.TimeField: {
            'base_template': 'input.html',
            'input_type': 'time'
        },
        serializers.FileField: {
            'base_template': 'input.html',
            'input_type': 'file'
        },
        serializers.BooleanField: {
            'base_template': 'checkbox.html'
        },
        serializers.ChoiceField: {
            'base_template': 'select.html',  # Also valid: 'radio.html'
        },
        serializers.MultipleChoiceField: {
            'base_template': 'select_multiple.html',  # Also valid: 'checkbox_multiple.html'
        },
        serializers.RelatedField: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.ManyRelatedField: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.Serializer: {
            'base_template': 'fieldset.html'
        },
        serializers.ListSerializer: {
            'base_template': 'list_fieldset.html'
        },
        serializers.ListField: {
            'base_template': 'list_field.html'
        },
        serializers.DictField: {
            'base_template': 'dict_field.html'
        },
        serializers.FilePathField: {
            'base_template': 'select.html',
        },
        serializers.JSONField: {
            'base_template': 'textarea.html',
        },
    })


class BrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    form_renderer_class = HTMLFormRenderer

