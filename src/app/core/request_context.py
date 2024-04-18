import inspect
import logging
import time
import uuid
from contextvars import ContextVar
from functools import update_wrapper
from typing import Optional, List

import fastapi
from starlette.datastructures import MutableHeaders

_ADDITIONAL_HEADERS_CONTEXT_KEY = "_additional_headers"
_SERVER_TIMING_CONTEXT_KEY = "_server_timing_events"
_REQUEST_ID_CONTEXT_KEY = "_request_id"


class _ServerTimingEvent:
    def __init__(
        self,
        name: str,
    ) -> None:
        super().__init__()
        self.name = name
        self._start = None
        self._end = None

    def start(self):
        self._start = time.perf_counter()
        return self

    def stop(self):
        self._end = time.perf_counter()

    def is_terminated(self) -> bool:
        return self._end is not None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

    def __repr__(self) -> str:
        if not self.is_terminated():
            return ""
        dur = self._end - self._start
        return f"{self.name};dur={dur:.6f}"


class RequestContext:
    """
    Exposes underlying Request object anywhere via static method.
    """

    _request_scope_context_storage: ContextVar[dict] = ContextVar(
        "request_context", default={}
    )

    _logger = logging.getLogger(__name__)

    @classmethod
    def bind_app(cls, app: fastapi.FastAPI):
        @app.middleware("http")
        async def init_http_middleware(request: fastapi.Request, call_next):
            _token = cls._request_scope_context_storage.set(cls._init_context(request))
            try:
                response: fastapi.Response = await call_next(request)
                cls._process_response(response)
                return response
            finally:
                cls._request_scope_context_storage.reset(_token)

    @classmethod
    def _init_context(cls, request: fastapi.Request) -> dict:
        # Generate request_id is missing
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        return {_REQUEST_ID_CONTEXT_KEY: request_id}

    @classmethod
    def get(cls) -> dict:
        try:
            return cls._request_scope_context_storage.get()
        except LookupError as e:
            cls._logger.warning(
                f"You are trying to access {cls.__name__} outside of the request-response cycle."
            )
            return {}

    @classmethod
    def get_request_id(cls) -> Optional[str]:
        return cls.get().get(_REQUEST_ID_CONTEXT_KEY)

    @classmethod
    def _get_additional_headers(cls) -> MutableHeaders:
        return cls.get().setdefault(_ADDITIONAL_HEADERS_CONTEXT_KEY, MutableHeaders())

    @classmethod
    def _get_server_timing_events(cls) -> List[_ServerTimingEvent]:
        return cls.get().setdefault(_SERVER_TIMING_CONTEXT_KEY, [])

    @classmethod
    def _add_server_timing_event(cls, event: _ServerTimingEvent) -> None:
        cls._get_server_timing_events().append(event)

    @classmethod
    def _generate_server_timing_header(cls) -> str:
        """
        Computes Server-Timing header on-the-fly based on current server_timing_events.
        """
        server_timing_events: List[_ServerTimingEvent] = cls._get_server_timing_events()
        return (
            ", ".join([str(e) for e in server_timing_events if e.is_terminated()])
            if server_timing_events
            else ""
        )

    @classmethod
    def _process_response(cls, response: fastapi.Response) -> None:
        headers = {
            "server-timing": cls._generate_server_timing_header(),
            "x-request-id": cls.get_request_id(),
        }
        response.headers.update({k: v for k, v in headers.items() if v})
        for k, v in cls._get_additional_headers().items():
            response.headers.append(k, v)

    @classmethod
    def add_header(cls, name: str, value: str) -> None:
        cls._get_additional_headers().append(name, value)

    @classmethod
    def server_timing_event(cls, event_name: Optional[str] = None):
        """
        Context Manager class to time operations.
        @param event_name- the server-timing event name

        Example:
            ```
            with RequestContext.server_timing_context_manager("my-event"):
                # do stuff
            ```
        The code here above will add the entry `my-event;dur={elapsed}` to the Server-Timing response header.
        """
        _event = _ServerTimingEvent(event_name)
        cls._get_server_timing_events().append(_event)
        return _event

    @classmethod
    def server_timing_event_func_decorator(cls, event_name: Optional[str] = None):
        """
        Use to annotate any method to time its execution (it becomes part of server-timing response header).
        @param event_name- the server-timing event name

        Example:
            ```
            @RequestContext.server_timing_func_decorator("my-event"):
            def do_stuff():
                ...
            ```
        The code here above will add the entry `my-event;dur={elapsed}` to the Server-Timing response header.
        """

        def decorator(f):
            name = event_name if event_name else f.__name__

            if inspect.iscoroutinefunction(f):

                async def async_wrapped_function(*args, **kwargs):
                    with cls.server_timing_event(name):
                        return await f(*args, **kwargs)

                return update_wrapper(async_wrapped_function, f)

            else:

                def wrapped_function(*args, **kwargs):
                    with cls.server_timing_event(name):
                        return f(*args, **kwargs)

                return update_wrapper(wrapped_function, f)

        return decorator


def setup_request_context(app: fastapi.FastAPI):
    RequestContext.bind_app(app)
