import os
import h5py
import toml
import argparse
import requests
import html
import hashlib

API_ROOT = 'https://data.scrc.uk/api/'
DATA_PRODUCT_URL = 'data_product/'
NAMESPACE_URL = 'namespace/'
STORAGE_LOCATION_URL = 'storage_location/'
OBJECT_URL = 'object/'


def is_leaf(node):
    for (_, child) in node.items():
        if isinstance(child, h5py.Group):
            return False
    return True


def find_leaf_nodes(name, node, names):
    if isinstance(node, h5py.Group) and is_leaf(node):
        names.append(name)


def process_hdf5(file):
    h5file = h5py.File(file, 'r')
    names = []
    h5file.visititems(lambda name, node: find_leaf_nodes(name, node, names))
    return names


def process_toml(file):
    data = toml.load(file)
    return list(data.keys())


def process(file):
    _, ext = os.path.splitext(file)
    if ext == '.h5':
        names = process_hdf5(file)
    elif ext in ('.txt', '.toml'):
        names = process_toml(file)
    else:
        raise ValueError('Unknown file type')
    return names


def url_to_id(url):
    return int(url.split('/')[-2])


def read_api(url, error_message):
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(r.content)

    data = r.json()

    if not data:
        raise Exception(error_message)

    if 'count' in data:
        if data['count'] == 0:
            raise Exception(error_message)
        return data['results'][0]

    return data


def get_component_names(component_urls):
    names = []
    for url in component_urls:
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(r.content)
        result = r.json()
        names.append(result['name'])
    return names


def find_object_by_file_hash(file_hash, opts):
    url = API_ROOT + STORAGE_LOCATION_URL + '?format=json&hash=%s' % html.escape(file_hash)

    result = read_api(url, 'Could not find storage location with file hash matching %s' % opts.file)
    storage_location_id = url_to_id(result['url'])

    url = API_ROOT + OBJECT_URL + '?format=json&storage_location=%d' % storage_location_id

    return read_api(url, 'Could not find object with storage_location %d' % storage_location_id)


def find_object_by_data_product(opts):
    url = API_ROOT + DATA_PRODUCT_URL + '?format=json&name=%s' % html.escape(opts.data_product)
    if opts.namespace:
        namespace_id = find_namespace_id(opts)
        url += '&namespace=%d' % namespace_id

    data_product = read_api(url, 'Could not find data product %s' % opts.data_product)
    object_url = data_product['object']

    return read_api(object_url, 'Failed to read object_url %s' % object_url)


def find_namespace_id(opts):
    url = API_ROOT + NAMESPACE_URL + '?format=json&name=%s' % html.escape(opts.namespace)
    namespace = read_api(url, 'Could not find namespace %s' % opts.namespace)
    return url_to_id(namespace['url'])


def check_file(opts):
    components = process(opts.file)

    if opts.data_product:
        object_data = find_object_by_data_product(opts)
    else:
        with open(opts.file, 'rb') as f:
            bytes = f.read()
        file_hash = hashlib.sha1(bytes)
        object_data = find_object_by_file_hash(file_hash.hexdigest(), opts)

    component_urls = object_data['components']
    names = get_component_names(component_urls)

    if opts.verbose:
        print('File components:')
        for c in components:
            print('> %s' % c)
        print()

    errors = []
    for c in components:
        if c not in names:
            errors.append('File component %s not found in registry' % c)
    for n in names:
        if n not in components:
            errors.append('Registry component %s not found in file' % n)

    if not errors:
        print('All components match those in database')
    else:
        print('Errors found:')
        for e in errors:
            print('> %s ' % e)


def get_status(opts):
    object_data = find_object_by_data_product(opts)

    storage_location_url = object_data['storage_location']
    storage_location_data = read_api(storage_location_url, 'failed to read storage_location %s' % storage_location_url)

    print('Data registry storage location hash:')
    print('> %s' % storage_location_data['hash'])
    print()

    component_urls = object_data['components']
    names = get_component_names(component_urls)
    print('Data registry components:')
    for n in names:
        print('> %s' % n)


def main(args=None):
    if args is None:
        import sys
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')

    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    check_parser = subparsers.add_parser('check', help='check file contains against registry')
    check_parser.add_argument('-d', '--data_product', type=str, help='Registry data product to look up')
    check_parser.add_argument('-n', '--namespace', type=str, help='Namespace of data product')
    check_parser.add_argument('file', type=str, help='File to process')

    status_parser = subparsers.add_parser('status', help='print data registry entry for data product')
    status_parser.add_argument('-n', '--namespace', type=str, help='Namespace of data product')
    status_parser.add_argument('data_product', type=str, help='Registry data product to look up')

    opts = parser.parse_args(args)

    if opts.subcommand == 'check':
        check_file(opts)
    elif opts.subcommand == 'status':
        get_status(opts)
    else:
        print('unknown command %s' % opts.subcommand)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
