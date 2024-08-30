import inspect
import logging
import time
import uuid
from contextvars import ContextVar
from functools import update_wrapper
from typing import Optional, List

import fastapi
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_ADDITIONAL_HEADERS_CONTEXT_KEY = "_additional_headers"
_SERVER_TIMING_CONTEXT_KEY = "_server_timing_events"
_SERVER_TIMING_HEADER = "server-timing"
_REQUEST_ID_CONTEXT_KEY = "_request_id"
_REQUEST_ID_HEADER = "x-request-id"


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
    def get(cls) -> dict:
        try:
            return cls._request_scope_context_storage.get()
        except LookupError as e:
            cls._logger.warning(
                f"You are trying to access {cls.__name__} outside of the request-response cycle."
            )
            return {}

    @classmethod
    def init_request_context(cls, /, *, request_id: str) -> None:
        cls._request_scope_context_storage.set({_REQUEST_ID_CONTEXT_KEY: request_id})

    @classmethod
    def get_request_id(cls) -> Optional[str]:
        return cls.get().get(_REQUEST_ID_CONTEXT_KEY)

    @classmethod
    def _additional_headers(cls) -> MutableHeaders:
        return cls.get().setdefault(_ADDITIONAL_HEADERS_CONTEXT_KEY, MutableHeaders())

    @classmethod
    def _server_timing_events(cls) -> List[_ServerTimingEvent]:
        return cls.get().setdefault(_SERVER_TIMING_CONTEXT_KEY, [])

    @classmethod
    def _get_server_timing_header(cls) -> str:
        """
        Computes Server-Timing header on-the-fly based on current server_timing_events.
        """
        server_timing_events: List[_ServerTimingEvent] = cls._server_timing_events()
        return (
            ", ".join([str(e) for e in server_timing_events if e.is_terminated()])
            if server_timing_events
            else ""
        )

    @classmethod
    def get_response_headers(cls) -> MutableHeaders:
        headers = cls._additional_headers()
        headers.append(_SERVER_TIMING_HEADER, cls._get_server_timing_header())
        headers.append(_REQUEST_ID_HEADER, cls.get_request_id())
        return headers

    @classmethod
    def add_header(cls, name: str, value: str) -> None:
        cls._additional_headers().append(name, value)

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
        cls._server_timing_events().append(_event)
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


class RequestContextMiddleware:
    def __init__(
        self,
        app: "ASGIApp",
    ) -> None:
        self.app = app

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Generate request_id is missing
        headers = MutableHeaders(scope=scope)
        request_id = headers.get(_REQUEST_ID_HEADER)

        if not request_id:
            request_id = uuid.uuid4().hex
            headers[_REQUEST_ID_HEADER] = request_id

        RequestContext.init_request_context(request_id=request_id)

        async def handle_outgoing_request(message: "Message") -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).update(RequestContext.get_response_headers())
            await send(message)

        await self.app(scope, receive, handle_outgoing_request)
        return


def setup_request_context(app: fastapi.FastAPI):
    app.add_middleware(RequestContextMiddleware)
