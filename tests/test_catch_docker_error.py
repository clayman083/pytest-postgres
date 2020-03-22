from unittest.mock import patch

import pytest
from docker.errors import APIError
from pytest_postgres.plugin import catch_docker_error


@patch('pytest_postgres.plugin.log')
def test_catch_docker_error_doesnt_mask_other_errors(fake_log):
    err = ValueError('not a docker API error!')
    with pytest.raises(ValueError):
        with catch_docker_error():
            raise err
    fake_log.exception.assert_not_called()


@patch('pytest_postgres.plugin.log')
def test_catch_docker_error(fake_log):
    err = APIError('oh no!')
    with catch_docker_error():
        raise err
    fake_log.exception.assert_called_with(err)
