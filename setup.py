"""
Setup file for tool to retrieve a real random address that geocode successfully
"""
from setuptools import setup


with open("README.md", 'r') as fh:
    long_description = fh.read()

setup(
    name='random-address',
    version='1.2.0',
    description='Tool to retrieve a real random address '
                'that geocode successfully',
    packages=['random_address'],
    package_data={'random_address': ['addresses-us-all.json']},
    include_package_data=True,
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    extras_require={
        "dev": [
            "pytest>=3.7",
        ],
    },
    url='https://github.com/neosergio/random-address',
    author='Sergio Infante',
    author_email='raulsergio9@gmail.com',
    project_urls={
        'Issue Tracker': 'https://github.com/neosergio/random-address/issues',
        'Source Code': 'https://github.com/neosergio/random-address',
        'Changelog': 'https://github.com/neosergio/random-address/blob/main/CHANGELOG.md',
    }
)
