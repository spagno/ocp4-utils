#!/usr/bin/env python3
import yaml
import tempfile
import os
import pathlib
import subprocess
import shutil
import base64
import requests
import ipaddress

from jinja2 import Environment, FileSystemLoader

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import pycdlib

DEFAULT_TEMPLATES = {
    "templateChrony": "chrony.conf.j2",
    "templateIF": "ifcfg-template.j2",
    "templateAppend": "append-template.j2",
    "templateIsolinux": "isolinux.cfg.j2",
    "templateEFI": "grub.cfg.j2",
}
FILETRANSPILE_BIN = os.getcwd() + "/filetranspile.py"


def GetFileTranspile(download_url):
    if not pathlib.Path(FILETRANSPILE_BIN).is_file():
        r = requests.get(download_url)
        with open(FILETRANSPILE_BIN, "wb") as f:
            f.write(r.content)


def GetData(data_file):
    data = ""
    try:
        with open(data_file, "r") as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                os._exit(1)
    except (FileNotFoundError, IOError):
        print("data.yaml not found")
        os._exit(1)
    return data


def SaveTemplate(template, data, file):
    with open(file, "w") as file_dest:
        file_dest.write(template.render(data))


def PrintTemplate(template, data):
    return template.render(data)


def CreateTempDir():
    return tempfile.mkdtemp(prefix="prepare-")


def CreateDir(path):
    try:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Creation of the directory %s success" % path)


def CheckTemplate(data, template, env):
    if template not in data:
        return env.get_template(DEFAULT_TEMPLATES[template])
    else:
        return env.get_template(data[template])


def CreateGenericPath(path):
    CreateDir(path)


def CreateHostnameFile(path, hostname):
    with open(path + "/hostname", "w") as file_hostname:
        file_hostname.write(hostname)


def CreateChronyFile(path, template_jinja, node):
    CreateDir(path)
    SaveTemplate(template_jinja, node, path + "/chrony.conf")


def CreateAppendFileTemp(template_jinja, node, append_file_tmp):
    path = os.path.dirname(append_file_tmp)
    CreateDir(path)
    SaveTemplate(template_jinja, node, append_file_tmp)


def CreateNetworkFiles(path, template, env, node):
    CreateDir(path)
    for interface in node["interfaces"]:
        template_jinja = CheckTemplate(interface, template, env)
        SaveTemplate(
            template_jinja, interface, path + "/ifcfg-" + interface["name"]
        )


def CreateAppendFile(tmppath, append_file_tmp, append_file):
    subprocess.run(
        [
            "/usr/bin/env",
            "python3",
            FILETRANSPILE_BIN,
            "-i",
            append_file_tmp,
            "-f",
            tmppath,
            "-o",
            append_file,
        ]
    )


def CreateBase64EncodedAppendFile(append_file):
    with open(append_file, "r") as file_source:
        data = file_source.read()
    encodedBytes = base64.b64encode(data.encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    with open(append_file + ".64", "w") as file_dest:
        file_dest.write(encodedStr)


def DeleteTempDir(tmppath):
    shutil.rmtree(tmppath)


def DeleteAppendFileTemp(append_file_tmp):
    os.remove(append_file_tmp)


def CreateISO(data, node, file_to_write):
    iso_path = os.getcwd() + data["paths"]["isos"]
    iso_file = iso_path + "/" + node["hostname"] + ".iso"
    CreateGenericPath(iso_path)
    shutil.copyfile(data["iso_file"], iso_file)
    iso = pycdlib.PyCdlib()
    iso.open(iso_file, "rb+")
    ip_strings = list()
    nameservers = list()
    for interface_data in node["interfaces"]:
        mtu = ""
        gateway = ""
        hostname = ""
        if "mtu" in interface_data:
            mtu = ":" + str(interface_data["mtu"])
        if "gateway" in interface_data:
            gateway = interface_data["gateway"]
        if len(ip_strings) == 0:
            hostname = node["hostname"]
        if "dns" in interface_data:
            nameservers.extend(interface_data["dns"])
        ip_string = "ip=%s::%s:%s:%s:%s:none%s" % (
            interface_data["ip"],
            gateway,
            ipaddress.ip_network(
                interface_data["ip"] + "/" + str(interface_data["cidr"]),
                False,
            ).netmask.__str__(),
            hostname,
            interface_data["name"],
            mtu,
        )
        ip_strings.append(ip_string)
    configuration = {}
    configuration.update(
        {
            "ip_strings": ip_strings,
            "dns": nameservers,
            "install_device": node["install_device"],
            "bios_image": data["bios_image"],
            "append_url": data["append_url"] + "/" + node["hostname"],
        }
    )
    if "templateIsolinux" in file_to_write:
        template_data = PrintTemplate(
            file_to_write["templateIsolinux"], configuration
        )
        iso.modify_file_in_place(
            BytesIO(template_data.encode()),
            len(template_data.encode()),
            "/ISOLINUX/ISOLINUX.CFG;1",
        )
    if "templateEFI" in file_to_write:
        template_data = PrintTemplate(
            file_to_write["templateEFI"], configuration
        )
        iso.modify_file_in_place(
            BytesIO(template_data.encode()),
            len(template_data.encode()),
            "/EFI/REDHAT/GRUB.CFG;1",
        )
    iso.write_fp(BytesIO())
    iso.close()


def main():
    data = GetData("data.yaml")
    GetFileTranspile(data["download_url"])
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    for node in data["nodes"]:
        tmppath = CreateTempDir()
        node.update(url_ignition_file=data["url_ignition_file"])
        append_file = (
            os.getcwd() + data["paths"]["configs"] + "/" + node["hostname"]
        )
        append_file_tmp = append_file + ".tmp"
        CreateGenericPath(tmppath + data["paths"]["generic"])
        CreateHostnameFile(
            tmppath + data["paths"]["generic"], node["hostname"]
        )
        file_to_write = {}
        for template in DEFAULT_TEMPLATES:
            template_jinja = CheckTemplate(node, template, env)
            if template == "templateChrony":
                path = tmppath + data["paths"]["ntp"]
                CreateChronyFile(path, template_jinja, node)
            elif (
                template == "templateIF"
                and "interfaces" in node
                and "create_iso" in node
                and not node["create_iso"]
            ):
                path += "/sysconfig/network-scripts"
                CreateNetworkFiles(path, template, env, node)
            elif template == "templateIsolinux" or template == "templateEFI":
                if (
                    "interfaces" in node
                    and "create_iso" in node
                    and node["create_iso"] is True
                ):
                    file_to_write.update({template: template_jinja})
            elif template == "templateAppend":
                CreateAppendFileTemp(template_jinja, node, append_file_tmp)
        if file_to_write:
            CreateISO(data, node, file_to_write)
        CreateAppendFile(tmppath, append_file_tmp, append_file)
        CreateBase64EncodedAppendFile(append_file)
        DeleteTempDir(tmppath)
        DeleteAppendFileTemp(append_file_tmp)


if __name__ == "__main__":
    main()
