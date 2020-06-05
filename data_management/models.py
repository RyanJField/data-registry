from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
import uuid


class BaseModel(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateField(auto_now=True)
    _extra_fields = ()

    def reverse_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True
        ordering = ['name', '-last_updated']

    def __str__(self):
        return self.name


class DataObject(BaseModel):
    # object_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    responsible_person = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_responsible_for',
            )
    issues = GenericRelation('Issue')

    class Meta:
        abstract = True


class DataObjectVersion(DataObject):
    _object = ''
    version_identifier = models.CharField(max_length=255)
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='superseded_by')

    @property
    def name(self):
        return '%s (version %s)' % (getattr(self, self._object).name, self.version_identifier)

    class Meta:
        abstract = True


class Issue(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    data_object = GenericForeignKey('content_type', 'object_id')
    severity = models.PositiveSmallIntegerField(default=1)
    desc = models.TextField(max_length=1024, null=False, blank=False, verbose_name='description')

    def __str__(self):
        return '%s [Severity %s]' % (self.name, self.severity)


class DataProductType(BaseModel):
    description = models.TextField(max_length=1024, null=False, blank=False)


class StorageType(BaseModel):
    description = models.TextField(max_length=1024)


class StorageRoot(BaseModel):
    type = models.ForeignKey(StorageType, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024)
    doi = models.URLField(max_length=1024)
    url = models.URLField(max_length=1024)
    git_repo = models.URLField(max_length=1024)


class DataStore(DataObject):
    store_root = models.ForeignKey(StorageRoot, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024)
    path = models.CharField(max_length=1024)
    toml_text = models.TextField(max_length=1024)
    hash = models.TextField(max_length=1024)
    local_cache_url = models.TextField(max_length=1024)


class Accessibility(BaseModel):
    description = models.TextField(max_length=1024, null=False, blank=False)
    access_info = models.TextField(max_length=1024, null=False, blank=False)


class SourceType(BaseModel):
    description = models.CharField(max_length=255, verbose_name='short description')


class Source(DataObject):
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    source_type = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)


class SourceVersion(DataObjectVersion):
    _object = 'source'
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)


class DataProduct(DataObject):
    _extra_fields = ('versions',)
    description = models.TextField(max_length=1024, null=False, blank=False)


class DataProductDataType(BaseModel):
    description = models.CharField(max_length=255)
    type = models.ForeignKey(DataProductType, on_delete=models.CASCADE)


class ProcessingScript(DataObject):
    _extra_fields = ('versions',)
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)


class ProcessingScriptVersion(DataObjectVersion):
    _object = 'processing_script'
    processing_script = models.ForeignKey(ProcessingScript, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)


class DataProductVersion(DataObjectVersion):
    _object = 'data_product'
    _extra_fields = ('components', 'model_runs')
    data_product = models.ForeignKey(DataProduct, on_delete=models.CASCADE, related_name='versions')
    data_type = models.ForeignKey(DataProductDataType, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)
    processing_script_version = models.ForeignKey(ProcessingScriptVersion, on_delete=models.CASCADE)
    source_versions = models.ManyToManyField(SourceVersion, blank=True)


class DataProductVersionComponent(DataObject):
    _extra_fields = ('model_runs',)
    data_product_version = models.ForeignKey(DataProductVersion, on_delete=models.CASCADE, related_name='components')


class Model(DataObject):
    _extra_fields = ('versions',)
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)


class ModelVersion(DataObjectVersion):
    _extra_fields = ('model_runs',)
    _object = 'model'
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)


class ModelRun(DataObject):
    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='model_runs')
    release_date = models.DateField()
    description = models.TextField(max_length=1024, null=False, blank=False)
    toml_config = models.TextField(max_length=1024, null=False, blank=False)
    inputs = models.ManyToManyField(DataProductVersionComponent, blank=True, related_name='model_runs')
    outputs = models.ManyToManyField(DataProductVersion, blank=True, related_name='model_runs')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    @property
    def name(self):
        return '%s (Run %s)' % (self.model_version.name, self.release_date)


all_object_models = dict(
    (name, cls) for (name, cls) in globals().items() 
    if isinstance(cls, type) and issubclass(cls, DataObject) and name not in ('DataObject', 'DataObjectVersion')
)

all_models = dict(
    (name, cls) for (name, cls) in globals().items()
    if isinstance(cls, type) and issubclass(cls, BaseModel) and name not in ('BaseModel', 'DataObject', 'DataObjectVersion')
)

