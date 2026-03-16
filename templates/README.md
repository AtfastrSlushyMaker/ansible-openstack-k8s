templates/ — Jinja2 templates used by playbooks and roles

This folder contains project-level templates used to render configuration and Kubernetes manifests. Examples:

- `hosts_k8s.ini.j2` — inventory template for generated k8s hosts
- `nginx-nodeport.yaml.j2` — optional demo app manifest

Templates are rendered by `ansible.builtin.template` tasks and written to `/tmp/` or host locations during runs.
