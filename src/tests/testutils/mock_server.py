import json
import os
import re
import typing

import pytest_httpserver
import werkzeug


class MockServer:
    def __init__(self, httpserver: pytest_httpserver.HTTPServer, base_dir: str = None):
        super().__init__()
        self.httpserver = httpserver
        self.received_requests: list[werkzeug.Request] = []
        self.base_dir = base_dir or os.path.dirname(__file__)

    @property
    def server_url(self):
        return f"http://{self.httpserver.host}:{self.httpserver.port}"

    def clear(self):
        self.httpserver.clear()
        self.received_requests.clear()

    def respond_with_data(
        self, path_regex: str, response_data: str, status_code: int = 200
    ):
        def handler(request: werkzeug.Request):
            self.received_requests.append(request)
            return werkzeug.Response(response_data, status=status_code)

        pattern = re.compile(path_regex, 0)
        self.httpserver.expect_request(pattern).respond_with_handler(handler)

    def respond_with_json(
        self, path_regex: str, response_json: typing.Any, status_code: int = 200
    ):
        response_data = json.dumps(response_json)
        self.respond_with_data(path_regex, response_data, status_code)

    def respond_with_file(self, path_regex: str, filepath: str, status_code: int = 200):
        with open(filepath) as f:
            response_data = f.read()
        self.respond_with_data(path_regex, response_data, status_code)
