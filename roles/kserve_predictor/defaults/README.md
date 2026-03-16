# defaults — Default variables for `kserve_predictor`

Contains `main.yml` with role defaults such as:
- `predictor_namespace`
- `predictor_image` and `tag`
- `registry` and `push` settings (used by CI or local builds)

Override these in `vars/cluster.yml` for your environment.
