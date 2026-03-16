# tasks/ — Tasks for `monitoring`

The `main.yml` task file renders templates and applies them to the cluster using `kubectl` (or another deployment mechanism if configured). Typical steps:
- Render `namespace` and resource manifests
- Apply manifests with `kubectl apply -f` or similar
- Optionally wait for deployments to become ready

Ensure the host running these tasks has `kubectl` and cluster credentials.
