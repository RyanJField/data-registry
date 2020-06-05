import prov.model
import prov.serializers
import prov.dot
import io
import json


def generate_prov_document(model_run):
    doc = prov.model.ProvDocument()
    doc.set_default_namespace('http://data.scrc.uk')
    mo = doc.entity('/api/model_output/' + str(model_run.id), (
        (prov.model.PROV_TYPE, 'file'),
        ('path', model_run.url),
        ('description', model_run.short_desc),
    ))
    for i, run in enumerate(model_run.model_runs.all()):
        r = doc.activity(
            '/api/model_run/' + str(run.id),
            str(run.run_date),
            None,
            {prov.model.PROV_TYPE: 'run'}
        )
        doc.generation(mo, r, None)
        model_version = run.model_version
        mv = doc.entity('/api/model_version/' + str(model_version.id), (
            (prov.model.PROV_TYPE, 'model'),
        ))
        doc.association(r, mv)
        model = model_version.model
        m = doc.entity('/api/model/' + str(model.id), (
            (prov.model.PROV_TYPE, 'model'),
        ))
        doc.revision(mv, m, identifier=model_version.version_identifier)
        for model_input_version in run.model_input_versions.all():
            miv = doc.entity('/api/model_input_version/' + str(model_input_version.id), (

            ))
            model_input = model_input_version.model_input
            mi = doc.entity('/api/model_input/' + str(model_input.id))
            doc.revision(miv, mi, identifier=model_input_version.version_identifier)
            doc.association(r, miv)

    return doc


def serialize_prov_document(doc, format):
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