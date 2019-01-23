#!/usr/bin/env python
# coding: utf-8
"""Launch VMs."""

import argparse
import os
import re
import shutil
import subprocess

# Prefix for hda files to identify which of types.
TYPE_PREFIX = {
    "normal": "n",
    "ring": "r",
    "vhost": "v",
    "orig": None
}

# for DPDK 16.07
QEMU_IVSHMEM = "/tmp/ivshmem_qemu_cmdline_pp_ivshmem"


def parse_args():
    """Parse command-line options and return arg obj."""
    parser = argparse.ArgumentParser(description="Run SPP and VMs")
    parser.add_argument(
        "-f", "--hda-file",
        type=str,
        help="Path of HDA file")
    parser.add_argument(
        "-q", "--qemu",
        type=str, default="qemu-system-x86_64",
        help="Path of QEMU command, default is 'qemu-system-x86_64'")
    parser.add_argument(
        "-i", "--vids",
        type=str, default="1",
        help="VM IDs of positive number, default is '1'" +
        "(exp. '1', '1,2,3' or '1-3')")
    parser.add_argument(
        "-t", "--type",
        type=str,
        help="Interface type ('normal','ring','vhost' or 'orig')")
    parser.add_argument(
        "-c", "--cores",
        type=int, default=4,
        help="Number of cores, default is '4'")
    parser.add_argument(
        "-m", "--mem",
        type=int, default=4096,
        help="Memory size, default is '4096'")
    parser.add_argument(
        "-d", "--dev-ids",
        type=str,
        help="List of vhost dev IDs such as '1,3-5'")
    parser.add_argument(
        "-vc", "--vhost-client",
        action='store_true',
        help="Enable vhost-client mode, default is False")
    parser.add_argument(
        "--graphic",
        action='store_true',
        help="Enable graphic mode, default is False")
    parser.add_argument(
        "--disable-kvm",
        action='store_true',
        help="Disable KVM for acceleration, default is False")
    parser.add_argument(
        "-nn", "--nof-nwif",
        type=int, default=1,
        help="Number of network interfaces, default is '1'")
    args = parser.parse_args()
    return args


def print_qemu_cmd(args):
    """Show qemu command options in well formatted style."""
    _args = args[:]
    while len(_args) > 1:
        if _args[1] is not None and (not re.match(r'^-', _args[1])):
            ary = []
            for i in range(0, 2):
                ary.append(_args.pop(0))
            if re.match(r'^-', ary[0]):
                print("  %s %s" % (ary[0], ary[1]))
            else:
                print("%s %s" % (ary[0], ary[1]))
        else:
            print("  %s" % _args.pop(0))


# [TODO] parse_vids() is similar to this method. It should be merged.
def dev_ids_to_list(dev_ids):
    """Parse vhost device IDs and return as a list.

    Example:
    '1,3-5' #=> [1,3,4,5]
    """
    res = []
    for dev_id_part in dev_ids.split(','):
        if '-' in dev_id_part:
            cl = dev_id_part.split('-')
            res = res + range(int(cl[0]), int(cl[1])+1)
        else:
            res.append(int(dev_id_part))
    return res


def qemu_version(qemu):
    """Return version of qemu.

    Params for qemu is different between its versions.
    This function is intented to use switch generating params
    for each of versions.
    """
    cmd = "%s -version" % qemu
    res = subprocess.check_output(cmd.split())

    ptn = "QEMU emulator version (\d+.\d+.\d+)"
    matched = re.match(ptn, res)

    return matched.group(1)


def gen_qemu_cmd(args, vid, imgfile, ifup_sh):
    """Generate qemu options and return as a list for subprocess."""
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
    spp_dev_opts = []  # spp_dev_opts is a 2d-array for several options.

    if args.type == "orig":
        # NIC options
        nic_opts = []
        for i in range(0, args.nof_nwif):
            tmp_mac = macaddr["orig"] % i
            tmp_netdev = "net_o0_%s" % i
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
            "-numa", "node,memdev=mem",
            "-mem-prealloc",
            "-hda", imgfile,
            "-m", str(args.mem),
            "-smp", "cores=%s,threads=1,sockets=1" % args.cores,
        ] + hugepage_opts + nic_opts + monitor_opts
        if args.disable_kvm is not True:
            qemu_opts.append("-enable-kvm")
        if args.graphic is False:
            qemu_opts.append("-nographic")

    elif (args.type in ["normal", "ring", "vhost"]):
        # NIC options
        nic_opts = []
        for i in range(0, args.nof_nwif):
            tmp_mac = macaddr[args.type] % (vid, i)
            tmp_netdev = "net_%s%s_%s" % (TYPE_PREFIX[args.type], vid, i)
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
            spp_dev_opts.append(tmp.split(" "))  # if ring, only one option.
            f.close()
        elif args.type == "vhost" and vid != 0:
            if args.dev_ids is None:
                print("Error: dev_ids is required!")
                exit(1)

            if vid != 0:
                # Attach several vhost interfaces
                nic_vu = "net_vu%s" % vid  # NIC for vhost-user

                print(dev_ids_to_list(args.dev_ids))

                for dev_id in dev_ids_to_list(args.dev_ids):
                    virt_mac = macaddr["virtio"] % (vid, dev_id)

                    if args.vhost_client is True:
                        spp_dev_opts.append([
                            "-chardev",
                            "socket,id=chr%s,path=/tmp/sock%s,server" % (
                                dev_id, dev_id
                            )
                        ])
                    else:
                        spp_dev_opts.append([
                            "-chardev",
                            "socket,id=chr%s,path=/tmp/sock%s" % (
                                dev_id, dev_id
                            )
                        ])

                    spp_dev_opts.append([
                        "-netdev",
                        "vhost-user,id=%s_%s,chardev=chr%s,vhostforce" % (
                            nic_vu, dev_id, dev_id
                        ),
                        "-device",
                        "virtio-net-pci,netdev=%s_%s,mac=%s" % (
                            nic_vu, dev_id, virt_mac
                        )
                    ])
    else:
        print("Error: Invalid VM type!")
        exit(1)

    qemu_opts = [
        "-cpu", "host",
        "-numa", "node,memdev=mem",
        "-mem-prealloc",
        "-hda", imgfile,
        "-m", str(args.mem),
        "-smp", "cores=%s,threads=1,sockets=1" % args.cores,
    ] + hugepage_opts + nic_opts
    if args.disable_kvm is not True:
        qemu_opts.append("-enable-kvm")
    if args.graphic is False:
        qemu_opts.append("-nographic")

    for spp_dev_opt in spp_dev_opts:
        qemu_opts = qemu_opts + spp_dev_opt

    qemu_opts = qemu_opts + monitor_opts

    return ["sudo", args.qemu] + qemu_opts


def confirm_ivshmem():
    """Check existing prmary and ivshmem file.

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
    """Parse a str of vids.

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
                if i >= 0:
                    vids.append(i)
        else:
            if int(ss) >= 0:
                vids.append(int(ss))

    # Remove overlapped elements and return it
    return list(set(vids))


def main():
    """Run main method of vm-launcher."""
    proj_dir = os.path.dirname(__file__) + "/.."  # Project root dir.
    tmpl_dir = "%s/hda/templates" % proj_dir
    inst_dir = "%s/hda/instances" % proj_dir
    ifup_sh = "%s/ifscripts/qemu-ifup.sh" % proj_dir

    subprocess.call(["mkdir", "-p", tmpl_dir])
    subprocess.call(["mkdir", "-p", inst_dir])

    args = parse_args()

    if args.hda_file is None:
        print("Error: HDA is required!")
        exit(1)

    if args.type is None:
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
    # Template is a parent and instances are children copied from
    # tempalte.
    #
    # proj_dir/hda/
    #             |--ubuntu1604.qcow2  # original
    #             |--templates/n0-ubuntu1604.qcow2  # template
    #             |--instances/
    #                 |--n1-ubuntu1604.qcow2  # instances
    #                 |--n2-ubuntu1604.qcow2
    #                 |-- ...
    #
    # The name of file is assinged as PREFIX-VID-HDA_NAME.
    # For example, template (vid is 0) of normal type is named as
    # "n0-ubuntu-16.04.2-server-amd64.qcow2".
    # Instance of vid 1 is "n1-ubuntu-16.04.2-server-amd64.qcow2".
    hda = args.hda_file.split("/")[-1]

    # Template is defined with vid 0.
    img_tmpl = "%s/%s%d-%s" % (tmpl_dir, TYPE_PREFIX[args.type], 0, hda)

    # If type is "orig" or template does not exist, vids option is
    # igrenored to launch original or template VM.
    if args.type == "orig":
        if vids != [0]:
            print("vid '0' is used and not required for 'orig' type.")
        print("Booting VM from %s ..." % args.hda_file)
        qemu_cmds.append(
            gen_qemu_cmd(args, 0, args.hda_file, ifup_sh)
        )
    # case of template does not exist
    elif (not os.path.exists(img_tmpl)):
        # Create template
        shutil.copy(args.hda_file, img_tmpl)
        print("Booting VM from %s ..." % img_tmpl)
        qemu_cmds.append(
            gen_qemu_cmd(args, 0, img_tmpl, ifup_sh)
        )
    # Boot VMs of vids option
    else:
        for vid in vids:
            if vid == 0:
                imgfile = img_tmpl
            else:
                img_inst = "%s/%s%s-%s" % (
                    inst_dir, TYPE_PREFIX[args.type], vid, hda
                )
                if (not os.path.exists(img_inst)):
                    # Create instance
                    shutil.copy(img_tmpl, img_inst)
                imgfile = img_inst

            print("Booting VM from %s ..." % imgfile)
            qemu_cmds.append(
                gen_qemu_cmd(args, vid, imgfile, ifup_sh)
            )

    # Before running qemu in background, do sudo to input password.
    subprocess.call(["sudo", "pwd"])

    for qc in qemu_cmds:
        qc.append("&")
        print_qemu_cmd(qc)
        subprocess.call(" ".join(qc), shell=True)


if __name__ == '__main__':
    main()
