from django.contrib import admin
from django.forms import ModelForm
from django.contrib.contenttypes.admin import GenericStackedInline

from .models import (
        Model,
        ModelVersion,
        ModelRun,
        Issue,
        Parameter,
        ParameterVersion,
        ParameterType,
        ParameterDataType,
        Source,
        SourceVersion,
        SourceType,
        ProcessingScript,
        ProcessingScriptVersion,
        ResearchOutput,
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

class DataObjectAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_by',)
    inlines = (IssueInline,)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

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
    readonly_fields = ('updated_by', 'name')

    #def save_model(self, request, obj, form, change):
    #    obj.name = '%s %s' % (getattr(obj, obj._object), obj.version_identifier)
    #    return super().save_model(request, obj, form, change)

admin.site.register(Model, DataObjectAdmin)
admin.site.register(ModelVersion, DataObjectVersionAdmin)
admin.site.register(ModelRun, DataObjectVersionAdmin)
admin.site.register(Issue, DataObjectAdmin)
admin.site.register(Parameter, DataObjectAdmin)
admin.site.register(ParameterVersion, DataObjectVersionAdmin)
admin.site.register(ParameterType, DataObjectAdmin)
admin.site.register(ParameterDataType, DataObjectAdmin)
admin.site.register(Source, DataObjectAdmin)
admin.site.register(SourceVersion, DataObjectVersionAdmin)
admin.site.register(SourceType, DataObjectAdmin)
admin.site.register(ProcessingScript, DataObjectAdmin)
admin.site.register(ProcessingScriptVersion, DataObjectVersionAdmin)
admin.site.register(ResearchOutput, DataObjectAdmin)

