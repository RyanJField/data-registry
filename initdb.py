from data_management import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

user = get_user_model().objects.first()

models.Object.objects.all().delete()
models.ObjectComponent.objects.all().delete()
models.CodeRun.objects.all().delete()

simple_network_sim = models.Object.objects.create(
        updated_by=user,
        responsible_person=user,
        name='simple_network_sim',
        type='CODE',
        version_identifier='0.1.0',
        accessibility='public',
        uri='git@github.com:ScottishCovidResponse/simple_network_sim.git',
)

human_pop_processing_script = models.Object.objects.create(
        updated_by=user,
        responsible_person=user,
        name='simple_network_sim human population processing script',
        type='CODE',
        version_identifier='0.1.0',
        accessibility='public',
        uri='git@github.com:ScottishCovidResponse/simple_network_sim.git',
)

pop_source = models.Object.objects.create(
        updated_by=user,
        responsible_person=user,
        name='Human Population Data Source',
        type='SOURCE',
        version_identifier='1',
        accessibility='public',
        uri='https://doi.org/some/paper/doi',
)

pop_source_comp = models.ObjectComponent.objects.create(
        updated_by=user,
        responsible_person=user,
        object=pop_source,
        name='Human Population',
)

pop = models.Object.objects.create(
        updated_by=user,
        responsible_person=user,
        name='Human Population Data',
        type='DATA_PRODUCT',
        version_identifier='1',
        accessibility='public',
        uri='https://github.com/ScottishCovidResponse/simple_network_sim/blob/master/sample_input_files/human/population/1/data.csv',
)

pop_comp = models.ObjectComponent.objects.create(
        updated_by=user,
        responsible_person=user,
        object=pop,
        name='Human Population',
)

pop_script_run = models.CodeRun.objects.create(
        updated_by=user,
        run_identifier='',
        code=human_pop_processing_script,
        run_date='2020-07-02T15:43:21Z',
)
pop_script_run.inputs.add(pop_source_comp)
pop_script_run.outputs.add(pop_comp)

out = models.Object.objects.create(
        updated_by=user,
        responsible_person=user,
        name='simple_network_sim output file',
        type='DATA_PRODUCT',
        version_identifier='1',
        accessibility='public',
        uri='ftp://server.com/some/stored/data',
)

out_comp = models.ObjectComponent.objects.create(
        updated_by=user,
        responsible_person=user,
        object=out,
        name='simple_network_sim output',
)

sns_run = models.CodeRun.objects.create(
        updated_by=user,
        run_identifier='',
        code=simple_network_sim,
        run_date='2020-07-02T15:43:21Z',
)
sns_run.inputs.add(pop_comp)
sns_run.outputs.add(out_comp)

models.Issue.objects.create(
        updated_by=user,
        content_type=ContentType.objects.get_for_model(models.ObjectComponent),
        object_id=pop_comp.id,
        name='Bad Parameter',
        description='This parameter is no good.',
        severity=8,
        )

models.Issue.objects.create(
        updated_by=user,
        content_type=ContentType.objects.get_for_model(models.Object),
        object_id=simple_network_sim.id,
        name='Problem with this version',
        description='Issue with version 1.0 of the model.',
        severity=2,
        )
