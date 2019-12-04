#!/usr/bin/env python
import os
from setuptools import setup


version = os.environ.get("PACKAGE_VERSION") or os.environ.get("CIRCLE_TAG")
url = "https://github.com/dreamdata-io/tap-googlesearch"


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tap-googlesearch",
    version=version,
    description="Singer.io tap for extracting data from Google Search Analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dreamdata.io",
    author_email="friends@dreamdata.io",
    url=url,
    download_url=f"{url}/archive/v{version}.tar.gz",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    license="MIT",
    install_requires=[
        "singer-python>=5.8.1, <6",
        "google-api-python-client==1.7.11",
        "ratelimit==2.2.1",
        "backoff>=1.8.0, <2",
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
