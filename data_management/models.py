from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from dynamic_validator import ModelFieldRequiredMixin


class BaseModel(ModelFieldRequiredMixin, models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateTimeField(auto_now=True)

    EXTRA_DISPLAY_FIELDS = ()
    REQUIRED_FIELDS = ['name']
    FILTERSET_FIELDS = ['name']

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

    class Meta(BaseModel.Meta):
        abstract = True


class DataObjectVersion(DataObject):
    VERSIONED_OBJECT = ''
    version_identifier = models.CharField(max_length=255)
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='superseded_by')

    REQUIRED_FIELDS = []
    
    @property
    def name(self):
        return '%s (version %s)' % (getattr(self, self.VERSIONED_OBJECT).name, self.version_identifier)

    class Meta(DataObject.Meta):
        abstract = True
        ordering = ['-version_identifier']


class Issue(BaseModel):
    """
    A quality issue which can be attached to any data object in the registry.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    data_object = GenericForeignKey('content_type', 'object_id')
    severity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(max_length=1024, null=False, blank=False, verbose_name='description')

    def __str__(self):
        return '%s [Severity %s]' % (self.name, self.severity)


class DataProductType(BaseModel):
    description = models.TextField(max_length=1024, null=False, blank=False)


class StorageType(BaseModel):
    description = models.TextField(max_length=1024, null=True, blank=True)


class URIField(models.URLField):
    default_validators = []


class StorageRoot(BaseModel):
    """
    The root location of a storage cache where model files are stored.
    """
    type = models.ForeignKey(StorageType, on_delete=models.CASCADE, null=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    uri = models.CharField(max_length=1024, null=False, blank=False)
    # uri = URIField(max_length=1024, null=False, blank=False)


class StorageLocation(DataObject):
    """
    The storage location of a model file relative to a StorageRoot.
    """
    store_root = models.ForeignKey(StorageRoot, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=True, blank=True)
    path = models.CharField(max_length=1024, null=True, blank=True)
    # toml_text = models.TextField(max_length=1024, null=True, blank=True)
    hash = models.CharField(max_length=1024, null=True, blank=True)
    local_cache_url = models.URLField(max_length=1024, null=True, blank=True)


class Accessibility(BaseModel):
    """
    The accessibility level of data.
    """
    description = models.TextField(max_length=1024, null=True, blank=True)
    access_info = models.CharField(max_length=1024, null=True, blank=True)


class SourceType(BaseModel):
    """
    Type of primary data source.
    """
    description = models.CharField(max_length=255, null=False, blank=False)


class Source(DataObject):
    """
    Primary source of data being using by models.
    """
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    source_type = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)


class SourceVersion(DataObjectVersion):
    """
    Version of primary source data that was used to populate a given DataProductVersion.
    """
    VERSIONED_OBJECT = 'source'
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['source', 'version_identifier'], name='source_version_unique_identifier')
        ]


class DataProduct(DataObject):
    """
    A data product that is used by or generated by a model.
    """
    EXTRA_DISPLAY_FIELDS = ('versions',)

    description = models.TextField(max_length=1024, null=False, blank=False)
    type = models.ForeignKey(DataProductType, on_delete=models.CASCADE)


# class DataProductDataType(BaseModel):
#     description = models.CharField(max_length=255)


class ProcessingScript(DataObject):
    """
    A processing script used to derive a DataProductVersion.
    """
    EXTRA_DISPLAY_FIELDS = ('versions',)
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)


class ProcessingScriptVersion(DataObjectVersion):
    """
    A specific version of ProcessingScript which was used in the generation of a DataProductVersion.
    """
    VERSIONED_OBJECT = 'processing_script'
    EXTRA_DISPLAY_FIELDS = ('data_product_versions',)
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    processing_script = models.ForeignKey(ProcessingScript, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['processing_script', 'version_identifier'],
                                    name='processing_script_version_unique_identifier')
        ]


class DataProductVersion(DataObjectVersion):
    """
    Specific version of a DataProduct that is associated with a ModelRun.
    """
    VERSIONED_OBJECT = 'data_product'
    EXTRA_DISPLAY_FIELDS = ('components', 'model_runs')
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    data_product = models.ForeignKey(DataProduct, on_delete=models.CASCADE, related_name='versions')
    # data_type = models.ForeignKey(DataProductDataType, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)
    processing_script_version = models.ForeignKey(ProcessingScriptVersion, on_delete=models.CASCADE, related_name='data_product_versions')
    source_versions = models.ManyToManyField(SourceVersion, blank=True)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['data_product', 'version_identifier'],
                                    name='data_product_version_unique_identifier')
        ]


class DataProductVersionComponent(DataObject):
    """
    A component of a DataProductVersion being used as the input to a ModelRun.
    """
    EXTRA_DISPLAY_FIELDS = ('model_runs',)
    FILTERSET_FIELDS = ['data_product_version', 'name']

    data_product_version = models.ForeignKey(DataProductVersion, on_delete=models.CASCADE, related_name='components')
    name = models.CharField(max_length=255, null=False, blank=False, unique=False)

    class Meta(DataObject.Meta):
        constraints = [
            models.UniqueConstraint(fields=['data_product_version', 'name'],
                                    name='data_product_version_component_unique_identifier')
        ]


class Model(DataObject):
    """
    An epidemiological model.
    """
    EXTRA_DISPLAY_FIELDS = ('versions',)

    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)


class ModelVersion(DataObjectVersion):
    """
    Version of a model that was used in a specific ModelRun.
    """
    EXTRA_DISPLAY_FIELDS = ('model_runs',)
    VERSIONED_OBJECT = 'model'
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['model', 'version_identifier'], name='model_version_unique_identifier')
        ]


class ModelRun(DataObject):
    """
    Run of a ModelVersion along with its associated input and outputs.
    """
    FILTERSET_FIELDS = ['model_version', 'release_id', 'release_date']

    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='model_runs')
    release_id = models.TextField(max_length=1024, null=False, blank=False)
    release_date = models.DateTimeField()
    description = models.TextField(max_length=1024, null=True, blank=True)
    model_config = models.TextField(max_length=1024, null=True, blank=True)
    submission_script = models.TextField(max_length=1024, null=True, blank=True)
    inputs = models.ManyToManyField(DataProductVersionComponent, blank=True, related_name='model_runs')
    outputs = models.ManyToManyField(DataProductVersion, blank=True, related_name='model_runs')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['model_version', 'release_id'], name='model_run_unique_identifier')
        ]
        ordering = ['-release_date']

    @property
    def name(self):
        return '%s (Run %s)' % (self.model_version.name, self.release_date)


def _is_data_object_subclass(name, cls):
    """
    Test if given class is a non-abstract subclasses of DataObject
    """
    return (
            isinstance(cls, type)
            and issubclass(cls, DataObject)
            and name not in ('DataObject', 'DataObjectVersion')
    )


def _is_base_model_subclass(name, cls):
    """
    Test if given class is a non-abstract subclasses of BaseModel
    """
    return (
            isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and name not in ('BaseModel', 'DataObject', 'DataObjectVersion')
    )


all_object_models = dict(
    (name, cls) for (name, cls) in globals().items() if _is_data_object_subclass(name, cls)
)

all_models = dict(
    (name, cls) for (name, cls) in globals().items() if _is_base_model_subclass(name, cls)
)
