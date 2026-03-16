## monitoring — Deploy Prometheus + Grafana + exporters

## Purpose

Renders and applies Kubernetes manifests to install Prometheus, Grafana, node-exporter and kube-state-metrics into the cluster.

## Files

- `templates/` contains `prometheus.yaml.j2`, `exporters.yaml.j2`, `namespace.yaml.j2` and Grafana dashboards templates.
- `tasks/main.yml` drives rendering and `kubectl apply` steps.

## Usage

Invoked from the top-level playbook during the monitoring deployment phase.

## Variables

See `defaults/main.yml` for role defaults and `vars/cluster.yml` for cluster-wide settings.

License: MIT
