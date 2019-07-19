"""Setup file."""
from setuptools import setup

setup(
    name='psizcollect',
    version='0.1.0',
    description='Toolbox for collecting similarity judgments.',
    long_description='See README associated with repository.',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    author='Brett D. Roads',
    author_email='brett.roads@gmail.com',
    license='Apache Licence 2.0',
    packages=['psizcollect'],
    install_requires=[
        'numpy', 'pandas', 'mysql-connector-python'
    ],
    include_package_data=True,
)
