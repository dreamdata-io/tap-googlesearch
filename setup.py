#!/usr/bin/env python

from setuptools import setup

setup(
    name="tap-googlesearch",
    version="0.0.1",
    description="Singer.io tap for extracting data AgileCMS",
    author="Dreamdata",
    url="https://dreamdata.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    install_requires=[
        "singer-python==5.8.1",
        "google-api-python-client",
        "ratelimit",
        "backoff",
    ],
    entry_points="""
        [console_scripts]
        tap-googlesearch=tap_googlesearch:main
    """,
    include_package_data=True,
    package_data={"tap_googlesearch": ["schemas/*.json"]},
    packages=["tap_googlesearch"],
    setup_requires=["pytest-runner"],
    extras_require={"test": [["pytest"]]},
)
