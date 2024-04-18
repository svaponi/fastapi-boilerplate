import fastapi
from starlette.testclient import TestClient

from app.core.cors import setup_cors
from tests.testutils.mock_environ import mock_environ


def _get_response(origin=None):
    app = fastapi.FastAPI()
    setup_cors(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        return client.get("/", headers={"origin": origin or "http://example.com"})


def test_cors_disabled():
    res = _get_response()
    assert res.headers.get("access-control-allow-origin") is None


def test_cors_enabled():
    with mock_environ(ENABLE_CORS="True"):
        res = _get_response()
        assert res.headers.get("access-control-allow-origin") == "*"


def test_cors_enabled_with_allow_origins():
    with mock_environ(
        ENABLE_CORS="True",
        CORS_ALLOW_ORIGINS="http://localhost:3000,http://localhost:3001",
    ):
        res = _get_response(origin="http://localhost:3000")
        assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
        res = _get_response(origin="http://localhost:3001")
        assert res.headers.get("access-control-allow-origin") == "http://localhost:3001"
        res = _get_response(origin="http://localhost:3002")
        assert res.headers.get("access-control-allow-origin") is None
        res = _get_response(origin="http://localhost:4000")
        assert res.headers.get("access-control-allow-origin") is None


def test_cors_enabled_with_allow_origin_regex():
    with mock_environ(
        ENABLE_CORS="True",
        CORS_ALLOW_ORIGIN_REGEX="http://localhost:300\\d",
    ):
        res = _get_response(origin="http://localhost:3000")
        assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
        res = _get_response(origin="http://localhost:3001")
        assert res.headers.get("access-control-allow-origin") == "http://localhost:3001"
        res = _get_response(origin="http://localhost:3002")
        assert res.headers.get("access-control-allow-origin") == "http://localhost:3002"
        res = _get_response(origin="http://localhost:4000")
        assert res.headers.get("access-control-allow-origin") is None
