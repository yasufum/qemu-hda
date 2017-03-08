#!/usr/bin/env python
# coding: utf-8

import os
import yaml
import subprocess
import argparse
import shutil
import re

# Original HDA which is copied for each of VM instances.
HDA = "ubuntu-16.04-server-amd64.qcow2"

# Path configurations
HOME = os.environ["HOME"]
QEMU = HOME + "/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64"
QEMU_IVSHMEM = "/tmp/ivshmem_qemu_cmdline_pp_ivshmem" # it depends on dpdk


work_dir = os.path.dirname(__file__)
img_dir = work_dir + "/img"
ifup_sh = "%s/../ifscripts/qemu-ifup.sh" % work_dir


# Parse command-line options
parser = argparse.ArgumentParser(description="Run SPP and VMs")
parser.add_argument(
        "-i", "--vids",
        type=str,
        help="VM IDs (exp. '1', '1,2,3' or '1-3')")
parser.add_argument(
        "-t", "--type",
        type=str,
        help="Interface type ('ring', 'vhost' and 'none')")
parser.add_argument(
        "-c", "--cores",
        type=int, default=2,
        help="Number of cores")
parser.add_argument(
        "-m", "--mem",
        type=int, default=2048,
        help="Memory size")
parser.add_argument(
        "-vn", "--vhost-num",
        type=int, default=1,
        help="Number of vhost interfaces")
parser.add_argument(
        "-nn", "--nof-nwif",
        type=int, default=1,
        help="Number of network interfaces")
args = parser.parse_args()


def print_qemu_cmd(args):
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
            virtio_macaddr = "00:AD:BE:FF:%02d:%02d"
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
            spp_dev_opts = [] # spp_dev_opts is a 2d-array for several options.
            spp_dev_opts.append(tmp.split(" ")) # in case of ring, only one option.
            f.close()
        else: # vhost
            # [TODO] restrict maximum num of vm_id defined in spp controller
            sock_id = vm_id  
            nic_vu = "net_vu%s" % vm_id  # NIC for vhost-user
            tmp_mac = virtio_macaddr % (vm_id, 0)
            spp_dev_opts = [] # spp_dev_opts is a 2d-array for several options.
            spp_dev_opts.append([
                   "-chardev", "socket,id=chr0,path=/tmp/sock%s" % sock_id,
                   "-netdev", "vhost-user,id=%s,chardev=chr0,vhostforce" % nic_vu,
                   "-device", "virtio-net-pci,netdev=%s,mac=%s" % (nic_vu, tmp_mac)
                   ])

            # Attach several vhost interfaces (experimental)
            if args.vhost_num > 1:
                # index to avoid ids are overwrapped.
                # socket id is named by appending numbers to original id from 0.
                # for example, additional sock ids for sock11 are named as sock110,
                # sock111, sock112, ... 
                for i in range(0, args.vhost_num-1):
                    tmp_mac = virtio_macaddr % (vm_id, i+1)
                    spp_dev_opts.append([
                           "-chardev",
                           "socket,id=chr%s%s,path=/tmp/sock%s%s" % (sock_id, i, sock_id, i),
                           "-netdev",
                           "vhost-user,id=%s%s,chardev=chr%s%s,vhostforce" % (nic_vu, i, sock_id, i),
                           "-device",
                           "virtio-net-pci,netdev=%s%s,mac=%s" % (nic_vu, i, tmp_mac)
                           ])

        qemu_opts = [
                "-cpu", "host",
                "-enable-kvm",
                "-numa", "node,memdev=mem",
                "-mem-prealloc",
                "-hda", img_inst,
                "-m", str(memsize),
                "-smp", "cores=%s,threads=1,sockets=1" % cores,
                "-nographic"
                ] + hugepage_opts + nic_opts 
        
        for spp_dev_opt in spp_dev_opts:
            qemu_opts = qemu_opts + spp_dev_opt

        qemu_opts = qemu_opts + monitor_opts

    return ["sudo", QEMU] + qemu_opts

    
def confirm_ivshmem():
    while not os.path.exists(QEMU_IVSHMEM):
        if not os.path.exists(QEMU_IVSHMEM):
            print("SPP primary process isn't ready for ivshmem.")
            print("Run SPP primary first.")
            input_str = raw_input("Continue to run? Y/n>\n")
        if input_str == "n" or input_str == "no":
            exit()


def main():
    cores = args.cores
    memsize = args.mem 
    nof_nwif = args.nof_nwif

    if args.vids == None:
        print("Error: At least one VM ID with '-i' option must be required!")
        print("Run 'run-vm.py -h' for help.")
        exit()

    # Separate vids and append it to an array
    # vids format is expedted to be like as "1,3-5,7"
    vids_str = args.vids
    if re.match(r'.*[a-zA-Z\+\*]', vids_str):
        print("Invalid argment: %s" % vids_str)
        exit()

    vids = []
    # First, separate with ",", then "-" and complete between the range of 'x-y'
    for ss in vids_str.split(","):
        if re.match(r'^\d+-\d+', ss):
            rng = ss.split("-")
            for i in range(int(rng[0]), int(rng[1])+1):
                vids.append(i)
        else:
            vids.append(int(ss))
    
    # Remove overlapped elements
    vids = list(set(vids))


    if (args.type == "none") and (len(vids) > 1):
        print("Error: You use only one VM with type 'none'")
        exit()

    # show prompt if spp primary doesn't run 
    if args.type == "ring":
        confirm_ivshmem()

    qemu_cmds = []
    for vid in vids:
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
            # format of template name is adding prefix and "0" with HDA, 'r0-${HDA}'
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

        qemu_cmds.append(
                gen_qemu_cmd(
                    args.type,
                    vid,
                    imgfile,
                    cores,
                    memsize,
                    nof_nwif)
                )

    # To stop running qemu in background before input password,
    # do sudo.
    subprocess.call(["sudo", "pwd"])

    for qc in qemu_cmds:
        qc.append("&")
        print_qemu_cmd(qc)
        subprocess.call(" ".join(qc), shell=True)


if __name__ == '__main__':
    main()
