# IOT Infrastructure Setup

## Provision node with Terraform

1. Export OpenStack password environment variable

    ```bash
    export TF_VAR_openstack_password="change-me"
    ```

1. Initialize terraform project

    ```bash
    terraform init
    ```

1. Deploy infrastructure

    ```bash
    terraform apply -auto-approve
    ```

## Configure node with Ansible

1. Make sure all nodes are reachable

    ```bash
    ansible all -m ping
    ```

1. Deploy basic setup on all nodes

    ```bash
    ansible-playbook pb-setup.yaml
    ```
