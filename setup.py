from setuptools import find_packages, setup


setup(
    name='pytest-postgres',
    version='0.7.0',
    packages=find_packages(),
    url='https://github.com/clayman74/pytest-postgres',
    licence='MIT',
    author='Kirill Sumorokov',
    author_email='sumorokov.k@gmail.com',
    description='Run PostgreSQL in Docker container in Pytest.',

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Testing",
        "Framework :: Pytest"
    ],
    keywords='pytest-postgres',

    install_requires=[
        'docker',
        'psycopg2-binary',
        'pytest',
    ],

    extras_require={
        'develop': [
            'flake8',
            'flake8-bugbear',
            'flake8-builtins-unleashed',
            'flake8-comprehensions',
            'flake8-import-order',
            'flake8-mypy',
            'flake8-pytest'
        ],
        'test': [
            'pytest',
            'coverage',
            'coveralls'
        ]
    },


    entry_points={
        'pytest11': [
            'postgres = pytest_postgres.plugin'
        ]
    }
)
