#!/usr/bin/env python
# coding: utf-8

import os
import yaml
import subprocess
import argparse
import shutil
import re

CORES = 2
MEMSIZE = 2048
NOF_NWIF = 1
HDA = "ubuntu-16.04-server-amd64.qcow2"
HOME = os.environ["HOME"]
QEMU = HOME + "/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64"
QEMU_IVSHMEM = "/tmp/ivshmem_qemu_cmdline_pp_ivshmem" # it depends on dpdk


work_dir = os.path.dirname(__file__)
img_dir = work_dir + "/img"
ifup_sh = "%s/../ifscripts/qemu-ifup.sh" % work_dir


parser = argparse.ArgumentParser(description="Run SPP and VMs")
parser.add_argument(
        "-i", "--vids",
        type=str,
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


def print_qemu_cmd(args):
    _args = args[:]
    while len(_args) > 1:
        if _args[1] != None and (not re.match(r'^-', _args[1])):
            ary = []
            for i in range(0, 2):
                ary.append(_args.pop(0))
            if re.match('^-', ary[0]):
                print("  %s %s" % (ary[0], ary[1]))
            else:
                print("%s %s" % (ary[0], ary[1]))
        else:
            print("  %s" % _args.pop(0))


# Generate qemu options and return as a list for subprocess
def gen_qemu_cmd(stype, vm_id, img_inst, cores, memsize, nof_nwif):

    if stype == "none":
        macaddr = "00:AD:00:BE:EF:%02d" # gen unique addr with index num.
        telnet_port = "44600"

        # NIC options
        nic_opts = []
        for i in range(0, nof_nwif):
            tmp_mac = macaddr % i
            tmp_netdev = "net_0_%s" % i
            nic_opts = nic_opts + [
                    "-device",
                    "e1000,netdev=%s,mac=%s" % (tmp_netdev, tmp_mac)
                    ]
            nic_opts = nic_opts + [
                    "-netdev",
                    "tap,id=%s,ifname=%s,script=%s" % (tmp_netdev, tmp_netdev, ifup_sh)
                    ]

        # monitor options
        monitor_opts = [
                "-monitor",
                "telnet::%s,server,nowait" % telnet_port]

        # object(hugepage) options
        hugepage_opt = [
                "memory-backend-file",
                "id=mem",
                "size=%sM" % memsize,
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
                "-hda", img_inst,
                "-m", str(memsize),
                "-smp", "cores=%s,threads=1,sockets=1" % cores,
                "-nographic"
                ] + hugepage_opts + nic_opts + monitor_opts

    else:
        if stype == "ring":
            prefix = "r"
            macaddr = "00:AD:BE:%02d:EF:%02d" # gen unique addr with vm_id and index num.
            telnet_port = "447%02d"  # gen unique port with vm_id
        else:
            prefix = "v"
            macaddr = "00:AD:BE:EF:%02d:%02d"
            telnet_port = "448%02d"

        # NIC options
        nic_opts = []
        for i in range(0, nof_nwif):
            tmp_mac = macaddr % (vm_id, i)
            tmp_netdev = "net_%s%s_%s" % (prefix, vm_id, i)
            nic_opts = nic_opts + [
                    "-device",
                    "e1000,netdev=%s,mac=%s" % (tmp_netdev, tmp_mac)
                    ]
            nic_opts = nic_opts + [
                    "-netdev",
                    "tap,id=%s,ifname=%s,script=%s" % (tmp_netdev, tmp_netdev, ifup_sh)
                    ]

        # monitor options
        telnet_p = telnet_port % vm_id
        monitor_opts = [
                "-monitor",
                "telnet::%s,server,nowait" % telnet_p]

        # object(hugepage) options
        hugepage_opt = [
                "memory-backend-file",
                "id=mem",
                "size=%sM" % memsize,
                "mem-path=/dev/hugepages",
                "share=on"
                ]
        hugepage_opt = ",".join(hugepage_opt)
        hugepage_opts = ["-object", hugepage_opt]

        # spp's device options (ring or vhost)
        if stype == "ring":
            # ivshmem options
            f = open(QEMU_IVSHMEM, "r")
            tmp = f.read()
            tmp = tmp.strip()
            spp_dev_opts = tmp.split(" ")
            f.close()
        else:
            sock_id = vm_id  # [TODO] restrict maximum num of vm_id(heuristically, 21 is not affect)
            nic_vu = "net_vu%s" % vm_id  # NIC for vhost-user
            spp_dev_opts = [
                   "-chardev", "socket,id=chr0,path=/tmp/sock%s" % sock_id,
                   "-netdev", "vhost-user,id=%s,chardev=chr0,vhostforce" % nic_vu,
                   "-device", "virtio-net-pci,netdev=%s" % nic_vu
                   ]

        qemu_opts = [
                "-cpu", "host",
                "-enable-kvm",
                "-numa", "node,memdev=mem",
                "-mem-prealloc",
                "-hda", img_inst,
                "-m", str(memsize),
                "-smp", "cores=%s,threads=1,sockets=1" % cores,
                "-nographic"
                ] + hugepage_opts + nic_opts + spp_dev_opts + monitor_opts

    return ["sudo", QEMU] + qemu_opts

    
def main():
    cores = CORES
    memsize = MEMSIZE
    nof_nwif = NOF_NWIF

    #[TODO] 複数vidを分割して、forで1つずつ起動させる
    vid = int(args.vids)

    img_hda = "%s/%s" % (work_dir, HDA)
    subprocess.call(["mkdir", "-p", img_dir])

    if args.type == "none":
        imgfile = img_hda

    else:
        if args.type == "ring":
            prefix = "r"
        elif args.type == "vhost":
            prefix = "v"
        else:
            print("invalid interface type!")
            exit()

        # Templates are created in working dir and instances are in img_dir.
        # format of template name is adding prefix and "0" with HDA,
        # like a r0-${HDA}
        img_temp= "%s/%s0-%s" % (work_dir, prefix, HDA)
        img_inst = "%s/%s%s-%s" % (img_dir, prefix, vid, HDA)

        if vid == 0:
            # Create template
            if (not os.path.exists(img_temp)):
                shutil.copy(img_hda, img_temp)
            imgfile = img_temp
        elif (not os.path.exists(img_inst)):
            # Create instance
            shutil.copy(img_temp, img_inst)
            imgfile = img_inst
        else:
            imgfile = img_inst

    qemu_cmd = gen_qemu_cmd(
            args.type,
            vid,
            imgfile,
            cores,
            memsize,
            nof_nwif)
    print_qemu_cmd(qemu_cmd)
    subprocess.call(qemu_cmd)


if __name__ == '__main__':
    main()
