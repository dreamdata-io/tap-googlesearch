#!/usr/bin/env python
import os
from setuptools import setup


version = os.environ.get("CIRCLE_TAG") or "0.0.1-dev"
url = "https://github.com/dreamdata-io/tap-googlesearch"

setup(
    name="tap-googlesearch",
    version=version,
    description="Singer.io tap for extracting data from Google Search Analytics",
    author="Dreamdata",
    url=url,
    download_url=f"{url}/archive/v{version}.tar.gz",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    license="MIT",
    install_requires=[
        "singer-python>=5.8.1, <6",
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
