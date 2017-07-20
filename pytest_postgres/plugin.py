import socket
import time
import uuid

import psycopg2
import pytest
from docker import Client as DockerClient


def pytest_addoption(parser):
    parser.addoption('--pg-image', action='store', default='postgres:latest',
                     help='Specify postgresql image name')
    parser.addoption('--pg-name', action='store', default=None,
                     help='Specify database container name to use.')
    parser.addoption('--pg-reuse', action='store_true',
                     help='Save database container at the end')


@pytest.fixture(scope='session')
def unused_port_factory():
    def f():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
    return f


@pytest.fixture(scope='session')
def docker():
    return DockerClient()


@pytest.yield_fixture(scope='session')
def pg_server(unused_port_factory, docker: DockerClient, request):
    pg_name = request.config.getoption('--pg-name')
    pg_image = request.config.getoption('--pg-image')
    pg_reuse = request.config.getoption('--pg-reuse')

    container = None
    port = None
    if not pg_name:
        pg_name = 'db-{}'.format(str(uuid.uuid4()))

    if pg_name:
        for item in docker.containers(all=True):
            for name in item['Names']:
                if pg_name in name:
                    container = item
                    break

    if not container:
        port = unused_port_factory()
        docker.pull(pg_image)
        container = docker.create_container(
            image=pg_image,
            name=pg_name,
            ports=[5432],
            host_config=docker.create_host_config(port_bindings={
                5432: port
            }),
            detach=True
        )

    docker.start(container=container['Id'])

    inspection = docker.inspect_container(container['Id'])
    host = inspection['NetworkSettings']['IPAddress']

    if not port:
        ports = inspection['NetworkSettings']['Ports']
        if '5432/tcp' in ports:
            port = ports['5432/tcp'][0]['HostPort']

    pg_params = {'database': 'postgres', 'user': 'postgres',
                 'password': 'postgres', 'host': 'localhost', 'port': port}

    delay = 0.001
    for i in range(100):
        try:
            with psycopg2.connect(**pg_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT version();')
            break
        except psycopg2.Error:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail('Cannot start postgres server')

    container['host'] = host
    container['port'] = port
    container['pg_params'] = pg_params

    yield container

    if not pg_reuse:
        docker.kill(container=container['Id'])
        docker.remove_container(container['Id'])
