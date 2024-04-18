import os

import fastapi
from starlette.middleware.cors import CORSMiddleware

from app.utils.getenv import getenv_bool


def setup_cors(app: fastapi.FastAPI):
    if getenv_bool("ENABLE_CORS", default=False):
        allow_origins = os.getenv("CORS_ALLOW_ORIGINS", default="*").split(",")
        allow_origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", default=None)
        if allow_origin_regex:
            allow_origins = []
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_origin_regex=allow_origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
