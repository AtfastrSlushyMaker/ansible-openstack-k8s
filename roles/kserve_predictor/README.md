# kserve_predictor — Deploy KServe predictor

Purpose
- Package model code into a ConfigMap or container image, and deploy a KServe `InferenceService` for model inference testing.

Contents
- `files/` — model and inference code, `Dockerfile`, `requirements.txt`.
- `templates/` — Jinja2 KServe manifests and optional exporter manifests.
- `tasks/` — build/push steps and manifest rendering/apply.
- `defaults/main.yml` — default predictor namespace and image names.

Usage
- Configure a container registry (private or public) and credentials in `vars/cluster.yml`.
- Run the role from the top-level playbook to build/push the image and deploy the KServe CR.

Notes for private infra
- If the cluster cannot pull images from the public internet, use a registry reachable from the cluster (Harbor, internal registry) and ensure nodes have access.

License: MIT
