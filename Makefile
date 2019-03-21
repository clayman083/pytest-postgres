.PHONY: clean clean-test clean-pyc clean-build docs

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint: ## check style with flake8
	flake8 pytest_postgres tests

test: ## run tests quickly with the default Python
	py.test

test-all: ## run tests on every Python version with tox
	tox -- --pg-image=postgres:alpine tests

coverage: ## check code coverage quickly with the default Python
	coverage run --source pytest_postgres -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

release: dist ## package and upload a release
	twine upload dist/*

install: clean ## install the package to the active Python's site-packages
	python setup.py install
