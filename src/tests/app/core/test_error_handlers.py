import fastapi
from starlette.testclient import TestClient

from app.core.error_handlers import setup_error_handlers


def test_error_handlers():
    app = fastapi.FastAPI()
    setup_error_handlers(app)

    @app.get("/ok")
    def ok():
        return dict(message="ok")

    @app.get("/value_error")
    def value_error():
        raise ValueError("Missing value")

    @app.get("/runtime_error")
    def runtime_error():
        raise RuntimeError("Oops...")

    @app.get("/too_many_requests")
    def too_many_requests():
        raise fastapi.HTTPException(429, "Too much")

    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/ok")
        print(f"{res.request.method} {res.url} >> {res.status_code} {res.text}")
        assert res.status_code == 200
        assert res.json().get("message") == "ok"

        res = client.get("/value_error")
        print(f"{res.request.method} {res.url} >> {res.status_code} {res.text}")
        assert res.status_code == 400
        assert res.json().get("message") == "Missing value"

        res = client.get("/runtime_error")
        print(f"{res.request.method} {res.url} >> {res.status_code} {res.text}")
        assert res.status_code == 500
        assert res.json().get("message") == "Internal server error"

        res = client.get("/too_many_requests")
        print(f"{res.request.method} {res.url} >> {res.status_code} {res.text}")
        assert res.status_code == 429
        assert res.json().get("message") == "Too much"
