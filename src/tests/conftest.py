import pytest
import pytest_httpserver
from starlette.testclient import TestClient

from app.app import create_app
from tests.testutils.mock_server import MockServer


@pytest.fixture
def app():
    app = create_app()
    yield app


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://localhost") as client:
        yield client


@pytest.fixture
def mock_server(httpserver: pytest_httpserver.HTTPServer):
    server = MockServer(httpserver)
    yield server
    server.clear()
