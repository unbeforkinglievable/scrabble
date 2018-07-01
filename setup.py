#!/usr/bin/env python
'''
    wordbiz_scrabble setup config
'''
from os import path
from subprocess import check_output, CalledProcessError
from setuptools import setup
import version

setup(
    name='wordbiz_scrabble',
    version=version.__version__,
    packages=['wordbiz_scrabble'],
    install_requires=[],
    author='Kenny Donahue',
    maintainer='Kenny Donahue',
    description='Wordbiz Scrabble client',
    include_package_data=True
)
