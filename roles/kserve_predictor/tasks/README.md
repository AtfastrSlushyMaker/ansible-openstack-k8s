# tasks/ — Tasks for `kserve_predictor`

`main.yml` typically performs these steps:
- Build a container image (or prepare a ConfigMap) from `files/` artifacts.
- Push the image to a configured registry (if enabled).
- Render the KServe manifest from `templates/kserve_predictor.yaml.j2` and apply it to the cluster.

For private infra, ensure the registry and image pull secrets are configured so cluster nodes can pull the image.
