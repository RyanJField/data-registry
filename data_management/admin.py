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


for name, cls in models.all_models.items():
    if issubclass(cls, models.Issue):
        admin.site.register(cls, IssueAdmin)
    else:
        data = {'list_display': cls.ADMIN_LIST_FIELDS + ('updated_by', 'last_updated')}
        admin_cls = type(name + 'Admin', (BaseAdmin,), data)
        admin.site.register(cls, admin_cls)
