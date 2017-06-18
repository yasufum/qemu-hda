# QEMU HDA Manager for SPP

- [What is this](#what-is-this)
- [How to use](#how-to-use)
  - [Install QEMU](#install-qemu)
  - [Get ISO file](#get-iso-file)
  - [Create VM image](#create-vm-image)
- [Run VM](#run-vm)


## What is this

Tools for creating HDA file and running a VM for
[SPP](http://dpdk.org/browse/apps/spp/).


## How to use

### Install QEMU

If you use IVSHMEM, you need to get a custom version of QEMU from
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

First, download a ISO file of Ubuntu16.04 form Ubuntu's site
to create HDA file and install Linux using the ISO file.
Ubuntu 14.04 might work but not be recommended.

Run `iso/img_creator.sh -d` to download the ISO file or download it
from Ubuntu site.
Links are listed in [iso/README.md](iso/README.md).

`img_creator.sh` is a helper script for setup a VM image.
It takes options as following.

- h: Show help message
- d: Download ISO of Ubuntu16.04
- s: Size of HDA file (default is 8G)
- c: Number of Cores of VM (default is 4)
- m: Memory size of VM (default is 4096)
- i: (optional) Path of the ISO

### Create VM image

Run `iso/img_creator.sh` to boot the VM with QEMU.
This script assumes that ISO is stored as
"iso/ubuntu-16.04.2-server-amd64.iso" or you give `-i`
with path of ISO if you put other path or rename it.

```sh
$ bash iso/img_creator.sh
```

After run the script, QEMU opens another window for installation.

Finally, shutdown OEMU's window after finished installation by clicking
close button of the window.
If you choose restart inside the window without close, QEMU attempts
installation again.


### Run VM

Now you can run VM using your image with QEMU.
However, you had better to use run scripts as following than input command
and options by hand.

#### Setup

First, copy image file into runscript/ which you created by `iso/img_creator.sh`.
Then, you edit `runscript/run-vm.py` to identify your image from the script.
You also edit the location of qemu executable.
Each of them are defined as following params in the scripts.
  - QEMU: location of specialized QEMU's exec file.
  - HDA: image file you created.

#### Usage

You are ready to run VM.
But before run the script, you have to consider which type of SPP interfaces
you use, or don't use.
SPP supports two types of interface, `ring` and `vhost` to communicate with VMs.
Please refer [setup guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md) of SPP for details.

You have to give a type with `-t` option.
There three types.
For `none` type, the script run from HDA and doesn't use SPP interface.

  - ring
  - vhost
  - none

To refer help message, run the script with `-h` option.

```sh
$ ./run-vm.py -h
usage: run-vm.py [-h] [-i VIDS] [-t TYPE] [-c CORES] [-m MEM]

Run SPP and VMs

optional arguments:
  -h, --help            show this help message and exit
  -i VIDS, --vids VIDS  VM IDs
  -t TYPE, --type TYPE  Interface type ('ring','vhost' and 'none')
  -c CORES, --cores CORES
                        Number of cores
  -m MEM, --mem MEM     Memory size
```

You can run one or more VMs at once with `-i` option which is for VM IDs.
You have to give at least one VM ID.

```sh
# one ring VM 
$ ./run-vm.py -t ring -i 5

# two vhost VMs
$ ./run-vm.py -t vhost -i 11,12

# three ring VMs 
$ ./run-vm.py -t ring -i 5,6,7
# or 
$ ./run-vm.py -t ring -i 5-7
# or 
$ ./run-vm.py -t ring -i 5,6-7
```

For `none` type, you can only one VM and VM ID is discarded (but required).

```sh
$ ./run-vm.py -t none -i 99

# Error because giving several IDs
$ ./run-vm.py -t none -i 98,99
Error: You use only one VM with type 'none'
```
