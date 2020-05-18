from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
import uuid

# Create your models here.

class BaseModel(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False
            )
    last_updated = models.DateField(auto_now=True)

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
    #name = models.CharField(max_length=255, null=False, blank=False, editable=False)
    version_identifier = models.CharField(max_length=255)
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    @property
    def name(self):
        return '%s (%s)' % (getattr(self, self._object).name, self.version_identifier)

    class Meta:
        abstract = True

class Issue(BaseModel):
    LOW_SEVERITY = 'L'
    MEDIUM_SEVERITY = 'M'
    HIGH_SEVERITY = 'H'
    ISSUE_SEVERITIES = (
            (LOW_SEVERITY, 'Low'),
            (MEDIUM_SEVERITY, 'Medium'),
            (HIGH_SEVERITY, 'High'),
            )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    data_object = GenericForeignKey('content_type', 'object_id')
    severity = models.CharField(max_length=1, choices=ISSUE_SEVERITIES, default=LOW_SEVERITY)
    desc = models.TextField(max_length=1024, null=False, blank=False)

    def __str__(self):
        labels = dict(self.ISSUE_SEVERITIES)
        return '%s [%s]: %s' % (self.content_type.model, labels[self.severity], self.data_object.name)

class Model(DataObject):
    url = models.CharField(max_length=255, null=False, blank=False)
    short_desc = models.TextField(max_length=1024, null=False, blank=False)
    long_desc_url = models.CharField(max_length=255, null=False, blank=True)

class ModelVersion(DataObjectVersion):
    _object = 'model'
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
    short_desc = models.TextField(max_length=1024)
    parameters = models.ManyToManyField('Parameter')

class ModelRun(DataObjectVersion):
    _object = 'model_version'
    model_version =  models.ForeignKey(ModelVersion, on_delete=models.CASCADE)
    release_date = models.DateField()
    short_desc = models.TextField(max_length=1024)
    url = models.CharField(max_length=255)
    parameter_versions = models.ManyToManyField('ParameterVersion')
    research_outputs = models.ManyToManyField('ResearchOutput')

class ParameterType(BaseModel):
    desc = models.CharField(max_length=255)

class ParameterDataType(BaseModel):
    desc = models.CharField(max_length=255)

class Parameter(DataObject):
    paramter_type = models.ForeignKey(ParameterType, on_delete=models.CASCADE)
    short_desc = models.TextField(max_length=1024)
    long_desc_url = models.CharField(max_length=255)

class ParameterVersion(DataObjectVersion):
    _object = 'parameter'
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    parameter_data_type = models.ForeignKey(ParameterDataType, on_delete=models.CASCADE)
    value = models.TextField(max_length=1024)
    short_desc = models.TextField(max_length=1024)
    source_versions = models.ManyToManyField('SourceVersion')

class SourceType(BaseModel):
    desc = models.CharField(max_length=255)

class Source(DataObject):
    doi = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    source_type = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    short_desc = models.TextField(max_length=1024)
    long_desc_url = models.CharField(max_length=255)

class SourceVersion(DataObjectVersion):
    _object = 'source'
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    doi = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    short_desc = models.TextField(max_length=1024)
    processing_script_version = models.ForeignKey('ProcessingScriptVersion', on_delete=models.CASCADE)

class ProcessingScript(DataObject):
    url = models.CharField(max_length=255)

class ProcessingScriptVersion(DataObjectVersion):
    _object = 'processing_script'
    processing_script = models.ForeignKey(ProcessingScript, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)

class ResearchOutput(DataObject):
    release_date = models.DateField()
    doi = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    short_desc = models.TextField(max_length=1024)
    long_desc_url = models.CharField(max_length=255)

