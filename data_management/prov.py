import prov.model
import prov.serializers
import prov.dot
import io
import json

from . import models


def _generate_object_meta(obj):
    data = []

    if obj.storage_location:
        data.append(('storage', str(obj.storage_location)))

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
        if component.name == "whole_object":
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
        '/api/data_product/' + str(data_product.id),
        {
            'last updated': str(data_product.last_updated),
            'version': data_product.version
        }
    )
    components = data_product.object.components.all()
    whole_object = get_whole_object_component(components)
    print(whole_object.outputs_of.all())
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
    doc.wasGeneratedBy(data, cr)
    prov_objects = {}
    for input in code_run.inputs.all():
        if input.object.id in prov_objects:
            obj = prov_objects[input.object.id]
        else:
            obj = doc.entity('/api/object/' + str(input.object.id), (
                (prov.model.PROV_TYPE, 'file'),
                *_generate_object_meta(input.object)
            ))
            doc.used(cr, obj)
            prov_objects[input.object.id] = obj

    return doc


def serialize_prov_document(doc, format):
    """
    Serialise a PROV document as either a JPEG or SVG image or an XML or PROV-N report.

    :param doc: A PROV-O document
    :param format: The format to generate: jpg, svg, xml or provn
    :return: The PROV report in the specified format
    """
    if format in ('jpg', 'svg'):
        dot = prov.dot.prov_to_dot(doc)
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

