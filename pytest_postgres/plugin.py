import logging
import time
import uuid

import docker as docker_client
import psycopg2
import pytest
from docker.errors import APIError, ImageNotFound

log = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption('--pg-image', action='store', default='postgres:latest',
                     help='Specify postgresql image name')
    parser.addoption('--pg-name', action='store', default=None,
                     help='Specify database container name to use.')
    parser.addoption('--pg-reuse', action='store_true',
                     help='Save database container at the end')
    parser.addoption('--pg-network', action='store', default=None,
                     help='Specify docker network for the PostgreSQL container')
    parser.addoption('--pg-host', action='store', default=None,
                     help='Specify PostgreSQL server host')
    parser.addoption('--pg-port', action='store', default=5432,
                     help='Specify PostgreSQL server port')
    parser.addoption('--pg-user', action='store', default='postgres',
                     help='Specify PostgreSQL server user name')
    parser.addoption('--pg-password', action='store', default='postgres',
                     help='Specify PostgreSQL server user password')
    parser.addoption('--pg-database', action='store', default='postgres',
                     help='Specify test database name')


class catch_docker_error:

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Catch and handle docker APIError:
        if exc_type is APIError:
            log.exception(exc_value)
            return True


@pytest.fixture(scope='session')
def docker():
    return docker_client.from_env()


def check_connection(params):
    delay = 0.01
    for _ in range(10):
        try:
            with psycopg2.connect(**params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT version();')
            break
        except psycopg2.Error:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail('Could not connect to PostgreSQL server')


def create_container(docker, image, name, ports, network=None, env_params=None):
    container = None
    env_params = env_params or {}

    if name:
        for item in docker.containers.list(all=True):
            if name in item.name:
                container = item
                break

    if not container:
        with catch_docker_error():
            docker.images.pull(image)

        container_params = {
            'image': image,
            'name': name,
            'detach': True,
            'environment': env_params,
        }

        if network:
            container_params['network'] = network
        else:
            container_params['ports'] = ports

        try:
            container = docker.containers.create(**container_params)
        except ImageNotFound:
            pytest.fail('Image `{0}` not found'.format(image))

    return container


@pytest.yield_fixture(scope='session')
def pg_server(docker, request):
    pg_host = request.config.getoption('--pg-host')
    pg_port = request.config.getoption('--pg-port')
    pg_user = request.config.getoption('--pg-user')
    pg_password = request.config.getoption('--pg-password')
    pg_database = request.config.getoption('--pg-database')

    pg_name = request.config.getoption('--pg-name')
    pg_image = request.config.getoption('--pg-image')
    pg_reuse = request.config.getoption('--pg-reuse')
    pg_network = request.config.getoption('--pg-network')

    network = None
    container = None

    if not pg_host:
        if not pg_name:
            pg_name = 'db-{}'.format(str(uuid.uuid4()))

        env_params = {
            'POSTGRES_USER': pg_user,
            'POSTGRES_DB': pg_database,
            'POSTGRES_PASSWORD': pg_password,
        }

        container = create_container(docker, pg_image, pg_name,
                                     ports={'5432/tcp': None},
                                     network=pg_network,
                                     env_params=env_params)
        container.start()
        container.reload()

        network = container.attrs['NetworkSettings']

        if pg_network:
            net = container.attrs['NetworkSettings']['Networks'][pg_network]
            pg_host = net['IPAddress']
        else:
            ports = container.attrs['NetworkSettings']['Ports']
            pg_host = 'localhost'
            pg_port = ports['5432/tcp'][0]['HostPort']

    pg_params = {
        'host': pg_host,
        'port': pg_port,
        'database': pg_database,
        'user': pg_user,
        'password': pg_password
    }

    try:
        check_connection(pg_params)
        yield {
            'network': network,
            'params': pg_params
        }
    finally:
        if not pg_reuse and container:
            with catch_docker_error():
                container.kill()
            with catch_docker_error():
                container.remove()
