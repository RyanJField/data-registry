from django.db import models
from dynamic_validator import ModelFieldRequiredMixin
from django.contrib.auth import get_user_model
import semantic_version.django_fields


PATH_FIELD_LENGTH = 1024 * 8
CHAR_FIELD_LENGTH = 1024
TEXT_FIELD_LENGTH = 1024**2


class BaseModel(ModelFieldRequiredMixin, models.Model):
    updated_by = models.ForeignKey(
            get_user_model(),
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateTimeField(auto_now=True)

    EXTRA_DISPLAY_FIELDS = ()
    REQUIRED_FIELDS = ()
    FILTERSET_FIELDS = ()

    def reverse_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True
        ordering = ['-last_updated']


###############################################################################
# Traceablity objects

class Issue(BaseModel):
    """
    A quality issue which can be attached to any data object in the registry.
    """
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    severity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)

    def __str__(self):
        return '%s [Severity %s]' % (self.name, self.severity)


class Object(BaseModel):
    """
    Data objects.
    """
    EXTRA_DISPLAY_FIELDS = (
        'components',
        'data_product',
        'code_repo_release',
        'external_object',
        'quality_control',
        'authors',
        'licences',
        'keywords',
    )
    FILTERSET_FIELDS = (
        'last_updated',
        'updated_by',
        'storage_location',
        'data_product',
        'code_repo_release',
        'external_object',
    )

    issues = models.ManyToManyField(Issue, related_name='object_issues', blank=True)
    storage_location = models.OneToOneField('StorageLocation', on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='location_for_object')

    def name(self):
        if self.storage_location:
            return str(self.storage_location)
        elif self.external_object:
            return str(self.external_object)
        else:
            return super().__str__(self)

    def __str__(self):
        return self.name()


class ObjectComponent(BaseModel):
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    issues = models.ManyToManyField(Issue, related_name='component_issues', blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='components', null=False)


class CodeRun(BaseModel):
    code_repo = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='code_repo_of', null=False)
    model_config = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='config_of', null=False)
    submission_script = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='submission_script_of', null=False)
    run_date = models.DateTimeField(null=False)
    run_identifier = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    inputs = models.ManyToManyField(ObjectComponent, related_name='inputs_of')
    outputs = models.ManyToManyField(ObjectComponent, related_name='outputs_of')


###############################################################################
# Metadata objects

class URIField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        super().__init__(*args, **kwargs)


class StorageRoot(BaseModel):
    """
    The root location of a storage cache where model files are stored.
    """
    PUBLIC = 0
    PRIVATE = 1
    CHOICES = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    )
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    root = URIField(null=False, blank=False)
    accessibility = models.SmallIntegerField(choices=CHOICES, default=PUBLIC)

    def is_public(self):
        return self.accessibility == self.PUBLIC

    def __str__(self):
        return self.name


class StorageLocation(BaseModel):
    """
    The storage location of a model file relative to a StorageRoot.
    """
    path = models.CharField(max_length=PATH_FIELD_LENGTH, null=False, blank=False)
    hash = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    storage_root = models.ForeignKey(StorageRoot, on_delete=models.CASCADE, related_name='locations')

    def full_uri(self):
        return self.storage_root.root + '/' + self.path

    def __str__(self):
        return self.full_uri()


class Source(BaseModel):
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    abbreviation = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    website = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class ExternalObject(BaseModel):
    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='external_object')
    doi_or_unique_name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False, unique=True)
    primary_not_supplement = models.BooleanField(default=True)
    release_date = models.DateTimeField()
    title = models.CharField(max_length=CHAR_FIELD_LENGTH)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='external_objects')
    original_store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='original_store_of', null=True, blank=True)
    version = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)


class QualityControlled(BaseModel):
    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='quality_control')


class Keyword(BaseModel):
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='keywords')
    keyphrase = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)


class Author(BaseModel):
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='authors')
    family_name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    personal_name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)


class Licence(BaseModel):
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='licences')
    licence_info = models.TextField()


class Namespace(BaseModel):
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)


class DataProduct(BaseModel):
    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='data_product')
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name='data_products')
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    version = semantic_version.django_fields.VersionField()


class CodeRepoRelease(BaseModel):
    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='code_repo_release')
    name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    version = semantic_version.django_fields.VersionField()
    website = models.URLField(null=True, blank=True)


class KeyValue(BaseModel):
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='metadata')
    key = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    value = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)


def _is_base_model_subclass(name, cls):
    """
    Test if given class is a non-abstract subclasses of BaseModel
    """
    return (
            isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and name not in ('BaseModel',)
    )


all_models = dict(
    (name, cls) for (name, cls) in globals().items() if _is_base_model_subclass(name, cls)
)
