# SPP HDA Manager

- [What is this](#what-is-this)
- [Getting Started](#getting-started)
- [How to Use](#how-to-use)
  - [Get ISO File](#get-iso-file)
  - [Setup HDA File](#setup-hda-file)
  - [Launching VMs](#launching-vms)
    - [Network Interfaces](#network-interfaces)
    - [Usage](#usage)
    - [Examples](#examples)
    - [IVSHMEM Support](#ivshmem-support)
  - [Manage VMs](#managing-vms)
    - [Login](#login)
    - [Update Hostname](#update-hostname)
    - [Shutdown](#shutdown)

## What is this

A set of tools for managing QEMU HDA files for running
[SPP](http://dpdk.org/browse/apps/spp/).


## Getting Started

This tool set is developed and tested on Ubuntu 16.04
with the binary of qemu `qemu-system-x86_64`.
You can install qemu as following.

```sh
$ sudo apt install qemu
```

To setup a hda file, you should get an ISO image, create a hda and
install OS in the hda file. `img_creator.sh` do the tasks.

It starts downloading Ubuntu ISO image, creating hda file with
`qemu-img` and launching a VM with QEMU in graphical mode.

```sh
$ bash bin/img_creator.sh
```

You might be failed to download the ISO sometimes because it is a large
size. In this case, you should run `img_creator.sh` with `-d` option
to resume downloading.
If you retry it without `-d`, it starts to install OS using incomplete
ISO file.

```sh
# Just downloading. Enable to resume.
$ bash bin/img_creator.sh -d
```

You will find the hda file as `ubuntu-16.04.x-server-amd64.iso`
by default. `x` is the minor version number.
You can launch a VM using this hda from qemu command, or launcher script
as explained later.

## How to Use

### Get ISO File

First of all, download ISO file of Ubuntu16.04 from Ubuntu's site
to create HDA file and install.
Ubuntu 14.04 might work, but not be recommended.

To download the ISO, just run `bin/img_creator.sh -d` or get it
from [Ubuntu site](http://releases.ubuntu.com/) directly.
List of download links is described in [iso/README.md](iso/README.md).

`img_creator.sh` is a helper script for setup hda file.
It takes several options as following.
It is useful for downloading with `-d` because it is enabled to resume
if the downloading is terminated for some reasons.

- -h: Show help message
- -d: Download ISO of Ubuntu16.04
- -s: Size of HDA file (default is 10G)
- -c: Number of Cores of VM (default is 4)
- -m: Memory size of VM (default is 4096)
- -i: (optional) Path of the ISO

### Setup HDA File

Create and setup a hda file using `bin/img_creator.sh` and retrieved ISO
file.
ISO is expected to be `iso/ubuntu-16.04.x-server-amd64.iso` by default,
or you can specify any of images with `-i` option.

```sh
# Using default ISO file
$ bash bin/img_creator.sh

# or without default
$ bash bin/img_creator.sh -i /path/to/your/iso
```

This script runs qemu in graphical mode for installation.

After finishing installation, shutdown the VM by closing the window.
Do not choose restart menu because it attempts to install again.

### Launching VMs

Now is the time to launch VMs. Here is an example of qemu and detailed options for launching a VM with single vhost interface.

```sh
sudo qemu-system-x86_64
  -cpu host
  -numa node,memdev=mem
  -mem-prealloc
  -hda ./bin/../hda/instances/v1-ubuntu-16.04.x-server-amd64.qcow2
  -m 4096
  -smp cores=4,threads=1,sockets=1
  -object memory-backend-file,id=mem,size=5000M,mem-path=/dev/hugepages,share=on
  -device e1000,netdev=net_v1_0,mac=00:AD:BE:B3:01:00
  -netdev tap,id=net_v1_0,ifname=net_v1_0,script=./bin/../ifscripts/qemu-ifup.sh
  -enable-kvm
  -nographic
  -chardev socket,id=chr1,path=/tmp/sock1
  -netdev vhost-user,id=net_vu1_1,chardev=chr1,vhostforce
  -device virtio-net-pci,netdev=net_vu1_1,mac=00:AD:BE:B4:01:01
  -monitor telnet::44901,server,nowait
```

You might need to launch several VMs for your usecases.
It means that you need to define these options appropriately for each of
VMs.
You can use libvirt for the purpose, or create a shell script by your
self to avoid it.
However, it is better to use `vm-launcher.py` to manage several VMs for SPP.
It provides a simple interface to configure the params of VMs dynamically.

#### Network Interfaces

For running DPDK application on a VM, you use virtual interfaces in addition to the standard Linux bridge. 
SPP and `vm-launcher.py` support `vhost`.

DPDK had also provided `ring` interface using IVSHMEM mechanism
before v16.11,
but currently not supported.
You can use IVSHMEM if you use v16.07 and customized qemu as explained in
[Ivshmem Support](#ivshmem-support) section.

You can choose the types of virtual interfaces, vhost or ring,
while launching a VM.
All of VMs launched with `vm-launcher.py` have another standard TAP device
as a management port for ssh login.
Here is a list of supported types and `normal` just has the management port.

- vhost
- ring (not supported in latest DPDK)
- normal

#### Usage

Before running `vm-launcher.py`, you should understand how this script
manages the hda files.
It defines two types of hda, `template` and `instance`.
For several VMs, you need to prepare each of hda files as instances.
These instances are copied from one template file.

If you launch a VM with ID=1 and does not exist the instance hda file,
`vm-launcher.py` creates a new hda by copying the template and assigns
a filename of ID=1.
Here is an example of launching a VM ID=1 with vhost interface.

```sh
$ ./bin/vm-launcher.py -kvm \
  -t vhost \  # interface type
  -i 1 \      # VM ID
  -d 1 \      # vhost device ID for using /tmp/sock1
  -f hda/ubuntu-16.04.x-server-amd64.qcow2
```

Template file is also copied from the original hda created by using
`img_creator.sh` as described in previous section.

As you give an ID and the path of original hda, `vm-launcher.py` checks
the existing of hda and create new one if it does not exist.

Each of template files is prepared for each of interface types.
In this case, hda file `v1-ubuntu-16.04.x-server-amd64.qcow2` for VM ID=1
is created from template.

```sh
$ tree hda
hda
├── README.md
├── instances
│   └── v1-ubuntu-16.04.x-server-amd64.qcow2
├── templates
│   └── v0-ubuntu-16.04.x-server-amd64.qcow2
└── ubuntu-16.04.x-server-amd64.qcow2
```

As you may understand, you can launch a VM from template with `-i 0`.
If you need to launch from original

```sh
# launch from template
$ ./bin/vm-launcher.py -kvm -t vhost -i 0 ...

# launch from original
$ ./bin/vm-launcher.py -kvm -t orig ...
```

All of options are refered with `-h` option.

```sh
$ python bin/vm-launcher.py -h
usage: vm-launcher.py [-h] [-f HDA_FILE] [-q QEMU] [-i VIDS] [-t TYPE]
                      [-c CORES] [-m MEM] [-d DEV_IDS] [-vc] [--graphic]
                      [-kvm] [-nn NOF_NWIF]

Run SPP and VMs

optional arguments:
  -h, --help            show this help message and exit
  -f HDA_FILE, --hda-file HDA_FILE
                        Path of HDA file
  -q QEMU, --qemu QEMU  Path of QEMU command, default is 'qemu-system-x86_64'
  -i VIDS, --vids VIDS  VM IDs of positive number, default is '1'(exp. '1',
                        '1,2,3' or '1-3')
  -t TYPE, --type TYPE  Interface type ('normal','ring','vhost' or 'orig')
  -c CORES, --cores CORES
                        Number of cores, default is '4'
  -m MEM, --mem MEM     Memory size, default is '4096'
  -d DEV_IDS, --dev-ids DEV_IDS
                        List of vhost dev IDs such as '1,3-5'
  -vc, --vhost-client   Enable vhost-client mode, default is False
  --graphic             Enable graphic mode, default is False
  -kvm, --enable-kvm    Enable KVM for acceleration, default is False
  -nn NOF_NWIF, --nof-nwif NOF_NWIF
                        Number of network interfaces, default is '1'

```

#### Examples

You can specify the resource usages of cores, memory or device IDs
as you need.
Without giving specific options, default values are applied for.

```sh
# with specified cores, memory and vhost devs
$ ./bin/vm-launcher.py -kvm -t vhost -i 1 \
  -c 2 \
  -m 2048 \
  -d 1,2 \  # uses /tmp/sock1 and /tmp/sock2
  ...
```

You should keep in mind if the resources is adequate for your usage
because it might cause a fatal kernel panic.
For example, if you configure hugepage as 2MB x 1024, you cannot
assign less than 2048MB.

#### IVSHMEM Support

If you use IVSHMEM, you need to get a patch from
https://github.com/garogers01/soft-patch-panel to compile customized qemu.
This patch is supposed to apply for qemu-2.3.0.

```sh
$ mkdir [WORK_DIR]
$ cd  [WORK_DIR]
$ git clone https://github.com/garogers01/soft-patch-panel.git
$ cd [WORK_DIR]/qemu-2.3.0

# configure with option and make it  
$ ./configure --enable-kvm --target-list=x86_64-softmmu --enable-vhost-net
$ make
```

Compilation would take a while.
After compilation, executable `qemu-system-x86_64` is placed
in `[WORK_DIR]/qemu-2.3.0/x86_64-softmmu/`.

### Manage VMs

If you launch VMs successfully, you login to the VMs and make some operations
for install and setup for applications inside the VMs.

You can login via the management port for which IP address is already assigned.
All of IP addresses are listed in `/var/lib/libvirt/dnsmasq/virbr0.status`.
However, it is bothering to refer it everytime you login.
You can use a helper script `bin/sppsh.py` for basic operations.
This script is for managing the VMs via ssh.

#### Login

All of VMs launched with `vm-launcher.py` are referred by using `sppsh.py -l`.

```h
$ ./bin/sppsh.py -l
id:0, host:sppvm, ipaddr:192.168.122.158
id:1, host:sppvm, ipaddr:192.168.122.199
...
```

You can login to each of VM with `id`, `host` or `ipaddr`.
This examples assume that the account on host is the same as the user on the VM.

```sh
# Login to id:0 on which the account `hoge` is the same as on host
$ ./bin/sppsh.py 0
hoge@192.168.122.158s password:
...
```

If you setup the name of account on the VM, you can use `-a` option for specifying
the account directly.

```sh
# If you login to id:0 as a user `fuga`
$ ./bin/sppsh.py 0 -a fuga
fuga@192.168.122.158s password:
...
```

You can also specify the hostname.

```sh
$ ./bin/sppsh.py sppvm
hoge@192.168.122.158s password:
...
```

However, you cannot use IP address for the script. You should use ssh command instead of
`sppsh.py`.

```sh
# Not OK for using IP address
$ ./bin/sppsh.py 192.168.122.158
No such hostname: '192.168.122.158'

# It is OK with ssh command
$ ssh 192.168.122.158
hoge@192.168.122.158s password:
...
```

#### Update Hostname

In general, it is better to assign to give the specific hostname for each of VMs to
identify.
Instance hda files are copied from copied and they have the same name as the template.
It is not useful if you manage several VMs.
For such a kind of situation, You can update the hostname with `-u` option.

```sh
$ ./bin/sppsh.py -u 192.168.122.158 NEW_HOSTNAME
```

#### Shutdown

You might need to shutdown for one or all of VMs.

```sh
# Shutdown with specific ID.
$ ./bin/sppsh.py --shutdown 0

# or all of VMs.
$ ./bin/sppsh.py --shutdown-all
```
