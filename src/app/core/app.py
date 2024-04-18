import contextlib
import logging
import typing

import fastapi
import starlette.config

from app.core.cors import setup_cors
from app.core.error_handlers import setup_error_handlers
from app.core.logging import setup_logging
from app.core.request_context import setup_request_context


@contextlib.asynccontextmanager
async def _lifespan(app: "App"):
    app.logger.info("Starting")
    yield
    app.logger.info("Shutting down")


class App(fastapi.FastAPI):
    def __init__(
        self,
        **extra: typing.Any,
    ) -> None:
        # IMPORTANT all logs previous to calling setup_logging will be not formatted
        setup_logging()

        super().__init__(lifespan=_lifespan, **extra)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = starlette.config.Config()

        # RequestContext is a nice-to-have util that allows to access request related attributes anywhere in the code
        setup_request_context(self)

        # Http error handlers (equivalent to try block that can handle uncaught exceptions)
        setup_error_handlers(self)

        # Setup cors
        setup_cors(self)


def create_app():
    return App()
