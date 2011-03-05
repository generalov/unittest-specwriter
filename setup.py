#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup


def read(*path):
    return open(os.path.join(os.path.dirname(__file__), *path)).read()

setup(
    name = "unittest-specwriter",
    version = "0.1",
    url = 'https://github.com/generalov/virtualenv-setup',
    license = 'BSD',
    description = "Writes the output in the form of test specifications.",
    long_description = read('README.rst').strip(),
    author = 'Evgeny V. Generalov',
    author_email = 'e.generalov@gmail.org',
    packages = ['specwriter'],
    zip_safe = False,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
