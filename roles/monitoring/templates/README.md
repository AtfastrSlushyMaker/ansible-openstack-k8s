# templates/ — Templates for `monitoring`

Contains Jinja2 templates that render Kubernetes manifests for Prometheus, Grafana, and exporters. Templates support variable substitution from `vars/cluster.yml` and role defaults.

Key templates
- `prometheus.yaml.j2` — Prometheus server and config
- `grafana.yaml.j2` — Grafana deployment and dashboards
- `exporters.yaml.j2` — node-exporter and kube-state-metrics
- `namespace.yaml.j2` — target namespace manifest
