from django.contrib import admin
from django.forms import ModelForm
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils.html import format_html
from django.urls import reverse

admin.site.site_header = 'SCRC Data Management'

from .models import (
        Model,
        ModelVersion,
        ModelRun,
        Issue,
        ModelInput,
        ModelInputVersion,
        ModelInputType,
        ModelInputDataType,
        Source,
        SourceVersion,
        SourceType,
        ProcessingScript,
        ProcessingScriptVersion,
        ModelOutput,
        )

# Register your models here.

class IssueForm(ModelForm):
    def save(self, **kwargs):
        self.instance.updated_by = self.updated_by
        return super().save(**kwargs)

class IssueInline(GenericStackedInline):
    model = Issue
    form = IssueForm

    def get_extra(self, request, obj=None, **kwargs):
        return 0

class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_by', 'last_updated')
    list_display = ('name', 'last_updated')

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

class DataObjectAdmin(BaseAdmin):
    inlines = (IssueInline,)

    def save_related(self, request, form, formsets, change):
        for formset in formsets:
            for f in formset:
                f.updated_by = request.user
        return super().save_related(request, form, formsets, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'responsible_person' in form.base_fields:
            form.base_fields['responsible_person'].initial = request.user
        return form

class DataObjectVersionAdmin(DataObjectAdmin):
    readonly_fields = ('updated_by', 'last_updated', 'name')

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

admin.site.register(Model, DataObjectAdmin)
admin.site.register(ModelVersion, DataObjectVersionAdmin)
admin.site.register(ModelRun, DataObjectAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(ModelInput, DataObjectAdmin)
admin.site.register(ModelInputVersion, DataObjectVersionAdmin)
admin.site.register(ModelInputType, BaseAdmin)
admin.site.register(ModelInputDataType, BaseAdmin)
admin.site.register(Source, DataObjectAdmin)
admin.site.register(SourceVersion, DataObjectVersionAdmin)
admin.site.register(SourceType, BaseAdmin)
admin.site.register(ProcessingScript, DataObjectAdmin)
admin.site.register(ProcessingScriptVersion, DataObjectVersionAdmin)
admin.site.register(ModelOutput, DataObjectAdmin)

