from uuid import uuid4

from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.urls import reverse
from dynamic_validator import ModelFieldRequiredMixin
from django.contrib.auth import get_user_model

from . import validators


PATH_FIELD_LENGTH = 1024 * 8
CHAR_FIELD_LENGTH = 1024
TEXT_FIELD_LENGTH = 1024**2


class BaseModel(ModelFieldRequiredMixin, models.Model):
    """
    Base model for all objects in the database. Used to defined common fields and functionality.
    """
    _field_names = None
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
    FILTERSET_FIELDS = '__all__'
    ADMIN_LIST_FIELDS = ()

    def reverse_name(self):
        return self.__class__.__name__.lower()

    @classmethod
    def field_names(cls):
        if cls._field_names is None:
            cls._field_names = tuple(field.name for field in cls._meta.get_fields() if field.name != 'id')
        return cls._field_names

    class Meta:
        abstract = True
        ordering = ['-last_updated']


###############################################################################
# Custom Fields

class URIField(models.CharField):
    """
    A field type used to specify that a field holds a URI.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        super().__init__(*args, **kwargs)


class NameField(models.CharField):
    """
    A field type used to specify that a field holds a simple name, one that we can apply a glob filter to
    when filtering the query.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        kwargs['validators'] = (validators.NameValidator(),)
        super().__init__(*args, **kwargs)


class VersionField(models.CharField):
    """
    A field type used to specify that a field holds a semantic version.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        kwargs['validators'] = (validators.VersionValidator(),)
        super().__init__(*args, **kwargs)


###############################################################################
# Traceablity objects

class FileType(BaseModel):
    """
    ***The file type of an object.***

    ### Writable Fields:
    `name`: Name of the file type. Examples:

    * Hierarchical Data Format version 5
    * Comma-separated values file
    * Microsoft Excel Open XML Spreadsheet

    `extension`: Filename extension. Examples:

    * h5
    * csv
    * xlsx

    The combination of `name` and `extension` are enforced to be unique.

    ### Read-only Fields:
    `url`: Reference to the instance of the `FileType`, final integer is the `FileType` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    """
    name = models.TextField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    extension = models.TextField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'extension'),
                name='unique_file_type_name_extension'),
        ]

class Issue(BaseModel):
    """
    ***A quality issue that can be attached to any `Object` or `ObjectComponent`.***

    ### Writable Fields:
    `severity`: Severity of this `Issue` as an integer, the larger the value the more severe the `Issue`

    `description`: Free text description of the `Issue`

    `object_issues`: List of `Object` URLs which the `Issue` is associated with

    `component_issues`: List of `ObjectComponent` URLs which the `Issue` is associated with

    `uuid` (*optional*): UUID of the `Issue`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `Issue`, final integer is the `Issue` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    # EXTRA_DISPLAY_FIELDS = (
    #     'last_updated',
    # )
    EXTRA_DISPLAY_FIELDS = ('object_issues', 'component_issues')
    SHORT_DESC_LENGTH = 40

    severity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=False, blank=False)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def short_desc(self):
        if self.description is None:
            return ''
        elif len(self.description) <= self.SHORT_DESC_LENGTH:
            return self.description
        else:
            return self.description[:self.SHORT_DESC_LENGTH - 3] + '...'

    def __str__(self):
        return '%s [Severity %s]' % (self.short_desc(), self.severity)


class Organisation(BaseModel):
    """
    ***Organisations that can be associated with an `Author`.***
    ### Writable Fields:
    `name`: Name of the `Organisation`

    `ror` (*optional*): Unique 9-character string representing the ROR ID of the `Organisation` (https://ror.org)

    `uuid` (*optional*): UUID of the `Organisation`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `Organisation`, final integer is the `Organisation` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    EXTRA_DISPLAY_FIELDS = (
        'ror_url',
    )

    name = models.CharField(max_length=PATH_FIELD_LENGTH, null=False, blank=False, unique=True)
    ror = models.CharField(max_length=9, null=True, blank=True, unique=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def ror_url(self):
        if self.ror:
            return 'https://ror.org/%s' % self.ror
        else:
            return None


class Author(BaseModel):
    """
    ***Authors that can be associated with an `Object` usually for use with `ExternalObject`s to record paper authors,
    etc.***

    ### Writable Fields:
    `family_name`: Family name of the `Author`

    `personal_name`: Personal name of the `Author`

    `orcid` (*optional*): ORCID iD of the `Author`

    `uuid` (*optional*): UUID of the `Author`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `Author`, final integer is the `Author` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('family_name', 'personal_name')
    EXTRA_DISPLAY_FIELDS = ('orcid_url',)

    family_name = NameField(null=False, blank=False)
    personal_name = NameField(null=False, blank=False)
    orcid = models.CharField(max_length=19, null=True, blank=True, unique=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def __str__(self):
        return '%s, %s' % (self.family_name, self.personal_name)

    def orcid_url(self):
        if self.orcid:
            return 'https://orcid.org/%s' % self.orcid
        else:
            return None


class Object(BaseModel):
    """
    ***Core traceability object used to represent any data object such `DataProduct`, `CodeRepoRelease`, etc. ***

    ### Writable Fields:
    `description` (*optional*): Free text description of the `Object`

    `storage_location` (*optional*): The URL of the `StorageLocation` which is the location of the physical data of
     this object, if applicable

    `issues` (*optional*): List of `Issues` URLs to associate with this `Object`

    `authors` (*optional*): List of `Author` URLs to associate with this `Object`

    `uuid` (*optional*): UUID of the `Object`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `Object`, final integer is the `Object` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `components`: List of `ObjectComponents` API URLs associated with this `Object`

    `data_product`: The `DataProduct` API URL if one is associated with this `Object`

    `code_repo_release`: The `CodeRepoRelease` API URL if one is associated with this `Object`

    `external_object`: The `ExternalObject` API URL if one is associated with this `Object`

    `quality_control`: The `QualityControl` API URL if one is associated with this `Object`

    `licences`: List of `Licence` API URLs associated with this `Object`

    `keywords`: List of `Keyword` API URLs associated with this `Object`
    """
    EXTRA_DISPLAY_FIELDS = (
        'components',
        'data_product',
        'code_repo_release',
        'external_objects',
        'quality_control',
        'authors',
        'licences',
        'keywords',
    )
    ADMIN_LIST_FIELDS = ('name', 'is_orphan')

    issues = models.ManyToManyField(Issue, related_name='object_issues', blank=True)
    storage_location = models.OneToOneField('StorageLocation', on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='location_for_object')
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    file_type = models.ForeignKey(FileType, on_delete=models.CASCADE, null=True, blank=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def name(self):
        if self.storage_location:
            return str(self.storage_location)
        else:
            try:
                return str(','.join(object for object in self.external_objects.all()))
            except ExternalObject.DoesNotExist:
                return super().__str__()

    def is_orphan(self):
        """
        Test is this object is connected to anything else.
        """
        if self.storage_location:
            return False
        try:
            if self.data_product:
                return False
        except DataProduct.DoesNotExist:
            pass
        try:
            if self.code_repo_release:
                return False
        except CodeRepoRelease.DoesNotExist:
            pass
        try:
            if self.external_objects:
                return False
        except ExternalObject.DoesNotExist:
            pass
        return True

    def __str__(self):
        return self.name()


class ObjectAuthorOrg(BaseModel):
    """
    ***A combination of an `Author` and list of `Organisation`s associated with a particular `Object`.***

    ### Writable Fields:
    `object`: The API URL of the `Object` to associate with this `ObjectAuthorOrg`

    `author`: The API URL of the `Author` to associated with this `ObjectAuthorOrg`

    `organisations`: List of API URLs of the `Organisation`s to associate with this `ObjectAuthorOrg`

    ### Read-only Fields:
    `url`: Reference to the instance of the `ObjectAuthorOrg`, final integer is the `ObjectAuthorOrg` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='authors', null=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=False, blank=False)
    organisations = models.ManyToManyField(Organisation, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'author'),
                name='unique_object_author'),
        ]


class ObjectComponent(BaseModel):
    """
    ***A component of a `Object` being used as the input to a `CodeRun` or produced as an output from a
    `CodeRun`.***

    ### Writable Fields:
    `object`: The API URL of the `Object` to associate this `ObjectComponent` with

    `name`: Name of the `ObjectComponent`, unique in the context of `ObjectComponent` and its `Object` reference

    `description` (*optional*): Free text description of the `ObjectComponent`

    `whole_object`: Specifies if this `ObjectComponent` refers to the whole object or not (default is `False`)

    `issues` (*optional*): List of `Issues` URLs to associate with this `ObjectComponent`

    ### Read-only Fields:
    `url`: Reference to the instance of the `ObjectComponent`, final integer is the `ObjectComponent` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `input_of`: List of `CodeRun` that the `ObjectComponent` is being used as an input to

    `output_of`: List of `CodeRun` that the `ObjectComponent` was created as an output of
    """
    ADMIN_LIST_FIELDS = ('object', 'name')
    EXTRA_DISPLAY_FIELDS = ('inputs_of', 'outputs_of')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='components', null=False)
    name = NameField(null=False, blank=False)
    issues = models.ManyToManyField(Issue, related_name='component_issues', blank=True)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    whole_object = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'name'),
                name='unique_object_component'),
        ]

    def __str__(self):
        return self.name


class CodeRun(BaseModel):
    """
    ***A code run along with its associated, code repo, configuration, input and outputs.***

    ### Writable Fields:
    `run_date`: datetime of the `CodeRun`

    `description` (*optional*): Free text description of the `CodeRun`

    `code_repo` (*optional*):  Reference to the `Object` associated with the `CodeRepoRelease` that was run

    `model_config`: Reference to the `Object` for the YAML configuration used for the `CodeRun`

    `submission_script`: Reference to the `Object` for the submission script used for the `CodeRun`

    `inputs`: List of `ObjectComponent` that the `CodeRun` used as inputs

    `outputs`: List of `ObjectComponent` that the `CodeRun` produced as outputs

    `uuid` (*optional*): UUID of the `CodeRun`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `ModelRun`, final integer is the `ModelRun` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    EXTRA_DISPLAY_FIELDS = ('prov_report',)
    ADMIN_LIST_FIELDS = ('description',)

    code_repo = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='code_repo_of', null=True, blank=True)
    model_config = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='config_of', null=True, blank=True)
    submission_script = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='submission_script_of', null=False, blank=False)
    run_date = models.DateTimeField(null=False, blank=False)
    description = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    inputs = models.ManyToManyField(ObjectComponent, related_name='inputs_of', blank=True)
    outputs = models.ManyToManyField(ObjectComponent, related_name='outputs_of', blank=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def prov_report(self):
        url = reverse('prov_report', kwargs={'pk': self.id})
        full_url = ''.join(['http://', get_current_site(None).domain, url])
        return full_url

    def __str__(self):
        if self.code_repo:
            return '%s run %s' % (self.code_repo, self.description)
        return self.uuid


###############################################################################
# Metadata objects

class StorageRoot(BaseModel):
    """
    ***The root location of a storage cache where model files are stored.***

    ### Writable Fields:
    `name`: Name of the `StorageRoot`, unique in the context of `StorageRoot`

    `root`: URI (including protocol) to the root of a `StorageLocation`, which when prepended to a `StorageLocation`

    `path` produces a complete URI to a file. Examples:

    * https://somewebsite.com/
    * ftp://host/ (ftp://username:password@host:port/)
    * ssh://host/
    * file:///someroot/ (file://C:\)
    * github://org:repo@sha/ (github://org:repo/ (master))

    `accessibility` (*optional*): Integer value for the Accessibility enum:

    * 0: Public (*default*) - the storage root is completely pubic with no provisos for use
    * 1: Private - the storage root is for inaccessible data or there are provisos attached to the data use

    ### Read-only Fields:
    `url`: Reference to the instance of the `StorageRoot`, final integer is the `StorageRoot` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    EXTRA_DISPLAY_FIELDS = ('locations',)
    ADMIN_LIST_FIELDS = ('name',)

    PUBLIC = 0
    PRIVATE = 1
    CHOICES = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    )
    name = NameField(null=False, blank=False)
    root = URIField(null=False, blank=False, unique=True)
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
    ***The location of an item relative to a `StorageRoot`.***

    ### Writable Fields:
    `path`: Path from a `StorageRoot` `uri` to the item location, when appended to a `StorageRoot` `uri`
    produces a complete URI.

    `hash`: If `StorageLocation` references a file, this is the calculated SHA1 hash of the file. If `StorageLocation`
    references a directory *TODO: can't be git sha for validation (doesn't care about local changes), could be recursive
    sha1 of all files in the directory (excluding .git and things referenced in .gitignore), but needs to be OS independent
    (order matters) and things like logging output might affect it...*

    `store_root`: Reference to the `StorageRoot` to append the `path` to.

    ### Read-only Fields:
    `url`: Reference to the instance of the `StorageLocation`, final integer is the `StorageLocation` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
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


class ExternalObject(BaseModel):
    """
    *** An external data object, i.e. one that has comes from somewhere other than being generated as part of the
      modelling pipeline.***

    ### Writable Fields:
    `doi_or_unique_name`: DOI or Name of the `ExternalObject`, unique in the context of the triple (`doi_or_unique_name`, `title`, `version`)

    `primary_not_supplement` (*optional*): Boolean flag to indicate that the `ExternalObject` is a primary source

    `release_date`: Date-time the `ExternalObject` was released

    `title`: Title of the `ExternalObject`

    `description` (*optional*):  Free text description of the `ExternalObject`

    `version`: `ExternalObject` version identifier

    `object`: API URL of the associated `Object`

    `original_store` (*optional*): `StorageLocation` that references the original location of this `ExternalObject`.
    For example, if the original data location could be transient and so the data has been copied to a more robust
    location, this would be the reference to the original data location.

    ### Read-only Fields:
    `url`: Reference to the instance of the `ExternalObject`, final integer is the `ExternalObject` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('doi_or_unique_name', 'title', 'version')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='external_objects')
    doi_or_unique_name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    primary_not_supplement = models.BooleanField(default=True)
    release_date = models.DateTimeField()
    title = models.CharField(max_length=CHAR_FIELD_LENGTH)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    original_store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='original_store_of', null=True, blank=True)
    version = VersionField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('doi_or_unique_name', 'title', 'version'),
                name='unique_external_object'),
        ]

    def __str__(self):
        return '%s %s version %s' % (self.doi_or_unique_name, self.title, self.version)


class QualityControlled(BaseModel):
    """
    ***Marks that the associated `Object` has been quality controlled.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    ### Read-only Fields:
    `url`: Reference to the instance of the `QualityControlled`, final integer is the `QualityControlled` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object',)

    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='quality_control')


class Keyword(BaseModel):
    """
    ***Keywords that can be associated with an `Object` usually for use with `ExternalObject`s to record paper keywords,
    etc.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `keyphrase`: Free text field for the key phrase to associate with the `Object`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Keyword`, final integer is the `Keyword` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object', 'keyphrase')

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='keywords')
    keyphrase = NameField(null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'keyphrase'),
                name='unique_keyword'),
        ]

    def __str__(self):
        return self.keyphrase


class Licence(BaseModel):
    """
    ***Licence that can be associated with an `Object` in case the code or data source has a specific licence that needs
    to be recorded.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `licence_info`: Free text field to store the information about the `Licence`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Licence`, final integer is the `Licence` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object',)

    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name='licences')
    licence_info = models.TextField()


class Namespace(BaseModel):
    """
    ***A namespace that can be used to group `DataProduct`s.***

    ### Writable Fields:
    `name`: The `Namespace` name

    `full_name`: The full name of the `Namespace`

    `website` (*optional*): Website URL associated with the `Namespace`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Namespace`, final integer is the `Namespace` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('name', 'full_name', 'website')

    name = NameField(null=False, blank=False)
    full_name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    website = models.URLField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name',),
                name='unique_name'),
            models.UniqueConstraint(
                fields=('full_name',),
                name='unique_full_name'),
        ]

    def __str__(self):
        return self.name


class DataProduct(BaseModel):
    """
    ***A data product that is used by or generated by a model.***

    ### Writable Fields:
    `name`: Name of the `DataProduct`, unique in the context of the triple (`name`, `version`, `namespace`)

    `version`: Version identifier of the `DataProduct`, must conform to semantic versioning syntax

    `object`: API URL of the associated `Object`

    `namespace`: API URL of the `Namespace` of the `DataProduct`

    ### Read-only Fields:
    `url`: Reference to the instance of the `DataProduct`, final integer is the `DataProduct` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('namespace', 'name', 'version')

    object = models.OneToOneField(Object, on_delete=models.CASCADE, related_name='data_product')
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name='data_products')
    name = NameField(null=False, blank=False)
    version = VersionField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('namespace', 'name', 'version'),
                name='unique_data_product'),
        ]

    def __str__(self):
        return '%s:%s version %s' % (self.namespace, self.name, self.version)


class CodeRepoRelease(BaseModel):
    """
    ***Information marking that an `Object` is an official release of a model code.***

    ### Writable Fields:
    `name`: Name of the `CodeRepoRelease`, unique in the context of the `CodeRepoRelease.version`

    `version`: Version identifier of the `CodeRepoRelease`, must conform to semantic versioning syntax, unique in the
    context of the `CodeRepoRelease.name`

    `object`: API URL of the associated `Object`

    `website` (*optional*): URL of the website for this code release, if applicable

    ### Read-only Fields:
    `url`: Reference to the instance of the `CodeRepoRelease`, final integer is the `CodeRepoRelease` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
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
    """
    ***Free meta-data key-values associated with an `Object`.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `key`: Meta-data name

    `value`: Meta-data value

    ### Read-only Fields:
    `url`: Reference to the instance of the `KeyValue`, final integer is the `KeyValue` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
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


###############################################################################
# General text storage

class TextFile(BaseModel):
    """
    ***Table for storing general small text files in the database.***

    This is should only be using for storing scripts which are a few lines in length and do not have a home elsewhere.
    These objects are not linked to the rest of the schema but can be referenced by URL using the `StorageRoot` and
    `StorageLocation` objects. If this table is migrated to a dedicated data store then the `StorageRoot` can be updated
    and if the relative `StorageLocation` paths remain the same the generated paths should still be valid.

    ### Writable Fields:
    `text`: Free text field for the file contents

    ### Read-only Fields:
    `url`: Reference to the instance of the `TextFile`, final integer is the `TextFile` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    text = models.TextField(max_length=TEXT_FIELD_LENGTH, null=False, blank=False)


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
