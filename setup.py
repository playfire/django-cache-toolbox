#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-cache-toolbox',
    description="Non-magical object caching for Django.",
    version='0.1',
    url='http://code.playfire.com/django-cache-toolbox',

    author='Playfire.com',
    author_email='tech@playfire.com',
    license='BSD',

    packages=find_packages(),
)
