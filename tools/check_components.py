import os
import h5py
import toml
import argparse
import requests
import html

API_ROOT = 'https://data.scrc.uk/api/'
DATA_PRODUCT_URL = 'data_product/'


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


def main(args=None):
    if args is None:
        import sys
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('data_product', type=str, help='Registry data product to look up')
    parser.add_argument('file', type=str, help='File to process')

    opts = parser.parse_args(args)
    components = process(opts.file)

    r = requests.get(API_ROOT + DATA_PRODUCT_URL + '?format=json&name=%s' % html.escape(opts.data_product))
    if r.status_code != 200:
        raise Exception(r.content)

    result = r.json()
    if not result:
        raise Exception('Could not find data product ' % opts.data_product)

    data_product = result[0]
    object_url = data_product['object']

    r = requests.get(object_url)
    if r.status_code != 200:
        raise Exception(r.content)

    result = r.json()
    component_urls = result['components']

    names = []

    for url in component_urls:
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(r.content)
        result = r.json()
        names.append(result['name'])

    success = True

    for c in components:
        if c not in names:
            print('File component %s not found in registry' % c)
            success = False

    for n in names:
        if n not in components:
            print('Registry component %s not found in file' % n)
            success = False

    if success:
        print('All components match those in database')


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
