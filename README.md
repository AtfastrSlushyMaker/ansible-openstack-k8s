# Kubernetes Cluster Deployment (OpenStack + Ansible)

This repository automates provisioning a small Kubernetes cluster on OpenStack, installing a monitoring stack, and deploying a simple KServe-based model predictor using Ansible and Heat.

**What this repo does**
- Provision infrastructure in OpenStack via Heat templates (`roles/heat_k8s_cluster`).
- Bootstrap Kubernetes control-plane and worker nodes, install required software (container runtime, kubeadm, kubelet).
- Deploy Prometheus + Grafana monitoring and exporters (`roles/monitoring`).
- Build and deploy an example KServe predictor for model inference (`roles/kserve_predictor`).

**Quick start**
1. Inspect and customize `vars/cluster.yml` for flavors, images, and counts.
2. Provide OpenStack credentials in `vars/credentials.yml` (kept local, not committed).
3. Run the orchestrator:

```bash
ansible-playbook deploy_k8s_cluster.yml
```

**Prerequisites**
- Ansible 2.9+ (or later) with required collections.
- Access to an OpenStack project and API credentials.
- `kubectl` available locally for verification.

**Repository layout (high level)**
- `deploy_k8s_cluster.yml` — top-level orchestration playbook.
- `roles/heat_k8s_cluster` — OpenStack + Kubernetes provisioning role.
- `roles/monitoring` — renders/applies Prometheus/Grafana manifests.
- `roles/kserve_predictor` — packages/pushes predictor image and deploys a KServe CR.
- `vars/` — cluster and credentials configuration.
- `templates/` — shared Jinja2 templates used across roles.

