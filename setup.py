#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

setup(
    name='webhook_logger',
    version='0.1.0',
    description="A Python logger to send information to Webhooks",
    long_description=readme + '\n\n' + history,
    author="Founders4Schools",
    author_email='dev@founders4schools.org.uk',
    url='https://github.com/founders4schools/webhook_logger',
    packages=[
        'webhook_logger',
    ],
    package_dir={'webhook_logger':
                 'webhook_logger'},
    include_package_data=True,
    install_requires=[],
    license="MIT license",
    zip_safe=False,
    keywords='webhook_logger',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=[]
)
