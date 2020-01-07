# OCP 4 Utils

Util script to generate append-files for ignition configuration using [filetranspile](https://github.com/ashcrow/filetranspiler)

## Usage

Clone the repository

```bash
# git clone https://github.com/spagno/ocp4-utils.git && cd ocp4-utils
```

Install the requirements

```bash
# pip install -r requirements.txt
```

Copy example.yaml into data.yaml and configure it

```bash
# cp example.yaml data.yaml
```

Templates definitions and mtu are optional. In the example.yaml file you'll find the default values.

```yaml
---
url_ignition_file: https://your.site.example.com/pub/ocp42
paths:
  generic: "/etc"
  network: "/etc/sysconfig/network-scripts"
  ntp: "/etc"
  configs: "/configFiles"
nodes:
- hostname: bootstrap.example.com
  role: bootstrap
  interfaces:
  - name: ens192
    ip: 192.0.2.28
    netmask: 24
    gateway: 192.0.2.254
    dns:
    - 192.0.2.13
    mtu: 1500
  ntp: 192.0.2.13
  templateIF: ifcfg-template.j2
  templateChrony: chrony.conf.j2
  templateAppend: append-template.j2
- hostname: master01.example.com
  role: master
  interfaces:
  - name: ens192
    ip: 192.0.2.29
    netmask: 24
    gateway: 192.0.2.254
    dns:
    - 192.0.2.13
    mtu: 1500
  ntp: 192.0.2.13
  templateIF: ifcfg-template.j2
  templateChrony: chrony.conf.j2
  templateAppend: append-template.j2
- hostname: worker01.example.com
  role: worker
  interfaces:
  - name: ens192
    ip: 192.0.2.30
    netmask: 24
    gateway: 192.0.2.254
    dns:
    - 192.0.2.13
    mtu: 1500
  ntp: 192.0.2.13
  templateIF: ifcfg-template.j2
  templateChrony: chrony.conf.j2
  templateAppend: append-template.j2
```

Run the script

```bash
# ./prepare.py
```

The directory 'configFiles' will be created with the ignition files in plain text and base64

```bash
# ls configFiles
bootstrap.example.com  bootstrap.example.com.64 master01.example.com master01.example.com.64 worker01.example.com worker01.example.com.64
```
