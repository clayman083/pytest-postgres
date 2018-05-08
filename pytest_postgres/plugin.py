import time
import uuid

import docker as docker_client
import psycopg2
import pytest


def pytest_addoption(parser):
    parser.addoption('--pg-image', action='store', default='postgres:latest',
                     help='Specify postgresql image name')
    parser.addoption('--pg-name', action='store', default=None,
                     help='Specify database container name to use.')
    parser.addoption('--pg-reuse', action='store_true',
                     help='Save database container at the end')
    parser.addoption('--pg-network', action='store', default=None,
                     help='Specify docker network for the PostgreSQL container')


@pytest.fixture(scope='session')
def docker():
    return docker_client.from_env()


def check_connection(params):
    delay = 0.01
    for _ in range(20):
        try:
            with psycopg2.connect(**params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT version();')
            break
        except psycopg2.Error:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail('Cannot start postgres server')


def create_container(docker, image, name, ports, network=None):
    container = None

    if name:
        for item in docker.containers.list(all=True):
            if name in item.name:
                container = item
                break

    if not container:
        try:
            docker.images.pull(image)
        except docker_client.errors.APIError:
            pass

        container_params = {'image': image, 'name': name, 'detach': True}

        if network:
            container_params['network'] = network
        else:
            container_params['ports'] = ports

        try:
            container = docker.containers.create(**container_params)
        except docker_client.errors.ImageNotFound:
            pytest.fail('Image `{0}` not found'.format(image))

    return container


@pytest.yield_fixture(scope='session')
def pg_server(docker, request):
    pg_name = request.config.getoption('--pg-name')
    pg_image = request.config.getoption('--pg-image')
    pg_reuse = request.config.getoption('--pg-reuse')
    pg_network = request.config.getoption('--pg-network')

    if not pg_name:
        pg_name = 'db-{}'.format(str(uuid.uuid4()))

    container = create_container(docker, pg_image, pg_name, {'5432/tcp': None},
                                 pg_network)
    container.start()
    container.reload()

    host = '127.0.0.1'
    port = 5432
    if pg_network:
        net = container.attrs['NetworkSettings']['Networks'][pg_network]
        host = net['IPAddress']
    else:
        ports = container.attrs['NetworkSettings']['Ports']
        port = ports['5432/tcp'][0]['HostPort']

    pg_params = {
        'database': 'postgres', 'user': 'postgres', 'password': 'postgres',
        'host': host, 'port': port
    }

    try:
        check_connection(pg_params)
        yield {
            'network': container.attrs['NetworkSettings'],
            'params': pg_params
        }
    finally:
        if not pg_reuse:
            container.kill()
            container.remove()
