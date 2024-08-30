import fastapi
from starlette.testclient import TestClient

from app.core.request_context import setup_request_context, RequestContext


def test_request_context():
    app = fastapi.FastAPI()
    setup_request_context(app)

    @app.get("/ok")
    @RequestContext.server_timing_event_func_decorator("total")
    def ok():
        RequestContext.add_header("x-test", "foobar")
        return dict(message="ok")

    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/ok", headers={"x-request-id": "001"})
        print(
            f"{res.request.method} {res.url} >> {res.status_code} {res.text} {res.headers}"
        )
        assert res.status_code == 200
        assert res.headers.get("x-request-id") == "001"
        assert res.headers.get("x-test") == "foobar"
        assert res.headers.get("server-timing") is not None
