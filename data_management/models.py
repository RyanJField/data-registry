from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from dynamic_validator import ModelFieldRequiredMixin
import semver


class BaseModel(ModelFieldRequiredMixin, models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateTimeField(auto_now=True)

    EXTRA_DISPLAY_FIELDS = ()
    REQUIRED_FIELDS = ('name',)
    FILTERSET_FIELDS = ('name',)

    def reverse_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True
        ordering = ['name', '-last_updated']

    def __str__(self):
        return self.name


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


class Object(BaseModel):
    """
    All data products, codes and data sources are represented as Objects in the registry.
    """
    EXTRA_DISPLAY_FIELDS = ('components', 'superseded_by', 'code_for_run')
    FILTERSET_FIELDS = ('name', 'type', 'version_identifier')

    TYPE_CODE = 'CODE'
    TYPE_SOURCE = 'SOURCE'
    TYPE_DATA_PRODUCT = 'DATA_PRODUCT'
    TYPE_CHOICES = [
        (TYPE_CODE, 'Code'),
        (TYPE_SOURCE, 'Source'),
        (TYPE_DATA_PRODUCT, 'Data Product'),
    ]

    # object_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    responsible_person = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_responsible_for',
            )
    issues = GenericRelation(Issue)
    type = models.CharField(max_length=128, choices=TYPE_CHOICES, null=False, blank=False)
    version_identifier = models.CharField(max_length=128, null=False, blank=False)
    accessibility = models.CharField(max_length=128)
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='superseded_by')
    uri = models.CharField(max_length=1024, null=False, blank=False)
    hash = models.CharField(max_length=1204, null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=['name', 'type', 'version_identifier'], name='object_unique_identifier')
        ]

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        try:
            semver.parse(self.version_identifier)
        except ValueError:
            raise ValidationError


class ObjectComponent(BaseModel):
    """
    A component of a registry objects, such as a parameter value taken from a paper.
    """
    EXTRA_DISPLAY_FIELDS = ('input_to_runs', 'output_of_runs', 'superseded_by')
    FILTERSET_FIELDS = ('object', 'name')

    responsible_person = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_responsible_for',
            )
    issues = GenericRelation(Issue)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='components')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='superseded_by')

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=['object', 'name'], name='object_component_unique_identifier')
        ]


class CodeRun(BaseModel):
    """
    Run of a ModelVersion along with its associated input and outputs.
    """
    FILTERSET_FIELDS = ('code', 'run_identifier', 'run_date')

    code = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='code_for_run')
    run_identifier = models.TextField(max_length=1024, null=False, blank=False)
    run_date = models.DateTimeField()
    description = models.TextField(max_length=1024, null=True, blank=True)
    model_config = models.TextField(max_length=1024, null=True, blank=True)
    submission_script = models.TextField(max_length=1024, null=True, blank=True)
    inputs = models.ManyToManyField(ObjectComponent, blank=True, related_name='input_to_runs')
    outputs = models.ManyToManyField(ObjectComponent, blank=True, related_name='output_of_runs')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=['code', 'run_identifier'], name='code_run_unique_identifier')
        ]
        ordering = ['-run_date']

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        try:
            semver.parse(self.run_identifier)
        except ValueError:
            raise ValidationError

    @property
    def name(self):
        return '%s (Run %s)' % (self.code.name, self.run_identifier)


all_object_models = {
    'Object': Object,
    'ObjectComponent': ObjectComponent,
    'CodeRun': CodeRun,
}

all_models = {
    'Object': Object,
    'ObjectComponent': ObjectComponent,
    'CodeRun': CodeRun,
    'Issue': Issue,
}
