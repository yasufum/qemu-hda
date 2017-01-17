### What is this?

Setup tools for creating and running VMs for SPP.


### How to use

#### (1) Get ISO file

This tools support Ubuntu (I've tested only 16.04, but 14.04 possibly run).
Download ISO file form Ubuntu's web page.
URLs are listed in [iso/iso-list.txt](iso/iso-list.txt).


#### (2) Create VM image

Put ISO file you downloaded into iso/ directory to be refered
the from script.

Then, move to iso/ and edit, run `img_creator.sh` script.
There are four params in the script.
  - HDA: name of image file of VM.
  - ISO: name of ISO you downloaded.
  - FORMAT: format type of image file. qcow2 is better if you use KVM.
  - HDASIZE: size of image file, 10G is adequate for ubuntu server.

Run the script as following.

```
$ bash img_creator.sh
```

After run the script, QEMU opens another window for installation.
So, you install Ubuntu by following the instructions.

Finally, shutdown OEMU's window after finished installation by clicking close button of the window.
If you choose restart inside the window without close, QEMU attempts installation again.


#### (3) Setup QEMU

Before run VM using this tool, you have to setup specialized qemu
for running DPDK with IVSHMEM.
Currently it's included in repository of
previous version of SPP (https://github.com/garogers01/soft-patch-panel).

##### 3-1 Get source

Create a directory for download and get source from the repository.

```
$ mkdir [WORK_DIR]
$ cd  [WORK_DIR]
$ git clone https://github.com/garogers01/soft-patch-panel.git
```

##### 3-2 Compile

Move to `[WORK_DIR]` and run make command for compilation.

```
$ cd [WORK_DIR]/qemu-2.3.0
$ ./configure --enable-kvm --target-list=x86_64-softmmu --enable-vhost-net
$ make
```

It would take a while to compile QEMU.
Compiled executable `qemu-system-x86_64` is placed in `[WORK_DIR]/qemu-2.3.0/x86_64-softmmu/`.


#### (4) Run VM

Now you can run VM of the image you created by using QEMU command.
But, you had better to use run scripts as following than input command and options by hand.

First, copy image file into runscript/ which you created by running img_creator.sh in section (2).

There are two scripts for running VM, ring.sh and vhost.sh, for your purpose (You might find other scripts in runscript/, but don't need to notice now).
SPP supports two types of resources to communicate with VMs.
Please refer [setup guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md) of SPP for details.

Edit the script for your environment.
There are several params in the scripts.
  - QEMU: location of specialized QEMU's exec file.
  - HDA: image file you created.

Finally, run the script with VM ID (1-9) to identify them.
If you don't add it, default (1) is used.

For convenience, `vhost.sh` assign sock interface as `$VM_ID` + 2.
If you give VM ID 3, `/tmp/sock12` is assigned. 

```
# ring interface
$ bash ring.sh 1

# vhost interface
$ bash vhost.sh 1
# /tmp/sock11 is assigned for VM_ID=1.
```
