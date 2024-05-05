# Google Cloud Integration

This page contains information on how to configure the application to use resources on Google Cloud.
Use-cases:

- Install private dependencies published on [Artifact Registry](https://cloud.google.com/artifact-registry).
- Publish docker image on [Artifact Registry](https://cloud.google.com/artifact-registry).
- Deploy to [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine).
- Deploy to [Cloud Run](https://cloud.google.com/run).

## Install Google Cloud CLI

- Install it from the [GCloud Installation](https://cloud.google.com/sdk/docs/install) page.
- Run in terminal:

```shell
gcloud init
```

- You will be asked to sign via Google Sign On.
- Choose your project from the menu.

## Add Google Cloud implementation of keyring to Poetry

1. Run in terminal:

```sh
poetry self add keyrings.google-artifactregistry-auth
```
