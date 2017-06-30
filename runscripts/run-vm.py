#!/usr/bin/env python
# coding: utf-8

import os
import yaml
import subprocess
import argparse
import shutil
import re

# Configurations
QEMU_IVSHMEM = "/tmp/ivshmem_qemu_cmdline_pp_ivshmem" # for DPDK
TYPE_PREFIX = {
        "normal": "n",
        "ring": "r",
        "vhost": "v",
        "orig": None
        }


def parse_args():
    """
    Parse command-line options and return arg obj.
    """

    parser = argparse.ArgumentParser(description="Run SPP and VMs")
    parser.add_argument(
            "-f", "--hda-file",
            type=str,
            help="Path of HDA file")
    parser.add_argument(
            "-q", "--qemu",
            type=str, default="qemu-system-x86_64",
            help="Path of QEMU command, default is 'qemu-system-x86_64'"
            )
    parser.add_argument(
            "-i", "--vids",
            type=str, default="1",
            help="VM IDs of positive number, default is '1'" +
            "(exp. '1', '1,2,3' or '1-3')"
            )
    parser.add_argument(
            "-t", "--type",
            type=str,
            help="Interface type ('normal','ring','vhost' or 'orig')")
    parser.add_argument(
            "-c", "--cores",
            type=int, default=2,
            help="Number of cores, default is '2'")
    parser.add_argument(
            "-m", "--mem",
            type=int, default=2048,
            help="Memory size, default is '2048'")
    parser.add_argument(
            "-vn", "--vhost-num",
            type=int, default=1,
            help="Number of vhost interfaces, default is '1'")
    parser.add_argument(
            "-nn", "--nof-nwif",
            type=int, default=1,
            help="Number of network interfaces, default is '1'")
    args = parser.parse_args()
    return args


def print_qemu_cmd(args):
    """Show qemu command options"""
    
    _args = args[:]
    while len(_args) > 1:
        if _args[1] != None and (not re.match(r'^-', _args[1])):
            ary = []
            for i in range(0, 2):
                ary.append(_args.pop(0))
            if re.match(r'^-', ary[0]):
                print("  %s %s" % (ary[0], ary[1]))
            else:
                print("%s %s" % (ary[0], ary[1]))
        else:
            print("  %s" % _args.pop(0))


def gen_qemu_cmd(args, vid, imgfile, ifup_sh):
    """Generate qemu options and return as a list for subprocess"""

    macaddr = {
        "orig":   "00:AD:BE:B0:FF:%02d",
        "normal": "00:AD:BE:B1:%02d:%02d",
        "ring":   "00:AD:BE:B2:%02d:%02d",
        "vhost":  "00:AD:BE:B3:%02d:%02d",
        "virtio": "00:AD:BE:B4:%02d:%02d"
        }

    telnet_port = {
            "orig":   "44600",
            "normal": "447%02d",
            "ring":   "448%02d",
            "vhost":  "449%02d"
            }

    # spp's device options (ring or vhost)
    spp_dev_opts = [] # spp_dev_opts is a 2d-array for several options.

    if args.type == "orig":
        # NIC options
        nic_opts = []
        for i in range(0, args.nof_nwif):
            tmp_mac = macaddr["orig"] % i
            tmp_netdev = "net_0_%s" % i
            nic_opts = nic_opts + [
                    "-device",
                    "e1000,netdev=%s,mac=%s" % (tmp_netdev, tmp_mac)
                    ]
            nic_opts = nic_opts + [
                    "-netdev",
                    "tap,id=%s,ifname=%s,script=%s" % (
                        tmp_netdev, tmp_netdev, ifup_sh
                        )
                    ]

        # monitor options
        monitor_opts = [
                "-monitor",
                "telnet::%s,server,nowait" % telnet_port["orig"]
                ]

        # object(hugepage) options
        hugepage_opt = [
                "memory-backend-file",
                "id=mem",
                "size=%sM" % args.mem,
                "mem-path=/dev/hugepages",
                "share=on"
                ]
        hugepage_opt = ",".join(hugepage_opt)
        hugepage_opts = ["-object", hugepage_opt]

        qemu_opts = [
                "-cpu", "host",
                "-enable-kvm",
                "-numa", "node,memdev=mem",
                "-mem-prealloc",
                "-hda", imgfile,
                "-m", str(args.mem),
                "-smp", "cores=%s,threads=1,sockets=1" % args.cores,
                "-nographic"
                ] + hugepage_opts + nic_opts + monitor_opts

    elif (args.type in ["normal", "ring", "vhost"]):
        # NIC options
        nic_opts = []
        for i in range(0, args.nof_nwif):
            tmp_mac = macaddr[args.type] % (vid, i)
            tmp_netdev = "net_%s%s" % (TYPE_PREFIX[args.type], i)
            nic_opts = nic_opts + [
                    "-device",
                    "e1000,netdev=%s,mac=%s" % (tmp_netdev, tmp_mac)
                    ]
            nic_opts = nic_opts + [
                    "-netdev",
                    "tap,id=%s,ifname=%s,script=%s" % (
                        tmp_netdev, tmp_netdev, ifup_sh
                        )
                    ]

        # monitor options
        tport = telnet_port[args.type] % vid
        monitor_opts = [
                "-monitor",
                "telnet::%s,server,nowait" % tport
                ]

        # object(hugepage) options
        hugepage_opt = [
                "memory-backend-file",
                "id=mem",
                "size=%sM" % args.mem,
                "mem-path=/dev/hugepages",
                "share=on"
                ]
        hugepage_opt = ",".join(hugepage_opt)
        hugepage_opts = ["-object", hugepage_opt]

        if args.type == "ring":
            # ivshmem options
            f = open(QEMU_IVSHMEM, "r")
            tmp = f.read()
            tmp = tmp.strip()
            spp_dev_opts.append(tmp.split(" ")) # if ring, only one option.
            f.close()
        elif args.type == "vhost":
            # Attach several vhost interfaces
            sock_id = vid  
            nic_vu = "net_vu%s" % vid  # NIC for vhost-user

            # TODO Consider assignment of sock id
            # Additional socket id is defined by adding from 0 to sock id.
            # For example, sock110, sock111, ... for sock11
            for i in range(0, args.vhost_num-1):
                virt_mac = macaddr["virtio"] % (vid, i)
                spp_dev_opts.append([
                       "-chardev",
                       "socket,id=chr%s%s,path=/tmp/sock%s%s" % (
                           sock_id, i, sock_id, i
                           ),
                       "-netdev",
                       "vhost-user,id=%s%s,chardev=chr%s%s,vhostforce" % (
                           nic_vu, i, sock_id, i
                           ),
                       "-device",
                       "virtio-net-pci,netdev=%s%s,mac=%s" % (
                           nic_vu, i, virt_mac
                           )
                       ])
    else:
        print("Error: Invalid VM type!")
        exit(1)

    qemu_opts = [
            "-cpu", "host",
            "-enable-kvm",
            "-numa", "node,memdev=mem",
            "-mem-prealloc",
            "-hda", imgfile,
            "-m", str(args.mem),
            "-smp", "cores=%s,threads=1,sockets=1" % args.cores,
            "-nographic"
            ] + hugepage_opts + nic_opts 
    
    for spp_dev_opt in spp_dev_opts:
        qemu_opts = qemu_opts + spp_dev_opt

    qemu_opts = qemu_opts + monitor_opts

    return ["sudo", args.qemu] + qemu_opts

    
def confirm_ivshmem():
    """
    Check SPP primary is running and ivshmem file is exists.
    If it doesn't exist, ask a user to start primary.
    """

    while not os.path.exists(QEMU_IVSHMEM):
        if not os.path.exists(QEMU_IVSHMEM):
            print("SPP primary process isn't ready for ivshmem.")
            print("Run SPP primary first.")
            input_str = raw_input("Continue to run? Y/n>\n")
        if input_str == "n" or input_str == "no":
            exit()


def parse_vids(vids_str):
    """
    Parse a str of vids opt and return as a unique int list of vid
    For example, "1-3,5,7" -> (1, 2, 3, 5, 7)
    """

    # Check if invalid char is included
    if re.match(r'.*[a-zA-Z\+\*]', vids_str):
        print("Invalid argment: %s" % vids_str)
        exit(1)

    vids = []
    # First, separate with ",", then "-" and complete between the
    # range of 'x-y'
    for ss in vids_str.split(","):
        if re.match(r'^\d+-\d+', ss):
            rng = ss.split("-")
            for i in range(int(rng[0]), int(rng[1])+1):
                if i > 0:
                    vids.append(i)
        else:
            if int(ss) > 0:
                vids.append(int(ss))
    
    # Remove overlapped elements and return it
    return list(set(vids))


def main():

    work_dir = os.path.dirname(__file__)
    tmpl_dir = work_dir + "/template"
    img_dir = work_dir + "/img"
    ifup_sh = "%s/../ifscripts/qemu-ifup.sh" % work_dir

    subprocess.call(["mkdir", "-p", tmpl_dir])
    subprocess.call(["mkdir", "-p", img_dir])

    args = parse_args()

    if args.hda_file == None:
        print("Error: HDA is required!")
        exit(1)

    if args.type == None:
        print("Error: VM type is required!")
        exit(1)

    if not (args.type in TYPE_PREFIX.keys()):
        print("Error: Invalid VM type!")
        exit(1)

    vids = parse_vids(args.vids)

    # Show prompt if spp primary doesn't run 
    if args.type == "ring":
        confirm_ivshmem()

    qemu_cmds = []

    # Create template and instance files.
    # Template file is a parent and instances generated from tempalte are
    # children. Instance is created by copying from template.
    #     work_dir/  (names are dummy and different from actual filename)
    #           |--template/n0-ubuntu1604.qcow2
    #           |--img/
    #               |--n1-ubuntu1604.qcow2
    #               |--n2-ubuntu1604.qcow2
    #               |-- ...
    # Filename is assinged as (prefix)+(vid)+(hda-name).
    # For example, "n0-ubuntu-16.04.2-server-amd64.qcow2" for template and
    # "n1-ubuntu-16.04.2-server-amd64.qcow2" for instance id 1.
    hda = args.hda_file.split("/")[-1]
    img_tmpl = "%s/%s%d-%s" % (tmpl_dir, TYPE_PREFIX[args.type], 0, hda)

    if args.type == "orig":
        qemu_cmds.append(
                gen_qemu_cmd(args, 0, args.hda_file, ifup_sh)
                )

    elif (not os.path.exists(img_tmpl)):
        # Create template
        shutil.copy(args.hda_file, img_tmpl)
        qemu_cmds.append(
                gen_qemu_cmd(args, 0, img_tmpl, ifup_sh)
                )
    else:
        for vid in vids:
            img_inst = "%s/%s%s-%s" % (img_dir, TYPE_PREFIX[args.type], vid, hda)

            if (not os.path.exists(img_inst)):
                # Create instance
                shutil.copy(img_tmpl, img_inst)
            imgfile = img_inst

            qemu_cmds.append(
                    gen_qemu_cmd(args, vid, imgfile, ifup_sh)
                    )

    # To stop running qemu in background before input password, do sudo.
    subprocess.call(["sudo", "pwd"])

    for qc in qemu_cmds:
        qc.append("&")
        print_qemu_cmd(qc)
        subprocess.call(" ".join(qc), shell=True)


if __name__ == '__main__':
    main()
