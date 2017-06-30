# QEMU HDA Manager for SPP

- [What is this](#what-is-this)
- [How to use](#how-to-use)
  - [Install QEMU](#install-qemu)
    - [DPDK and IVSHMEM](#dpdk-and-ivshmem)
  - [Get ISO file](#get-iso-file)
  - [Create VM image](#create-vm-image)
- [Run VM](#run-vm)


## What is this

Tools for creating HDA file and running a VM for
[SPP](http://dpdk.org/browse/apps/spp/).


## How to use

### Install QEMU

This tool is tested only for qemu-2.3.0 (might work for 2.4.0).
Options might be invaid for version 2.5 or later.

#### DPDK and IVSHMEM

If you use DPDK with IVSHMEM, you need to get a custom version of QEMU from
https://github.com/garogers01/soft-patch-panel.
Currently, it only supports qemu-2.3.0.

Skip this section if you don't use customized QEMU.

Clone the source in any directory and setup it with options.

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


### Get ISO file

First, download ISO file of Ubuntu16.04 from Ubuntu's site
to create HDA file and install Linux using the ISO file.
Ubuntu 14.04 might work but not be recommended.

Run `iso/img_creator.sh -d` to download the ISO file or download it
from Ubuntu site.
Links are listed in [iso/README.md](iso/README.md).

`img_creator.sh` is a helper script for setup a VM image.
It takes options as following.

- -h: Show help message
- -d: Download ISO of Ubuntu16.04
- -s: Size of HDA file (default is 8G)
- -c: Number of Cores of VM (default is 4)
- -m: Memory size of VM (default is 4096)
- -i: (optional) Path of the ISO

### Create VM image

Run `iso/img_creator.sh` to boot the VM with QEMU.
This script assumes that ISO is stored as
"iso/ubuntu-16.04.2-server-amd64.iso".
You can give the path with `-i` option
if you put other path or rename it.

If 'img_creator.sh` cannot find ISO, it starts downloading before installation.

```sh
$ bash iso/img_creator.sh
```

After run the script, QEMU opens another window for installation.

Finally, shutdown OEMU's window after finished installation by clicking
close button of the window.
If you choose restart inside the window without close, QEMU attempts
installation again.


### Run VMs

`run-vm.py` is a helper script for running VMs for SPP.

#### Usage

Before run the script, you have to consider which type of SPP interfaces
you use.
SPP supports two types of interface, `ring` and `vhost` to communicate with VMs.
Please refer
[setup guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md)
of SPP for details.
You can also run VMs without SPP interface.

You have to give the path of HDA and interface type while running
the script.

First time you run the scirpt, it creates copies of HDA in
`runscripts/template/`.
Template file is a kind of parent images of each of VMs.
Each of VMs is launched using child of template file.
Install SPP and setup for each each of interfaces.

Image file is named as `r0-ubuntu-16.04.2-server-amd64.qcow2`
which means "(type-prefix)(vid)-(original-hda-filename)".
Template is assigned the number 0 for vid.

If template exists, `run-vm.py` copies image from template for launching VM.

```
runscripts/
      |--template/r0-ubuntu-16.04.2-server-amd64.qcow2
      |--img/
          |--r1-ubuntu-16.04.2-server-amd64.qcow2
          |--r2-ubuntu-16.04.2-server-amd64.qcow2
          |-- ...
```

There are four types, `normal`, `ring`, `vhost` and `orig`. 
`ring` and `vhost` are SPP interfaces.
On the other hand, `normal` runs VMs without SPP interfaces.
`orig` type is for using original HDA to update itself.

To refer help message, run the script with `-h` option.

```sh
$ ./run-vm.py -h
usage: run-vm.py [-h] [-f HDA_FILE] [-q QEMU] [-i VIDS] [-t TYPE] [-c CORES]
                 [-m MEM] [-vn VHOST_NUM] [-nn NOF_NWIF]

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
                        Number of cores, default is '2'
  -m MEM, --mem MEM     Memory size, default is '2048'
  -vn VHOST_NUM, --vhost-num VHOST_NUM
                        Number of vhost interfaces, default is '1'
  -nn NOF_NWIF, --nof-nwif NOF_NWIF
                        Number of network interfaces, default is '1'
```

You can run one or more VMs at once with `-i` option which is for VM IDs.
You have to give at least one VM ID.

```sh
# one ring VM 
$ ./run-vm.py -t ring -i 5 -h [HDA]

# two vhost VMs
$ ./run-vm.py -t vhost -i 11,12 -h [HDA]

# three ring VMs 
$ ./run-vm.py -t ring -i 5,6,7 -h [HDA]
# or 
$ ./run-vm.py -t ring -i 5-7 -h [HDA]
# or 
$ ./run-vm.py -t ring -i 5,6-7 -h [HDA]
```

For `none` type, you can only one VM and VM ID is discarded (but required).

```sh
$ ./run-vm.py -t none -i 99

# Error because giving several IDs
$ ./run-vm.py -t none -i 98,99
Error: You use only one VM with type 'none'
```
