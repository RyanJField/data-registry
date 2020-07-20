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

    if obj.data_product:
        data.append(('namespace', str(obj.data_product.namespace)))
        data.append(('name', str(obj.data_product.name)))
        data.append(('version', str(obj.data_product.version)))

    try:
        data.append(('name', str(obj.code_repo_release.name)))
        data.append(('version', str(obj.code_repo_release.version)))
        data.append(('website', str(obj.code_repo_release.website)))
    except models.CodeRepoRelease.DoesNotExist:
        pass

    try:
        data.append(('title', str(obj.external_object.title)))
        data.append(('version', str(obj.external_object.version)))
        data.append(('release_date', str(obj.external_object.release_date)))
    except models.ExternalObject.DoesNotExist:
        pass

    return data


def generate_prov_document(code_run):
    """
    Generate a PROV document for a CodeRun detailing all the input and outputs and how they were generated.

    This uses the W3C PROV ontology (https://www.w3.org/TR/prov-o/).

    :param code_run: The CodeRun to generate the PROV document for
    :return: A PROV-O document
    """
    doc = prov.model.ProvDocument()
    doc.set_default_namespace('http://data.scrc.uk')
    cr = doc.activity(
        '/api/code_run/' + str(code_run.id),
        str(code_run.run_date),
        None,
        {
            prov.model.PROV_TYPE: 'run',
            'run_identifier': code_run.run_identifier,
        }
    )
    prov_objects = {}
    prov_object_components = {}
    for input in code_run.inputs.all():
        if input.id in prov_object_components:
            i = prov_object_components[input.id]
        else:
            i = doc.entity('/api/object_component/' + str(input.id), (
                (prov.model.PROV_TYPE, 'file'),
                ('name', input.name)
            ))
            prov_object_components[input.id] = i
        doc.association(cr, i)

        if input.object.id in prov_objects:
            obj = prov_objects[input.object.id]
        else:
            obj = doc.entity('/api/object/' + str(input.object.id), (
                (prov.model.PROV_TYPE, 'file'),
                *_generate_object_meta(input.object)
            ))
        doc.association(i, obj)

    for output in code_run.outputs.all():
        if output.id in prov_object_components:
            o = prov_object_components[output.id]
        else:
            o = doc.entity('/api/object_component/' + str(output.id), (
                (prov.model.PROV_TYPE, 'file'),
                ('name', output.name)
            ))
            prov_object_components[output.id] = o
        doc.association(cr, o)

        if output.object.id in prov_objects:
            obj = prov_objects[output.object.id]
        else:
            obj = doc.entity('/api/object/' + str(output.object.id), (
                (prov.model.PROV_TYPE, 'file'),
                *_generate_object_meta(output.object)
            ))
        doc.association(o, obj)

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