from django.db import models
from dynamic_validator import ModelFieldRequiredMixin
from django.contrib.auth import get_user_model

from . import validators


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
    ADMIN_LIST_FIELDS = ()

    def reverse_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True
        ordering = ['-last_updated']


###############################################################################
# Custom Fields

class URIField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        super().__init__(*args, **kwargs)


class NameField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        kwargs['validators'] = (validators.NameValidator(),)
        super().__init__(*args, **kwargs)


class VersionField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        kwargs['validators'] = (validators.VersionValidator(),)
        super().__init__(*args, **kwargs)


###############################################################################
# Traceablity objects

class Issue(BaseModel):
    """
    A quality issue which can be attached to any data object in the registry.
    """
    FILTERSET_FIELDS = ('severity',)
    SHORT_DESC_LENGTH = 40

    severity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)

    def short_desc(self):
        if self.description is None:
            return ''
        elif len(self.description) <= self.SHORT_DESC_LENGTH:
            return self.description
        else:
            return self.description[:self.SHORT_DESC_LENGTH - 3] + '...'

    def __str__(self):
        return '%s [Severity %s]' % (self.short_desc(), self.severity)


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
    ADMIN_LIST_FIELDS = ('name',)

    issues = models.ManyToManyField(Issue, related_name='object_issues', blank=True)
    storage_location = models.OneToOneField('StorageLocation', on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='location_for_object')
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)

    def name(self):
        if self.storage_location:
            return str(self.storage_location)
        else:
            try:
                return str(self.external_object)
            except ExternalObject.DoesNotExist:
                return super().__str__()

    def __str__(self):
        return self.name()


class ObjectComponent(BaseModel):
    FILTERSET_FIELDS = ('name', 'last_updated', 'object')
    ADMIN_LIST_FIELDS = ('object', 'name')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='components', null=False)
    name = NameField(null=False, blank=False)
    issues = models.ManyToManyField(Issue, related_name='component_issues', blank=True)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'name'),
                name='unique_object_component'),
        ]

    def __str__(self):
        return self.name


class CodeRun(BaseModel):
    FILTERSET_FIELDS = ('run_date', 'run_identifier', 'last_updated')
    ADMIN_LIST_FIELDS = ('run_identifier',)

    code_repo = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='code_repo_of', null=True, blank=True)
    model_config = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='config_of', null=True, blank=True)
    submission_script = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='submission_script_of', null=False, blank=False)
    run_date = models.DateTimeField(null=False, blank=False)
    run_identifier = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    inputs = models.ManyToManyField(ObjectComponent, related_name='inputs_of', blank=True)
    outputs = models.ManyToManyField(ObjectComponent, related_name='outputs_of', blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('run_identifier',),
                name='unique_code_run'),
        ]

    def __str__(self):
        if self.code_repo:
            return '%s run %s' % (self.code_repo, self.run_identifier)
        return self.run_identifier


###############################################################################
# Metadata objects

class StorageRoot(BaseModel):
    """
    The root location of a storage cache where model files are stored.
    """
    FILTERSET_FIELDS = ('name', 'root', 'last_updated', 'accessibility')
    ADMIN_LIST_FIELDS = ('name',)

    PUBLIC = 0
    PRIVATE = 1
    CHOICES = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    )
    name = NameField(null=False, blank=False)
    root = URIField(null=False, blank=False)
    accessibility = models.SmallIntegerField(choices=CHOICES, default=PUBLIC)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name',),
                name='unique_storage_root'),
        ]

    def is_public(self):
        return self.accessibility == self.PUBLIC

    def __str__(self):
        return self.name


class StorageLocation(BaseModel):
    """
    The storage location of a model file relative to a StorageRoot.
    """
    FILTERSET_FIELDS = ('last_updated', 'path', 'hash')
    ADMIN_LIST_FIELDS = ('storage_root', 'path')

    path = models.CharField(max_length=PATH_FIELD_LENGTH, null=False, blank=False)
    hash = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    storage_root = models.ForeignKey(StorageRoot, on_delete=models.CASCADE, related_name='locations')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('storage_root', 'path', 'hash'),
                name='unique_storage_location'),
        ]

    def full_uri(self):
        return self.storage_root.root + self.path

    def __str__(self):
        return self.full_uri()


class Source(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'name', 'abbreviation')
    ADMIN_LIST_FIELDS = ('name',)

    name = NameField(null=False, blank=False)
    abbreviation = NameField(null=False, blank=False)
    website = models.URLField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name',),
                name='unique_source'),
        ]

    def __str__(self):
        return self.name


class ExternalObject(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'doi_or_unique_name', 'release_date', 'title', 'version')
    ADMIN_LIST_FIELDS = ('doi_or_unique_name', 'title', 'version')

    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='external_object')
    doi_or_unique_name = NameField(null=False, blank=False, unique=True)
    primary_not_supplement = models.BooleanField(default=True)
    release_date = models.DateTimeField()
    title = models.CharField(max_length=CHAR_FIELD_LENGTH)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='external_objects')
    original_store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='original_store_of', null=True, blank=True)
    version = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('doi_or_unique_name', 'title', 'version'),
                name='unique_external_object'),
        ]

    def __str__(self):
        return '%s %s version %s' % (self.doi_or_unique_name, self.title, self.version)


class QualityControlled(BaseModel):
    ADMIN_LIST_FIELDS = ('object',)

    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='quality_control')


class Keyword(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'keyphrase')
    ADMIN_LIST_FIELDS = ('object', 'keyphrase')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='keywords')
    keyphrase = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'keyphrase'),
                name='unique_keyword'),
        ]

    def __str__(self):
        return self.keyphrase


class Author(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'family_name', 'personal_name')
    ADMIN_LIST_FIELDS = ('object', 'family_name', 'personal_name')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='authors')
    family_name = NameField(null=False, blank=False)
    personal_name = NameField(null=False, blank=False)

    def __str__(self):
        return '%s, %s' % (self.family_name, self.personal_name)


class Licence(BaseModel):
    FILTERSET_FIELDS = ('last_updated',)
    ADMIN_LIST_FIELDS = ('object',)

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='licences')
    licence_info = models.TextField()


class Namespace(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'name')
    ADMIN_LIST_FIELDS = ('name',)

    name = NameField(null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name',),
                name='unique_namespace'),
        ]

    def __str__(self):
        return self.name


class DataProduct(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'namespace', 'name', 'version')
    ADMIN_LIST_FIELDS = ('namespace', 'name', 'version')

    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='data_product')
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name='data_products')
    name = NameField(null=False, blank=False)
    version = VersionField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('namespace', 'name', 'version'),
                name='unique_data_product'),
        ]

    def __str__(self):
        return '%s:%s version %s' % (self.namespace, self.name, self.version)


class CodeRepoRelease(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'name', 'version')
    ADMIN_LIST_FIELDS = ('name', 'version')

    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='code_repo_release')
    name = NameField(null=False, blank=False)
    version = VersionField()
    website = models.URLField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'version'),
                name='unique_code_repo_release'),
        ]

    def __str__(self):
        return '%s version %s' % (self.name, self.version)


class KeyValue(BaseModel):
    FILTERSET_FIELDS = ('last_updated', 'key')
    ADMIN_LIST_FIELDS = ('object', 'key')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='metadata')
    key = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    value = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'key'),
                name='unique_key_value'),
        ]

    def __str__(self):
        return self.key


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
