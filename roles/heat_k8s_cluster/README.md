# heat_k8s_cluster — Provision OpenStack VMs and prepare Kubernetes

Purpose

- Provision a Kubernetes cluster on OpenStack using Heat templates and Ansible.
- Produce an Ansible inventory from Heat outputs, bootstrap control-plane and workers, and install required node software.

What it contains

- `templates/` — Jinja2 Heat templates and Kubernetes YAML fragments.
- `tasks/` — orchestration tasks: create/update Heat stack, render inventory, install OS packages and Kubernetes components, init/join cluster.
- `defaults/main.yml` — sensible defaults (images, flavors, counts, keypair names).
- `vars/` — optional role-specific overrides used by the role.
- `files/` — auxiliary scripts or static artifacts copied to hosts.
- `handlers/` — follow-up handlers triggered by tasks.
- `tests/` — small test inventory/playbook for role-level testing.

How Ansible talks to Heat (brief)

- This role uses the `openstack.cloud` collection to interact with Heat/OpenStack via the OpenStack SDK.
- Flow: render Heat Jinja2 templates -> use `openstack.cloud.heat` to create/update a stack -> wait for stack completion -> call `openstack.cloud.stack_info` to collect outputs -> translate outputs into a dynamic inventory file (e.g., `hosts_k8s.ini`) used by subsequent Ansible plays.
- Authentication is provided via `vars/credentials.yml`, environment variables or `clouds.yml` used by `openstacksdk`.

Typical tasks

- Create keypair and security group rules
- Render and deploy Heat stack
- Fetch stack outputs and render inventories
- Install container runtime, kubelet, kubeadm
- Initialize control-plane and join workers

Prerequisites & notes

- Requires OpenStack credentials with permission to create stacks, servers, keypairs, and networks.
- Designed for private/university infrastructure: adjust network, flavor, and image variables in `vars/cluster.yml`.
- Keep `vars/credentials.yml` out of version control.

Testing

- Use files under `tests/` to run the role locally or in CI against a test environment.

License: MIT
