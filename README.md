# Kubernetes Cluster Deployment (OpenStack + Ansible)

Ansible playbooks and roles to provision a Kubernetes cluster on OpenStack using Heat, install a Prometheus/Grafana monitoring stack, and deploy an example KServe predictor. This repository implements Phase 3 of a five-phase integrated university project: automation to create and configure instances on our private OpenStack infrastructure.

Overview

- `roles/heat_k8s_cluster`: renders Heat templates, creates/updates a Heat stack, collects stack outputs, and produces an Ansible inventory used to bootstrap nodes (container runtime, kubeadm/kubelet) and initialize/join the cluster.
- `roles/monitoring`: renders and applies Prometheus/Grafana manifests to the cluster.
- `roles/kserve_predictor`: packages model code, builds/pushes an image (or uses ConfigMaps), and deploys a KServe `InferenceService` manifest.

How Ansible interacts with OpenStack/Heat

- Templates rendered by Ansible are passed to the `openstack.cloud.heat` module (openstack collection) which uses `openstacksdk` to create/update stacks.
- On stack completion, the role queries stack outputs (`openstack.cloud.stack_info`) and converts IPs/hostnames into a dynamic `hosts_k8s.ini` used by later playbooks to SSH into created VMs and run bootstrap tasks.
- Credentials may come from `vars/credentials.yml`, environment variables, or `clouds.yaml` supported by `openstacksdk`.

Project phases (integrated university project)

- Phase 1 — Architecture: concept and design of the overall system and infrastructure.
- Phase 2 — OpenStack infra: create and deploy the private OpenStack infrastructure where resources will run.
- Phase 3 — Automation (this repo): Ansible/Heat automation that provisions and configures VMs and Kubernetes on the private infra.
- Phase 4 — Webapp development: build the application that will run on the provisioned cluster.
- Phase 5 — Deployment: CI/CD and production deployment of the webapp onto the infrastructure created in earlier phases.

Quick start

1. Edit `vars/cluster.yml` to match your images, flavors, network IDs, node counts, and registry settings.
2. Copy `vars/credentials.yml.example` → `vars/credentials.yml` and fill in OpenStack credentials.
3. Run the orchestrator:

```bash
ansible-playbook deploy_k8s_cluster.yml
```

Prerequisites

- Ansible 2.9+ and the `openstack.cloud` collection (or newer Ansible + collections).
- Python `openstacksdk` available to Ansible for OpenStack modules.
- OpenStack account with permissions to create stacks, servers, networks, keypairs.
- `kubectl` locally for verification and for `roles/monitoring` tasks (or ensure a host with `kubectl` has cluster access).

Configuration and variables

- `vars/cluster.yml` — primary cluster configuration (images, flavors, counts, registry, networking).
- `vars/credentials.yml.example` — example credentials; copy to `vars/credentials.yml` for local runs.
- Role defaults live under `roles/*/defaults/main.yml` and can be overridden by `vars/cluster.yml`.

KServe predictor & registry notes

- For private infra, configure a registry reachable from the cluster (Harbor, private registry). Set credentials and image names in `vars/cluster.yml`.
- The `kserve_predictor` role can build and push images; CI pipelines are recommended for reproducible builds.


