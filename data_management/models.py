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
    object_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    responsible_person = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_responsible_for',
            )
    issues = GenericRelation('Issue')

    class Meta:
        abstract = True


class DataObjectVersion(DataObject):
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
        return '%s [Severity %d]' % (self.name, self.severity)


class Model(DataObject):
    _extra_fields = ('versions',)
    url = models.URLField(max_length=255, null=False, blank=False)
    short_desc = models.TextField(max_length=1024, null=False, blank=False, verbose_name='short description')
    long_desc_url = models.URLField(max_length=255, null=False, blank=True)


class ModelVersion(DataObjectVersion):
    _extra_fields = ('runs',)
    _object = 'model'
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='versions')
    url = models.URLField(max_length=255)
    short_desc = models.TextField(max_length=1024, verbose_name='short description')


class ModelRun(DataObject):
    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='runs')
    run_date = models.DateField()
    short_desc = models.TextField(max_length=1024, verbose_name='short description', blank=True)
    url = models.URLField(max_length=255, blank=True)
    model_input_versions = models.ManyToManyField('ModelInputVersion', blank=True, related_name='model_runs')
    model_outputs = models.ManyToManyField('ModelOutput', blank=True, related_name='model_runs')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    @property
    def name(self):
        return '%s (Run %s)' % (self.model_version.name, self.run_date)


class ModelInputType(BaseModel):
    desc = models.CharField(max_length=255, verbose_name='short description')


class ModelInputDataType(BaseModel):
    desc = models.CharField(max_length=255, verbose_name='short description')


class ModelInput(DataObject):
    model_input_type = models.ForeignKey(ModelInputType, on_delete=models.CASCADE)
    short_desc = models.TextField(max_length=1024, verbose_name='short description')
    long_desc_url = models.URLField(max_length=255, blank=True)


class ModelInputVersion(DataObjectVersion):
    _object = 'model_input'
    model_input = models.ForeignKey(ModelInput, on_delete=models.CASCADE, related_name='versions')
    model_input_data_type = models.ForeignKey(ModelInputDataType, on_delete=models.CASCADE)
    value = models.TextField(max_length=1024)
    short_desc = models.TextField(max_length=1024, blank=True, verbose_name='short description')
    source_versions = models.ManyToManyField('SourceVersion', blank=True)


class SourceType(BaseModel):
    desc = models.CharField(max_length=255, verbose_name='short description')


class Source(DataObject):
    doi = models.URLField(max_length=255, blank=True)
    url = models.URLField(max_length=255, blank=True)
    source_type = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    short_desc = models.TextField(max_length=1024, verbose_name='short description')
    long_desc_url = models.URLField(max_length=255, blank=True)


class SourceVersion(DataObjectVersion):
    _object = 'source'
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='versions')
    doi = models.URLField(max_length=255, blank=True)
    url = models.URLField(max_length=255, blank=True)
    short_desc = models.TextField(max_length=1024, verbose_name='short description')
    processing_script_version = models.ForeignKey('ProcessingScriptVersion', on_delete=models.CASCADE, related_name='generated_sources')


class ProcessingScript(DataObject):
    url = models.URLField(max_length=255)


class ProcessingScriptVersion(DataObjectVersion):
    _object = 'processing_script'
    processing_script = models.ForeignKey(ProcessingScript, on_delete=models.CASCADE, related_name='versions')
    url = models.URLField(max_length=255)


class ModelOutput(DataObject):
    STATUS_PRIVATE = 0
    STATUS_PUBLIC = 1
    STATUS_CHOICES = (
            (STATUS_PRIVATE, 'private'),
            (STATUS_PUBLIC, 'public'),
            )
    release_date = models.DateField()
    doi = models.URLField(max_length=255, blank=True)
    url = models.URLField(max_length=255, blank=True)
    short_desc = models.TextField(max_length=1024, verbose_name='short description', blank=True)
    long_desc_url = models.URLField(max_length=255, blank=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_PRIVATE)
    _extra_fields = ('model_runs',)

    def status_string(self):
        return dict(self.STATUS_CHOICES)[self.status]


all_object_models = dict(
    (name, cls) for (name, cls) in globals().items() 
    if isinstance(cls, type) and issubclass(cls, DataObject) and name not in ('DataObject', 'DataObjectVersion')
)

all_models = dict(
    (name, cls) for (name, cls) in globals().items()
    if isinstance(cls, type) and issubclass(cls, BaseModel) and name not in ('BaseModel', 'DataObject', 'DataObjectVersion')
)

