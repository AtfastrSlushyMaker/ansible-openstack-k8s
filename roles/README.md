# roles/ — Ansible roles directory

This directory contains the project's Ansible roles. Each role encapsulates a unit of functionality with its own:

- `defaults/` — default configuration values
- `tasks/` — main task entrypoints and step files
- `templates/` — Jinja2 templates rendered by the role
- `files/` — static files copied to targets
- `handlers/` — idempotent follow-up actions triggered by `notify`
- `meta/` — role metadata and dependencies
- `tests/` — simple example inventory/playbook for local validation

Roles in this repository

- `heat_k8s_cluster` — provision OpenStack resources and bootstrap Kubernetes.
- `monitoring` — render and apply Prometheus/Grafana manifests.
- `kserve_predictor` — package and deploy an example KServe inference service.

Usage

- Roles are invoked by the top-level `deploy_k8s_cluster.yml` playbook or can be tested individually using playbooks in each role's `tests/` directory.

License: MIT
