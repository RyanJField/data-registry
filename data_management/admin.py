from django.contrib import admin
from django.forms import ModelForm
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils.html import format_html
from django.urls import reverse

from . import models

admin.site.site_header = 'SCRC Data Management'


class IssueForm(ModelForm):
    def save(self, **kwargs):
        self.instance.updated_by = self.updated_by
        return super().save(**kwargs)


class IssueInline(GenericStackedInline):
    model = models.Issue
    form = IssueForm

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_by', 'last_updated')
    list_display = ('last_updated',)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)


class ObjectAdmin(BaseAdmin):
    inlines = (IssueInline,)

    def save_related(self, request, form, formsets, change):
        for formset in formsets:
            for f in formset:
                f.updated_by = request.user
        return super().save_related(request, form, formsets, change)


class IssueAdmin(BaseAdmin):
    exclude = ('content_type', 'object_id')
    readonly_fields = ('updated_by', 'last_updated', 'data_object_link')
    list_display = ('name', 'data_object', 'severity', 'last_updated')

    def data_object_link(self, instance):
        url = reverse('admin:%s_%s_change' % (instance.content_type.app_label, instance.content_type.model),
                args=(instance.data_object.id,))
        return format_html(
                '<a href="{0}">{1}</a>',
                url,
                instance.data_object,
                )

    data_object_link.short_description = 'data object'

    def has_add_permission(self, request, obj=None):
        return False


for _, cls in models.all_models.items():
    if isinstance(cls, models.Object):
        admin.site.register(cls, ObjectAdmin)
    elif isinstance(cls, models.Issue):
        admin.site.register(cls, IssueAdmin)
    else:
        admin.site.register(cls, BaseAdmin)
