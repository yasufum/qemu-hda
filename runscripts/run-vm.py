#!/usr/bin/env python
# coding: utf-8

import os
import yaml
import subprocess
import argparse
import shutil

CORES = 2
MEMSIZE = 2048
HDA = "ubuntu-16.04-server-amd64.qcow2"
HOME = os.environ["HOME"]
QEMU = HOME + "/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64"
QEMU_IVSHMEM = "/tmp/ivshmem_qemu_cmdline_pp_ivshmem" # it depends on dpdk

ring_attr = {
        "prefix": "r",
        "macaddr": "00:AD:BE:%02d:EF:%02d", # gen unique addr with vm_id and index num.
        "telnet_port": "447%02d"  # gen unique port with vm_id
        }
vhost_attr = {
        "prefix": "v",
        "macaddr": "00:AD:BE:EF:%02d:%02d",
        "telnet_port": "448%02d"
        }


work_dir = os.path.dirname(__file__)
img_dir = work_dir + "/img"
ifup_sh = "%s/../ifscripts/qemu-ifup.sh" % work_dir


parser = argparse.ArgumentParser(description="Run SPP and VMs")
parser.add_argument(
        "-i", "--vid",
        type=int, default=0,
        help="VM ID")
parser.add_argument(
        "-t", "--type",
        type=str,
        help="Interface type (ring or vhost)")
parser.add_argument(
        "-c", "--cores",
        type=int, default=2,
        help="Number of cores")
parser.add_argument(
        "-m", "--mem",
        type=int, default=2048,
        help="Memory size")
args = parser.parse_args()



# Generate qemu options and return as a list for subprocess
def gen_qemu_cmd(vm_id, img_inst, cores, memsize, nof_nwif):
    # Setup NIC options
    nic_opts = []
    for i in range(0, nof_nwif):
        tmp_mac = "00:AD:BE:%02d:EF:%02d" % (vm_id, i)
        tmp_netdev = "net_r%s_%s" % (vm_id, i)
        nic_opts = nic_opts + [
                "-device",
                "e1000,netdev=%s,mac=%s" % (tmp_netdev, tmp_mac)
                ]
        nic_opts = nic_opts + [
                "-netdev",
                "tap,id=%s,ifname=%s,script=%s" % (tmp_netdev, tmp_netdev, ifup_sh)
                ]

    # Setup ivshmem options
    f = open(QEMU_IVSHMEM, "r")
    tmp = f.read()
    ivshmem_opts = tmp.split(" ")
    f.close()

    telnet_port = "447%02d" % vm_id

    hugepage_opt = [
            "memory-backend-file",
            "id=mem",
            "size=%sM" % memsize,
            "mem-path=/dev/hugepages",
            "share=on"
            ]
    hugepage_opt = ",".join(hugepage_opt)

    qemu_opt = [
            "-cpu", "host",
            "-enable-kvm",
            "-object", hugepage_opt,
            "-numa", "node,memdev=mem",
            "-mem-prealloc",
            "-hda", img_inst,
            "-m", str(memsize),
            "-smp", "cores=%s,threads=1,sockets=1" % cores,
            "-monitor", "telnet::%s,server,nowait" % telnet_port,
            "-nographic"
            ] + nic_opts + ivshmem_opts

    return ["sudo", QEMU] + qemu_opt

    
def main():
    cores = CORES
    memsize = MEMSIZE
    nof_nwif = 1

    if args.type == "ring":
        vm_attr = ring_attr
    elif args.type == "vhost":
        vm_attr = vhost_attr
    else:
        print("invalid interface type!")
        exit()
    
    prefix = vm_attr["prefix"]

    img_hda = "%s/%s" % (work_dir, HDA)

    subprocess.call(["mkdir", "-p", img_dir])

    # format of template name is adding prefix and "0" with HDA,
    # like a r0-${HDA}
    img_temp= "%s/%s0-%s" % (work_dir, prefix, HDA)

    img_inst = "%s/%s%s-%s" % (img_dir, prefix, args.vid, HDA)

    if (args.vid == 0) and (not os.path.exists(img_temp)):
        shutil.copy(img_hda, img_temp)
        qemu_cmd = gen_qemu_cmd(
                args.vid,
                img_temp,
                cores,
                memsize,
                nof_nwif)
        subprocess.call(qemu_cmd)
    elif (not os.path.exists(img_inst)):
        shutil.copy(img_temp, img_inst)
        qemu_cmd = gen_qemu_cmd(
                args.vid,
                img_inst,
                cores,
                memsize,
                nof_nwif)
        subprocess.call(qemu_cmd)
    else:
        qemu_cmd = gen_qemu_cmd(
                args.vid,
                img_inst,
                cores,
                memsize,
                nof_nwif)
        subprocess.call(qemu_cmd)


if __name__ == '__main__':
    main()
