#!/usr/bin/env python

from distutils.core import setup

setup(name='component-checker',
      version='1.0',
      description='Data Registry Component Checker',
      author='Jonathan Hollocombe',
      author_email='Jonathan.Hollocombe@ukaea.uk',
      url='https://github.com/ScottishCovidResponse/data-registry',
      packages=['check_components.py'],
      requires=['h5py>=2.10.0', 'toml>=0.10.1', 'requests>=2.23.0']
      )
