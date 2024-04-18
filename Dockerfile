#
# See https://fastapi.tiangolo.com/deployment/docker/#docker-image-with-poetry
#
FROM python:3.12-slim as requirements-stage

# Install poetry
RUN pip install "poetry>=1.2.2"

# Use poetry to generate requirements.txt
WORKDIR /tmp
COPY ./pyproject.toml ./poetry.lock* ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12-slim

# define non-root user
ARG USER=app
ARG USERID=1001
ARG GROUP=app
ARG GROUPID=1001
RUN addgroup --gid $GROUPID $GROUP
RUN adduser --uid $USERID --ingroup $GROUP $USER --disabled-password

## Define workdir
ARG WORKDIR=/home/$USER

# Create workdir
RUN mkdir -p $WORKDIR

# Move to workdir
WORKDIR $WORKDIR

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Install in-docker deps
RUN pip install --no-cache-dir uvicorn

# Install deps
COPY --from=requirements-stage /tmp/requirements.txt requirements.txt

# Use PIP_INSTALL_ARGS to pass credentials to the pip install process. This is required of you want to use private libraries.
# Example:
#   docker build --build-arg "PIP_INSTALL_ARGS=--extra-index-url https://oauth2accesstoken:$(gcloud auth print-access-token)@$(gcloud config get compute/region)-python.pkg.dev/$(gcloud config get project)/pylib/simple/" -t app .
# See https://stackoverflow.com/questions/72214875/inject-google-artifact-registry-credentials-to-docker-build
ARG PIP_INSTALL_ARGS
RUN pip install $PIP_INSTALL_ARGS --no-cache-dir -r requirements.txt

# Copy local code to the container image
ADD src/app/ app/

# Switch to non-root user
USER $USER

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
