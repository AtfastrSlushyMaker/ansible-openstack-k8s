# templates/ — Templates for `kserve_predictor`

Contains Jinja2 manifests used to render the KServe `InferenceService` and related resources. Templates are parameterized using role defaults and `vars/cluster.yml`.

Main template: `kserve_predictor.yaml.j2` — renders the KServe CR and service definitions.
