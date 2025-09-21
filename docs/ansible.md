## Konfiguration einer Node mit Ansible

Nachdem die virtuelle Maschine im OpenStack Cluster bereitgestellt wurde, wird sie mit Ansible automatisch konfiguriert. Ansible setzt – analog zu Terraform – auf einen Infrastructure-as-Code (IaC) Ansatz: Der gewünschte Zielzustand der Node wird deklarativ beschrieben und idempotent angewendet. Dadurch lassen sich Konfigurationen reproduzierbar, sicher und schnell ausrollen.

Das Ansible Setup gliedert sich in drei Teile:
1. Basis-Konfiguration von Ansible (Inventory, ansible.cfg)
2. Playbooks und Rollen für System-Setup (Updates, Docker, Shell, Benutzer)
3. Playbook zum Ausrollen der Projektartefakte (docker-compose, Volumes, Berechtigungen)

```YAML
# ansible.cfg (Auszug)
[defaults]
inventory = inventory.yaml

[privilege_escalation]
become=true

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=10

# inventory.yaml (Auszug)
all:
  vars:
    ansible_python_interpreter: auto_silent
    ansible_ssh_private_key_file: ~/.ssh/id_cas
    ansible_user: ubuntu
  hosts:
    iot-node:
      ansible_host: 141.72.13.185
```

Die `ansible.cfg` verweist auf das YAML-Inventar, aktiviert `become` (sudo) und optimiert SSH-Verbindungen. Im Inventory werden Benutzer, Schlüsseldatei und Ziel-Host hinterlegt. Damit kann ohne zusätzliche Parameter gearbeitet werden (z. B. `ansible all -m ping`).

```YAML
# pb-setup.yaml (Auszug)
---
- hosts: all
  name: Install updates and required packages
  vars:
    ubuntu_packages:
      - curl
      - wget
      - zsh
      - nano
      - python3
      - python3-pip
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-compose-plugin
  roles:
    - update

- hosts: all
  name: Install Oh-My-Zsh
  roles:
    - { role: oh-my-zsh-install, user: "{{ ansible_facts['env']['SUDO_USER'] | default('root') }}" }
    - { role: oh-my-zsh-install, user: root }

- hosts: all
  name: Deploy users
  tasks:
    - name: Ensure sudo group has passwordless access
      ansible.builtin.lineinfile:
        path: /etc/sudoers.d/sudo-group-nopasswd
        line: "%sudo ALL=(ALL) NOPASSWD: ALL"
        create: yes
        mode: '0440'
        validate: 'visudo -cf %s'

    - name: Import users and create accounts incl. SSH keys
      include_tasks: tasks/add_user.yaml
      loop:
        - "{'NAME':'alex_dixon',        'SHELL':'/bin/zsh', 'GROUPS':'sudo'}"
        - "{'NAME':'dario_nieddu',      'SHELL':'/bin/zsh', 'GROUPS':'sudo'}"
        - "{'NAME':'dominik_seus',      'SHELL':'/bin/zsh', 'GROUPS':'sudo'}"
        - "{'NAME':'florian_dieterich', 'SHELL':'/bin/zsh', 'GROUPS':'sudo'}"
      loop_control:
        loop_var: USERMGMT_USER
```

- Die Rolle `update` übernimmt System-Updates, fügt den Docker APT-Repo/GPG-Key hinzu und installiert die benötigten Pakete (Docker Engine + Compose Plugin u. a.).
- Die Rolle `oh-my-zsh-install` installiert Oh-My-Zsh für Root und den aktiven Benutzer und setzt sinnvolle ZSH Defaults.
- Die Benutzer werden anhand vorbereiteter SSH-Public-Keys (`ansible/files/ssh_keys/*.pub`) angelegt, erhalten passwordless sudo und individuelle Shells. Das Task-File `tasks/add_user.yaml` setzt außerdem ein initiales Zufallspasswort und hinterlegt die Public Keys als `authorized_keys`.

```YAML
# pb-deploy-project.yaml (Auszug)
- name: Deploy project_setup and prepare volume mounts
  hosts: all
  become: true
  gather_facts: false
  vars:
    project_dir: "/home/ubuntu/project"
    local_project_setup_dir: "{{ playbook_dir }}/../../project_setup"
    grafana_uid: 472
    grafana_gid: 472
    influxdb_uid: 1000
    influxdb_gid: 1000
    n8n_uid: 1000
    n8n_gid: 1000
  tasks:
    - name: Copy entire project_setup contents to destination
      ansible.builtin.copy:
        src: "{{ local_project_setup_dir }}/"
        dest: "{{ project_dir }}/"
        owner: ubuntu
        group: ubuntu
        mode: "0644"
        directory_mode: "0755"
        force: true

    - name: Create host directories for Docker volume mounts
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: directory
        mode: "{{ item.mode | default('0750') }}"
      loop:
        - { path: "{{ project_dir }}/grafana_data", mode: "0750" }
        - { path: "{{ project_dir }}/influxdb_data", mode: "0750" }
        - { path: "{{ project_dir }}/n8n_data",     mode: "0750" }

    - name: Set ownership for data directories to match container users
      ansible.builtin.command: "chown -R {{ item.uid }}:{{ item.gid }} {{ item.path }}"
      changed_when: true
      loop:
        - { path: "{{ project_dir }}/grafana_data", uid: "{{ grafana_uid }}", gid: "{{ grafana_gid }}" }
        - { path: "{{ project_dir }}/influxdb_data", uid: "{{ influxdb_uid }}", gid: "{{ influxdb_gid }}" }
        - { path: "{{ project_dir }}/n8n_data",     uid: "{{ n8n_uid }}",     gid: "{{ n8n_gid }}" }
```

Das Projektverzeichnis wird vollständig auf die Node kopiert. Zusätzlich werden Host-Verzeichnisse für Container-Volumes angelegt und die Besitzrechte so gesetzt, dass die Standard-UIDs/GIDs der verwendeten Images (Grafana, InfluxDB, n8n) konsistent schreiben können. Damit sind `docker-compose up -d` und Persistenz out of the box möglich.

### Ausführung

- Erreichbarkeit testen:
  - `ansible all -m ping`
- Basis-Setup (Updates, Docker, Zsh, Benutzer):
  - `ansible-playbook pb-setup.yaml`
- Projekt ausrollen und Volumes vorbereiten:
  - `ansible-playbook pb-deploy-project.yaml`

Hinweis: Der Fokus dieser Dokumentation liegt auf dem Kernfluss (Basis-Setup, Shell, Benutzer, Projekt-Deployment). Ausführliche Betriebssystem-Details (z. B. Release-Codenamen, exakte Paketquellen pro Ubuntu-Version) und Playbook-Optimierungen (z. B. Fact Gathering, SSH Optimierungen) sind im Code ersichtlich, werden hier zugunsten der Lesbarkeit aber nur knapp angerissen.
