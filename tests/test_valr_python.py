import pytest
import requests_mock

from valr_python import Client
from valr_python.base_client import _sign_request  # noqa
from valr_python.error import APIError
from valr_python.error import RequiresAuthentication


@pytest.fixture
def mock_client():
    c = Client()
    c.base_url = 'mock://test/'
    return c


def test_client(mock_client):
    mock_client.api_secret = 'api_secret'
    mock_client.api_key = 'api_key'
    mock_client.base_url = 'base_url'
    mock_client.timeout = 10

    assert mock_client.api_key == 'api_key'
    assert mock_client.api_secret == 'api_secret'
    assert mock_client.base_url == 'base_url'
    assert mock_client.timeout == 10


def test_client_do_authentication(mock_client):

    adapter = requests_mock.Adapter()
    mock_client._session.mount('mock', adapter)
    adapter.register_uri('GET', 'mock://test/', text='{}', status_code=200)

    with pytest.raises(RequiresAuthentication):
        mock_client._do('GET', 'mock://test/', is_authenticated=True)

    # no exceptions, because no error present
    mock_client._do('GET', '/')

    mock_client.api_secret = 'api_secret'
    mock_client.api_key = 'api_key'
    mock_client._do('GET', '/', is_authenticated=True)


def test_client_authentication_error(mock_client):

    with pytest.raises(RequiresAuthentication):
        mock_client.get_balances()


def test_client_do_basic(mock_client):
    adapter = requests_mock.Adapter()
    mock_client._session.mount('mock', adapter)

    adapter.register_uri('GET', 'mock://test/', text='ok')
    with pytest.raises(Exception):
        res = mock_client._do('GET', '/')

    adapter.register_uri('GET', 'mock://test/', text='{"key":"value"}')
    res = mock_client._do('GET', '/')
    assert res['key'] == 'value'

    adapter.register_uri('GET', 'mock://test/', text='{}', status_code=400)
    res = mock_client._do('GET', '/')  # no exception, because no error present

    adapter.register_uri('GET', 'mock://test/',
                         text='{"error_code":"code","error":"message"}',
                         status_code=400)
    with pytest.raises(APIError) as e:
        res = mock_client._do('GET', '/')
    assert e.value.code == 'code'
    assert e.value.message == 'message'


def test_request_signature_basic():
    api_secret = 'superdupersecret'
    timestamp = 1577572690093
    method = 'GET'
    path = '/v1/account/balances'
    body = ''
    signature = _sign_request(api_secret=api_secret, timestamp=timestamp, method=method, path=path, body=body)
    assert signature == '647d276537b952fe37f349422a4a60a76ecc2e3fad509a523b03dccd1a940525f8ff06314ad1adc5625000223c514637cd9682ee89ffc285b7493e7c64e746aa'  # noqa
