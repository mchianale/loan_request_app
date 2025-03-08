# setup.py
from setuptools import setup

setup(
    name='kafkaClient',
    version='0.1',
    py_modules=["kafkaClient"],
    install_requires=[
        'confluent_kafka',
        'python-dotenv',
        'pydantic'
    ],
    include_package_data=True,
)