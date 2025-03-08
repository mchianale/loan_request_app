# setup.py
from setuptools import setup

setup(
    name='loanObjects',
    version='0.1',
    py_modules=["loanObjects"],
    install_requires=[
        'pydantic',
        'pydantic[email]'
    ],
    include_package_data=True,
)