#!/usr/bin/env python
# coding: utf-8

import argparse
import re
import subprocess
import yaml

# Network info of VMs is registerd virbr0.status.
# This is an example.
# [
#     {
#         "ip-address": "192.168.122.157",
#         "mac-address": "00:ad:be:b1:00:00",
#         "hostname": "spp",
#         "expiry-time": 1512366825
#     }
# ]
dns_file = "/var/lib/libvirt/dnsmasq/virbr0.status"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Login VM listed in %s" % dns_file)
    parser.add_argument(
        "hostname",
        nargs="?",
        type=str,
        help="Login host")
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="Show entries")
    parser.add_argument(
        "-u", "--update",
        metavar=("ipaddr", "new_hostname"),
        nargs=2,
        type=str,
        help="Update hostname of ipaddr or id")
    parser.add_argument(
        "-r", "--run",
        metavar=('ipaddr', 'cmd'),
        nargs=2,
        type=str,
        help="Run command on the VM of ipaddr or id " +
        "(exp: sppsh -r 0 'touch a.txt')")
    parser.add_argument(
        "--shutdown",
        action="store_true",
        help="Shutdown VM")
    parser.add_argument(
        "--shutdown-all",
        action="store_true",
        help="Shutdown all VMs")
    parser.add_argument(
        "-a", "--account",
        type=str,
        help="Login account")
    return parser.parse_args()


def get_ipaddr(target, addr_table):
    """Resolve IP address from given target

    Target must be an IP addr or index of addr_table.
    addr_table is a yaml obj of '/var/lib/libvirt/dnsmasq/virbr0.status'
    """

    if re.match(r'^\d+\.\d+\.\d+\.\d+$', target):  # Case of IP address
        ipaddr = target  # Use given target as IP address
    elif re.match(r'^\d+$', target):  # or index number
        # Find IP address of index
        idx = int(target)
        if idx < len(addr_table):
            ipaddr = addr_table[idx]["ip-address"]
    else:
        raise(ValueError("Invalid ipaddr or id!"))
    return ipaddr


def main():
    f = open(dns_file, "r")
    dns_entries = yaml.load(f)
    f.close()

    args = parse_args()

    if len(dns_entries) == 0:
        print("No VMs running...")
        exit()

    if args.shutdown_all is True:
        for i in range(0, len(dns_entries)):
            # Avoid error for empty hostname
            subprocess.call([
                "ssh", "-t", dns_entries[i]["ip-address"],
                "sudo", "shutdown", "-h", "now"
                ])

    # Update hostname
    elif args.update is not None:
        ipaddr = get_ipaddr(args.update[0], dns_entries)

        # Update hostname and reboot
        subprocess.call([
            "ssh", "-t", str(ipaddr),
            "sudo", "hostnamectl", "set-hostname", str(args.update[1])
            ])
        subprocess.call([
            "ssh", "-t", str(ipaddr),
            "sudo", "reboot"
            ])

    # Run secondary process
    elif args.run is not None:
        ipaddr = get_ipaddr(args.run[0], dns_entries)
        cmd = args.run[1]

        subprocess.call(
            ["ssh", "-t", str(ipaddr)] +
            cmd.split(", ")
            )

    # Shutdown VM
    elif args.shutdown is True:
        for i in range(0, len(dns_entries)):
            # Avoid error for empty hostname
            if "hostname" in dns_entries[i]:
                hn = dns_entries[i]["hostname"]
            else:
                hn = ""

            if (hn == args.hostname) or re.match(str(i), args.hostname):
                subprocess.call([
                    "ssh", "-t", dns_entries[i]["ip-address"],
                    "sudo", "shutdown", "-h", "now"
                    ])
                exit()

    # show entries
    elif args.list is True:
        i = 0
        for ent in dns_entries:
            if "hostname" in ent:
                hn = ent["hostname"]
            else:
                hn = ""
            print("id:%s, host:%s, ipaddr:%s" % (i, hn, ent["ip-address"]))
            i += 1
        exit()

    # Login
    else:
        if args.hostname is None:
            print("VM ID or hostname is required!")
            print("See help 'sppsh -h' for details.")
            exit()

        for i in range(0, len(dns_entries)):
            # Avoid error for empty hostname
            if "hostname" in dns_entries[i]:
                hn = dns_entries[i]["hostname"]
            else:
                hn = ""

            if (hn == args.hostname) or re.match(str(i), args.hostname):
                if args.account is not None:
                    account = args.account + "@" + dns_entries[i]["ip-address"]
                else:
                    account = dns_entries[i]["ip-address"]

                subprocess.call(["ssh", account])
                exit()

        # hostname not found
        print("No such hostname: '%s'" % args.hostname)


if __name__ == '__main__':
    main()
