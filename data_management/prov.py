from prov import identifier
from data_management.views import external_object
import prov.model
import prov.serializers
import prov.dot
import io
import json

from . import models


def _generate_object_meta(obj):
    data = []

    data.append(('last_updated', obj.last_updated))

    if obj.storage_location:
        data.append(('storage', str(obj.storage_location)))

    if obj.description:
        data.append(('description', obj.description))

    try:
        data.append(('namespace', str(obj.data_product.namespace)))
        data.append(('name', str(obj.data_product.name)))
        data.append(('version', str(obj.data_product.version)))
    except models.DataProduct.DoesNotExist:
        pass

    try:
        data.append(('name', str(obj.code_repo_release.name)))
        data.append(('version', str(obj.code_repo_release.version)))
        data.append(('website', str(obj.code_repo_release.website)))
    except models.CodeRepoRelease.DoesNotExist:
        pass

    return data

def get_whole_object_component(components):
    for component in components:
        if component.whole_object:
            return component

def generate_prov_document(data_product):
    """
    Generate a PROV document for a DataProduct detailing all the input and outputs and how they were generated.

    This uses the W3C PROV ontology (https://www.w3.org/TR/prov-o/).

    :param data_product: The DataProduct to generate the PROV document for
    :return: A PROV-O document
    """
    doc = prov.model.ProvDocument()
    doc.set_default_namespace('http://data.scrc.uk')
    data = doc.entity(
        '/api/object/' + str(data_product.object.id),
        (
            *_generate_object_meta(data_product.object),
        )
    )
    for author in data_product.object.authors.all():
        author_agent = doc.agent(
            '/api/author/' + str(author.name),
            {
                'identifier': author.identifier
            }
        )
        doc.wasAttributedTo(data, author_agent)
    if data_product.external_object:
        external_object = data_product.external_object
        external_object_entity = doc.entity(
            '/api/external_object/' + str(external_object.id),
            {
                'title': external_object.title,
                'identifier': external_object.identifier,
                'alternate_identifier': external_object.alternate_identifier,
                'alternate_identifier_type': external_object.alternate_identifier_type,
                'release_date': external_object.release_date,
            }
        )
        doc.specializationOf(external_object_entity, data)

    components = data_product.object.components.all()
    whole_object = get_whole_object_component(components)
    obj = whole_object.object
    code_run = whole_object.outputs_of.all()[0]
    cr = doc.activity(
        '/api/code_run/' + str(code_run.id),
        str(code_run.run_date),
        None,
        {
            prov.model.PROV_TYPE: 'run',
            'description': code_run.description,
        }
    )
    code_repo_release = code_run.code_repo.code_repo_release
    code_release_entity = doc.entity(
        'api/code_repo_release/' + str(code_repo_release.id),
        {
            'name': code_repo_release.name,
            'version': code_repo_release.version,
            'website': code_repo_release.website
        }
    )
    for author in code_repo_release.object.authors.all():
        author_agent = doc.agent(
            '/api/author/' + str(author.name),
            {
                'identifier': author.identifier
            }
        )
        doc.wasAttributedTo(code_release_entity, author_agent)
    doc.used(cr, code_release_entity)
    model_config = code_run.model_config
    model_config_entity = doc.entity(
        'api/object/' + str(model_config.id),
        (
            *_generate_object_meta(model_config),
        )
    )
    for author in model_config.authors.all():
        author_agent = doc.agent(
            '/api/author/' + str(author.name),
            {
                'identifier': author.identifier
            }
        )
        doc.wasAttributedTo(model_config_entity, author_agent)
    doc.used(cr, model_config_entity)
    submission_script = code_run.submission_script
    submission_script_entity = doc.entity(
        'api/object/' + str(submission_script.id),
        (
            *_generate_object_meta(submission_script),
        )
    )
    for author in submission_script.authors.all():
        author_agent = doc.agent(
            '/api/author/' + str(author.name),
            {
                'identifier': author.identifier
            }
        )
        doc.wasAttributedTo(submission_script_entity, author_agent)

    doc.wasGeneratedBy(data, cr)
    doc.used(cr, submission_script_entity)
    prov_objects = {}
    for input in code_run.inputs.all():
        if input.object.id in prov_objects:
            obj = prov_objects[input.object.id]
        else:
            obj = doc.entity('/api/object/' + str(input.object.id),
            (
                (prov.model.PROV_TYPE, 'file'),
                *_generate_object_meta(input.object),
            ))
            doc.used(cr, obj)
            doc.wasDerivedFrom(data, obj)
            prov_objects[input.object.id] = obj
            for author in input.object.authors.all():
                author_agent = doc.agent(
                    '/api/author/' + str(author.name),
                    {
                        'identifier': author.identifier
                    }
                )
                doc.wasAttributedTo(obj, author_agent)

    return doc


def serialize_prov_document(doc, format, show_attributes=True):
    """
    Serialise a PROV document as either a JPEG or SVG image or an XML or PROV-N report.

    :param doc: A PROV-O document
    :param format: The format to generate: jpg, svg, xml or provn
    :return: The PROV report in the specified format
    """
    if format in ('jpg', 'svg'):
        dot = prov.dot.prov_to_dot(doc, show_element_attributes=show_attributes)
        with io.BytesIO() as buf:
            if format == 'jpg':
                buf.write(dot.create_jpg())
            else:
                buf.write(dot.create_svg())
            buf.seek(0)
            return buf.read()
    elif format == 'xml':
        with io.StringIO() as buf:
            serializer = prov.serializers.get('xml')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return buf.read()
    elif format == 'provn':
        with io.StringIO() as buf:
            serializer = prov.serializers.get('provn')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return buf.read()
    else:
        with io.StringIO() as buf:
            serializer = prov.serializers.get('json')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return json.loads(buf.read())

