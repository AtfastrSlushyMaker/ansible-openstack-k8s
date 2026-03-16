tasks/ — Task entrypoints for `heat_k8s_cluster`

- `main.yml` — high-level orchestration (create/update Heat stack, query outputs, render inventory)
- `k8s_install_software.yml` — installs container runtime and kubeadm/kubelet
- `k8s_master_setup.yml` — initializes the master node
- `k8s_worker_setup.yml` — joins worker nodes to the cluster

These task files are included by the top-level playbook `deploy_k8s_cluster.yml`.
