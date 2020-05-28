from data_management.models import *
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

user = get_user_model().objects.first()

model = Model.objects.create(
        responsible_person=user,
        updated_by=user, 
        name='Test Model',
        url='http://model.url',
        short_desc='Test model',
        )

model_version1 = ModelVersion.objects.create(
        responsible_person=user,
        updated_by=user,
        model=model,
        version_identifier='1.0',
        url='http://git.url',
        short_desc='Version 1.0 of Test Model',
        )

model_version2 = ModelVersion.objects.create(
        responsible_person=user,
        updated_by=user,
        model=model,
        version_identifier='1.1',
        url='http://git.url',
        short_desc='Bugfix of version 1.0 of Test Model',
        supersedes=model_version1
        )

model_version3 = ModelVersion.objects.create(
        responsible_person=user,
        updated_by=user,
        model=model,
        version_identifier='2.0',
        url='http://git.url',
        short_desc='Version 2.0 of Test Model',
        supersedes=model_version1
        )

model_input_type = ModelInputType.objects.create(
        updated_by=user,
        name='Parameter',
        desc='Model parameters',
        )

model_input = ModelInput.objects.create(
        responsible_person=user,
        updated_by=user,
        name='Parameter 1',
        model_input_type=model_input_type,
        short_desc='Model parameter 1',
        long_desc_url='',
        )

model_input_data_type = ModelInputDataType.objects.create(
        updated_by=user,
        name='Double',
        desc='Float64 data',
        )

model_input_version = ModelInputVersion.objects.create(
        responsible_person=user,
        updated_by=user,
        model_input=model_input,
        version_identifier='1.0',
        model_input_data_type=model_input_data_type,
        value='1.234',
        short_desc='Version 1.0 of Parameter 1'
        )

source_type = SourceType.objects.create(
        updated_by=user,
        name='Research paper',
        desc='Type for data coming from papers',
        )

source = Source.objects.create(
        responsible_person=user,
        updated_by=user,
        name='Test source',
        doi='http://url.of.article',
        source_type=source_type,
        short_desc='Test research paper source',
        )

processing_script = ProcessingScript.objects.create(
        responsible_person=user,
        updated_by=user,
        name='Test script',
        url='http://url.of.script',
        )

processing_script_version = ProcessingScriptVersion.objects.create(
        responsible_person=user,
        updated_by=user,
        version_identifier='1.0',
        processing_script=processing_script,
        url='http://url.of_script.version',
        )

source_version = SourceVersion.objects.create(
        responsible_person=user,
        updated_by=user,
        source=source,
        version_identifier='1.0',
        doi='http://doi.of.data',
        url='',
        short_desc='Version 1.0 of Test script',
        processing_script_version=processing_script_version,
        )

model_input_version.source_versions.add(source_version)
model_input_version.save()

model_run = ModelRun.objects.create(
        responsible_person=user,
        updated_by=user,
        model_version=model_version3,
        run_date='2020-05-18',
        short_desc='Run of test model on 2020-05-18',
        url='',
        )

model_run.model_input_versions.add(model_input_version)

model_output = ModelOutput.objects.create(
        responsible_person=user,
        updated_by=user,
        name='Output of test model run on 2020-05-18',
        release_date='2020-05-18',
        )

model_run.model_outputs.add(model_output)
model_run.save()

Issue.objects.create(
        updated_by=user,
        content_type=ContentType.objects.get_for_model(Model),
        object_id=model.id,
        name='Bad Model',
        desc='Don\'t use this model.',
        severity=3,
        )

Issue.objects.create(
        updated_by=user,
        content_type=ContentType.objects.get_for_model(ModelVersion),
        object_id=model_version1.id,
        name='Problem with this version',
        desc='Issue with version 1.0 of the model.',
        severity=8,
        )

Issue.objects.create(
        updated_by=user,
        content_type=ContentType.objects.get_for_model(ModelInputVersion),
        object_id=model_input.id,
        name='Bad Parameter',
        desc='This parameter is no good.',
        severity=2,
        )
