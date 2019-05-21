#!/usr/bin/python3

from setuptools import setup, find_packages
import os

def strip_comments(l):
    return l.split('#', 1)[0].strip()

def reqs(*f):
    return list(filter(None, [strip_comments(l) for l in open(os.path.join(os.getcwd(), *f)).readlines()]))

setup(
    name='setup-LagoGW',
    version='0.0.1',
    author="lagopus project team",
    author_email="lagopus-devel@lists.sourceforge.net",
    license="Apache license 2.0",
    packages=find_packages(),
    install_requires=reqs('requirements.txt'),
    test_suite='nose.collector',
    entry_points={
        "console_scripts":[
            "setup-lagogw = lago_gw.setup_lagogw:main",
        ]
    }
)
