from django.contrib import admin

from . import models

admin.site.site_header = 'SCRC Data Management'


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_by', 'last_updated')
    list_display = ('last_updated',)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)


class IssueAdmin(BaseAdmin):
    readonly_fields = ('updated_by', 'last_updated', 'linked_objects')
    list_display = ('name', 'severity', 'last_updated')

    @classmethod
    def linked_objects(cls, issue):
        return list(issue.object_issues.all()) + list(issue.component_issues.all())

    def has_add_permission(self, request, obj=None):
        return False


DISPLAY_FIELDS = {
    'Object': ('name', 'updated_by', 'last_updated'),
    'ObjectComponent': ('name', 'updated_by', 'last_updated',),
    'CodeRun': ('run_identifier', 'updated_by', 'last_updated',),
    'StorageRoot': ('name', 'updated_by', 'last_updated',),
    'StorageLocation': ('path', 'updated_by', 'last_updated',),
    'Source': ('name', 'updated_by', 'last_updated',),
    'ExternalObject': ('doi_or_unique_name', 'updated_by', 'last_updated',),
    'QualityControlled': ('object', 'updated_by', 'last_updated',),
    'Keyword': ('object', 'keyphrase', 'updated_by', 'last_updated',),
    'Author': ('object', 'family_name', 'personal_name', 'updated_by', 'last_updated',),
    'Licence': ('object', 'updated_by', 'last_updated',),
    'Namespace': ('name', 'updated_by', 'last_updated',),
    'DataProduct': ('namespace', 'name', 'updated_by', 'last_updated',),
    'CodeRepoRelease': ('name', 'version', 'updated_by', 'last_updated',),
    'KeyValue': ('object', 'key', 'updated_by', 'last_updated',),
}


for name, cls in models.all_models.items():
    if issubclass(cls, models.Issue):
        admin.site.register(cls, IssueAdmin)
    else:
        data = {'list_display': DISPLAY_FIELDS[name]}
        admin_cls = type(name + 'Admin', (BaseAdmin,), data)
        admin.site.register(cls, admin_cls)
