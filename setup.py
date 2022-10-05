from setuptools import setup
import os

VERSION = "0.2.1"


test_requirements = ["pytest>=7.0.1", "pytest-dotenv>=0.5.2"]
jupyter_extras = ["ipywidgets==7.6.5"]
dev_requirements = [
    "black>=22.1.0",
    "datasette>=0.60.2",
    "ipykernel>=6.9.1",
    "isort>=5.10.1",
]
dev_requirements.extend(test_requirements)
dev_requirements.extend(jupyter_extras)


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
    install_requires=[
        "httpx==0.23.0",
        "playwright==1.24.1",
        "python-dotenv==0.20.0",
        "pytz==2022.1",
        "rich==12.5.1",
        "typer==0.6.1",
    ],
    extras_require={
        "test": test_requirements,
        "jupyter": jupyter_extras,
        "dev": dev_requirements,
    },
    python_requires=">=3.7",
)
