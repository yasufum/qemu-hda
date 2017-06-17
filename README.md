# SPP VM Manager

- [What is this](#what-is-this)
- [How to use](#how-to-use)
  - [Get ISO file](#get-iso-file)
  - [Create VM image](#create-vm-image)
- [Install QEMU](#install-qemu)
- [Run VM](#run-vm)


## What is this

Tools for creating and running a VM for
[SPP](http://dpdk.org/browse/apps/spp/).


## How to use

### Get ISO file

First, download a ISO file form Ubuntu's web page
to create HDA file and install Linux using the ISO file.
Links are listed in [iso/README.md](iso/README.md).


### Create VM image

Put the ISO file you download into iso/ directory to be refered
the from script.

Then, move to iso/ and edit, run `img_creator.sh` script.
There are four params in the script.
  - HDA: name of image file of VM.
  - ISO: name of ISO you downloaded.
  - FORMAT: format type of image file. qcow2 is better if you use KVM.
  - HDASIZE: size of image file, 10G is adequate for ubuntu server.

Run the script as following.

```sh
$ bash img_creator.sh
```

After run the script, QEMU opens another window for installation.
So, you install Ubuntu by following the instructions.

Finally, shutdown OEMU's window after finished installation by clicking close button of the window.
If you choose restart inside the window without close, QEMU attempts installation again.


### Install QEMU

Before run VM using this tool, you have to setup specialized qemu
for running DPDK with IVSHMEM.
Currently it's included in repository of
previous version of SPP (https://github.com/garogers01/soft-patch-panel).

#### Get source

Create a directory for download and get source from the repository.

```
$ mkdir [WORK_DIR]
$ cd  [WORK_DIR]
$ git clone https://github.com/garogers01/soft-patch-panel.git
```

#### Compile

Move to `[WORK_DIR]` and run make command for compilation.

```
$ cd [WORK_DIR]/qemu-2.3.0
$ ./configure --enable-kvm --target-list=x86_64-softmmu --enable-vhost-net
$ make
```

It would take a while to compile QEMU.
Compiled executable `qemu-system-x86_64` is placed in `[WORK_DIR]/qemu-2.3.0/x86_64-softmmu/`.


### Run VM

Now you can run VM of the image you created by using QEMU command.
However, you had better to use run scripts as following than input command and options by hand.

#### Setup

First, copy image file into runscript/ which you created by running `iso/img_creator.sh` in section (2).
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
