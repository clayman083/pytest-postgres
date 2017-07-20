from setuptools import setup, find_packages


setup(
    name='pytest-postgres',
    version='0.1.1',
    packages=find_packages(),
    url='https://github.com/clayman74/pytest-postgres',
    licence='MIT',
    author='Kirill Sumorokov',
    author_email='sumorokov.k@gmail.com',
    description='Run PostgreSQL in Docker container in Pytest.',
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Testing",
        "Framework :: Pytest"
    ],

    install_requires=[
        'docker-py >= 1.10.0',
        'psycopg2 >= 2.6',
        'pytest >= 3.0.2',
    ],

    entry_points={
        'pytest11': [
            'postgres = pytest_postgres.plugin'
        ]
    }
)
