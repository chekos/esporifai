from setuptools import setup
import os

VERSION = "0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="esporifai",
    description="A simple CLI to get data from the Spotify API",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Sergio Sánchez Zavala",
    url="https://github.com/chekos/esporifai",
    project_urls={
        "Issues": "https://github.com/chekos/esporifai/issues",
        "CI": "https://github.com/chekos/esporifai/actions",
        "Changelog": "https://github.com/chekos/esporifai/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["esporifai"],
    entry_points="""
        [console_scripts]
        esporifai=esporifai.cli:cli
    """,
    install_requires=["click"],
    extras_require={
        "test": ["pytest"]
    },
    python_requires=">=3.7",
)
